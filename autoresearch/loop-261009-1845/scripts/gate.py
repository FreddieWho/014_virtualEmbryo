"""Apply the frozen v0088 decision gate to the best route, vs the incumbent arm.

The frozen gate (evaluate_source.py:66) is:
  mean_gain > 0  AND  wins >= 4  AND  de/direction/severity_abs mean skill delta >= -2
This reports each condition explicitly so the candidate is not oversold.
"""
import numpy as np
import pandas as pd

WEIGHTS = {
    "de_skill": 0.30,
    "direction_skill": 0.25,
    "severity_abs_skill": 0.25,
    "mmd_skill": 0.12,
    "variogram_skill": 0.08,
}


def per_query(frame):
    f = frame[frame.model == "conditional"].copy()
    f["total"] = sum(f[k] * w for k, w in WEIGHTS.items())
    return f


def main():
    b = per_query(pd.read_csv("/home/huyudi/vework/eval/baseline_reference/metrics.csv"))
    c = per_query(pd.read_csv(
        "/home/huyudi/vework/variants2/resp_lam15_unmasked_mc20/source_evaluation/metrics.csv"))

    qb = b.groupby("query")[["total"] + list(WEIGHTS)].mean()
    qc = c.groupby("query")[["total"] + list(WEIGHTS)].mean()
    dt = qc["total"] - qb["total"]

    for m in WEIGHTS:
        pass
    comp_delta = {m: float(qc[m].mean() - qb[m].mean()) for m in WEIGHTS}

    wins = int((dt > 0).sum())
    print(f"mean_gain      {dt.mean():+.4f}   (gate > 0)        -> {dt.mean() > 0}")
    print(f"wins           {wins}/{len(dt)}         (gate >= 4)       -> {wins >= 4}")
    for m in ["de_skill", "direction_skill", "severity_abs_skill"]:
        v = comp_delta[m]
        print(f"{m:18}{v:+8.4f}   (gate >= -2)      -> {v >= -2}")
    print(f"\ncomponent deltas: " + "  ".join(f"{m.replace('_skill','')}={v:+.3f}" for m, v in comp_delta.items()))
    passes = dt.mean() > 0 and wins >= 4 and all(comp_delta[m] >= -2 for m in ["de_skill", "direction_skill", "severity_abs_skill"])
    print(f"\nFROZEN GATE: {'PASS' if passes else 'FAIL'}")


if __name__ == "__main__":
    main()