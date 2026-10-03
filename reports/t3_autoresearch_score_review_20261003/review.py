"""Read-only replay of scored v0070; no target labels or model selection."""
import csv
import hashlib
import json
from pathlib import Path
import sys

import anndata as ad
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.t3_autoresearch import retained_model as model

rows = list(csv.DictReader((ROOT / 'submissions/INDEX.tsv').open(), delimiter='\t'))
rows = {r['version']: r for r in rows if r['board'] == 'T3:gata4'}
def dense(x):
    return x.toarray() if hasattr(x, 'toarray') else np.asarray(x)

parent = ad.read_h5ad(ROOT / rows['v0009']['path'])
child = ad.read_h5ad(ROOT / rows['v0070']['path'])
a, b = dense(parent.X), dense(child.X)
d = np.load(ROOT / 'artifacts/t3_autoresearch_delivery_20261003/MODEL_RESPONSE.npy').reshape(-1)
expected = np.maximum(a.astype(float) + d, 0).astype('float32')
gi = list(child.var_names).index('Gata4')
expected[:, gi] = 0
mean_change = b.mean(0, dtype=np.float64) - a.mean(0, dtype=np.float64)
ix = model.GENES.index('Gata4')
sim = model.KERNEL[ix, :26]
w = np.exp((sim - sim.max()) / .15)
w /= w.sum()
report = {
    'candidate': 'v0070', 'parent': 'v0009', 'incumbent': 'v0048',
    'identity_matches_index': all(hashlib.sha256(p.read_bytes()).hexdigest() == rows['v0070']['sha256'] for p in [ROOT / rows['v0070']['path'], ROOT / 'deliveries/t3_gata4__ar_complex__v0070.h5ad']),
    'exact_emission_replay': bool(np.array_equal(b, expected)),
    'obs_order_preserved': bool(child.obs_names.equals(parent.obs_names)),
    'var_order_preserved': bool(child.var_names.equals(parent.var_names)),
    'coordinates_preserved': bool(np.array_equal(child.obsm['spatial'], parent.obsm['spatial'])) if 'spatial' in child.obsm else bool(np.array_equal(child.obsm['spatial_3D'], parent.obsm['spatial_3D'])),
    'parent_density': float(np.count_nonzero(a) / a.size),
    'output_density': float(np.count_nonzero(b) / b.size),
    'activated_entries': int(((a == 0) & (b > 0)).sum()),
    'negative_preclip_entries': int((a + d < 0).sum()),
    'largest_emitted_mean_delta_error': float(np.max(np.abs(mean_change - d))),
    'largest_error_gene': str(child.var_names[np.argmax(np.abs(mean_change - d))]),
    'specific_complex_donors': [{'gene': g, 'similarity': float(s), 'weight': float(v)} for g,s,v in zip(model.GENES[:26],sim,w) if s > 0],
    'total_weight_on_zero_overlap_donors': float(w[sim == 0].sum()),
    'target_truth_used': False,
    'interpretation': 'Emission diagnostics, not target metrics or causal attribution.'
}
assert all(report[k] for k in ['identity_matches_index','exact_emission_replay','obs_order_preserved','var_order_preserved','coordinates_preserved'])
(Path(__file__).parent / 'OUTPUT_AUDIT.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
