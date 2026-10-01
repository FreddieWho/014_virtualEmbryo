"""T1-9 density-temperature tilt on the frozen r2joint draw (deterministic).

Same pool (mass.npy), same pool types (E8.5 report85), same composition plan,
only the density weights are tempered: w^T with T in {0.5, 2.0}. T=1.0 must
reproduce best_donors exactly (asserted = control). T=2 sharpens density
selection, T=0.5 flattens toward uniform. Output = mass[donor] whole rows with
donor-correct obs. No RNG, no target peeking (train pools + frozen caches only).

Usage: python .auto/generate_t1_densT.py <T>
"""
import sys
import numpy as np
import pandas as pd
import anndata as ad
from pathlib import Path
sys.path.insert(0, ".auto")
sys.path.insert(0, "scripts/t1_three")
from t1_common import CAND_TMP  # noqa
from ops import joint_donors  # noqa

ROOT = Path(".").resolve()
T = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
SH = ROOT / "artifacts/t1_seven/T1-SEVEN-20260930-v1/shared/report"
mass = np.load(SH / "mass.npy").astype(np.float32)
w = np.load(SH / "weights.npy").astype(np.float64)
c = np.load(SH / "composition.npy")
bd = np.load(SH / "best_donors.npy")
s = np.load(ROOT / "artifacts/t1_three/T1-THREE-20260929-v1/shared/SPLITS.npz")
e85 = ad.read_h5ad(ROOT / "data/E8.5_RNA.h5ad")
pt = e85.obs["celltype"].astype(str).to_numpy()[s["report85"]]
del e85
ctl = joint_donors(pt, w, c)
assert np.array_equal(ctl, bd), "T=1.0 control drift — frozen cache moved, STOP"
wT = np.power(w, T)
donor = joint_donors(pt, wT, c) if T != 1.0 else ctl
out = mass[donor]
lab = pt[donor]
n_change = int((donor != bd).sum())
obs = pd.DataFrame({"celltype": pd.Categorical(lab)}, index=[f"densT{i}" for i in range(len(out))])
rep = ad.read_h5ad(ROOT / "artifacts/t1_three/T1-THREE-20260929-v1/r2joint/report_prediction.h5ad")
b = ad.AnnData(X=np.asarray(out, dtype=np.float32), obs=obs, var=rep.var.copy())
b.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": "log1p_normalized"}
b.uns["ve_t1_autoresearch"] = {"scope": "report_proxy_only", "target_used": False,
                               "note": f"density temperature T={T}"}
b.write_h5ad(str(CAND_TMP), compression="gzip", compression_opts=1)
print(f"T1-9 densT T={T} donor_changes_vs_v0035={n_change}/{len(donor)} -> {CAND_TMP}")
