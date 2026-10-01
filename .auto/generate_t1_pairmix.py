"""T1-5 winner-pair mix at report level: r2joint(v0035) x r3mix(v0036) stratified mix.

Mirrors the server-winning s2mix construction (70/30 stratified whole-row mix of
the best+backup pair) but at report scope with the ACTUAL pair members
(r2joint-report x r3mix-report rows). Fraction scan {0.5, 0.7, 0.85} (fraction of
slots taken from r2joint side), one seed per fraction for the curve + 3-seed
confirm on candidates. Per-type largest-remainder quotas, no-replacement draw
inside each side, frozen seed, slot order verified identical. Whole rows only.

Reads: r2joint + r3mix report_prediction.h5ad (research outputs).
Usage: python .auto/generate_t1_pairmix.py <fraction> <seed>
"""
import sys
import numpy as np
import anndata as ad
from pathlib import Path
sys.path.insert(0, ".auto")
sys.path.insert(0, "scripts/t1_three")
from t1_common import dense, write_candidate, CAND_TMP  # noqa
from ops import mixture_indices  # noqa

ROOT = Path(".").resolve()
FILES = {"35": ROOT / "artifacts/t1_three/T1-THREE-20260929-v1/r2joint/report_prediction.h5ad",
         "36": ROOT / "artifacts/t1_three/T1-THREE-20260929-v1/r3mix/report_prediction.h5ad",
         "38": ROOT / "artifacts/t1_seven/T1-SEVEN-20260930-v1/n2covot/report_prediction.h5ad"}
PA = FILES[sys.argv[3]] if len(sys.argv) > 3 else FILES["35"]
PB = FILES[sys.argv[4]] if len(sys.argv) > 4 else FILES["36"]

frac = float(sys.argv[1]) if len(sys.argv) > 1 else 0.7
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 20260921
a = ad.read_h5ad(PA)
b = ad.read_h5ad(PB)
assert a.shape == b.shape
assert np.array_equal(np.asarray(a.obs_names), np.asarray(b.obs_names)), "slot drift"
ta = a.obs["celltype"].astype(str).to_numpy()
tb = b.obs["celltype"].astype(str).to_numpy()
X, Y = dense(a.X), dense(b.X)
sides, rows = mixture_indices(ta, tb, frac, seed)
out = np.empty_like(X)
ptypes = np.empty(len(out), dtype=object)
ta_arr = ta
for i, (s, r) in enumerate(zip(sides.tolist(), rows.tolist())):
    out[i] = X[r] if s == 0 else Y[r]
    ptypes[i] = ta[r] if s == 0 else tb[r]
n_a = int((sides == 0).sum())
print(f"T1-5 pairmix frac={frac} seed={seed} nA={n_a}/{len(out)} -> {CAND_TMP}")
import pandas as pd
obs = pd.DataFrame({"celltype": pd.Categorical(ptypes)},
                   index=[f"mix{i}" for i in range(len(out))])
b = ad.AnnData(X=out.astype(np.float32), obs=obs, var=a.var.copy())
b.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": "log1p_normalized"}
b.uns["ve_t1_autoresearch"] = {"scope": "report_proxy_only", "target_used": False,
                                "note": "pairmix slots carry donor type labels"}
b.write_h5ad(str(CAND_TMP), compression="gzip", compression_opts=1)
