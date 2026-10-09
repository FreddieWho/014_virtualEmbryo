"""Summarize completed component variants against the frozen baseline."""
import glob
import json

BASE = 74.73758790750969


def main():
    rows = []
    for f in sorted(glob.glob("/home/huyudi/vework/eval/out_*.json")):
        try:
            d = json.load(open(f))
        except json.JSONDecodeError:
            continue
        rows.append(
            (d["variant"], d["axis"], str(d["value"]), d["total"], d["components"])
        )
    rows.sort(key=lambda r: -r[3])
    header = f"{'variant':24} {'axis':20} {'val':8} {'total':>11} {'delta':>10}"
    print(header)
    print("-" * len(header))
    for v, a, val, t, _ in rows:
        print(f"{v:24} {a:20} {val:8} {t:11.6f} {t - BASE:+10.6f}")
    print("-" * len(header))
    print(f"{'frozen baseline':24} {'-':20} {'-':8} {BASE:11.6f} {0.0:+10.6f}")


if __name__ == "__main__":
    main()