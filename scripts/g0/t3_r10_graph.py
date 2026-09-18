#!/usr/bin/env python3
"""G1-T3-R10 GRAPH (D3): embryo coexpression kNN graph + Gata4 seed propagation.

GEARS needs perturbation training data (absent) — substitute its core idea
(unseen gene placed via knowledge graph) with: E8.75 WT gene-gene Pearson graph
(5k-cell subsample, kNN k=15 symmetrized row-stochastic) + personalized PageRank
from Gata4 seed (alpha 0.85, 50 iters). Shift magnitude propto propagation score
(top-150), sign from CellOracle majority, cardiac-full/else-half gate.
Gata4 -> 0. Deterministic.
"""
import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "g0"))
import anndata as ad
import numpy as np
from scipy import sparse
from _t3_util import (AMPL, CAP_FRAC, E875, finalize, load_base, wt_dispersion,
                      cello_stat, apply_lineage, RUN_SEED)

TASK_ID = "G1-T3-R10-GRAPH"
SUB_N = 5000
SUB_SEED = 20260917
KNN = 15
ALPHA = 0.85
ITERS = 50
TOPK = 150


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--out-version", default="v0022_g0_t3_r10_graph")
    args = ap.parse_args()
    base = load_base()
    panel, gidx = base["panel"], base["gidx"]
    src = ad.read_h5ad(E875, backed="r")
    svar = [str(v) for v in src.var_names]
    pidx = [svar.index(p) for p in panel]
    rng = np.random.default_rng(SUB_SEED)
    idx = rng.choice(src.shape[0], size=SUB_N, replace=False)
    Xs = src.X[idx][:, pidx]
    if sparse.issparse(Xs):
        Xs = Xs.toarray()
    Xs = np.asarray(Xs, dtype=np.float64)
    src.file.close()
    C = np.corrcoef(Xs.T)
    C = np.nan_to_num(C, nan=0.0)
    np.fill_diagonal(C, 0.0)
    W = np.zeros_like(C)
    nn = np.argsort(-np.abs(C), axis=1)[:, :KNN]
    for i in range(len(panel)):
        W[i, nn[i]] = np.abs(C[i, nn[i]])
    W = np.maximum(W, W.T)
    rs = W.sum(1, keepdims=True)
    P = W / np.maximum(rs, 1e-12)
    seed = np.zeros(len(panel))
    seed[gidx["Gata4"]] = 1.0
    v = seed.copy()
    for _ in range(ITERS):
        v = ALPHA * (P.T @ v) + (1 - ALPHA) * seed
    v[gidx["Gata4"]] = 0.0
    keep = np.argsort(-v)[:TOPK]
    vmax = float(v[keep[0]])
    stat = cello_stat()
    disp = wt_dispersion(panel)
    shifts = {}
    for i in keep:
        gene = panel[i]
        sign = float(stat.loc[gene, "sign_maj"]) if gene in stat.index else 0.0
        if sign == 0.0:
            continue
        rsd, rng_ = disp[gene]
        shifts[gene] = sign * min(AMPL * rsd, CAP_FRAC * rng_) * (float(v[i]) / vmax)
    Xout = apply_lineage(base["Xout"], gidx, shifts, base["cardiac"], fallback=0.5)
    rows = sorted(shifts.items(), key=lambda kv: abs(kv[1]), reverse=True)[:5]
    finalize(Xout, base, args.out_version, Path(args.run_dir),
             {"atom_id": TASK_ID, "lane": "L_A_GRAPH", "method": "coexp_ppr_from_gata4",
              "parent": "v0009 rows", "seed": RUN_SEED, "target_used": False,
              "atom_short": "g0_t3_r10"},
             "L_A_GRAPH", {"task": TASK_ID, "identity_repro_v0009": True,
                           "n_shifted": len(shifts),
                           "cardiac_frac": float(base["cardiac"].mean()),
                           "top5": [{"gene": g_, "shift": s_} for g_, s_ in rows]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
