"""Per-genotype robustness check for the best route vs the incumbent.

A composite gain that comes from one held-out genotype is not a real improvement;
this reports per-query win counts and per-query deltas.
"""
import numpy as np
import pandas as pd

BASE_CSV = "/home/huyudi/vework/eval/baseline_reference/metrics.csv"
BEST_CSV = "/home/huyudi/vework/variants2/resp_lam15_unmasked_mc20/source_evaluation/metrics.csv"

WEIGHTS = {
    "de_skill": 0.30,
    "direction_skill": 0.25,
    "severity_abs_skill": 0.25,
    "mmd_skill": 0.12,
    "variogram_skill": 0.08,
}


def composite_by_query(frame):
    f = frame[frame.model == "conditional"].copy()
    f["total"] = sum(f[k] * w for k, w in WEIGHTS.items())
    return f.groupby("query").total.mean()


def main():
    b = pd.read_csv(BASE_CSV)
    best = pd.read_csv(BEST_CSV)
    cb, cs = composite_by_query(b), composite_by_query(best)
    d = (cs - cb).sort_values(ascending=False)
    print(f"{'query':10}{'incumbent':>11}{'candidate':>11}{'delta':>10}")
    for q, v in d.items():
        print(f"{q:10}{cb[q]:11.4f}{cs[q]:11.4f}{v:+10.4f}")
    wins = int((d > 0).sum())
    print(f"\nwins {wins}/{len(d)}   mean delta {d.mean():+.4f}   "
          f"worst {d.min():+.4f}   best {d.max():+.4f}")


if __name__ == "__main__":
    main()