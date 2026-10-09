import argparse,json
from pathlib import Path
from types import SimpleNamespace as NS
import numpy as np
from runtime import initialize,REPO
from run_external import external_matrix
from copula import fit_conditional,regularize

def main():
 p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--external',required=True);p.add_argument('--outdir',required=True);p.add_argument('--fold',action='store_true');p.add_argument('--score',action='store_true');a=p.parse_args()
 v,_=initialize(a.data);import t2_recipes as r
 g=v.panel('T2:embryo:val_interp');L=v.load_stage('E6.75' if a.fold else 'E7.25',g);R=v.load_stage('E8.0',g)
 if a.fold:
  par=NS(board='T2:embryo:val_interp',left='E6.75:6.75',right='E8.0:8.0',target=7.25,n=5000,seed=20261009,label='celltype',carrier='left',C=2.,geometry='logrms',zero_preserve=False);base,_=r.run_interp(par)
 else:
  import anndata as ad
  base=ad.read_h5ad(REPO/'artifacts/t2_embryo_campaign_20261009/e3_original_recipe.h5ad')
 ext=external_matrix(a.external,g);outdir=Path(a.outdir);outdir.mkdir(parents=True,exist_ok=True);pred={'unmodified':base};result={'fold':a.fold,'pseudo_fold_limitation':'External E7.25 is independent but same stage as official pseudo-target; not a clean stage-exclusion backtest','arms':{}}
 for name,fit in [('internal',np.vstack([L.X,R.X])),('scrna',ext),('scrna_shuffle',ext[:,np.random.default_rng(20261009).permutation(len(g))])]:
  B,d=fit_conditional(fit);out=base.copy();out.X,audit=regularize(base.X,base.obs.celltype,B);out.uns['copula_audit']=json.dumps({'fit':d,'output':audit});out.write_h5ad(outdir/(name+'.h5ad'));pred[name]=out;result['arms'][name]={'fit':d,'audit':audit,'contract':v.format_check(outdir/(name+'.h5ad'),'T2:embryo:val_interp')};print(name,'built',flush=True)
 result['arms']['unmodified']={}
 if a.score:
  if not a.fold:raise ValueError('Only released stage evaluation')
  from backtest import Board
  T=v.load_stage('E7.25',g)
  for seed in [0,1,2]:
   board=Board('T2',g,T,L,seed)
   for name,P in pred.items():
    raw=board.raw(P);sk=board.skills(raw);result['arms'][name].setdefault('evaluation',[]).append({'seed':seed,'raw':raw,'skills':sk});print(seed,name,sk,flush=True)
   (outdir/'RESULT.json').write_text(json.dumps(result,indent=2))
 (outdir/'RESULT.json').write_text(json.dumps(result,indent=2))
if __name__=='__main__':main()
