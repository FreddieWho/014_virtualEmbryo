"""iter14 (Route C): QTE-quadratic — 3-node Lagrange extrapolation in QUANTILE space.

Same marginal-mapping machinery as iter12, but the per-gene per-state quantile function
is extrapolated from three nodes (t=8.25, 8.75, 9.5) to t=10.5 by exact Lagrange
interpolation of the polynomial through those three points, evaluated per probability
grid point. States missing E8.25 fall back to the 2-point linear rule (iter12);
states missing E8.75 stay at baseline. Deterministic, no RNG, no knobs.
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
T825, T875, T95, TT = 8.25, 8.75, 9.5, 10.5


def lagrange3(y1, y2, y3):
    """Evaluate the quadratic through (T825,y1),(T875,y2),(T95,y3) at TT."""
    L1 = ((TT - T875) * (TT - T95)) / ((T825 - T875) * (T825 - T95))
    L2 = ((TT - T825) * (TT - T95)) / ((T875 - T825) * (T875 - T95))
    L3 = ((TT - T825) * (TT - T875)) / ((T95 - T825) * (T95 - T875))
    return L1 * y1 + L2 * y2 + L3 * y3


def main():
    panel = common.read_panel(PANEL)
    V = common.load_parent(PARENT, PARENT_SHA)
    XV = common.dense(V.X).astype(np.float64)
    tV = np.asarray(V.obs["celltype"].astype(str))
    XL = {}
    for k, rel in (("e825", "data/E8.25_late.h5ad"), ("e875", "data/E8.75.h5ad"), ("e95", "data/E9.5.h5ad")):
        X, t, _, _ = common.load_stage(rel, panel)
        XL[k] = (X, t)
    pgrid = (np.arange(GRID) + 0.5) / GRID
    X_out = XV.copy()
    mode = {}
    for s in sorted(set(tV.tolist())):
        have = [k for k in ("e825", "e875", "e95") if (XL[k][1] == s).sum() >= 50]
        pred_idx = np.flatnonzero(tV == s)
        Xs = XV[pred_idx]
        o = np.argsort(Xs, axis=0, kind="stable")
        r = np.empty_like(o)
        np.put_along_axis(r, o, np.arange(len(pred_idx))[:, None].repeat(Xs.shape[1], axis=1), axis=0)
        p2 = (r + 0.5) / len(pred_idx)
        if "e95" not in have or "e875" not in have:
            mode[s] = "unchanged"
            continue
        Q9 = np.quantile(XL["e95"][0][XL["e95"][1] == s], pgrid, axis=0)
        Q8 = np.quantile(XL["e875"][0][XL["e875"][1] == s], pgrid, axis=0)
        if "e825" in have:
            Q5 = np.quantile(XL["e825"][0][XL["e825"][1] == s], pgrid, axis=0)
            Qpred = lagrange3(Q5, Q8, Q9)
            mode[s] = "quad"
        else:
            Qpred = Q9 + (Q9 - Q8)
            mode[s] = "linear"
        new = np.empty_like(Xs)
        for g in range(Xs.shape[1]):
            new[:, g] = np.interp(p2[:, g], pgrid, Qpred[:, g])
        X_out[pred_idx] = new
    clip_frac = float((X_out < 0).mean())
    np.clip(X_out, 0, None, out=X_out)
    Xf = np.ascontiguousarray(X_out, dtype=np.float32)
    assert np.isfinite(Xf).all() and (Xf >= 0).all()
    out_a = V.copy()
    out_a.X = Xf
    common.fix_obsm(out_a)
    common.stamp_uns(out_a, normalization="log_normalized",
                     provenance={"atom_id": "AUTORESEARCH-T2-EXTRAP-C", "iter": 14,
                                 "method": "qte_lagrange3_quantile_space", "grid": GRID, "target_used": False})
    if OUT.exists():
        OUT.unlink()
    sha = common.write_candidate(out_a, OUT)
    from collections import Counter
    print(f"iter14 QTE3: sha={sha[:12]} clip={clip_frac:.4f} modes={dict(Counter(mode.values()))}")


if __name__ == "__main__":
    main()
