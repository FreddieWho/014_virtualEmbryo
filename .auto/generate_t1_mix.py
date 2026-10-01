"""T1-4 winner-ensemble probe: v0035 x v0038 whole-row coin-flip mix (3 seeds).

Both parents are server winners (v0035 53.43 = joint-selection, v0038 53.55 =
covOT-projection on the same v0035 base). Per report slot, a frozen coin flip
(seed) picks the v0035 row or the v0038 row WHOLE (no averaging — averaging would
break coexpression per the T1 whole-row lesson; mirrors s2mix/r3mix construction
but with a new pair). Slot order verified identical before mixing.
Resampling design -> 3 seeds (median+min bar).

Reads: both report_prediction.h5ad files (research outputs, not submissions).
Writes .auto/t1_candidate.h5ad.

Usage: python .auto/generate_t1_mix.py <seed>
"""
import sys
import numpy as np
import anndata as ad
from pathlib import Path
sys.path.insert(0, ".auto")
from t1_common import dense, write_candidate, CAND_TMP  # noqa

ROOT = Path(".").resolve()
P35 = ROOT / "artifacts/t1_three/T1-THREE-20260929-v1/r2joint/report_prediction.h5ad"
P38 = ROOT / "artifacts/t1_seven/T1-SEVEN-20260930-v1/n2covot/report_prediction.h5ad"

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 20261014
rng = np.random.default_rng(seed)
a = ad.read_h5ad(P35)
b = ad.read_h5ad(P38)
assert a.shape == b.shape, (a.shape, b.shape)
assert np.array_equal(np.asarray(a.obs_names), np.asarray(b.obs_names)), "slot order drift"
assert np.array_equal(a.obs["celltype"].astype(str), b.obs["celltype"].astype(str)), "slot type drift"
X, Y = dense(a.X), dense(b.X)
coin = rng.random(len(a)) < 0.5
out = np.where(coin[:, None], X, Y)
print(f"T1-4 mix seed={seed} frac_v0035={coin.mean():.3f} n={out.shape}")
write_candidate(CAND_TMP, out, a)
