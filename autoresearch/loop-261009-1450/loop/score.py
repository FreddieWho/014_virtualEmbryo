"""Composite local score extraction for the autoresearch component loop.

Reads the frozen four-arm source_evaluation summary written by the adapted
evaluate_source_local.py and prints the composite total for one arm, or the
frozen incumbent conditional total when no arm is given.

Metric: skill-weighted composite over 7 held-out genotypes x 3 seeds,
replicating the frozen WEIGHTS in evaluate_source.py:
    de .30 / direction .25 / severity_abs .25 / mmd .12 / variogram .08
Direction: higher_is_better
"""
import sys
from pathlib import Path

import pandas as pd

SUMMARY = Path("/home/huyudi/vework/eval/source_evaluation/summary.csv")
WEIGHTS = {
    "de_skill": 0.30,
    "direction_skill": 0.25,
    "severity_abs_skill": 0.25,
    "mmd_skill": 0.12,
    "variogram_skill": 0.08,
}


def composite(frame):
    return sum(frame[m].mean() * w for m, w in WEIGHTS.items())


def main():
    if not SUMMARY.exists():
        print("METRIC_ERROR:no_summary")
        return
    frame = pd.read_csv(SUMMARY)
    arm = sys.argv[1] if len(sys.argv) > 1 else "conditional"
    if arm not in set(frame.model):
        print("METRIC_ERROR:unknown_arm")
        return
    print(f"{composite(frame[frame.model == arm]):.6f}")


if __name__ == "__main__":
    main()