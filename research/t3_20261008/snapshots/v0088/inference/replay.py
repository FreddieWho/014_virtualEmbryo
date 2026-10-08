"""Portable source-free v88 inference. Only untreated carrier and frozen trained prior."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='2'
from pathlib import Path
import json,hashlib
import numpy as np,anndata as ad,joblib
from threadpoolctl import threadpool_limits
threadpool_limits(2)
from emitter_v88 import emit
P=Path(__file__).resolve().parent;m=json.loads((P/'MANIFEST.json').read_text())
for name,digest in m['files'].items():assert hashlib.sha256((P/name).read_bytes()).hexdigest()==digest,('Hash mismatch',name)
model=joblib.load(P/'state_emitter.joblib');z=np.load(P/'generic_response.npz');response={k:z[k] for k in z.files};a=ad.read_h5ad(P/'WT_carrier7449.h5ad');arm=m['arm'];p,d=emit(model,a.X,response,residual=arm in ['residual','both'],conditional=arm in ['conditional','both']);digest=hashlib.sha256(p.tobytes()).hexdigest();assert digest==m['expression_sha256'];assert np.array_equal(d,np.load(P/'expected_donor_rows.npy'));assert np.max(abs(np.expm1(p.astype(float)).sum(1)-10000))<.02
print(json.dumps(dict(status='PASS',shape=list(p.shape),expression_sha256=digest,donor_replay_exact=True,source_KO_inputs_needed=False,target_KO_inputs_needed=False),indent=2))
