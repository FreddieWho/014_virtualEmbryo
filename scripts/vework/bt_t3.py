#!/usr/bin/env python
"""T3 leave-one-KO-out scaffold with the official T3 construction (10% WT reference, KO 10% halves, weights
.30/.25/.25/.12/.08). Folds:
  mab21l2 (now)  : WT E9.5 -> Mab21l2 KO E9.5    (program = [Mab21l2], lineage all)
  gata4 (10-20)  : WT E8.75 -> Gata4 KO E8.75, each replicate separately (program = [Gata4], lineage mesp1)
Each fold evaluates the SAME builder code (t3_build.build) that makes the beta-catenin files, i.e. the method class,
not the gene. Ceilings default to the published T3:gata4 anchors for the response metrics' scale."""
import argparse, sys, json
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
from backtest import Board, fmt
from vecommon import load_stage, panel
import t3_build as T3

FOLDS = {"mab21l2": dict(wt="E9.5", ko=["E9.5_mab21l2_ko"], gene="Mab21l2", lineage="all"),
         "gata4": dict(wt="E8.75", ko=["Gata4_KO_rep1", "Gata4_KO_rep2"], gene="Gata4", lineage="mesp1")}  # names TBC 10-20


def recipes(f):
    G = f["gene"]
    return {"uniform_draw": dict(carrier="uniform"),
            "strat_pbmatch": dict(carrier="strat_pbmatch"),
            "uniform+gene_zero": dict(carrier="uniform", zero=[G]),
            "uniform+program_loss_s0.25": dict(carrier="uniform", program=[G], strength=0.25, zero=[G]),
            "uniform+program_loss_s0.5": dict(carrier="uniform", program=[G], strength=0.5, zero=[G])}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--fold", default="mab21l2"); ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--out", default=None); a = ap.parse_args()
    f = FOLDS[a.fold]; g = panel("T3:gata4"); WT = load_stage(f["wt"], g); res = {}
    for rep in f["ko"]:
        KO = load_stage(rep, g)
        for s in range(a.seeds):
            B = Board("T3", g, KO, WT, seed=s)
            for rn, kw in recipes(f).items():
                P, _ = T3.build(wt=f["wt"], seed=500 + s, lineage=f["lineage"], **kw)
                sk = B.skills(B.raw(P), ceil_from="T3:gata4"); res.setdefault(rn, []).append(sk)
                print(fmt(f"[{rep} s{s}] {rn}", sk), flush=True)
    print("--- mean"); summ = {rn: {k: float(np.mean([d[k] for d in v])) for k in v[0]} for rn, v in res.items()}
    for rn, sk in summ.items(): print(fmt(rn, sk))
    if a.out: Path(a.out).write_text(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
