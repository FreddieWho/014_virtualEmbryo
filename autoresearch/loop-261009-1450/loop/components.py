"""Per-component deltas of each variant against the frozen conditional baseline."""
import glob
import json

import pandas as pd

BASE_CSV = "/home/huyudi/vework/eval/baseline_reference/summary.csv"
FIELDS = ["de_skill", "mmd_skill", "variogram_skill", "severity_abs_skill"]


def main():
    frame = pd.read_csv(BASE_CSV)
    g = frame[frame.model == "conditional"]
    base = {k: g[k].mean() for k in FIELDS}

    patterns = [
        "/home/huyudi/vework/eval/out_prop_penalty_*.json",
        "/home/huyudi/vework/eval/out_zero_frac_*.json",
    ]
    rows = []
    for pat in patterns:
        for f in sorted(glob.glob(pat)):
            d = json.load(open(f))
            c = d["components"]
            rows.append(
                (
                    d["variant"],
                    *(c[k] - base[k] for k in FIELDS),
                )
            )

    header = f"{'variant':24}" + "".join(f"{k.replace('_skill',''):>10}" for k in FIELDS)
    print(header)
    print("-" * len(header))
    for r in rows:
        print(f"{r[0]:24}" + "".join(f"{v:+10.5f}" for v in r[1:]))


if __name__ == "__main__":
    main()