"""T1-3 QTE-steered whole-row donor projection (deterministic).

Steering: same per-type QTE target vectors as T1-2 (Qpred = QB+(QB-QA), rank-mapped).
Output: for each recipient row, the EXACT nearest E9.5-train donor row of the same
type (euclidean in log1p gene space, BLAS form, no approximation, no RNG).
Fallback types (<5 train cells either stage) keep baseline rows.
Hypothesis: QTE carries direction signal (T1-2 dir +0.072) while whole rows preserve
coexpression (repairs T1-2 energy 0.348 veto). Single data-frozen shot.

Reads (source-only): data/E8.5/E9.5, SPLITS.npz, baseline report. No target peeking.
Writes .auto/t1_candidate.h5ad (report slots keep template obs/var identity).
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
t85 = e85.obs["celltype"].astype(str).to_numpy()
t95 = e95.obs["celltype"].astype(str).to_numpy()
X85 = dense(e85.X[:, ix85]).astype(np.float64)
X95 = dense(e95.X[:, ix95]).astype(np.float64)
del e85, e95

out = np.empty_like(X)
G = X.shape[1]
BLOCK = 4096
stats = {}
for typ in np.unique(rtypes):
    rix = np.flatnonzero(rtypes == typ)
    ai = tr85[t85[tr85] == typ]
    bi = tr95[t95[tr95] == typ]
    if len(ai) < 5 or len(bi) < 5:
        out[rix] = X[rix]
        stats[typ] = {"mode": "fallback", "n_rec": len(rix)}
        continue
    A, B = X85[ai], X95[bi]
    QA = np.sort(A, axis=0)
    QB = np.sort(B, axis=0)
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
        for j in range(hi - lo):
            qa = np.interp(p[:, j], gA, QA[:, lo + j])
            qb = np.interp(p[:, j], gB, QB[:, lo + j])
            Y[:, lo:hi][:, j] = qb + (qb - qa)
    Y = np.clip(Y, 0, None).astype(np.float32)
    D = B.astype(np.float32)  # donor pool (same type, E9.5 train)
    # exact nearest donor per recipient: argmin ||Y-d||^2 via BLAS
    Yn = (Y * Y).sum(1)
    Dn = (D * D).sum(1)
    CH = 256
    pick = np.empty(nR, dtype=np.int64)
    for lo in range(0, nR, CH):
        hi = min(nR, lo + CH)
        G2 = Y[lo:hi] @ D.T
        d2 = Yn[lo:hi, None] + Dn[None, :] - 2 * G2
        pick[lo:hi] = np.argmin(d2, axis=1)
    out[rix] = D[pick]
    stats[typ] = {"mode": "projected", "n_rec": len(rix),
                  "n_donors": len(bi), "uniq_donors": int(len(np.unique(pick)))}
    del A, B, QA, QB, R, Y, D
assert (out >= 0).all() and np.isfinite(out).all()
write_candidate(CAND_TMP, out, a)
proj = sum(v["n_rec"] for v in stats.values() if v["mode"] == "projected")
fb = sum(v["n_rec"] for v in stats.values() if v["mode"] == "fallback")
print(f"T1-3 projected={proj} fallback={fb} types={len(stats)} -> {CAND_TMP}")
