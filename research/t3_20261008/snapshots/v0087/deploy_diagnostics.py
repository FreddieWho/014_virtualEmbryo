import os
for v in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[v]='2'
import sys,json,hashlib
from pathlib import Path
import numpy as np,pandas as pd,anndata as ad
from threadpoolctl import threadpool_limits
threadpool_limits(2)
from crossko_hurdle_v2 import CrossKOHurdle as CrossKO
sys.path.insert(0,'/workspace/shared/t3repo/third_party/veckit');from common import core_metrics as cm
P=Path(__file__).parent;S=P/'crossko7_hurdle_v2_results';O=P/'deployment_diagnostics';O.mkdir(exist_ok=True)
selection=json.loads((S/'SELECTION.json').read_text());eligible=[x for x in selection['criteria'] if x['passes']];assert eligible,'No source-eligible method';chosen=sorted(eligible,key=lambda x:(-x['mean_direction'],x['mse']))[0]['model'];method,mode=chosen.split('_');data={}
for gene in ['WT','Dnmt3a','Kmt2a','Kdm2b','Dnmt1','Dnmt3b','Ehmt2','Kmt2b']:
 a=ad.read_h5ad(S/f'{gene}_whitelisted_panel10000.h5ad');data[gene]=(a.X,a.obs)
wt,wo=data['WT'];rng=np.random.default_rng(711);controls={}
for sex in wo.sex.unique():
 blocks=[]
 for e in wo.loc[wo.sex==sex,'embryo'].unique():
  ix=np.flatnonzero((wo.sex==sex)&(wo.embryo==e));blocks.append(wt[rng.choice(ix,500,replace=len(ix)<500)])
 controls[sex]=np.concatenate(blocks)
records=[]
for gene,(x,o) in data.items():
 if gene=='WT':continue
 for e in sorted(o.embryo.unique()):
  mask=o.embryo==e;sex=o.loc[mask,'sex'].iloc[0];records.append(dict(gene=gene,sample_unit=e,unit_kind='embryo',control=controls[sex],ko=x[mask]))
e=np.load('/workspace/shared/t3_observation_reset/go_expanded7/GO_EXPANDED_EMBEDDING.npz');priors=dict(zip(e['genes'].astype(str),e['embedding']));model=CrossKO(states=8,min_cells=10).fit_atlas(wt).fit_interventions(records,priors,'Gata4');z=model.pca.transform(wt);sl=model.km.predict(z);dist=np.linalg.norm(z-model.km.cluster_centers_[sl],axis=1);threshold=np.array([np.quantile(dist[sl==i],.95) for i in range(8)]);response=model.predict('Gata4',method);predictions={};receipts=[]
for name,stage in [('mab','E9.5'),('gata4','E8.75')]:
 response=model.predict('Mab21l2' if name=='mab' else 'Gata4',method)
 a=ad.read_h5ad('/workspace/shared/virtual_embryo_data/'+stage+'.h5ad');X=a.X.toarray() if hasattr(a.X,'toarray') else np.asarray(a.X);ix=np.sort(np.random.default_rng(20260904).choice(len(X),7449,replace=False));base=X[ix].copy();obs=a.obs.iloc[ix].copy();state=model.assign(base);zz=model.pca.transform(base);dd=np.linalg.norm(zz-model.km.cluster_centers_[state],axis=1);outside=dd>threshold[state];supported=response['support'][state]
 lineage=obs.celltype.astype(str).isin(['V-CM','IFT-CM','HEM-Endoth','Intra-Endoth-1','Intra-Endoth-2']).to_numpy()|obs.cm_celltype.astype(str).isin(['vCM1','vCM2','aCM1','aCM2','OFT/RV-CM','aSHF','pSHF']).to_numpy()
 for variant,mask in [('all_supported',supported)]+([('positive_lineage',supported&lineage)] if name=='gata4' else []):
  pred=base.copy();pred[mask]=model.emit(base[mask],response,mode=mode)[0];out=ad.AnnData(pred,obs=obs,var=a.var.copy());out.obsm['spatial_3D']=np.asarray(a.obsm['spatial_3D'])[ix].copy();out.uns['scope']='Experimental seven-KO developmental prior; not target causal evidence; no hidden target outcomes';out.uns['source_method']=chosen;out.uns['source_genes']=model.training_genes;out.uns['RNA_knockout_forced']=False;out.uns['provenance']='GSE137337 seven permitted E8.5 epigenetic KO identities; GSE122187 WT; original publisher SNP embryo whitelists; seven-gene source leave-intervention-out';file=O/f'{name}_{variant}.h5ad';out.write_h5ad(file,compression='gzip');r=ad.read_h5ad(file);assert np.array_equal(r.X,pred) and np.array_equal(r.var_names,a.var_names);assert np.array_equal(r.X[~mask],base[~mask]);assert np.isfinite(r.X).all() and (r.X>=0).all();assert np.isfinite(r.obsm['spatial_3D']).all();assert np.max(abs(np.expm1(pred.astype(float)).sum(1)-10000))<.02
  delta=pred.mean(0,dtype=float)-base.mean(0,dtype=float);row=dict(stage=name,variant=variant,source_method=chosen,mask_cells=int(mask.sum()),changed_cells=int(np.any(pred!=base,axis=1).sum()),outside95_cells=int(outside.sum()),changed_outside95=int(np.any(pred!=base,axis=1)[outside].sum()),detection=float((pred>0).mean()),base_detection=float((base>0).mean()),zero_to_positive=int(((base==0)&(pred>0)).sum()),positive_to_zero=int(((base>0)&(pred==0)).sum()),delta_L2=float(np.linalg.norm(delta)),max_log_change=float(abs(pred-base).max()),delta_on_outside95_L2=float(np.linalg.norm((pred[outside]-base[outside]).mean(0))) if outside.any() else 0,sha256=hashlib.sha256(file.read_bytes()).hexdigest(),file=str(file));receipts.append(row);predictions[name+'_'+variant]=pred
  pd.DataFrame(dict(gene=a.var_names,WT_mean=base.mean(0),pred_mean=pred.mean(0),delta=delta,WT_detection=(base>0).mean(0),pred_detection=(pred>0).mean(0))).to_csv(O/f'{name}_{variant}_gene_changes.csv',index=False)
  if name=='gata4':pd.DataFrame(dict(celltype=obs.celltype,cm_celltype=obs.cm_celltype,state=state,outside95=outside,lineage=lineage,in_gate=mask,changed=np.any(pred!=base,axis=1))).to_csv(O/f'{name}_{variant}_row_provenance.csv',index=False)
 if name=='mab':mab_reference=X;mab_base=base
# Persist frozen prediction hashes before outcome load.
(O/'PREDICTIONS_FROZEN.json').write_text(json.dumps(dict(selected_by_source=chosen,source_selection=selection,training_genes=model.training_genes,protocol_sha256=hashlib.sha256((P/'DEPLOYMENT_DIAGNOSTIC_PROTOCOL.md').read_bytes()).hexdigest(),code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),emitter_sha256=hashlib.sha256((P/'crossko_hurdle_v2.py').read_bytes()).hexdigest(),predictions=receipts,Mab_outcome_loaded=False,Gata_outcome_loaded=False),indent=2));print(json.dumps(receipts,indent=2),flush=True)
ko=ad.read_h5ad('/workspace/shared/virtual_embryo_data/E9.5_mab21l2_ko.h5ad');truth=ko.X.toarray() if hasattr(ko.X,'toarray') else np.asarray(ko.X);metrics=[]
for name,pred in [('WT',mab_base),('sevenKO_hurdle',predictions['mab_all_supported']),('historical_adult',np.load('/workspace/shared/t3new_20261008/mab_anchored_v2.npy'))]:
 s,r2=cm.severity_slope(pred,truth,mab_reference);metrics.append(dict(model=name,de=cm.de_score(pred,truth,mab_reference)['score'],direction=cm.de_direction(pred,truth,mab_reference),severity_abs=abs(s),severity_r2=r2,mmd=cm.mmd_unbiased(pred,truth,seed=0),variogram=cm.variogram_score(pred,truth,seed=0),mse=float(np.mean((pred.mean(0,dtype=float)-truth.mean(0,dtype=float))**2))));print(metrics[-1],flush=True)
(O/'MAB_EXTERNAL_DIAGNOSTIC.json').write_text(json.dumps(metrics,indent=2));(O/'COMPLETE.json').write_text(json.dumps(dict(status='completed',no_hidden_outcomes=True,no_submission=True,diagnostic_artifacts=3),indent=2))
