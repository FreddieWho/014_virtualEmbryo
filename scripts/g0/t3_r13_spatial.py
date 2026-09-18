#!/usr/bin/env python3
"""G1-T3-R13 SPATIAL (D7): R6 response + spatial kNN smoothing (distribution attack).

70+ arithmetic says distribution/shape terms must rise too. Substitute for unknown
server spatial weights (recorded): mild spatial smoothing (k=15 via spatial_3D
cKDTree, 0.5x blend) applied ONLY to shifted-gene columns of the R6 construction,
then Gata4 -> 0. Tests whether local mmd_u/variogram move while de disaster-check
holds. Deterministic.
"""
import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "g0"))
import numpy as np
from scipy.spatial import cKDTree
from _t3_util import (AMPL, CAP_FRAC, SHRINK_C, finalize, load_base, wt_dispersion,
                      cello_stat, RUN_SEED)

TASK_ID = "G1-T3-R13-SPATIAL"
KNN = 15
BLEND = 0.5


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--out-version", default="v0025_g0_t3_r13_spatial")
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
    Xout = base["Xout"]
    card = base["cardiac"]
    shifted_cols = []
    for gene, s in shifts.items():
        if s == 0.0:
            continue
        j = gidx[gene]
        Xout[card, j] = Xout[card, j] + s
        Xout[~card, j] = Xout[~card, j] + 0.5 * s
        shifted_cols.append(j)
    tree = cKDTree(np.asarray(base["v9"].obsm["spatial_3D"], dtype=np.float64))
    _, nb = tree.query(np.asarray(base["v9"].obsm["spatial_3D"], dtype=np.float64), k=KNN + 1)
    nb = nb[:, 1:]
    for j in shifted_cols:
        col = Xout[:, j]
        Xout[:, j] = (1 - BLEND) * col + BLEND * col[nb].mean(1)
    rows = sorted(shifts.items(), key=lambda kv: abs(kv[1]), reverse=True)[:5]
    finalize(Xout, base, args.out_version, Path(args.run_dir),
             {"atom_id": TASK_ID, "lane": "L_A_SPATIAL", "method": "cascade_plus_spatial_k15",
              "parent": "v0009 rows", "seed": RUN_SEED, "target_used": False,
              "atom_short": "g0_t3_r13"},
             "L_A_SPATIAL", {"task": TASK_ID, "identity_repro_v0009": True,
                             "n_shifted": len(shifted_cols),
                             "cardiac_frac": float(card.mean()),
                             "top5": [{"gene": g_, "shift": s_} for g_, s_ in rows]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
