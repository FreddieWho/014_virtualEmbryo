"""Read-only exact inference from an explicitly supplied trusted local asset directory."""
import argparse, os, sys, json, hashlib
from pathlib import Path
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']: os.environ[key]='2'
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--version',choices=['v0087','v0088'],required=True)
p.add_argument('--assets',type=Path,required=True,help='Trusted cache with four manifest-bound inference assets')
a=p.parse_args();root=Path(__file__).resolve().parents[1];s=root/'snapshots'/a.version
manifest=json.loads((s/'inference/MANIFEST.json').read_text());assets=a.assets.resolve()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
for name in ['state_emitter.joblib','generic_response.npz','WT_carrier7449.h5ad','expected_donor_rows.npy']:
 f=assets/name
 if not f.is_file():p.error(f'Missing cached artifact: {name}. Read REPRODUCTION.md; this repository does not distribute trained assets.')
 if sha(f)!=manifest['files'][name]:p.error(f'Untrusted or mismatched artifact: {name}')
# Verify archived code before loading a model that imports its Python classes.
inv=json.loads((root/'SNAPSHOT_INVENTORY.json').read_text())
for row in inv:
 if row['path'].startswith(f'snapshots/{a.version}/') and row['path'].endswith('.py'):
  assert sha(root/row['path'])==row['sha256'],row['path']
sys.path.insert(0,str(s))
import numpy as np, anndata as ad, joblib
from threadpoolctl import threadpool_limits
threadpool_limits(2)
model=joblib.load(assets/'state_emitter.joblib');z=np.load(assets/'generic_response.npz');response={k:z[k] for k in z.files};carrier=ad.read_h5ad(assets/'WT_carrier7449.h5ad')
if a.version=='v0088':
 from emitter_v88 import emit
 pred,donor=emit(model,carrier.X,response,residual=False,conditional=True)
else:pred,donor=model.emit(carrier.X,response,mode='combined')
digest=hashlib.sha256(np.ascontiguousarray(pred).tobytes()).hexdigest()
assert digest==manifest.get('expression_sha256',manifest.get('frozen_expression_sha256'))
assert np.array_equal(donor,np.load(assets/'expected_donor_rows.npy'))
assert np.max(abs(np.expm1(pred.astype(float)).sum(1)-10000))<.02
print(json.dumps(dict(status='PASS',version=a.version,expression_sha256=digest,shape=list(pred.shape),donor_replay_exact=True,output_files_written=False),indent=2))
