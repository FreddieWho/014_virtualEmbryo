import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='2'
import sys,json,pickle,hashlib
from pathlib import Path
import numpy as np,anndata as ad
ROOT=Path('/workspace/shared/t2_heart_extra_20261008');sys.path.insert(0,str(ROOT));import flow
split=sys.argv[1] if len(sys.argv)>1 else 'dev';d=ROOT/split
b=json.loads((d/'BUILD.json').read_text());copy=ad.read_h5ad(d/'copy.h5ad');r=ad.read_h5ad(d/'incumbent_recipe.h5ad');panel=flow.PANEL.read_text().splitlines();types=copy.obs.celltype.astype(str).to_numpy();lib=np.expm1(copy.X.astype(float)).sum(1)
report={'split':split,'input_build':b,'checks':{},'no_target_read':True}
for kind in ['pca','go']:
 a=ad.read_h5ad(d/f'{kind}_flow.h5ad');m=pickle.loads((d/f'{kind}_model.pkl').read_bytes());replay=flow.predict(copy,m,1.5 if split=='dev' else 4/3);orph=~np.isin(types,list(m['states']));aud=json.loads((d/f'{kind}_fit_audit.json').read_text());delta=a.X-r.X
 checks={'finite':bool(np.isfinite(a.X).all()),'nonnegative':bool((a.X>=0).all()),'panel_exact':list(a.var_names)==panel,'rows_exact':list(a.obs_names)==list(copy.obs_names),'coordinates_equal':bool(np.array_equal(a.obsm['spatial_3D'],copy.obsm['spatial_3D'])),'replay_exact':bool(np.array_equal(replay,a.X)),'replay_max_abs':float(np.max(np.abs(replay-a.X))),'replay_close':bool(np.allclose(replay,a.X,rtol=1e-6,atol=1e-6)),'orphans_exact':bool(np.array_equal(a.X[orph],copy.X[orph])),'library_max_relative_error':float(np.max(np.abs(np.expm1(a.X.astype(float)).sum(1)/lib-1))),'delta_from_recipe_rms':float(np.sqrt(np.mean(delta**2))),'changed_rows':int(np.any(delta!=0,axis=1).sum()),'states':len(m['states']),'row_mass_error_max':max(v['max_row_mass_error'] for v in aud.values()),'realized_mean_correction_by_state':{s:float(np.linalg.norm(delta[types==s].mean(0))) for s in m['states']},'max_abs_value':float(np.max(a.X))}
 report['checks'][kind]=checks
print(json.dumps(report['checks'],indent=2));assert all(all(c[k] for k in ['finite','nonnegative','panel_exact','rows_exact','coordinates_equal','replay_close','orphans_exact']) and c['library_max_relative_error']<1e-4 for c in report['checks'].values())
out=Path('/workspace/shared/t2_extra_independent_audit')/f'{split}_matrix_audit.json';out.write_text(json.dumps(report,indent=2));print(json.dumps(report['checks'],indent=2))
