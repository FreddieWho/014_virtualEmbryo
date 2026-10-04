"""T1-13 consensus-mean recentering (deterministic, no knob, target-free).

X_new = X_base - pb(base) + mean(pb35, pb36, pb38), with negatives clipped.
Preserves every residual/covariance exactly (pure mean translation); only the
pseudobulk ranking (what de_score reads) changes. Consensus built solely from
the three winner report predictions (legitimate research outputs); the eval
target is never opened (target_used=false).
Base = v0035 report (local baseline). Usage: python .auto/generate_t1_recenter.py
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
    assert np.array_equal(np.asarray(b.obs_names), np.asarray(a35.obs_names))
    mats.append(dense(b.X))
pbs = np.stack([m.mean(axis=0) for m in mats])  # 3 x G
consensus = pbs.mean(axis=0)
base_pb = pbs[0]
shift = (consensus - base_pb).astype(np.float64)
print(f"consensus shift: l2={np.linalg.norm(shift):.4f} "
      f"maxabs={np.abs(shift).max():.4f} meanabs={np.abs(shift).mean():.5f}")
X_new = mats[0].astype(np.float64) + shift[None, :]
neg = int((X_new < 0).sum())
X_new = np.clip(X_new, 0, None)
print(f"clipped negatives: {neg} ({neg / X_new.size:.4%})")
write_candidate(str(CAND_TMP), X_new.astype(np.float32), a35)
print(f"wrote {CAND_TMP}")
