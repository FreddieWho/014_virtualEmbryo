import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='2'
import sys,json,pickle
from pathlib import Path
import anndata as ad,numpy as np
R=Path('/workspace/shared/t2_heart_extra_20261008');sys.path.insert(0,str(R));import graph_velocity as g
split=sys.argv[1] if len(sys.argv)>1 else 'dev';d=R/split;c=ad.read_h5ad(d/'copy.h5ad');t=c.obs.celltype.astype(str).to_numpy();lib=np.expm1(c.X.astype(float)).sum(1);report={}
for kind in ['graph','perm']:
 a=ad.read_h5ad(d/(kind+'.h5ad'));m=pickle.loads((d/(kind+'_model.pkl')).read_bytes());r=g.predict(c,m);orph=~np.isin(t,list(m['states']));mins=[float(np.linalg.eigvalsh(v['laplacian']).min()) for v in m['states'].values()]
 report[kind]={'finite':bool(np.isfinite(a.X).all()),'nonnegative':bool((a.X>=0).all()),'row_gene_identity':list(a.obs_names)==list(c.obs_names) and list(a.var_names)==list(c.var_names),'coordinates_exact':bool(np.array_equal(a.obsm['spatial_3D'],c.obsm['spatial_3D'])),'replay_exact':bool(np.array_equal(r,a.X)),'replay_max_abs':float(np.max(np.abs(r-a.X))),'orphan_count':int(orph.sum()),'orphans_exact':bool(np.array_equal(a.X[orph],c.X[orph])),'library_max_relative':float(np.max(np.abs(np.expm1(a.X.astype(float)).sum(1)/lib-1))),'laplacian_min_eigenvalue':min(mins),'model_states':list(m['states'])}
for v in report.values():assert v['finite'] and v['nonnegative'] and v['row_gene_identity'] and v['coordinates_exact'] and v['replay_max_abs']<1e-6 and v['orphans_exact'] and v['library_max_relative']<1e-4 and v['laplacian_min_eigenvalue']>-1e-8
p=Path('/workspace/shared/t2_extra_independent_audit')/(split+'_graph_audit.json');p.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
