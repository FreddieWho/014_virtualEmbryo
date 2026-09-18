#!/usr/bin/env python3
"""G1-T3-R11 SIGNMAX (D6 reframed): sign-consistency maximization.

D6 'de direct optimization' is infeasible: the only local de proxy is blind
(R1-R6: de identical to 4 decimals), so no rank-consistent differentiable target
exists — recorded, gate failed honestly. Substitute that keeps D6's intent
(attack the de weakest link directly): per-gene shift direction/amplitude from
cross-state SIGN CONSISTENCY (agreement fraction a over 76 sim states):
shift = majority_sign x WT_amp x a^2 (size-free; consistent genes full, split genes
killed). Differs from R6 (effect-size weighted): pure-consistency weighting.
Cardiac-full/else-half gate. Gata4 -> 0. Deterministic.
"""
import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "g0"))
from _t3_util import (AMPL, CAP_FRAC, finalize, load_base, wt_dispersion,
                      cello_stat, apply_lineage, RUN_SEED)

TASK_ID = "G1-T3-R11-SIGNMAX"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--out-version", default="v0023_g0_t3_r11_signmax")
    args = ap.parse_args()
    base = load_base()
    panel, gidx = base["panel"], base["gidx"]
    stat = cello_stat()
    disp = wt_dispersion([g for g in panel if g != "Gata4"])
    shifts, rows = {}, []
    for gene in panel:
        if gene == "Gata4" or gene not in stat.index:
            continue
        a = float(stat.loc[gene, "agree"])
        sign = float(stat.loc[gene, "sign_maj"])
        if sign == 0.0:
            continue
        rsd, rng = disp[gene]
        s = sign * min(AMPL * rsd, CAP_FRAC * rng) * a * a
        shifts[gene] = s
        rows.append((gene, s, a))
    Xout = apply_lineage(base["Xout"], gidx, shifts, base["cardiac"], fallback=0.5)
    top = sorted(rows, key=lambda r: abs(r[1]), reverse=True)[:5]
    finalize(Xout, base, args.out_version, Path(args.run_dir),
             {"atom_id": TASK_ID, "lane": "L_A_SIGNMAX", "method": "sign_consistency_squared",
              "parent": "v0009 rows", "seed": RUN_SEED, "target_used": False,
              "atom_short": "g0_t3_r11"},
             "L_A_SIGNMAX", {"task": TASK_ID, "identity_repro_v0009": True,
                             "n_shifted": len(rows),
                             "cardiac_frac": float(base["cardiac"].mean()),
                             "top5": [{"gene": g_, "shift": s_, "agree": a_} for g_, s_, a_ in top]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
