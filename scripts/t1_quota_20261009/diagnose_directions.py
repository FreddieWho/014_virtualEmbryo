"""Full released-source pseudobulk direction collateral-effect diagnostic."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
import argparse,json
from pathlib import Path
import anndata as ad,numpy as np
from build_cp10k import sha
p=argparse.ArgumentParser();p.add_argument('--reference',required=True);p.add_argument('--parent',required=True);p.add_argument('--candidate',required=True);p.add_argument('--out',required=True);a=p.parse_args()
src=ad.read_h5ad(a.reference,backed='r');m=np.zeros(src.n_vars);n=src.n_obs;genes=np.asarray(src.var_names)
for lo in range(0,n,256):m+=np.asarray(src.X[lo:lo+256].astype(float).sum(0)).ravel()
m/=n;src.file.close()
x=ad.read_h5ad(a.parent);y=ad.read_h5ad(a.candidate);assert np.array_equal(x.var_names,genes) and np.array_equal(y.var_names,genes)
u=np.asarray(x.X.astype(float).mean(0)).ravel()-m;v=np.asarray(y.X.astype(float).mean(0)).ravel()-m;use=(np.abs(u)>=.01)|(np.abs(v)>=.01)
r={'full_panel':len(genes),'reference_cells':n,'reference_scope':'all released official E9.5 cells; source-reference directions, not future truth','parent_sha256':sha(a.parent),'candidate_sha256':sha(a.candidate),'reference_sha256':sha(a.reference),'substantial_source_reference_genes':int(use.sum()),'source_reference_direction_flips_abs_threshold_0_01':int(((np.sign(u)!=np.sign(v))&use).sum()),'pseudobulk_l2_change':float(np.linalg.norm(v-u)),'max_pseudobulk_change':float(np.abs(v-u).max()),'detection_support_exact':bool(np.array_equal(x.X.indptr,y.X.indptr) and np.array_equal(x.X.indices,y.X.indices))}
Path(a.out).write_text(json.dumps(r,indent=2));print(r)
