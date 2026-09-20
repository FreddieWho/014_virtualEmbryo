"""Recover rejection diagnostics from the final checkpoint; no GCN retraining."""
import hashlib
import json
from pathlib import Path
import anndata as ad
import numpy as np
import torch
from scipy import sparse
from sklearn.linear_model import Ridge

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'artifacts/t3_next/T3-R6-OP2-20260921-v1'
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
manifest_path = ROOT / 'reports/t3_r56_launch_20260921/SOURCE_MANIFEST.json'
m = json.loads(manifest_path.read_text())
for v in m['files'].values():
    assert sha(ROOT / v['path']) == v['sha256']
lock = json.loads((RUN / 'INPUT_LOCK.json').read_text())
for name, expected in lock['inputs'].items():
    assert sha(ROOT / name) == expected, name
parent_path = next(ROOT / x for x in lock['inputs'] if x.startswith('submissions/'))
parent = ad.read_h5ad(parent_path)
data = ad.read_h5ad(ROOT / m['files']['expression']['path'])
dense = lambda x: x.toarray() if sparse.issparse(x) else np.asarray(x)
x = dense(data[:, parent.var_names].X).astype(np.float32)
conditions = data.obs.condition.astype(str).to_numpy()
genes = sorted(set(conditions) - {'ctrl'})
effects = np.stack([x[conditions == g].mean(0) - x[conditions == 'ctrl'].mean(0) for g in genes])
emb = np.load(ROOT / m['files']['embedding']['path'], allow_pickle=False)
order = emb['genes'].astype(str).tolist()
ii = [order.index(g) for g in genes + ['Gata4']]
z = emb['embedding'][ii].astype(np.float32)
z = (z - z[:-1].mean(0)) / np.maximum(z[:-1].std(0), 1e-4)
a = sparse.load_npz(ROOT / m['files']['adjacency']['path'])[ii][:, ii].toarray().astype(np.float32)
a += np.eye(len(z), dtype=np.float32)
a /= np.maximum(a.sum(1, keepdims=True), 1e-8)
torch.set_num_threads(8)
state = torch.load(RUN / 'graph_final.pt', map_location='cpu', weights_only=True)
h = torch.nn.Linear(z.shape[1], 32)
out = torch.nn.Linear(32, x.shape[1])
h.load_state_dict(state['h'])
out.load_state_dict(state['out'])
with torch.no_grad():
    at = torch.from_numpy(a)
    graph = out(at @ torch.relu(h(at @ torch.from_numpy(z)))).numpy()[-1]
ridge = Ridge(alpha=10).fit(z[:-1], effects).predict(z[-1:])[0]
base = dense(parent.X).astype(np.float32)
gi = list(parent.var_names).index('Gata4')
cfg = json.loads((RUN / 'code/design.json').read_text())
threshold = cfg['disaster_bounds']['negative_clip_fraction_max']
result = {'method': 'Final GCN checkpoint inference; deterministic final ridge refit only. No GCN retraining or parameter change.',
          'source_manifest_sha256': sha(manifest_path), 'checkpoint_sha256': sha(RUN / 'graph_final.pt'),
          'parent_sha256': sha(parent_path), 'threshold': threshold, 'lanes': {}}
for lane, delta in [('r6ridge', ridge), ('r6graph', graph)]:
    predicted = base + delta
    predicted[:, gi] = 0
    negative = predicted < 0
    result['lanes'][lane] = {'negative_clip_fraction': float(negative.mean()),
        'negative_entries': int(negative.sum()), 'total_entries': int(negative.size),
        'minimum_before_clip': float(predicted.min()), 'residual_rms': float(np.sqrt(np.mean(delta**2))),
        'passes': bool(negative.mean() <= threshold)}
result['evidence_sha256'] = {name: sha(RUN / name) for name in ['RESULT.json', 'GENE_HOLDOUT.json', 'INPUT_LOCK.json', 'graph_holdout.pt', 'graph_final.pt']}
(Path(__file__).parent / 'DIAGNOSTICS.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
