import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
import json,pickle,sys
from pathlib import Path
import numpy as np,anndata as ad
from scipy.spatial.distance import cdist
sys.path.insert(0,str(Path(__file__).resolve().parent))
import flow
R=flow.ROOT
split=sys.argv[1] if len(sys.argv)>1 else 'dev'; d=R/split
base=ad.read_h5ad(d/'copy.h5ad');recipe=ad.read_h5ad(d/'incumbent_recipe.h5ad');types=base.obs.celltype.astype(str).to_numpy()
results={}
prior=json.loads(flow.GO.read_text());assert prior['genes']==flow.PANEL.read_text().splitlines()
for kind in ['pca','go']:
 m=pickle.loads((d/(kind+'_model.pkl')).read_bytes());a=ad.read_h5ad(d/(kind+'_flow.h5ad'))
 x=flow.dense(a.X);b=flow.dense(base.X);r=flow.dense(recipe.X)
 assert a.var_names.equals(base.var_names) and a.obs_names.equals(base.obs_names)
 assert np.array_equal(a.obsm['spatial_3D'],base.obsm['spatial_3D'])
 assert np.isfinite(x).all() and x.min()>=0
 lib=np.expm1(b.astype(float)).sum(1);err=np.max(np.abs(np.expm1(x.astype(float)).sum(1)/lib-1));assert err<1e-4
 orphan=~np.isin(types,list(m['states']));assert np.array_equal(x[orphan],b[orphan])
 replay=flow.predict(base,m,1.5 if split=='dev' else 4/3);replay_err=float(np.max(np.abs(replay-x)));assert replay_err<1e-6
 fit=json.loads((d/(kind+'_fit_audit.json')).read_text());assert max(v['max_row_mass_error'] for v in fit.values())<1e-7
 st={}
 for s in m['states']:
  ix=types==s;v=(x[ix]-r[ix]);st[s]={'cells':int(ix.sum()),'realized_mean_shift_vs_recipe_l2':float(np.linalg.norm(v.mean(0))),'realized_abs_diff_mean':float(np.abs(v).mean()),'mean_shift_recipe_l2':float(np.linalg.norm((r[ix]-b[ix]).mean(0)))}
 results[kind]={'rows':len(x),'genes':x.shape[1],'shared_rows':int((~orphan).sum()),'orphan_rows':int(orphan.sum()),'library_relative_error_max':float(err),'exact_coordinate_preservation':True,'exact_orphan_expression_preservation':True,'exact_independent_model_replay':bool(np.array_equal(replay,x)),'independent_replay_max_abs_error':replay_err,'replay_tolerance':1e-6,'max_sinkhorn_row_mass_error':max(v['max_row_mass_error'] for v in fit.values()),'finite_nonnegative':True,'state_drift_audit':st}
flow.dump(d/'AUDIT.json',results);print(json.dumps({k:{q:v for q,v in val.items() if q!='state_drift_audit'}for k,val in results.items()},indent=2))
