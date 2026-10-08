"""Portable, no-source-KO inference replay. Run: python inference/replay.py"""
from pathlib import Path
import os,sys,json,hashlib
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='2'
P=Path(__file__).resolve().parent;ROOT=P.parent;sys.path.insert(0,str(ROOT))
import numpy as np,anndata as ad,joblib
from threadpoolctl import threadpool_limits
threadpool_limits(2)
manifest=json.loads((P/'MANIFEST.json').read_text())
for name,digest in manifest['files'].items():
 assert hashlib.sha256((P/name).read_bytes()).hexdigest()==digest,('Input hash mismatch',name)
model=joblib.load(P/'state_emitter.joblib');z=np.load(P/'generic_response.npz');response={k:z[k] for k in z.files};carrier=ad.read_h5ad(P/'WT_carrier7449.h5ad');pred,donor=model.emit(carrier.X,response,mode='combined');digest=hashlib.sha256(np.ascontiguousarray(pred).tobytes()).hexdigest();assert digest==manifest['frozen_expression_sha256'];assert np.array_equal(donor,np.load(P/'expected_donor_rows.npy'));assert np.max(abs(np.expm1(pred.astype(float)).sum(1)-10000))<.02
print(json.dumps(dict(status='PASS',shape=list(pred.shape),expression_sha256=digest,source_KO_files_needed=False,hidden_target_files_needed=False,donor_replay_exact=True),indent=2))
