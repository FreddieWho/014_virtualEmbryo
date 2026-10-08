"""E14.5-only terminal-rank Hermite model. Does not open external E9.5."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ.setdefault(k,'2')
import argparse,json,pickle,sys
from pathlib import Path
import numpy as np,pandas as pd,anndata as ad
from scipy.stats import rankdata
from scipy.spatial.distance import cdist
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import flow
R=flow.ROOT

def fit_endpoint(path):
 # Caller must pass source-audited E14.5 CM-enriched mixed bins only.
 p=Path(path); assert '14.5' in p.name or 'e145' in str(p).lower(), 'stage-separated endpoint path required'
 permit_path=p.parent/'T2_DATA_PERMIT.json';permit=json.loads(permit_path.read_text())
 assert permit['status']=='ALLOW_E145_ONLY_RAW_SPATIAL_ENDPOINT' and permit['model_input_allowed'] and permit['stage']==14.5
 match=[r for r in permit['model_artifacts'] if Path(r['path']).resolve()==p.resolve()]
 assert len(match)==1 and match[0]['sha256']==flow.sha(p), 'endpoint source permit/hash mismatch'
 ext=ad.read_h5ad(p)
 genes=[str(g) for g in ext.var_names];assert genes==flow.PANEL.read_text().splitlines()
 assert 'stage' in ext.obs and all(str(v) in ('14.5','E14.5') for v in ext.obs['stage']), 'wrong stage metadata'
 measured=np.asarray(ext.var['measured_in_source'],bool);assert measured.shape==(500,) and measured.sum()>=200
 counts=flow.dense(ext.X).astype(np.float64);assert counts.ndim==2 and counts.shape[1]==500
 assert np.isfinite(counts).all() and np.min(counts)>=0 and np.max(np.abs(counts-np.rint(counts)))<1e-6
 common=np.flatnonzero(measured);counts=counts[:,common];keep=counts.sum(1)>0;counts=counts[keep]
 assert len(counts)>=16,'insufficient endpoint cardiac bins'
 normalized=counts*10000/counts.sum(1,keepdims=True);x=np.log1p(normalized)
 k=min(32,len(counts)//8)
 pca=PCA(n_components=min(32,len(counts)-1,len(common)),svd_solver='randomized',random_state=flow.SEED).fit(x)
 labels=KMeans(n_clusters=k,n_init=5,random_state=flow.SEED).fit_predict(pca.transform(x))
 means=np.stack([normalized[labels==j].mean(0) for j in range(k)])
 ranks=(rankdata(means,axis=1,method='average')-1)/(len(common)-1)
 return {'common_indices':common,'endpoint_ranks':ranks,'endpoint_raw_means':means,'bin_counts':np.bincount(labels,minlength=k),'external_path':str(p),'external_sha':flow.sha(p),'n_bins':len(counts),'pca':pca,'gene_panel_sha':flow.sha(flow.PANEL),'source_kind':'E14.5 Stereo-seq CM-enriched mixed spatial bins','permit_sha':flow.sha(permit_path)}

def source_model(e,l):
 x,y=flow.dense(e.X),flow.dense(l.X);te=e.obs.celltype.astype(str).to_numpy();tl=l.obs.celltype.astype(str).to_numpy();d={}
 for s in sorted(set(te)&set(tl)):
  if min(np.sum(te==s),np.sum(tl==s))>=16:d[s]=np.median(y[tl==s],axis=0)-np.median(x[te==s],axis=0)
 return d

def recipe(carrier,med):
 x=flow.dense(carrier.X);out=x.copy();t=carrier.obs.celltype.astype(str).to_numpy();lib=np.expm1(x.astype(float)).sum(1)
 for s,d in med.items():
  ix=np.flatnonzero(t==s);out[ix]=flow.normalize(x[ix]+.9*d,lib[ix])
 return out

def predict(carrier,m,mode):
 x=flow.dense(carrier.X);base=recipe(carrier,m['median_deltas']);out=base.copy();types=carrier.obs.celltype.astype(str).to_numpy();eligible=np.array(['CM' in s for s in types]);ix=np.flatnonzero(eligible);common=m['endpoint']['common_indices'];xc=x[np.ix_(ix,common)].astype(float)
 endpoint=m['endpoint']['endpoint_ranks'].copy()
 if mode=='endperm':endpoint=endpoint[:,np.random.default_rng(flow.SEED).permutation(len(common))]
 ranks=(rankdata(xc,axis=1,method='average')-1)/(len(common)-1)
 if mode=='endfree':target=xc.copy();nearest=None
 else:
  cost=cdist(ranks,endpoint,'sqeuclidean');idx=np.argsort(cost,axis=1)[:,:min(8,len(endpoint))];d=np.take_along_axis(cost,idx,axis=1);bw=np.maximum(np.median(d,axis=1,keepdims=True),1e-12);w=np.exp(-(d-d[:,:1])/bw);w/=w.sum(1,keepdims=True)
  rq=np.sum(w[:,:,None]*endpoint[idx],axis=1);q=np.clip(rq,0,1)*(len(common)-1);lo=np.floor(q).astype(int);hi=np.minimum(lo+1,len(common)-1);a=q-lo;sx=np.sort(xc,axis=1)
  target=(1-a)*np.take_along_axis(sx,lo,axis=1)+a*np.take_along_axis(sx,hi,axis=1);nearest=idx[:,0]
 H=m['endpoint_time']-m['late_time'];h=m['target_time']-m['late_time'];u=h/H
 q=3*u*u-2*u*u*u;coef=H*(u**3-2*u*u+u)/(m['late_time']-m['early_time'])
 delta=np.zeros_like(xc)
 for s,d in m['median_deltas'].items():delta[types[ix]==s]=d[common]
 y=xc+coef*delta+q*(target-xc)
 # Only common genes are reprojected; excluded genes remain recipe-exact.
 raw=np.expm1(np.maximum(y,0));targetlib=np.expm1(base[np.ix_(ix,common)].astype(float)).sum(1)
 y=np.log1p(raw*targetlib[:,None]/np.maximum(raw.sum(1,keepdims=True),1e-20)).astype(np.float32)
 out[np.ix_(ix,common)]=y
 audit={'eligible_cm_rows':len(ix),'eligible_labels':sorted(set(types[ix])),'common_genes':len(common),'endpoint_weight':q,'source_delta_coefficient':coef,'changed_value_fraction':float(np.mean(out!=base)),'mean_abs_delta_vs_recipe':float(np.mean(np.abs(out-base))),'external_gene_missing_not_changed':bool(np.array_equal(out[:,np.setdiff1d(np.arange(500),common)],base[:,np.setdiff1d(np.arange(500),common)])),'non_cm_recipe_exact':bool(np.array_equal(out[~eligible],base[~eligible]))}
 return out,audit

def build(split,external):
 d=R/split;d.mkdir(exist_ok=True);en,ln,times=('E8.25_late','E8.75',(8.25,8.75,9.5)) if split=='dev' else ('E8.75','E9.5',(8.75,9.5,10.5))
 e,l=flow.load(en),flow.load(ln);m={'endpoint':fit_endpoint(external),'median_deltas':source_model(e,l),'early_time':times[0],'late_time':times[1],'target_time':times[2],'endpoint_time':14.5,'source_hashes':{s:flow.sha(flow.DATA/(s+'.h5ad'))for s in [en,ln]}}
 mp=d/'endpoint_model.pkl';assert not mp.exists();mp.write_bytes(pickle.dumps(m,protocol=5))
 if split=='dev':carrier=l
 else:
  sys.path.insert(0,'/workspace/shared/t3repo');from scripts.t2_pseudo_holdout import select_indices
  ix=select_indices(l.obs.celltype.astype(str).to_numpy(),n_cells=25179,seed=20260821);carrier=l[ix].copy()
  pd.DataFrame({'out_row':np.arange(len(ix)),'source_row':ix,'obs_name':carrier.obs_names}).to_csv(d/'source_row_ledger.tsv',sep='\t',index=False)
 for mode in ['endpoint','endfree','endperm']:
  out,audit=predict(carrier,m,mode);meta={'method':mode+'_cardiac_rank_hermite','model_sha':flow.sha(mp),'code_sha':flow.sha(__file__),'external_sha':m['endpoint']['external_sha'],'source_hashes':m['source_hashes'],'prediction_target_used':False,'terminal_zero_velocity_is_regularizing_assumption':True}
  artifact=flow.save(carrier,out,d/(mode+'.h5ad'),meta);flow.dump(d/(mode+'_audit.json'),{'artifact':artifact,'diagnostics':audit});print(mode,audit,flush=True)
 if split=='final':flow.save(carrier,recipe(carrier,m['median_deltas']),d/'endpoint_recipe.h5ad',{'method':'reconstructed_source_recipe_not_exact_historical_v30'})

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('split',choices=['dev','final']);p.add_argument('--external',required=True);a=p.parse_args();build(a.split,a.external)
