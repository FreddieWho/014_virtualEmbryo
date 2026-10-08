import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ.setdefault(k,'2')
import sys,pickle,json
from pathlib import Path
import numpy as np,anndata as ad
from scipy.stats import rankdata
from scipy.spatial.distance import cdist
import endpoint_flow as ef
import flow
R=flow.ROOT

def predict(carrier,m,permuted=False):
 x=flow.dense(carrier.X);base=ef.recipe(carrier,m['median_deltas']);out=base.copy();types=carrier.obs.celltype.astype(str).to_numpy();eligible=np.array(['CM' in s for s in types]);ix=np.flatnonzero(eligible);common=m['endpoint']['common_indices'];xc=x[np.ix_(ix,common)].astype(float)
 endpoint=m['endpoint']['endpoint_ranks'].copy()
 if permuted:endpoint=endpoint[:,np.random.default_rng(flow.SEED).permutation(len(common))]
 ranks=(rankdata(xc,axis=1,method='average')-1)/(len(common)-1);cost=cdist(ranks,endpoint,'sqeuclidean');idx=np.argsort(cost,axis=1)[:,:min(8,len(endpoint))];d=np.take_along_axis(cost,idx,axis=1);bw=np.maximum(np.median(d,axis=1,keepdims=True),1e-12);w=np.exp(-(d-d[:,:1])/bw);w/=w.sum(1,keepdims=True)
 rq=np.sum(w[:,:,None]*endpoint[idx],axis=1);qidx=np.clip(rq,0,1)*(len(common)-1);lo=np.floor(qidx).astype(int);hi=np.minimum(lo+1,len(common)-1);a=qidx-lo;sx=np.sort(xc,axis=1);target=(1-a)*np.take_along_axis(sx,lo,axis=1)+a*np.take_along_axis(sx,hi,axis=1)
 u=(m['target_time']-m['late_time'])/(m['endpoint_time']-m['late_time']);q=3*u*u-2*u*u*u
 b=base[np.ix_(ix,common)].astype(float);y=b+q*(target-xc);raw=np.expm1(np.maximum(y,0));lib=np.expm1(b).sum(1);y=np.log1p(raw*lib[:,None]/np.maximum(raw.sum(1,keepdims=True),1e-20)).astype(np.float32);out[np.ix_(ix,common)]=y
 diag={'eligible_cm_rows':len(ix),'eligible_labels':sorted(set(types[ix])),'common_genes':len(common),'endpoint_coefficient':q,'source_recipe_drift_unchanged':True,'changed_fraction':float(np.mean(out!=base)),'mean_abs_diff_vs_recipe':float(np.mean(np.abs(out-base))),'non_cm_exact':bool(np.array_equal(out[~eligible],base[~eligible])),'missing_gene_exact':bool(np.array_equal(out[:,np.setdiff1d(np.arange(500),common)],base[:,np.setdiff1d(np.arange(500),common)]))}
 return out,diag

def build(split):
 d=R/split;mp=d/'endpoint_model.pkl';m=pickle.loads(mp.read_bytes());l=flow.load('E8.75' if split=='dev' else 'E9.5')
 if split=='final':
  sys.path.insert(0,'/workspace/shared/t3repo');from scripts.t2_pseudo_holdout import select_indices
  ix=select_indices(l.obs.celltype.astype(str).to_numpy(),n_cells=25179,seed=20260821);carrier=l[ix].copy()
 else:carrier=l
 for lane,permuted in [('endmatched',False),('endmatchedperm',True)]:
  x,diag=predict(carrier,m,permuted);art=flow.save(carrier,x,d/(lane+'.h5ad'),{'method':'fixed_drift_endpoint_rank_residual','endpoint_permuted':permuted,'endpoint_model_sha':flow.sha(mp),'code_sha':flow.sha(__file__),'model_selection':'adaptive ablation after Hermite confound; no held-stage data in fit','external_E95_used':False});flow.dump(d/(lane+'_audit.json'),{'artifact':art,'diagnostics':diag});print(lane,diag,flush=True)
if __name__=='__main__':build(sys.argv[1])
