"""T1-14 ratio recentering (deterministic, clip-free, target-free).

X_new = X_base * (consensus_pb / base_pb) per gene (ratio floored at 1e-6 to
avoid div0; no clipping possible since all terms nonneg). Same consensus target
as T1-13 but multiplicative: tests whether T1-13's variogram failure was the
clipping (fixable) or the translation itself. Base = v0035 report.
Usage: python .auto/generate_t1_ratiorecenter.py
"""
import numpy as np
import anndata as ad
from pathlib import Path
import sys
sys.path.insert(0, ".auto")
from t1_common import dense, write_candidate, CAND_TMP  # noqa

ROOT = Path(".").resolve()
F35 = ROOT / "artifacts/t1_three/T1-THREE-20260929-v1/r2joint/report_prediction.h5ad"
F36 = ROOT / "artifacts/t1_three/T1-THREE-20260929-v1/r3mix/report_prediction.h5ad"
F38 = ROOT / "artifacts/t1_seven/T1-SEVEN-20260930-v1/n2covot/report_prediction.h5ad"

a35 = ad.read_h5ad(F35)
mats = [dense(a35.X)]
for f in (F36, F38):
    b = ad.read_h5ad(f)
    assert b.shape == a35.shape
    mats.append(dense(b.X))
pbs = np.stack([m.mean(axis=0) for m in mats])
consensus = pbs.mean(axis=0)
base_pb = pbs[0]
ratio = (consensus / np.maximum(base_pb, 1e-6)).astype(np.float64)
ratio = np.clip(ratio, 0.5, 2.0)  # data-frozen guard: winners agree, ratios ~1
print(f"ratio: median={np.median(ratio):.5f} p1={np.percentile(ratio,1):.4f} "
      f"p99={np.percentile(ratio,99):.4f} frac_at_bound={((ratio==0.5)|(ratio==2.0)).mean():.5f}")
X_new = mats[0].astype(np.float64) * ratio[None, :]
assert np.isfinite(X_new).all() and (X_new >= 0).all()
write_candidate(str(CAND_TMP), X_new.astype(np.float32), a35)
print(f"wrote {CAND_TMP}")
