#!/usr/bin/env python
"""T2 leave-one-released-stage-out backtest (and, after 10-20, real-truth folds via --fold *_truth)."""
import argparse, sys, json
from pathlib import Path
from types import SimpleNamespace as NS
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
from backtest import Board, fmt
from vecommon import load_stage, panel
import t2_recipes as R

FOLDS = {  # name: (board panel, left, right, held-out target, time, reference stage, n, kind)
    "embryo_loo": ("T2:embryo:val_interp", "E6.75:6.75", "E8.0:8.0", "E7.25", 7.25, "E6.75", 5000, "interp"),
    "heart_interp_loo": ("T2:heart:val_interp", "E8.25_late:8.25", "E9.5:9.5", "E8.75", 8.75, "E8.25_late", 5872, "interp"),
    "extrap_loo": ("T2:heart:val_extrap", "E8.25_late:8.25", "E8.75:8.75", "E9.5", 9.5, "E8.75", 25179, "extrap"),
    # available after 2026-10-20 (validation truths released; file names to be confirmed):
    "embryo_truth": ("T2:embryo:val_interp", "E7.25:7.25", "E8.0:8.0", "E7.5", 7.5, "E7.25", 5000, "interp"),
    "heart_interp_truth": ("T2:heart:val_interp", "E8.25_late:8.25", "E8.75:8.75", "E8.5", 8.5, "E8.25_late", 5872, "interp"),
    "extrap_truth": ("T2:heart:val_extrap", "E8.75:8.75", "E9.5:9.5", "E10.5", 10.5, "E9.5", 25179, "extrap"),
}
RECIPES = {
    "E1_bridge_logrms": dict(kind="interp", C=2.0, geometry="logrms", zero_preserve=False),
    "E2_bridge_aniso_zp": dict(kind="interp", C=2.0, geometry="aniso", zero_preserve=True),
    "H1_bridge_aniso": dict(kind="interp", C=2.0, geometry="aniso", zero_preserve=False),
    "H2_bridge_aniso_zp": dict(kind="interp", C=2.0, geometry="aniso", zero_preserve=True),
    "X1_median09_lib": dict(kind="extrap", damp=0.9, stat="median", lib_preserve=True, timescale="none"),
    "Xb_baseline_mean": dict(kind="extrap", damp=1.0, stat="mean", lib_preserve=False, timescale="none"),
}


def build(fold, rname, seed):
    board, left, right, tgt, t, ref, n, kind = FOLDS[fold]; r = dict(RECIPES[rname])
    if r.pop("kind") != kind: return None
    if kind == "interp":
        a = NS(board=board, left=left, right=right, target=t, n=n, seed=seed, label="celltype", carrier="left", **r)
        return R.run_interp(a)[0]
    a = NS(board=board, prev=left, last=right, target=t, n=n, seed=seed, label="celltype", min_cells=30, **r)
    return R.run_extrap(a)[0]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--fold", required=True); ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--recipes", default=",".join(RECIPES)); ap.add_argument("--out", default=None)
    a = ap.parse_args()
    board, left, right, tgt, t, ref, n, kind = FOLDS[a.fold]; g = panel(board)
    T, Rf = load_stage(tgt, g), load_stage(ref, g)
    res = {}
    for s in range(a.seeds):
        B = Board("T2", g, T, Rf, seed=s)
        print(fmt(f"[s{s}] floor(copy_last)", B.skills(B.floor)))
        for rn in a.recipes.split(","):
            P = build(a.fold, rn, seed=100 + s)
            if P is None: continue
            sk = B.skills(B.raw(P)); res.setdefault(rn, []).append(sk); print(fmt(f"[s{s}] {rn}", sk), flush=True)
    print("--- mean over seeds")
    summ = {rn: {k: float(np.mean([d[k] for d in v])) for k in v[0]} for rn, v in res.items()}
    for rn, sk in summ.items(): print(fmt(rn, sk))
    if a.out: Path(a.out).write_text(json.dumps({"fold": a.fold, "per_seed": res, "mean": summ}, indent=1))


if __name__ == "__main__":
    main()
