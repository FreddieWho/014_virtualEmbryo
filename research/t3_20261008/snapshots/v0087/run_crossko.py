import os
for x in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[x]='2'
import sys,json,hashlib,time
from pathlib import Path
import numpy as np,pandas as pd,anndata as ad
from threadpoolctl import threadpool_limits
threadpool_limits(2)
from crossko import CrossKO
sys.path.insert(0,'/workspace/shared/t3repo/third_party/veckit');from common import core_metrics as cm
P=Path(__file__).parent;A=Path('/workspace/shared/t3_developmental_sources/annotations');O=P/'crossko_results';O.mkdir(exist_ok=True)
def norm(x):
 s=np.asarray(x.sum(1)).ravel();assert(s>0).all();return np.log1p(x.toarray()*10000/s[:,None]).astype('float32')
data={};merge=[]
for gene in ['WT','Dnmt3a','Kmt2a','Kdm2b']:
 file=P/'source_panel'/('WT_idmatched_raw_panel.h5ad' if gene=='WT' else gene+'_raw_panel.h5ad');a=ad.read_h5ad(file);obs=pd.read_csv(A/f'{gene}_E8.5_cell_annotations.tsv',sep='\t');assert obs.barcode.is_unique;keep=obs.barcode.isin(a.obs_names);idx=a.obs_names.get_indexer(obs.loc[keep,'barcode']);sub=a[idx].copy();obs=obs.loc[keep].reset_index(drop=True);sub.obs=obs.set_index('barcode');z=norm(sub.X);data[gene]=(z,obs);merge.append(dict(gene=gene,whitelist=len(keep),matched=int(keep.sum()),missing=int((~keep).sum()),embryos=obs.embryo.nunique(),sex_embryos=obs[['embryo','sex']].drop_duplicates().sex.value_counts().to_dict(),input_sha256=hashlib.sha256(file.read_bytes()).hexdigest()));sub.X=z;sub.write_h5ad(O/f'{gene}_whitelisted_panel10000.h5ad',compression='gzip');print('loaded',gene,z.shape,flush=True)
(O/'MERGE_RECEIPT.json').write_text(json.dumps(merge,indent=2));wt,wo=data['WT'];emb=np.load('/workspace/shared/t3_observation_reset/go_expanded/GO_EXPANDED_EMBEDDING.npz');priors={str(g):v for g,v in zip(emb['genes'],emb['embedding'])};records=[]
for gene in ['Dnmt3a','Kmt2a','Kdm2b']:
 z,obs=data[gene]
 for e in sorted(obs.embryo.unique()):
  mask=obs.embryo==e;sex=obs.loc[mask,'sex'].unique();assert len(sex)==1;c=wt[wo.sex==sex[0]];records.append(dict(gene=gene,sample_unit=e,unit_kind='embryo',control=c,ko=z[mask],sex=sex[0]))
# Bind provenance before response scoring.
(O/'FROZEN.json').write_text(json.dumps(dict(protocol_sha256=hashlib.sha256((P/'CROSSKO_PROTOCOL.md').read_bytes()).hexdigest(),code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),model_sha256=hashlib.sha256((P/'crossko.py').read_bytes()).hexdigest(),GO_sha256=hashlib.sha256(Path('/workspace/shared/t3_observation_reset/go_expanded/GO_EXPANDED_EMBEDDING.npz').read_bytes()).hexdigest(),controls='sex-matched WT; equal embryo training and evaluation samples',states=8,quantiles=21,seed=241),indent=2))
rows=[];replicate=[];rng=np.random.default_rng(241)
for query in ['Dnmt3a','Kmt2a','Kdm2b']:
 z,obs=data[query];all_e=sorted(obs.embryo.unique());discovery=all_e[::2];evaluation=all_e[1::2];truth=[];control=[]
 for e in evaluation:
  rr=np.flatnonzero(obs.embryo==e);chosen=rng.choice(rr,500,replace=len(rr)<500);truth.append(z[chosen]);sex=obs.loc[rr[0],'sex'];cr=np.flatnonzero(wo.sex==sex);control.append(wt[rng.choice(cr,500,replace=False)])
 truth=np.concatenate(truth);reference=np.concatenate(control);base=reference[rng.choice(len(reference),7449,replace=True)].copy();model=CrossKO(states=8,min_cells=10).fit_atlas(wt).fit_interventions(records,priors,query);assert query not in model.training_genes
 query_discovery=[r for r in records if r['gene']==query and r['sample_unit'] in discovery];oracle_parts=[model.summarize_response(r['control'],r['ko']) for r in query_discovery];oracle={key:np.mean([r[key] for r in oracle_parts],axis=0) for key in ['delta','composition','support']};oracle['support']=oracle['support']>=.5
 preds={'identity':base};provenance={}
 for method in ['mean','nearest','ridge']:
  response=model.predict(query,method)
  for mode in ['within','combined']:
   pred,ix=model.emit(base,response,mode=mode);preds[method+'_'+mode]=pred
  provenance[method]=dict(support=response['support'].tolist(),composition=response['composition'].tolist())
 preds['known_response_oracle']=model.emit(base,oracle,mode='combined')[0]
 (O/f'{query}_MODEL.json').write_text(json.dumps(dict(training_genes=model.training_genes,discovery=discovery,evaluation=evaluation,response_info=provenance,query_prior='GO ontology only'),indent=2))
 for name,pred in preds.items():
  out=ad.AnnData(pred,var=sub.var.copy());file=O/f'{query}_{name}.h5ad';out.write_h5ad(file,compression='gzip');pred2=ad.read_h5ad(file).X;assert np.array_equal(pred,pred2);assert np.isfinite(pred).all();assert np.max(abs(np.expm1(pred.astype(float)).sum(1)-10000))<.01
  s,r2=cm.severity_slope(pred,truth,reference);row=dict(query=query,model=name,de=cm.de_score(pred,truth,reference)['score'],direction=cm.de_direction(pred,truth,reference),severity_abs=abs(s),severity_r2=r2,mmd=cm.mmd_unbiased(pred,truth,seed=0),variogram=cm.variogram_score(pred,truth,seed=0),mse=float(np.mean((pred.mean(0,dtype=float)-truth.mean(0,dtype=float))**2)),detection=float((pred>0).mean()),sha256=hashlib.sha256(file.read_bytes()).hexdigest());rows.append(row)
  # Per-biological-embryo response metric; not independent KO identities.
  for i,e in enumerate(evaluation):replicate.append(dict(query=query,model=name,embryo=e,sex=obs.loc[obs.embryo==e,'sex'].iloc[0],direction=cm.de_direction(pred,truth[i*500:(i+1)*500],reference),mse=float(np.mean((pred.mean(0,dtype=float)-truth[i*500:(i+1)*500].mean(0,dtype=float))**2))))
  pd.DataFrame(rows).to_csv(O/'metrics.csv',index=False);pd.DataFrame(replicate).to_csv(O/'embryo_metrics.csv',index=False);print(row,flush=True)
summary=pd.DataFrame(rows).groupby('model')[['de','direction','severity_abs','mmd','variogram','mse']].mean();summary.to_csv(O/'summary.csv');print(summary.to_string(),flush=True)
# Apply frozen necessary criteria only, no hidden-target metrics.
f=pd.DataFrame(rows);candidates=[]
for method in ['nearest','ridge']:
 for mode in ['within','combined']:
  name=method+'_'+mode;r=f[f.model==name].set_index('query');identity=f[f.model=='identity'].set_index('query');mean=f[f.model=='mean_'+mode].set_index('query');pass_=bool(r.direction.median()>.05 and (r.mse<identity.mse).sum()>=2 and r.direction.mean()>mean.direction.mean());candidates.append(dict(model=name,passes=pass_,mean_direction=float(r.direction.mean()),median_direction=float(r.direction.median()),mse_wins=int((r.mse<identity.mse).sum()),mean_direction_control=float(mean.direction.mean()),mse=float(r.mse.mean())))
(O/'SELECTION.json').write_text(json.dumps(dict(criteria=candidates,status='completed',no_target_outcomes=True,candidate_built=False),indent=2));print('COMPLETE',flush=True)
