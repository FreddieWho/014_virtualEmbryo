"""Portable final-model replay or full refit; no server/held-out target access.
Usage: python reproduce.py --root PACK_ROOT --mode replay|refit --out rebuilt.h5ad
"""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='2'
import argparse,json,pickle,hashlib,sys
from pathlib import Path
import numpy as np,anndata as ad
import flow,endpoint_flow as ef,endpoint_residual as er

def select(types,n_cells=25179,seed=20260821):
 groups=sorted(np.unique(types));gi={g:np.flatnonzero(types==g)for g in groups};counts=np.array([len(gi[g])for g in groups],float);exact=counts*n_cells/len(types);take=np.floor(exact).astype(int);left=n_cells-int(take.sum());order=sorted(range(len(groups)),key=lambda i:(-(exact[i]-take[i]),groups[i]));
 for i in order[:left]:take[i]+=1
 rng=np.random.default_rng(seed);return np.sort(np.concatenate([rng.choice(gi[g],size=int(take[i]),replace=False)for i,g in enumerate(groups)]))

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('--mode',choices=['replay','refit'],required=True);p.add_argument('--out',required=True,type=Path);a=p.parse_args();r=a.root
 inputs=r/'inputs';flow.DATA=inputs;flow.PANEL=inputs/'T2__heart__val_extrap.genes.txt';genes=flow.PANEL.read_text().splitlines()
 latest=ad.read_h5ad(inputs/'E9.5.h5ad')[:,genes].copy();latest.X=flow.dense(latest.X);ix=select(latest.obs.celltype.astype(str).to_numpy());carrier=latest[ix].copy()
 if a.mode=='replay':m=pickle.loads((r/'model/endpoint_model.pkl').read_bytes())
 else:
  early=ad.read_h5ad(inputs/'E8.75.h5ad')[:,genes].copy();early.X=flow.dense(early.X)
  m={'endpoint':ef.fit_endpoint(inputs/'endpoint/E14.5_cm_enriched_panel_raw.h5ad'),'median_deltas':ef.source_model(early,latest),'early_time':8.75,'late_time':9.5,'target_time':10.5,'endpoint_time':14.5,'source_hashes':{s:flow.sha(inputs/(s+'.h5ad'))for s in ['E8.75','E9.5']}}
 x,diag=er.predict(carrier,m,False);carrier.X=x;carrier.uns['ve_contract']={'schema':'ve.contract.v1','normalization':'log_normalized'};carrier.uns['reproduction_mode']=a.mode;a.out.parent.mkdir(parents=True,exist_ok=True);carrier.write_h5ad(a.out)
 original=ad.read_h5ad(r/'candidate/submission.h5ad');err=float(np.max(np.abs(flow.dense(original.X)-x)));coords=bool(np.array_equal(original.obsm['spatial_3D'],carrier.obsm['spatial_3D']));names=bool(original.obs_names.equals(carrier.obs_names));panel=bool(original.var_names.equals(carrier.var_names));assert err<=2e-6 and coords and names and panel
 result={'mode':a.mode,'max_abs_X_error':err,'exact_X':bool(np.array_equal(original.X,x)),'coordinate_exact':coords,'obs_names_exact':names,'var_names_exact':panel,'tolerance':2e-6,'output':str(a.out),'diagnostics':diag};Path(str(a.out)+'.verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
