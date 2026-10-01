"""T1-6 mild composition-tilt probe (whole-row, 3 seeds).

Desired type counts = halfway between v0035-report counts and E9.5-train
proportions (largest-remainder to 3357; types absent from train keep halfway
toward 0, i.e. halve — the rule is uniform, no per-type tuning). Draw whole
v0035-report rows per type with a frozen seed (replacement only when a type needs
more rows than available). Total stays 3357. Donor-correct obs rebuilt.

Mild strength is untested (s1growth pushed 0.5->0.75 at full scope and lost on
server; this halves the step at report scope). Refs: train via frozen SPLITS only.
Usage: python .auto/generate_t1_comptilt.py <seed>
"""
import sys
import numpy as np
import pandas as pd
import anndata as ad
from pathlib import Path
sys.path.insert(0, ".auto")
from t1_common import dense, CAND_TMP  # noqa

ROOT = Path(".").resolve()
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 20261020
rng = np.random.default_rng(seed)
s = np.load(ROOT / "artifacts/t1_three/T1-THREE-20260929-v1/shared/SPLITS.npz")
tr95 = s["train95"]
e95t = ad.read_h5ad(ROOT / "data/E9.5_RNA.h5ad").obs["celltype"].astype(str).to_numpy()
prop = pd.Series(e95t[tr95]).value_counts(normalize=True)
a = ad.read_h5ad(ROOT / "artifacts/t1_three/T1-THREE-20260929-v1/r2joint/report_prediction.h5ad")
X = dense(a.X)
rt = a.obs["celltype"].astype(str).to_numpy()
cur = pd.Series(rt).value_counts()
tot = len(rt)
raw = {t: 0.5 * cur[t] + 0.5 * tot * prop.get(t, 0.0) for t in cur.index}
base = {t: int(np.floor(v)) for t, v in raw.items()}
rem = tot - sum(base.values())
# raw need not sum to tot (train vocab misses ~48% of report mass): first honor
# fractional parts, then top up any remaining shortfall pro-rata to current counts.
frac_order = sorted(cur.index, key=lambda t: raw[t] - base[t], reverse=True)
want = dict(base)
for t in frac_order[:max(0, min(rem, len(frac_order)))]:
    want[t] += 1
deficit = tot - sum(want.values())
if deficit > 0:
    extra = {t: deficit * cur[t] / tot for t in cur.index}
    ebase = {t: int(np.floor(v)) for t, v in extra.items()}
    erem = deficit - sum(ebase.values())
    eorder = sorted(cur.index, key=lambda t: extra[t] - ebase[t], reverse=True)
    for t in cur.index:
        want[t] += ebase[t]
    for t in eorder[:erem]:
        want[t] += 1
assert sum(want.values()) == tot
idx, lab = [], []
for t in cur.index:
    pool = np.flatnonzero(rt == t)
    k = want[t]
    pick = rng.choice(pool, size=k, replace=(k > len(pool)))
    idx.extend(pick.tolist())
    lab.extend([t] * k)
order = rng.permutation(len(idx))
idx = np.asarray(idx)[order]
lab = np.asarray(lab)[order]
assert len(idx) == tot
obs = pd.DataFrame({"celltype": pd.Categorical(lab)}, index=[f"tilt{i}" for i in range(tot)])
b = ad.AnnData(X=X[idx], obs=obs, var=a.var.copy())
b.uns["ve_contract"] = {"schema": "ve.contract.v1", "normalization": "log1p_normalized"}
b.uns["ve_t1_autoresearch"] = {"scope": "report_proxy_only", "target_used": False}
b.write_h5ad(str(CAND_TMP), compression="gzip", compression_opts=1)
print(f"T1-6 comptilt seed={seed} want_sum={sum(want.values())} -> {CAND_TMP}")
