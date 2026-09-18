#!/usr/bin/env python3
"""G1-T3-R12 DEBIAS (D1 adapted): R6 response + global-offset debias (two-step).

dbDiffusion's second step corrects model bias; our analogue without a generative
model (recorded adaptation, no GPU training claimed): step 1 = R6 cascade shifts
(same table: rel x t-shrink x WT amp, cardiac-full/else-half); step 2 = subtract
the per-gene population-mean applied shift (removes global offset bias, keeps only
the lineage-differential component). Gata4 -> 0. Deterministic.
"""
import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "g0"))
import numpy as np
from _t3_util import (AMPL, CAP_FRAC, SHRINK_C, finalize, load_base, wt_dispersion,
                      cello_stat, RUN_SEED)

TASK_ID = "G1-T3-R12-DEBIAS"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--out-version", default="v0024_g0_t3_r12_debias")
    args = ap.parse_args()
    base = load_base()
    panel, gidx = base["panel"], base["gidx"]
    stat = cello_stat()
    maxabs = float(stat["mean"].abs().max())
    disp = wt_dispersion([g for g in panel if g != "Gata4"])
    shifts = {}
    for gene in panel:
        if gene == "Gata4" or gene not in stat.index:
            continue
        mean, sd, n = float(stat.loc[gene, "mean"]), float(stat.loc[gene, "std"]), int(stat.loc[gene, "count"])
        t = 0.0 if (mean == 0.0 or n == 0) else (float("inf") if sd == 0.0 else mean / (sd / np.sqrt(n)))
        shr = 1.0 if np.isinf(t) else abs(t) / (abs(t) + SHRINK_C)
        rsd, rng = disp[gene]
        amp = min(AMPL * rsd, CAP_FRAC * rng)
        shifts[gene] = float(np.sign(mean)) * amp * (abs(mean) / maxabs) * shr if mean != 0 else 0.0
    Xout, bias = base["Xout"], {}
    card = base["cardiac"]
    for gene, s in shifts.items():
        if s == 0.0:
            continue
        j = gidx[gene]
        full = np.zeros(Xout.shape[0], dtype=np.float32)
        full[card] += s
        full[~card] += 0.5 * s
        full -= full.mean()  # step-2 debias: remove population offset
        bias[gene] = float(full.mean() + 0)  # ~0 by construction; recorded
        Xout[:, j] = Xout[:, j] + full
    rows = sorted(shifts.items(), key=lambda kv: abs(kv[1]), reverse=True)[:5]
    finalize(Xout, base, args.out_version, Path(args.run_dir),
             {"atom_id": TASK_ID, "lane": "L_A_DEBIAS", "method": "cascade_plus_offset_debias",
              "parent": "v0009 rows", "seed": RUN_SEED, "target_used": False,
              "atom_short": "g0_t3_r12"},
             "L_A_DEBIAS", {"task": TASK_ID, "identity_repro_v0009": True,
                            "n_shifted": sum(1 for s in shifts.values() if s != 0),
                            "cardiac_frac": float(card.mean()),
                            "top5": [{"gene": g_, "shift": s_} for g_, s_ in rows]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
