#!/usr/bin/env python3
"""G1-T3-R9 HOP2 (D4 reframed): two-hop coexpression decay.

D4 LLM-embedding is infeasible without API (recorded) AND motif scores are binary
(17 x 1.0, rest 0 — verified 2026-09-17), so graded-motif is dead too. Substitute:
hop1 = 17 motif genes (R1 sign/amplitude rule: -sign(pearson_wt)x0.15rsd, cap);
hop2 = top-40 genes by max|corr| with any hop1 gene in E8.75 WT (fixed 5k-cell
subsample, seed locked), amplitude x0.5 decay, sign aligned to the best-correlated
hop1 gene's shift direction. Global application (no lineage gate — differs from R6).
Gata4 -> 0. Deterministic.
"""
import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "g0"))
import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse
from _t3_util import (AMPL, CAP_FRAC, E875, E95WT, GRN, finalize, load_base,
                      wt_dispersion, RUN_SEED)

TASK_ID = "G1-T3-R9-HOP2"
SUB_N = 5000
SUB_SEED = 20260917


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--out-version", default="v0021_g0_t3_r9_hop2")
    args = ap.parse_args()
    base = load_base()
    panel, gidx = base["panel"], base["gidx"]
    df = pd.read_parquet(GRN, columns=["gene_short_name", "Gata4"])
    sub = df[df["gene_short_name"].isin(panel)].drop_duplicates("gene_short_name")
    hop1 = sorted(sub[sub["Gata4"] > 0]["gene_short_name"].tolist())
    hop1 = [g for g in hop1 if g != "Gata4"]
    assert len(hop1) == 17, f"hop1 drift: {len(hop1)}"
    # R1 sign rule from E9.5 WT Pearson(Gata4, target).
    w = ad.read_h5ad(E95WT, backed="r")
    var = [str(v) for v in w.var_names]
    cols = ["Gata4"] + hop1
    ci = [var.index(c) for c in cols]
    X = w.X[:, ci]
    if sparse.issparse(X):
        X = X.toarray()
    X = np.asarray(X, dtype=np.float64)
    w.file.close()
    g = X[:, 0]
    disp = wt_dispersion(hop1)
    shifts = {}
    hop1_shift = {}
    for j, gene in enumerate(hop1):
        x = X[:, 1 + j]
        r = float(np.corrcoef(g, x)[0, 1]) if np.std(g) > 0 and np.std(x) > 0 else 0.0
        s = int(np.sign(r)) if r != 0 else 0
        rsd, rng = disp[gene]
        amp = min(AMPL * rsd, CAP_FRAC * rng)
        shifts[gene] = -s * amp if s != 0 else 0.0
        hop1_shift[gene] = shifts[gene]
    # hop2: coexpression with hop1 set in E8.75 WT subsample.
    src = ad.read_h5ad(E875, backed="r")
    rng = np.random.default_rng(SUB_SEED)
    idx = rng.choice(src.shape[0], size=SUB_N, replace=False)
    Xs = src.X[idx]
    if sparse.issparse(Xs):
        Xs = Xs.toarray()
    Xs = np.asarray(Xs, dtype=np.float64)
    svar = [str(v) for v in src.var_names]
    pidx = [svar.index(p) for p in panel]
    P = Xs[:, pidx]
    src.file.close()
    hcol = np.column_stack([Xs[:, svar.index(h)] for h in hop1])  # SUB_N x 17
    Pc = P - P.mean(0)
    Hc = hcol - hcol.mean(0)
    denom = np.sqrt((Pc ** 2).sum(0))[:, None] * np.sqrt((Hc ** 2).sum(0))[None, :]
    C = (Pc.T @ Hc) / np.maximum(denom, 1e-12)
    best = np.abs(C).max(1)
    bj = C[np.arange(len(panel)), np.abs(C).argmax(1)]
    order = np.argsort(-best)
    hop2 = []
    for oi in order:
        gene = panel[oi]
        if gene in hop1 or gene == "Gata4":
            continue
        hop2.append((gene, float(best[oi]), float(bj[oi])))
        if len(hop2) == 40:
            break
    disp2 = wt_dispersion([h[0] for h in hop2])
    for gene, bc, bcorr in hop2:
        anchor = hop1[int(np.abs(C[panel.index(gene)]).argmax())]
        asgn = float(np.sign(hop1_shift[anchor])) if hop1_shift[anchor] != 0 else 0.0
        if asgn == 0.0:
            continue
        rsd, rng_ = disp2[gene]
        shifts[gene] = asgn * float(np.sign(bcorr)) * min(AMPL * rsd, CAP_FRAC * rng_) * 0.5
    Xout = base["Xout"]
    for gene, s in shifts.items():
        if s != 0.0:
            Xout[:, gidx[gene]] = Xout[:, gidx[gene]] + s
    rows = sorted(shifts.items(), key=lambda kv: abs(kv[1]), reverse=True)[:5]
    finalize(Xout, base, args.out_version, Path(args.run_dir),
             {"atom_id": TASK_ID, "lane": "L_A_HOP2", "method": "motif_hop1_plus_coexp_hop2_decay",
              "parent": "v0009 rows", "seed": RUN_SEED, "target_used": False,
              "atom_short": "g0_t3_r9"},
             "L_A_HOP2", {"task": TASK_ID, "identity_repro_v0009": True,
                          "n_hop1": len(hop1), "n_hop2": len(hop2),
                          "n_shifted": sum(1 for s in shifts.values() if s != 0),
                          "top5": [{"gene": g_, "shift": s_} for g_, s_ in rows]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
