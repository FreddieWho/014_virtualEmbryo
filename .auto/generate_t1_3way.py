"""T1-11 three-way winner mix at report level: r2joint(35) x r3mix(36) x n2covot(38).

Equal thirds (data-frozen, no knob): quotas n/3 each with largest-remainder
rounding; per-type allocation within each side; no-replacement draw; frozen seed.
Whole rows only, donor-correct obs. Reads the three recorded report files.
Usage: python .auto/generate_t1_3way.py <seed>
"""
import sys
import numpy as np
import anndata as ad
import pandas as pd
from pathlib import Path
sys.path.insert(0, ".auto")
sys.path.insert(0, "scripts/t1_three")
from t1_common import dense, CAND_TMP  # noqa
from ops import allocation  # noqa

ROOT = Path(".").resolve()
F35 = ROOT / "artifacts/t1_three/T1-THREE-20260929-v1/r2joint/report_prediction.h5ad"
F36 = ROOT / "artifacts/t1_three/T1-THREE-20260929-v1/r3mix/report_prediction.h5ad"
F38 = ROOT / "artifacts/t1_seven/T1-SEVEN-20260930-v1/n2covot/report_prediction.h5ad"

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 20260921
aa = ad.read_h5ad(F35)
bb = ad.read_h5ad(F36)
cc = ad.read_h5ad(F38)
assert aa.shape == bb.shape == cc.shape, (aa.shape, bb.shape, cc.shape)
assert np.array_equal(np.asarray(aa.obs_names), np.asarray(bb.obs_names))
assert np.array_equal(np.asarray(aa.obs_names), np.asarray(cc.obs_names)), "slot drift"
mats = [dense(aa.X), dense(bb.X), dense(cc.X)]
types = [aa.obs["celltype"].astype(str).to_numpy(),
         bb.obs["celltype"].astype(str).to_numpy(),
         cc.obs["celltype"].astype(str).to_numpy()]
n = aa.shape[0]
# equal-thirds quotas with largest remainder
base = n // 3
quotas = [base, base, base]
for i in range(n - 3 * base):
    quotas[i] += 1
rng = np.random.default_rng(seed)
rows, sides = [], []
for side, (t, q) in enumerate(zip(types, quotas)):
    for tt, k in allocation(t, q).items():
        chosen = rng.permutation(np.flatnonzero(t == tt))[:int(k)]
        rows.extend(chosen.tolist())
        sides.extend([side] * len(chosen))
order = rng.permutation(n)
rows = np.asarray(rows)[order]
sides = np.asarray(sides)[order]
out = np.empty_like(mats[0])
ptypes = np.empty(n, dtype=object)
for i, (s, r) in enumerate(zip(sides.tolist(), rows.tolist())):
    out[i] = mats[s][r]
    ptypes[i] = types[s][r]
print(f"T1-11 3way equal-thirds seed={seed} quotas={quotas} -> {CAND_TMP}")
obs = pd.DataFrame({"celltype": pd.Categorical(ptypes)},
                   index=[f"mix3_{i}" for i in range(n)])
b = ad.AnnData(X=out.astype(np.float32), obs=obs, var=aa.var.copy())
b.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": "log1p_normalized"}
b.uns["ve_t1_autoresearch"] = {"scope": "report_proxy_only", "target_used": False,
                               "note": "3way equal-thirds whole-row mix 35/36/38"}
b.write_h5ad(str(CAND_TMP), compression="gzip", compression_opts=1)
