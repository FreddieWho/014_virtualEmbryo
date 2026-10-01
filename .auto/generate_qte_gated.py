"""iter17 (Route C): significance-gated quantile trend extrapolation.

Same marginal mapping as iter12 (Qpred = Q9 + (Q9-Q8) per state per gene, cells mapped
through their within-state rank probability), but each (state, gene) pair is first tested
for evidence of real temporal change: Welch t on the E8.75 vs E9.5 cell populations,
Benjamini-Hochberg FDR at 0.05 across all pairs. Pairs that fail the gate keep their
baseline (E9.5) values, i.e. the do-nothing floor. Rationale: a quantile shift estimated
from noise adds noise; only move genes with evidence. Data-derived threshold, no scan,
deterministic, no RNG.
"""
from pathlib import Path
import numpy as np
import sys
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from scripts.t2_round2 import common

PARENT = "submissions/scored/baseline-001/T2_heart_val_extrap/submission.h5ad"
PARENT_SHA = "f30beba62da673bb4c980d92eec2bc9ea03696e5c2b65414307c2e0402bd7504"
PANEL = "data/gene_panel/T2__heart__val_extrap.genes.txt"
OUT = REPO / ".auto" / "candidate.h5ad"
GRID = 2001
FDR = 0.05


def main():
    panel = common.read_panel(PANEL)
    V = common.load_parent(PARENT, PARENT_SHA)
    XV = common.dense(V.X).astype(np.float64)
    tV = np.asarray(V.obs["celltype"].astype(str))
    X875, t875, _, _ = common.load_stage("data/E8.75.h5ad", panel)
    X95, t95, _, _ = common.load_stage("data/E9.5.h5ad", panel)
    pgrid = (np.arange(GRID) + 0.5) / GRID
    shared = sorted(set(t95.tolist()) & set(t875.tolist()))
    # ---- BH-FDR gate over all (state, gene) pairs
    tstats = []
    for s in shared:
        A, B = X95[t95 == s], X875[t875 == s]
        va, vb = A.var(0), B.var(0)
        se = np.sqrt(va / A.shape[0] + vb / B.shape[0]) + 1e-12
        tstats.append(np.abs((A.mean(0) - B.mean(0)) / se))
    T = np.concatenate(tstats)
    # two-sided p via normal approx (n large); BH
    from math import erfc, sqrt
    p = np.array([erfc(t / sqrt(2)) for t in T])
    order = np.argsort(p)
    m = len(p)
    thresh = np.zeros(m)
    prev = 1.0
    for k in range(m - 1, -1, -1):
        prev = min(prev, p[order[k]] * m / (k + 1))
        thresh[k] = prev
    keep_sorted = p[order] <= thresh
    keep = np.zeros(m, dtype=bool)
    keep[order[keep_sorted]] = True
    # reshape back per state
    idx = 0
    gates = {}
    for s in shared:
        n = len(tstats[len(gates)])
        gates[s] = keep[idx:idx + n]
        idx += n
    X_out = XV.copy()
    for s in shared:
        pred_idx = np.flatnonzero(tV == s)
        Xs = XV[pred_idx]
        o = np.argsort(Xs, axis=0, kind="stable")
        r = np.empty_like(o)
        np.put_along_axis(r, o, np.arange(len(pred_idx))[:, None].repeat(Xs.shape[1], axis=1), axis=0)
        p2 = (r + 0.5) / len(pred_idx)
        Q9 = np.quantile(X95[t95 == s], pgrid, axis=0)
        Q8 = np.quantile(X875[t875 == s], pgrid, axis=0)
        Qpred = Q9 + (Q9 - Q8)
        g = gates[s]
        for gi in np.flatnonzero(g):
            X_out[pred_idx, gi] = np.interp(p2[:, gi], pgrid, Qpred[:, gi])
    clip_frac = float((X_out < 0).mean())
    np.clip(X_out, 0, None, out=X_out)
    Xf = np.ascontiguousarray(X_out, dtype=np.float32)
    assert np.isfinite(Xf).all() and (Xf >= 0).all()
    out_a = V.copy()
    out_a.X = Xf
    common.fix_obsm(out_a)
    common.stamp_uns(out_a, normalization="log_normalized",
                     provenance={"atom_id": "AUTORESEARCH-T2-EXTRAP-C", "iter": 17,
                                 "method": "qte_fdr_gated", "fdr": FDR, "grid": GRID,
                                 "target_used": False})
    if OUT.exists():
        OUT.unlink()
    sha = common.write_candidate(out_a, OUT)
    frac = {s: round(float(gates[s].mean()), 3) for s in shared}
    print(f"iter17 gateQTE: sha={sha[:12]} clip={clip_frac:.4f} kept_frac={frac} "
          f"total_kept={int(keep.sum())}/{m}")


if __name__ == "__main__":
    main()
