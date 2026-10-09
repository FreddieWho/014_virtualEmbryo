#!/usr/bin/env python3
"""Independent-process refit and candidate replay; does not modify candidate."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS','NUMBA_NUM_THREADS'):os.environ[k]='1'
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,json,hashlib
import numpy as np,anndata as ad
from threadpoolctl import threadpool_limits,threadpool_info
HERE=Path(__file__).resolve().parent;REPO=HERE.parent/'repo'
sys.path.insert(0,str(REPO/'scripts/t2_embryo_campaign_20261009'))
from runtime import initialize
from copula import fit_conditional,regularize

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--result',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    r=json.loads(Path(a.result).read_text());assert r['mode']=='final' and r['status']=='COMPLETE'
    v,_=initialize(a.data);g=v.panel('T2:heart:val_interp')
    base=ad.read_h5ad(r['parent']['path']);out=ad.read_h5ad(r['arms']['heart_copula']['path'])
    assert sha(r['parent']['path'])==r['parent']['sha256']
    assert sha(r['arms']['heart_copula']['path'])==r['arms']['heart_copula']['sha256']
    stages=[v.load_stage(s['stage'],g) for s in r['fit_sources']]
    B,fit=fit_conditional(np.vstack([x.X for x in stages]));oldB=np.load(r['B_file']['path'])
    Y,_=regularize(base.X,base.obs.celltype,B)
    lab=np.asarray(base.obs.celltype).astype(str)
    check={'fresh_fit_B_array_exact':bool(np.array_equal(B,oldB)), 'fresh_candidate_X_array_exact':bool(np.array_equal(Y,out.X)), 'obs_exact':base.obs.equals(out.obs),'var_exact':base.var.equals(out.var),'coords_exact':bool(np.array_equal(base.obsm['spatial_3D'],out.obsm['spatial_3D'])),'global_gene_marginals_exact':bool(np.array_equal(np.sort(base.X,axis=0),np.sort(out.X,axis=0))),'state_gene_marginals_exact':all(np.array_equal(np.sort(base.X[lab==s],axis=0),np.sort(out.X[lab==s],axis=0)) for s in set(lab))}
    report={'status':'PASS' if all(check.values()) else 'FAIL','checks':check,'parent_sha256':r['parent']['sha256'],'candidate_sha256':r['arms']['heart_copula']['sha256'],'fresh_fit':fit,'threadpools':threadpool_info(),'note':'Fresh independent process refits heart coefficients and reconstructs expression; compares arrays and immutable file hashes. No cross-environment or cross-thread identity claim.'}
    Path(a.out).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert all(check.values())
if __name__=='__main__':
    with threadpool_limits(limits=1):main()
