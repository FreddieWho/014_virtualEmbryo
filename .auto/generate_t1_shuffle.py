"""T1-10 shuffle control: permute v0035 donors within type (3 seeds).

Takes the frozen best_donors vector and randomly permutes donor assignment AMONG
same-type slots (composition/type counts unchanged, density info destroyed).
If output ~= v0035 locally, within-type selection is irrelevant to the proxy
(strong bound on the whole family). If it collapses, selection matters.
Whole rows, donor-correct obs, guardrails as usual.

Usage: python .auto/generate_t1_shuffle.py <seed>
"""
import sys
import numpy as np
import pandas as pd
import anndata as ad
from pathlib import Path
sys.path.insert(0, ".auto")
from t1_common import CAND_TMP  # noqa

ROOT = Path(".").resolve()
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 20261029
rng = np.random.default_rng(seed)
SH = ROOT / "artifacts/t1_seven/T1-SEVEN-20260930-v1/shared/report"
mass = np.load(SH / "mass.npy").astype(np.float32)
bd = np.load(SH / "best_donors.npy")
s = np.load(ROOT / "artifacts/t1_three/T1-THREE-20260929-v1/shared/SPLITS.npz")
e85 = ad.read_h5ad(ROOT / "data/E8.5_RNA.h5ad")
pt = e85.obs["celltype"].astype(str).to_numpy()[s["report85"]]
del e85
slot_type = pt[bd]  # type wanted by each slot (= donor's type)
perm = bd.copy()
for t in np.unique(slot_type):
    ix = np.flatnonzero(slot_type == t)
    perm[ix] = rng.permutation(perm[ix])
n_change = int((perm != bd).sum())
out = mass[perm]
lab = pt[perm]
rep = ad.read_h5ad(ROOT / "artifacts/t1_three/T1-THREE-20260929-v1/r2joint/report_prediction.h5ad")
obs = pd.DataFrame({"celltype": pd.Categorical(lab)}, index=[f"shuf{i}" for i in range(len(out))])
b = ad.AnnData(X=np.asarray(out, dtype=np.float32), obs=obs, var=rep.var.copy())
b.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": "log1p_normalized"}
b.uns["ve_t1_autoresearch"] = {"scope": "report_proxy_only", "target_used": False,
                               "note": f"within-type donor shuffle seed={seed}"}
b.write_h5ad(str(CAND_TMP), compression="gzip", compression_opts=1)
print(f"T1-10 shuffle seed={seed} donor_changes={n_change}/{len(perm)} -> {CAND_TMP}")
