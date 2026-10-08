import json,hashlib
from pathlib import Path
import numpy as np,pandas as pd,anndata as ad
from scipy.stats import spearmanr
P=Path('/workspace/shared/t3_v88_optimization_20261008/deployment');R=Path('/workspace/shared/t3_v87_restored');base=ad.read_h5ad(R/'v0087/t3_gata4__embhurdle__v0087.h5ad');wt=ad.read_h5ad(R/'inference/WT_carrier7449.h5ad');oldmean=base.X.mean(0,dtype=float);delta0=oldmean-wt.X.mean(0,dtype=float);report={}
for arm in ['baseline','residual','conditional','both']:
 p=P/f'gata4_{arm}.h5ad';a=ad.read_h5ad(p);X=np.asarray(a.X);assert a.shape==base.shape==(7449,500);assert np.array_equal(a.var_names,base.var_names);assert np.array_equal(a.obs_names,base.obs_names);assert a.obs_names.is_unique;assert np.isfinite(X).all() and (X>=0).all();assert np.array_equal(a.obsm['spatial_3D'],base.obsm['spatial_3D'])
 mu=X.mean(0,dtype=float);delta=mu-wt.X.mean(0,dtype=float);masserr=float(abs(np.expm1(X.astype(float)).sum(1)-10000).max());assert masserr<.02
 if arm=='baseline':assert np.array_equal(X,base.X)
 report[arm]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'shape':list(a.shape),'mean_shift_l2_vs_v87':float(np.linalg.norm(mu-oldmean)),'mean_shift_max_abs_vs_v87':float(abs(mu-oldmean).max()),'native_float32_mean_max_abs_vs_v87':float(abs(X.mean(0)-base.X.mean(0)).max()),'response_l2':float(np.linalg.norm(delta)),'amplitude_ratio':float(np.linalg.norm(delta)/np.linalg.norm(delta0)),'response_rank_spearman_vs_v87':float(spearmanr(delta,delta0).statistic),'detection':float((X>0).mean()),'max_panel_mass_error':masserr,'covariance_frobenius_change_vs_v87':float(np.linalg.norm(np.cov(X,rowvar=False)-np.cov(base.X,rowvar=False)))}
Path('/workspace/shared/t3_v88_independent_audit/DEPLOYMENT_AUDIT.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
