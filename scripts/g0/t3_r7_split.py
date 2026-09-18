#!/usr/bin/env python3
"""G1-T3-R7 SPLIT (D8): pure cardiac response — fallback=0 ablation of R6's 0.5x.

Same CellOracle cascade u + t-shrink as R6; Unknown/Peri-BW get ZERO shift
(does response dilute outside cardiac lineage?). Gata4 -> 0. Deterministic.
"""
import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "g0"))
from _t3_util import (AMPL, CAP_FRAC, SHRINK_C, finalize, load_base, wt_dispersion,
                      cello_stat, apply_lineage, RUN_SEED)

TASK_ID = "G1-T3-R7-SPLIT"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--out-version", default="v0019_g0_t3_r7_split")
    args = ap.parse_args()
    base = load_base()
    panel, gidx = base["panel"], base["gidx"]
    stat = cello_stat()
    maxabs = float(stat["mean"].abs().max())
    disp = wt_dispersion([g for g in panel if g != "Gata4"])
    import numpy as np
    shifts, rows = {}, []
    for gene in panel:
        if gene == "Gata4" or gene not in stat.index:
            continue
        mean, sd, n = float(stat.loc[gene, "mean"]), float(stat.loc[gene, "std"]), int(stat.loc[gene, "count"])
        t = 0.0 if (mean == 0.0 or n == 0) else (float("inf") if sd == 0.0 else mean / (sd / np.sqrt(n)))
        shr = 1.0 if np.isinf(t) else abs(t) / (abs(t) + SHRINK_C)
        rsd, rng = disp[gene]
        amp = min(AMPL * rsd, CAP_FRAC * rng)
        s = float(np.sign(mean)) * amp * (abs(mean) / maxabs) * shr if mean != 0 else 0.0
        shifts[gene] = s
        rows.append((gene, s))
    nz = sum(1 for _, s in rows if s != 0)
    Xout = apply_lineage(base["Xout"], gidx, shifts, base["cardiac"], fallback=0.0)
    top = sorted(rows, key=lambda r: abs(r[1]), reverse=True)[:5]
    finalize(Xout, base, args.out_version, Path(args.run_dir),
             {"atom_id": TASK_ID, "lane": "L_A_SPLIT", "method": "cello_cascade_cardiac_only",
              "parent": "v0009 rows", "seed": RUN_SEED, "target_used": False,
              "atom_short": "g0_t3_r7"},
             "L_A_SPLIT", {"task": TASK_ID, "identity_repro_v0009": True,
                           "n_shifted": nz, "fallback": 0.0,
                           "cardiac_frac": float(base["cardiac"].mean()),
                           "top5": [{"gene": g, "shift": s} for g, s in top]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
