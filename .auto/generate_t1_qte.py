"""T1-2 plain per-type per-gene quantile trend extrapolation (deterministic).

For each recipient type T (from baseline report obs):
  QA_T = sorted E8.5-train values, QB_T = sorted E9.5-train values (SPLITS train85/95
  from artifacts/t1_three/.../shared/SPLITS.npz — same frozen seed-20260921 split).
  Qpred_T = QB_T + (QB_T - QA_T)   [factor 1.0: E8.5->E9.5 interval (1 day) equals
  E9.5->E10.5 horizon (1 day); no time correction, unlike T2's 4/3].
Each baseline report row maps through its own within-recipient-type rank probability.
Types with <5 train cells on either stage -> rows unchanged (fallback).
Negative Qpred clipped at 0 (clip fraction reported).

Structurally distinct from R1-B (no zero/positive split) and o1mass (no parametric
form): full-marginal linear extrap, single data-frozen shot, no scan.

Reads (allowed, source-only): data/E8.5_RNA.h5ad, data/E9.5_RNA.h5ad, SPLITS.npz,
baseline report. NEVER reads pseudo_target (eval target) or E10.5 truth.

Usage: python .auto/generate_t1_qte.py -> writes .auto/t1_candidate.h5ad
"""
import sys
import numpy as np
import anndata as ad
from pathlib import Path
sys.path.insert(0, ".auto")
from t1_common import load_baseline_report, dense, write_candidate, CAND_TMP  # noqa

ROOT = Path(".").resolve()
SPLITS = ROOT / "artifacts/t1_three/T1-THREE-20260929-v1/shared/SPLITS.npz"
GENES = (ROOT / "data/gene_panel/T1__val.genes.txt").read_text().splitlines()

a, X = load_baseline_report()
rtypes = a.obs["celltype"].astype(str).to_numpy()
s = np.load(SPLITS)
tr85, tr95 = s["train85"], s["train95"]

e85 = ad.read_h5ad(ROOT / "data/E8.5_RNA.h5ad")
e95 = ad.read_h5ad(ROOT / "data/E9.5_RNA.h5ad")
ix85 = e85.var_names.get_indexer(GENES)
ix95 = e95.var_names.get_indexer(GENES)
assert (ix85 >= 0).all() and (ix95 >= 0).all()
t85 = e85.obs["celltype"].astype(str).to_numpy()
t95 = e95.obs["celltype"].astype(str).to_numpy()
X85 = dense(e85.X[:, ix85])
X95 = dense(e95.X[:, ix95])
del e85, e95

out = np.empty_like(X)
n_map = n_fallback = 0
per_type = {}
BLOCK = 4096
G = X.shape[1]
for typ in np.unique(rtypes):
    rix = np.flatnonzero(rtypes == typ)
    A = X85[np.ix_(tr85[t85[tr85] == typ])] if False else None  # placeholder (replaced below)
    # train cells of this type on each stage
    a_idx = tr85[t85[tr85] == typ]
    b_idx = tr95[t95[tr95] == typ]
    if len(a_idx) < 5 or len(b_idx) < 5:
        out[rix] = X[rix]
        n_fallback += len(rix)
        per_type[typ] = {"mode": "fallback", "n_rec": len(rix), "n85": len(a_idx), "n95": len(b_idx)}
        continue
    A = X85[a_idx]
    B = X95[b_idx]
    QA = np.sort(A, axis=0).astype(np.float64)
    QB = np.sort(B, axis=0).astype(np.float64)
    nA, nB = len(A), len(B)
    gA = (np.arange(nA) + 0.5) / nA
    gB = (np.arange(nB) + 0.5) / nB
    R = X[rix].astype(np.float64)
    nR = len(rix)
    Y = np.empty_like(R)
    for lo in range(0, G, BLOCK):
        hi = min(G, lo + BLOCK)
        Rb = R[:, lo:hi]
        order = np.argsort(Rb, axis=0, kind="stable")
        rank = np.empty_like(order)
        rank[order, np.arange(hi - lo)] = np.arange(nR)[:, None]
        p = (rank + 0.5) / nR
        qa = np.empty_like(Rb)
        qb = np.empty_like(Rb)
        for j in range(hi - lo):
            qa[:, j] = np.interp(p[:, j], gA, QA[:, lo + j])
            qb[:, j] = np.interp(p[:, j], gB, QB[:, lo + j])
        Y[:, lo:hi] = qb + (qb - qa)
    neg = int((Y < 0).sum())
    Y = np.clip(Y, 0, None)
    out[rix] = Y.astype(np.float32)
    n_map += len(rix)
    per_type[typ] = {"mode": "qte", "n_rec": len(rix), "n85": len(a_idx), "n95": len(b_idx),
                     "neg_frac": neg / (len(rix) * G)}
    del A, B, QA, QB, R, Y
neg_total = int((out < 0).sum())
assert (out >= 0).all() and np.isfinite(out).all()
write_candidate(CAND_TMP, out, a)
import json
print(json.dumps({"mapped": n_map, "fallback": n_fallback,
                  "types": len(per_type),
                  "fallback_types": [t for t, v in per_type.items() if v["mode"] == "fallback"]}))
print(f"T1-2 QTE done -> {CAND_TMP}")
