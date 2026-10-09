import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS','NUMBA_NUM_THREADS'):os.environ[k]='1'
from pathlib import Path
import sys,json,argparse,hashlib
import numpy as np,anndata as ad
from scipy.stats import rankdata
from sklearn.covariance import LedoitWolf
from threadpoolctl import threadpool_info,threadpool_limits
ROOT=Path(__file__).resolve().parent;REPO=ROOT/'repo';OLD=Path('/workspace/shared/t2_operator_transfers_20261009');DATA=OLD/'data/official'
sys.path.insert(0,str(REPO/'scripts/t2_embryo_campaign_20261009'))
from runtime import initialize
from copula import gaussian_ranks,fit_conditional,regularize
V,INIT=initialize(DATA)
import t2_recipes as recipe
from types import SimpleNamespace as NS
BOARD='T2:heart:val_interp'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def reg(X,lab,B,alpha):
 Y=X.copy();lab=np.asarray(lab).astype(str)
 for s in sorted(set(lab)):
  i=np.flatnonzero(lab==s)
  if len(i)<4:continue
  z=gaussian_ranks(X[i]);rk=rankdata(z,axis=0,method='average');ck=rankdata(z@B,axis=0,method='average');key=(1-alpha)*rk+alpha*ck
  order=np.argsort(key,axis=0,kind='stable');v=np.empty_like(X[i]);np.put_along_axis(v,order,np.sort(X[i],axis=0),axis=0);Y[i]=v
 return Y

def fit_within(X,lab):
 Z=np.empty(X.shape,np.float64);lab=np.asarray(lab).astype(str)
 for s in sorted(set(lab)):
  i=np.flatnonzero(lab==s);Z[i]=gaussian_ranks(X[i])
 m=LedoitWolf().fit(Z);P=m.precision_;B=-P/np.diag(P)[None,:];np.fill_diagonal(B,0)
 return B,{'fit_cells':len(X),'groups':len(set(lab)),'shrinkage':float(m.shrinkage_),'definition':'Gaussian rank within pooled-endpoint state, one pooled LW covariance'}

def audit(base,out):
 lab=np.asarray(base.obs.celltype).astype(str)
 assert np.array_equal(np.sort(base.X,axis=0),np.sort(out.X,axis=0))
 assert all(np.array_equal(np.sort(base.X[lab==s],axis=0),np.sort(out.X[lab==s],axis=0)) for s in set(lab))
 assert np.array_equal(base.obsm['spatial_3D'],out.obsm['spatial_3D']) and base.obs.equals(out.obs) and base.var.equals(out.var)
 a=np.expm1(base.X.astype(float)).sum(1);b=np.expm1(out.X.astype(float)).sum(1)
 # Within-state signed/absolute covariance diagnostics, descriptive only.
 cor=[]
 for s in sorted(set(lab)):
  x=out.X[lab==s].astype(float)
  if len(x)<4:continue
  sd=x.std(0);good=sd>1e-8
  if good.sum()>1:
   z=(x[:,good]-x[:,good].mean(0))/sd[good];C=z.T@z/len(z);cor.append((len(z),float((np.abs(C).sum()-len(C))/(len(C)*(len(C)-1)))))
 return {'exact_state_gene_marginals':True,'same_geometry_rows_metadata':True,'mean_abs_change':float(np.abs(base.X-out.X).mean()),'changed_entry_fraction':float(np.mean(base.X!=out.X)),'library_ratio_quantiles':np.quantile(b/np.maximum(a,1e-12),[0,.01,.5,.99,1]).tolist(),'library_absolute_quantiles':np.quantile(b,[0,.01,.5,.99,1]).tolist(),'weighted_abs_within_state_gene_correlation':sum(n*c for n,c in cor)/sum(n for n,c in cor)}

def main():
 p=argparse.ArgumentParser();p.add_argument('--mode',choices=['dev','final','replay'],required=True);p.add_argument('--choice');p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
 dev=a.mode=='dev';genes=V.panel(BOARD);stages=['E8.25_late','E9.5' if dev else 'E8.75'];A=[V.load_stage(s,genes) for s in stages];X=np.vstack([z.X for z in A]);lab=np.concatenate([np.asarray(z.obs.celltype).astype(str) for z in A]);B,bmeta=fit_conditional(X)
 if dev:
  base,_=recipe.run_interp(NS(board=BOARD,left='E8.25_late:8.25',right='E9.5:9.5',target=8.75,n=5872,seed=20261008,label='celltype',carrier='left',C=2.,geometry='aniso',zero_preserve=False))
 else:
  path=OLD/'heart_interp/exact_parent_replay/T2_heart_val_interp__H1_bridgeC2_aniso.h5ad';assert sha(path)=='7cc2e31445613a7e9e13525ea3b3ce8bf386855f8df0b70d6ba47f1ae2a23a37';base=ad.read_h5ad(path)
 baseline=base.copy();baseline.X=reg(base.X,base.obs.celltype,B,.5)
 exactold=ad.read_h5ad(OLD/('heart_interp/holdout/heart_copula.h5ad' if dev else 'heart_interp/final/t2_hrt_int__heart_copula__v0025.h5ad'))
 assert np.array_equal(baseline.X,exactold.X) and np.array_equal(baseline.obsm['spatial_3D'],exactold.obsm['spatial_3D'])
 configs={'global_b075':(B,.75),'global_b100':(B,1.)}
 if dev or a.choice=='within_state_b050':
  BW,bwmeta=fit_within(X,lab);configs['within_state_b050']=(BW,.5);np.save(out/'within_B.npy',BW)
 np.save(out/'global_B.npy',B)
 result={'mode':a.mode,'source_commit':'7dfe148f5c55d2a066e6adf1e4e46b08c631d08b','fit_sources':{s:sha(DATA/(s+'.h5ad')) for s in stages},'parent_v25_sha256':'efb0c7298be54493d3d540257daf1f9c9664d8e64fe14bba8dd349669ea977c2','h1_sha256':'7cc2e31445613a7e9e13525ea3b3ce8bf386855f8df0b70d6ba47f1ae2a23a37','exact_v25_arrays_reproduced':True,'fit_global':bmeta,'threadpools':threadpool_info(),'protected_target_read':False,'arms':{},'status':'RUNNING'}
 if 'bwmeta' in locals():result['fit_within']=bwmeta
 preds={'v25':baseline}
 if dev:
  perm=np.random.default_rng(20261009).permutation(500);configs['gene_shuffle_b050']=(B[np.ix_(perm,perm)],.5)
 else:configs={a.choice:configs[a.choice]}
 for name,(bb,alpha) in configs.items():
  Q=base.copy();Q.X=reg(base.X,base.obs.celltype,bb,alpha);check=audit(baseline,Q);Q.uns['final_slot_provenance']=json.dumps({'axis':name,'alpha':alpha,'parent_v25_sha256':result['parent_v25_sha256'],'carrier_h1_sha256':result['h1_sha256'],'fit_sources':result['fit_sources'],'source_commit':result['source_commit'],'not_iterated_on_v25':True},sort_keys=True)
  path=out/('t2_hrt_int__copula_refine__v0026.h5ad' if not dev else name+'.h5ad');Q.write_h5ad(path);fc=V.format_check(path,BOARD);assert fc['pass'];result['arms'][name]={'path':str(path),'sha256':sha(path),'checks':check,'contract':fc,'blend':alpha};preds[name]=Q
  print('built',name,check,flush=True)
 result['arms']['v25']={'checks':audit(baseline,baseline)}
 if dev:
  from backtest import Board
  # Target accessed only after all arms freeze; all500 panel genes, same scorer/seeds.
  T=V.load_stage('E8.75',genes)
  for seed in [0,1,2]:
   board=Board('T2',genes,T,A[0],seed)
   for name,P in preds.items():
    raw=board.raw(P);sk=board.skills(raw);result['arms'][name].setdefault('evaluation',[]).append({'seed':seed,'raw':raw,'skills':sk,'floor':board.floor,'ceiling':board.ceil});print(seed,name,sk,flush=True);(out/'RESULT.json').write_text(json.dumps(result,indent=2))
  for name,z in result['arms'].items():
   z['mean_total']=float(np.mean([v['skills']['TOTAL'] for v in z['evaluation']]))
   z['mean_raw']={k:float(np.mean([v['raw'][k] for v in z['evaluation']])) for k in ['mmd_u','variogram','neighborhood_mmd']}
 result['status']='COMPLETE';(out/'RESULT.json').write_text(json.dumps(result,indent=2));print('COMPLETE',flush=True)
if __name__=='__main__':
 with threadpool_limits(limits=1):main()
