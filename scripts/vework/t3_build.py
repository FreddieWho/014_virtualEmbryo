#!/usr/bin/env python
"""T3 builders from released WT only (no KO data of any gene is read here).

carrier   : 'uniform'      -> uniform random draw of n WT cells (v0008 class; scored 46.79 on gata4)
            'strat_pbmatch'-> per-celltype stratified draw + per-gene rescale to the full-WT pseudobulk (A/B, 45.7-45.9)
genotype  : --zero GENE[,..] in --lineage cells; --half GENE[,..] (counts x0.5, heterozygous) in lineage cells
program   : 'program loss' (v0048-like mechanism generalised to a gene PROGRAM; usable when the KO gene is not on
            the panel, e.g. Ctnnb1): activity a_i = mean within-WT z-score of --program genes; per gene, ridge slope of
            log-expression on a_i with celltype fixed effects, fitted on lineage cells; slopes shrunk |t|/(|t|+2);
            KO effect in lineage cells: count-space multiplier exp(-s*beta_g*(a_i - q10_type(a))), clipped to [1/2, 2]
            -> zeros stay zero, output stays non-negative.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
from vecommon import load_stage, panel, make_submission, format_check

# Mesp1-lineage at E8.75 (literature prior: Saga et al. 1999; Devine et al. 2014; Lescroart et al. 2014)
MESP1_LINEAGE = {"V-CM", "IFT-CM", "JCF", "Endo", "Peri", "aPHM", "pPHM", "PAM-1", "PAM-2", "PAM-3", "PAM-4",
                 "LPM", "ExEM-1", "ExEM-2", "Allantois", "Intra-Endoth-1", "Intra-Endoth-2", "HEM-Endoth",
                 "SOM", "d-CSE", "V-CSE"}
# generic canonical Wnt/beta-catenin readouts present on the 500-gene panel (pathway-feedback and textbook direct
# targets; NOT taken from any Ctnnb1-mutant study): Dkk1, Wif1, Rspo3, Tbx6, Dll1, Msx2, Fgf8, Wnt3a, Hoxb1
WNT_PROGRAM = ["Dkk1", "Wif1", "Rspo3", "Tbx6", "Dll1", "Msx2", "Fgf8", "Wnt3a", "Hoxb1"]


def build(wt="E8.75", n=7449, seed=20261008, carrier="uniform", lineage="mesp1", zero=(), half=(),
          program=(), strength=0.0, board="T3:gata4"):
    g = panel(board); gi = {x: i for i, x in enumerate(g)}
    W = load_stage(wt, g); lab = np.asarray(W.obs["celltype"]).astype(str)
    rng = np.random.default_rng(seed)
    if carrier == "uniform":
        rows = np.sort(rng.choice(W.n_obs, min(n, W.n_obs), replace=False))
    else:
        shares = {s: (lab == s).mean() for s in np.unique(lab)}
        counts = {s: int(n * p) for s, p in shares.items()}
        rem = sorted(shares, key=lambda s: (n * shares[s] - counts[s], s), reverse=True)
        for i in range(n - sum(counts.values())): counts[rem[i]] += 1
        rows = np.sort(np.concatenate([rng.choice(np.flatnonzero(lab == s), k, replace=False) for s, k in counts.items() if k]))
    X = W.X[rows].astype(np.float64); lab_r = lab[rows]
    if carrier == "strat_pbmatch":
        pb_full = W.X.mean(0).astype(np.float64); pb = X.mean(0)
        X *= np.where(pb > 0, pb_full / np.maximum(pb, 1e-12), 1.0)
    lin = np.ones(len(rows), bool) if lineage == "all" else np.isin(lab_r, list(MESP1_LINEAGE))
    diag = {"lineage_cells": int(lin.sum())}
    if program and strength > 0:
        prog = [p for p in program if p in gi]; diag["program_on_panel"] = prog
        WX = W.X.astype(np.float64); linW = np.ones(W.n_obs, bool) if lineage == "all" else np.isin(lab, list(MESP1_LINEAGE))
        Z = (WX[:, [gi[p] for p in prog]] - WX[:, [gi[p] for p in prog]].mean(0)) / (WX[:, [gi[p] for p in prog]].std(0) + 1e-9)
        act = Z.mean(1)
        # fit on lineage cells with celltype fixed effects (demean within type)
        Xl, al, tl = WX[linW], act[linW], lab[linW]
        Xd, ad_ = Xl.copy(), al.copy()
        for t in np.unique(tl):
            m = tl == t; Xd[m] -= Xd[m].mean(0); ad_[m] -= ad_[m].mean()
        lam = 0.01 * len(ad_)
        beta = (ad_ @ Xd) / (ad_ @ ad_ + lam)
        resid = Xd - np.outer(ad_, beta)
        se = np.sqrt(resid.var(0) / max(ad_ @ ad_, 1e-9))
        tstat = np.abs(beta) / np.maximum(se, 1e-12); beta = beta * tstat / (tstat + 2.0)
        q10 = {t: np.quantile(act[lab == t], 0.10) for t in np.unique(lab)}
        a_r = act[rows]; base = np.array([q10[t] for t in lab_r])
        excess = np.clip(a_r - base, 0, None) * lin
        logfc = np.clip(-strength * np.outer(excess, beta), -np.log(2), np.log(2))
        X = np.log1p(np.expm1(X) * np.exp(logfc))
        top = np.argsort(beta)[::-1]
        diag.update(top_pos=[g[i] for i in top[:8]], top_neg=[g[i] for i in top[-8:]],
                    mean_abs_pb_shift=float(np.abs(X.mean(0) - W.X[rows].mean(0)).mean()))
    for z in zero:
        if z in gi: X[lin, gi[z]] = 0
    for h in half:
        if h in gi: X[lin, gi[h]] = np.log1p(0.5 * np.expm1(X[lin, gi[h]]))
    C = np.asarray(W.obsm["spatial_3D"])[rows, :3]
    prov = dict(recipe="t3_build", wt=wt, n=int(len(rows)), seed=seed, carrier=carrier, lineage=lineage, zero=list(zero),
                half=list(half), program=list(program), strength=strength, **diag)
    out = make_submission(X, g, C, np.asarray(W.obs_names)[rows], prov); out.obs["celltype"] = lab_r
    return out, prov


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--wt", default="E8.75"); ap.add_argument("--n", type=int, default=7449)
    ap.add_argument("--seed", type=int, default=20261008); ap.add_argument("--board", default="T3:gata4")
    ap.add_argument("--carrier", choices=["uniform", "strat_pbmatch"], default="uniform")
    ap.add_argument("--lineage", choices=["mesp1", "all"], default="mesp1")
    ap.add_argument("--zero", default=""); ap.add_argument("--half", default="")
    ap.add_argument("--program", default=""); ap.add_argument("--strength", type=float, default=0.0)
    ap.add_argument("--sources", default="none"); ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    sp = lambda s: [x for x in s.split(",") if x]
    prog = WNT_PROGRAM if a.program == "WNT" else sp(a.program)
    out, prov = build(a.wt, a.n, a.seed, a.carrier, a.lineage, sp(a.zero), sp(a.half), prog, a.strength, a.board)
    prov["external_sources"] = a.sources; out.uns["ve_provenance"] = json.dumps(prov, default=str)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True); out.write_h5ad(a.out)
    fc = format_check(Path(a.out), a.board)
    print(json.dumps({"provenance": prov, "format_check": fc}, indent=1, default=str))
    return 0 if fc["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
