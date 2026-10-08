import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='2'
import sys,json,pickle
from pathlib import Path
import numpy as np,anndata as ad
R=Path('/workspace/shared/t2_heart_extra_20261008');sys.path.insert(0,str(R));import endpoint_flow as e
split=sys.argv[1] if len(sys.argv)>1 else 'dev';d=R/split;m=pickle.loads((d/'endpoint_model.pkl').read_bytes())
if split=='dev':c=ad.read_h5ad(d/'copy.h5ad')
else:
 src=e.flow.load('E9.5');import pandas as pd;ids=pd.read_csv(d/'source_row_ledger.tsv',sep='\t').source_row.to_numpy();c=src[ids].copy()
base=e.recipe(c,m['median_deltas']);t=c.obs.celltype.astype(str).to_numpy();elig=np.array(['CM' in v for v in t]);common=m['endpoint']['common_indices'];other=np.setdiff1d(np.arange(500),common);lib=np.expm1(base.astype(float)).sum(1);clib=np.expm1(base[:,common].astype(float)).sum(1);report={'split':split,'external_sha':m['endpoint']['external_sha'],'external_path':m['endpoint']['external_path'],'n_endpoint_bins':m['endpoint']['n_bins'],'common_genes':len(common),'checks':{}}
for kind in ['endpoint','endfree','endperm']:
 a=ad.read_h5ad(d/(kind+'.h5ad'));replay,info=e.predict(c,m,kind)
 q={'finite':bool(np.isfinite(a.X).all()),'nonnegative':bool((a.X>=0).all()),'row_gene_identity':list(a.obs_names)==list(c.obs_names) and list(a.var_names)==list(c.var_names),'coordinates_exact':bool(np.array_equal(a.obsm['spatial_3D'],c.obsm['spatial_3D'])),'replay_exact':bool(np.array_equal(a.X,replay)),'replay_max_abs':float(np.max(np.abs(a.X-replay))),'non_cm_exact':bool(np.array_equal(a.X[~elig],base[~elig])),'unmeasured_genes_exact':bool(np.array_equal(a.X[:,other],base[:,other])),'library_max_relative_error':float(np.max(np.abs(np.expm1(a.X.astype(float)).sum(1)/lib-1))),'common_library_max_relative_error':float(np.max(np.abs(np.expm1(a.X[:,common].astype(float)).sum(1)/clib-1))),'diagnostics':info};report['checks'][kind]=q
 for k in ['finite','nonnegative','row_gene_identity','coordinates_exact','non_cm_exact','unmeasured_genes_exact']:assert q[k],(kind,k)
 assert q['replay_max_abs']<1e-6 and q['library_max_relative_error']<1e-4 and q['common_library_max_relative_error']<1e-4
p=Path('/workspace/shared/t2_extra_independent_audit')/(split+'_endpoint_audit.json');p.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
