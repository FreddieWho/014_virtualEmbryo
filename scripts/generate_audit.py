#!/usr/bin/env python3
"""Regenerate AUDIT.md from authoritative sources. Derived file — do not hand-edit.

Sources: submissions/INDEX.tsv (scores), reports/LANE_VERDICTS.tsv (lane verdicts),
docs/coordination/T{1,2,3}_TRACKING.md (current branch = last branch line), TODO.md.
Usage: python scripts/generate_audit.py  (run from repo root, commit output with sources)
"""
from __future__ import annotations

import csv
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TIE = 0.1


def load_index():
    rows = []
    with open(REPO / "submissions/INDEX.tsv", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            rows.append(r)
    return rows


def load_verdicts():
    rows = []
    with open(REPO / "reports/LANE_VERDICTS.tsv", encoding="utf-8") as f:
        for r in csv.DictReader((l for l in f if not l.startswith("#")), delimiter="\t"):
            rows.append(r)
    return rows


def current_branch() -> str:
    for line in (REPO / "TODO.md").read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("- **当前执行分支"):
            return line.strip()[2:].strip()
    return "?"


def main() -> None:
    idx = load_index()
    scored = [r for r in idx if r.get("score_status") == "scored"]
    best: dict = {}
    for r in scored:
        t = r["board"]
        try:
            s = float(r["server_score"])
        except ValueError:
            continue
        if t not in best or s > best[t][0]:
            best[t] = (s, r["version"], r["method"])
    pending = [r for r in idx if r.get("score_status") == "score_pending"]
    v = load_verdicts()
    from collections import Counter
    vc = Counter(r["verdict"] for r in v)

    L = []
    L.append("# AUDIT — project scoreboard (GENERATED, do not hand-edit)")
    L.append("")
    L.append(f"Regenerate: `python scripts/generate_audit.py`. Sources: INDEX.tsv + LANE_VERDICTS.tsv + TODO.md.")
    L.append("")
    L.append("## Server bests (numeric; selection follows ±0.1 TIE band, incumbent stays)")
    for t in sorted(best):
        s, ver, lane = best[t]
        L.append(f"- {t}: **{s}** ({ver} {lane})")
    L.append("")
    L.append(f"Score-pending rows: {len(pending)}" + (f" ({', '.join(r['version']+'/'+r['method'] for r in pending)})" if pending else ""))
    L.append("Boards without scored INDEX rows are omitted above; see reports/SERVER_SCORE_REGISTRY.md.")
    L.append("")
    L.append(f"## Lane verdicts ({len(v)} rows in LANE_VERDICTS.tsv)")
    for k in ("PASS", "SHIPPED", "FAIL", "VOID", "PARKED", "PENDING_SERVER", "GATE_ONLY"):
        if vc.get(k):
            L.append(f"- {k}: {vc[k]}")
    fails = [r for r in v if r["verdict"] in ("FAIL", "VOID")]
    if fails:
        L.append("- Closed lanes (one-line cause):")
        for r in fails:
            L.append(f"  - {r['lane']}: {r['key_metric'][:110]}")
    L.append("")
    L.append("## Current branch (from TODO.md)")
    L.append(f"- {current_branch()}")
    L.append("")
    L.append("Full evidence: reports/LANE_VERDICTS.tsv (per-lane) → run RESULT.md → submissions/INDEX.tsv (scores).")
    (REPO / "AUDIT.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote AUDIT.md: {len(best)} tasks, {len(v)} lanes, {len(pending)} pending")


if __name__ == "__main__":
    main()
