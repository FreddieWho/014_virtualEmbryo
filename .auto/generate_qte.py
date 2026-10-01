"""iter12 (Route C): quantile-space trend extrapolation (QTE). NEW ALGORITHM.

Motivation: every prior extrapolation lane shifted the per-state MEAN of each gene
(baseline delta / shrink / cap), which leaves within-state distribution shape untouched
and destroys mass via clipping. This algorithm extrapolates the full per-gene MARGINAL
instead: for each state s and gene g, build quantile functions Q8 (E8.75) and Q9 (E9.5)
on a fixed probability grid, extrapolate one interval in quantile space

    Qpred(p) = Q9(p) + (Q9(p) - Q8(p))

then map each baseline cell to Qpred evaluated at its own within-state rank probability.
Because baseline rows ARE E9.5 cells, the mapping is exactly a per-quantile delta, i.e.
the mean shift generalised to the entire distribution. Deterministic, no RNG, no knobs
(the one-interval linear extrapolation is canonical; no lambda scan).
States without E8.75 support are left unchanged (same convention as v0001 lineage).
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


def main():
    panel = common.read_panel(PANEL)
    V = common.load_parent(PARENT, PARENT_SHA)
    XV = common.dense(V.X).astype(np.float64)
    tV = np.asarray(V.obs["celltype"].astype(str))
    X875, t875, _, _ = common.load_stage("data/E8.75.h5ad", panel)
    X95, t95, _, _ = common.load_stage("data/E9.5.h5ad", panel)
    pgrid = (np.arange(GRID) + 0.5) / GRID
    shared = sorted(set(t95.tolist()) & set(t875.tolist()))
    X_out = XV.copy()
    diag = {}
    for s in shared:
        m9 = t95 == s
        m8 = t875 == s
        A = X95[m9]            # (n9, G) E9.5
        B = X875[m8]           # (n8, G) E8.75
        n9, n8 = A.shape[0], B.shape[0]
        # within-state rank probability of every E9.5 cell, per gene
        order = np.argsort(A, axis=0, kind="stable")
        ranks = np.empty_like(order)
        np.put_along_axis(ranks, order, np.arange(n9)[:, None].repeat(A.shape[1], axis=1), axis=0)
        p = (ranks + 0.5) / n9                      # (n9, G)
        Q9 = np.quantile(A, pgrid, axis=0)          # (GRID, G)
        Q8 = np.quantile(B, pgrid, axis=0)
        Qpred = Q9 + (Q9 - Q8)
        # map every baseline cell of this state through Qpred at its own rank prob
        pred_idx = np.flatnonzero(tV == s)
        # baseline rows are E9.5 cells: align by obs_name where possible, else by order
        A_by_name = {str(n): i for i, n in enumerate(np.asarray(V.obs_names)[pred_idx])}
        # rank probabilities of baseline cells within their own state (recomputed, self-consistent)
        Xs = XV[pred_idx]
        o2 = np.argsort(Xs, axis=0, kind="stable")
        r2 = np.empty_like(o2)
        np.put_along_axis(r2, o2, np.arange(len(pred_idx))[:, None].repeat(Xs.shape[1], axis=1), axis=0)
        p2 = (r2 + 0.5) / len(pred_idx)
        new = np.empty_like(Xs)
        for g in range(Xs.shape[1]):
            new[:, g] = np.interp(p2[:, g], pgrid, Qpred[:, g])
        X_out[pred_idx] = new
        diag[s] = {"n9": int(n9), "n8": int(n8), "n_pred": int(len(pred_idx)),
                   "mean_shift_abs": float(np.abs(new.mean(0) - Xs.mean(0)).mean())}
    clip_frac = float((X_out < 0).mean())
    np.clip(X_out, 0, None, out=X_out)
    Xf = np.ascontiguousarray(X_out, dtype=np.float32)
    assert np.isfinite(Xf).all() and (Xf >= 0).all()
    out_a = V.copy()
    out_a.X = Xf
    common.fix_obsm(out_a)
    common.stamp_uns(out_a, normalization="log_normalized",
                     provenance={"atom_id": "AUTORESEARCH-T2-EXTRAP-C", "iter": 12,
                                 "method": "quantile_trend_extrapolation", "grid": GRID,
                                 "target_used": False})
    if OUT.exists():
        OUT.unlink()
    sha = common.write_candidate(out_a, OUT)
    print(f"iter12 QTE: sha={sha[:12]} clip={clip_frac:.4f} shared={shared}")
    print("diag:", {k: round(v['mean_shift_abs'], 4) for k, v in diag.items()})


if __name__ == "__main__":
    main()
