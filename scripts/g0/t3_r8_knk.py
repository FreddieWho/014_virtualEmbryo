#!/usr/bin/env python3
"""G1-T3-R8 KNK (D5): scTenifoldKnk rank -> full 500-gene displacement.

Knk gives unsigned manifold-shift distance per gene (no expression matrix).
Mapping (recorded, fixed): rank quantile q (top distance -> 1) x WT amplitude
x CellOracle majority sign x cardiac-full/else-half lineage gate.
Gata4 -> 0. Deterministic.
"""
import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "g0"))
import numpy as np
import pandas as pd
from _t3_util import (AMPL, CAP_FRAC, KNK, finalize, load_base, wt_dispersion,
                      cello_stat, apply_lineage, RUN_SEED)

TASK_ID = "G1-T3-R8-KNK"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--out-version", default="v0020_g0_t3_r8_knk")
    args = ap.parse_args()
    base = load_base()
    panel, gidx = base["panel"], base["gidx"]
    knk = pd.read_csv(KNK, sep="\t")
    assert len(knk) == 498, f"knk row drift: {len(knk)}"
    knk = knk[knk.gene != "Gata4"].copy()
    knk["rank"] = knk["distance"].rank(pct=True)  # top distance -> ~1
    stat = cello_stat()
    disp = wt_dispersion([g for g in panel if g != "Gata4"])
    shifts, rows = {}, []
    for _, r in knk.iterrows():
        gene = r["gene"]
        if gene not in gidx or gene == "Gata4":
            continue
        sign = float(stat.loc[gene, "sign_maj"]) if gene in stat.index else 0.0
        if sign == 0.0:
            continue
        rsd, rng = disp[gene]
        s = sign * min(AMPL * rsd, CAP_FRAC * rng) * float(r["rank"])
        shifts[gene] = s
        rows.append((gene, s))
    Xout = apply_lineage(base["Xout"], gidx, shifts, base["cardiac"], fallback=0.5)
    top = sorted(rows, key=lambda r: abs(r[1]), reverse=True)[:5]
    finalize(Xout, base, args.out_version, Path(args.run_dir),
             {"atom_id": TASK_ID, "lane": "L_A_KNK", "method": "knk_rank_x_wt_x_cello_sign",
              "parent": "v0009 rows", "seed": RUN_SEED, "target_used": False,
              "atom_short": "g0_t3_r8"},
             "L_A_KNK", {"task": TASK_ID, "identity_repro_v0009": True,
                         "n_shifted": len(rows),
                         "cardiac_frac": float(base["cardiac"].mean()),
                         "top5": [{"gene": g, "shift": s} for g, s in top]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
