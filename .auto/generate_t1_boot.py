"""T1-1 bootstrap luck-band probe (diagnostic, no mechanism).

Within each obs celltype of the v0035 report matrix, resample rows WITH replacement
(same per-type counts), fixed seed. Measures pure row-identity noise of the report
proxy: if de moves on pure bootstrap, single-seed resampling 'gains' are luck.

Usage: python .auto/generate_t1_boot.py <seed>  -> writes .auto/t1_candidate.h5ad
"""
import sys
import numpy as np
sys.path.insert(0, ".auto")
from t1_common import load_baseline_report, dense, write_candidate, CAND_TMP  # noqa

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 20261011
rng = np.random.default_rng(seed)
a, X = load_baseline_report()
types = a.obs["celltype"].astype(str).to_numpy()
out = np.empty_like(X)
for typ in np.unique(types):
    ix = np.flatnonzero(types == typ)
    pick = rng.choice(ix, size=len(ix), replace=True)
    out[ix] = X[pick]
b = a.copy()
write_candidate(CAND_TMP, out, b)
print(f"T1-1 bootstrap seed={seed} n={X.shape} types={len(np.unique(types))} -> {CAND_TMP}")
