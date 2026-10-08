import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='2'
import sys,json,hashlib
from pathlib import Path
import numpy as np,pandas as pd,anndata as ad,joblib
from threadpoolctl import threadpool_limits
threadpool_limits(2)
from emitter_v88 import emit
from scipy.stats import spearmanr
P=Path(__file__).parent;R=Path('/workspace/shared/t3_v87_restored');O=P/'deployment';O.mkdir(exist_ok=True)
model=joblib.load(R/'inference/state_emitter.joblib');z=np.load(R/'inference/generic_response.npz');response={k:z[k] for k in z.files};arms={'baseline':(False,False),'residual':(True,False),'conditional':(False,True),'both':(True,True)};receipts=[]
for target in ['gata4','mab']:
 if target=='gata4':a=ad.read_h5ad(R/'inference/WT_carrier7449.h5ad')
 else:
  w=ad.read_h5ad('/workspace/shared/virtual_embryo_data/E9.5.h5ad');ix=np.sort(np.random.default_rng(20260904).choice(w.n_obs,7449,replace=False));a=w[ix].copy();a.X=a.X.toarray() if hasattr(a.X,'toarray') else a.X
 baseline=None
 for name,(res,cond) in arms.items():
  p,donor=emit(model,a.X,response,residual=res,conditional=cond)
  if baseline is None:baseline=p
  if target=='gata4' and name=='baseline':assert hashlib.sha256(np.ascontiguousarray(p).tobytes()).hexdigest()=='2420c6b992fed7c431bf2cf4a4fb30d630fcba9bafa8d9b5898b5caae4db1f98'
  out=a.copy();out.X=p;out.uns['model_scope']='Developmental generic response; no target KO labels; WT-only conditional association';out.uns['emitter_arm']=name;file=O/f'{target}_{name}.h5ad';out.write_h5ad(file,compression='gzip');reload=ad.read_h5ad(file);assert np.array_equal(reload.X,p);np.save(O/f'{target}_{name}_donor.npy',donor)
  delta=p.mean(0,dtype=float)-a.X.mean(0,dtype=float);bd=baseline.mean(0,dtype=float)-a.X.mean(0,dtype=float)
  row=dict(target=target,arm=name,sha256=hashlib.sha256(file.read_bytes()).hexdigest(),array_sha256=hashlib.sha256(p.tobytes()).hexdigest(),donors_same_as_baseline=bool(np.array_equal(donor,np.load(O/f'{target}_baseline_donor.npy'))),detection=float((p>0).mean()),mean_log_L2_drift=float(np.linalg.norm(p.mean(0,dtype=float)-baseline.mean(0,dtype=float))),response_L2=float(np.linalg.norm(delta)),response_rank_correlation=float(spearmanr(delta,bd).statistic),max_row_mass_error=float(abs(np.expm1(p.astype(float)).sum(1)-10000).max()))
  receipts.append(row);print(row,flush=True)
(O/'PREDICTIONS_FROZEN.json').write_text(json.dumps(dict(receipts=receipts,loaded_Mab_outcomes=False,loaded_target_outcomes=False,protocol_sha256=hashlib.sha256((P/'PROTOCOL.md').read_bytes()).hexdigest()),indent=2))
print('FROZEN_ALL_OUTPUTS',flush=True)
