"""Ranked table of route-loop variants that completed successfully."""
import glob
import json

BASE = 74.73758790750969
FIELDS = ["de_skill", "direction_skill", "severity_abs_skill", "mmd_skill", "variogram_skill"]


def main():
    rows, errors = [], []
    for f in sorted(glob.glob("/home/huyudi/vework/eval/out2_*.json")):
        try:
            d = json.load(open(f))
        except json.JSONDecodeError:
            continue
        (errors if d.get("status") == "metric-error" else rows).append(d)

    header = f"{'name':26}{'emitter':8}{'response':20}{'total':>11}{'delta':>10}  g"
    print(header)
    print("-" * (len(header) + 6))
    for d in sorted(rows, key=lambda r: -r["total"]):
        print(f"{d['name']:26}{d['emitter']:8}{d['response']:20}"
              f"{d['total']:11.6f}{d['total'] - BASE:+10.6f}  {d.get('guard','')[:1]}")
    print("-" * (len(header) + 6))
    print(f"{'incumbent v0088':26}{'-':8}{'frozen':20}{BASE:11.6f}{0.0:+10.6f}")

    best = max(rows, key=lambda r: r["total"])
    print(f"\nBEST {best['name']}  {best['total']:.6f}  ({best['total'] - BASE:+.6f})")
    print(f"{'component':22}{'value':>10}{'vs incumbent':>14}")
    for k in FIELDS:
        print(f"{k:22}{best['components'][k]:10.4f}{'':>14}")

    if errors:
        print(f"\n{len(errors)} routes could not run as response swaps:")
        for d in errors:
            last = str(d.get("error", "")).strip().splitlines()[-1][:70]
            print(f"  {d['name']:24} {last}")


if __name__ == "__main__":
    main()