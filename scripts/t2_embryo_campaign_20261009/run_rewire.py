import argparse,json,re
from pathlib import Path
from types import SimpleNamespace as NS
import numpy as np
from runtime import initialize,REPO
from external_programs import load_prior
from rewire import rewire

def main():
 p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--external',required=True);p.add_argument('--outdir',required=True);p.add_argument('--fold',action='store_true');p.add_argument('--score',action='store_true');p.add_argument('--locality',action='store_true');p.add_argument('--parent');a=p.parse_args()
 v,_=initialize(a.data);import t2_recipes as r
 g=v.panel('T2:embryo:val_interp');L=v.load_stage('E6.75' if a.fold else 'E7.25',g);R=v.load_stage('E8.0',g);t=.4 if a.fold else 1/3
 if a.fold:
  par=NS(board='T2:embryo:val_interp',left='E6.75:6.75',right='E8.0:8.0',target=7.25,n=5000,seed=20261009,label='celltype',carrier='left',C=2.,geometry='logrms',zero_preserve=False);base,_=r.run_interp(par)
 else:
  import anndata as ad
  base=ad.read_h5ad(REPO/'artifacts/t2_embryo_campaign_20261009/e3_original_recipe.h5ad')
 if a.parent:
  import anndata as ad
  base=ad.read_h5ad(a.parent)
 lookup={str(n):i for i,n in enumerate(L.obs_names)};srcrows=np.array([lookup[re.sub(r'__(?:r|dup)\d+$','',str(n))] for n in base.obs_names]);source_coords=np.asarray(L.obsm['spatial_3D'])[srcrows]
 w,source=load_prior(Path(a.external)/'gse65924_e70_gene_spatial_rank_prior.tsv',g)
 outdir=Path(a.outdir);outdir.mkdir(parents=True,exist_ok=True);pred={'unmodified':base};result={'fold':a.fold,'source':source,'arms':{'unmodified':{}}}
 for name,mode,shuffle in [('internal','internal',False),('spatial','spatial',False),('spatial_shuffle','spatial',True)]:
  X,perm,d=rewire(base.X,base.obsm['spatial_3D'],base.obs.celltype,L.X,L.obsm['spatial_3D'],L.obs.celltype,R.X,R.obsm['spatial_3D'],R.obs.celltype,t,w,mode,shuffle,source_coords=source_coords,locality=a.locality)
  out=base.copy();inverse=np.argsort(perm);out.obsm['spatial_3D']=np.asarray(base.obsm['spatial_3D'])[inverse].copy();d['delivery_representation']='inverse coordinate permutation; X/obs/layers exact';d['coordinate_array_exact']=False;d['coordinate_multiset_exact']=True;out.uns['rewire_audit']=json.dumps(d);out.write_h5ad(outdir/(name+'.h5ad'));np.save(outdir/(name+'_permutation.npy'),inverse);pred[name]=out;result['arms'][name]={'diagnostics':d,'contract':v.format_check(outdir/(name+'.h5ad'),'T2:embryo:val_interp')};print(name,'built',flush=True)
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
