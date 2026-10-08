"""Held-stage evaluator. This process never writes predictor parameters."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='2'
import argparse,json,sys,hashlib,time
from pathlib import Path
import numpy as np,anndata as ad
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,'/workspace/shared/t3repo')
from scripts.t2_pseudo_holdout import select_indices
SCORER=Path('/workspace/shared/t3repo/third_party/veckit')
sys.path.insert(0,str(SCORER))
import score_h5ad

def write(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
def split():
 assert (ROOT/'dev/BUILD.json').exists(),'predictor must finish before target open'
 a=ad.read_h5ad('/workspace/shared/virtual_embryo_data/E9.5.h5ad')
 ix=select_indices(a.obs.celltype.astype(str).to_numpy(),n_cells=a.n_obs//2,seed=20261008)
 reserve=np.setdiff1d(np.arange(a.n_obs),ix); out=ROOT/'evaluation';out.mkdir(exist_ok=True)
 for name,ind in [('dev',ix),('reserve',reserve)]:a[ind].copy().write_h5ad(out/(name+'_e95.h5ad'));write(out/(name+'_ids.json'),a.obs_names[ind].tolist())
 write(out/'SPLIT.json',{'seed':20261008,'dev_count':len(ix),'reserve_count':len(reserve),'prior_history':'E9.5 reused historical released stage; not independent biological validation or historically untouched reserve','predictor_code_sha256':hashlib.sha256((ROOT/'flow.py').read_bytes()).hexdigest()})

def score(lane,partition):
 out=ROOT/'evaluation';target=out/(partition+'_e95.h5ad');pred=ROOT/'dev'/({'copy':'copy','incumbent_recipe':'incumbent_recipe','pca':'pca_flow','go':'go_flow','graph':'graph','perm':'perm','endpoint':'endpoint','endfree':'endfree','endperm':'endperm','endmatched':'endmatched','endmatchedperm':'endmatchedperm'}[lane]+'.h5ad')
 for seed in [20261003,20261011,20261019]:
  dest=out/f'{partition}_{lane}_s{seed}.json'
  if dest.exists():continue
  args=argparse.Namespace(task='T2',setting='heart',input=pred,target=target,reference=ROOT/'dev/copy.h5ad',allow_reorder=False,seed=seed)
  start=time.time();meta,metrics=score_h5ad.score_t2(args)
  write(dest,{'meta':meta,'metrics':metrics,'seed':seed,'elapsed_seconds':time.time()-start,'scorer_sha256':hashlib.sha256((SCORER/'score_h5ad.py').read_bytes()).hexdigest()})
  print(dest.name,metrics,flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action');p.add_argument('--partition',default='dev');a=p.parse_args()
 if a.action=='split':split()
 else:score(a.action,a.partition)
