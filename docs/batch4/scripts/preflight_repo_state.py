#!/usr/bin/env python3
"""Read-only Batch 4 repository preflight."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

REQUIRED = [
    "AGENTS.md",
    "STATUS.md",
    "reports/SERVER_SCORE_REGISTRY.md",
    "submissions/INDEX.tsv",
    "docs/coordination/README.md",
    "docs/coordination/T1_TRACKING.md",
    "docs/coordination/T2_TRACKING.md",
    "docs/coordination/T3_TRACKING.md",
    "scripts/prepare_t1_t3_submission.py",
    "third_party/veckit/score_h5ad.py",
]

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def git(repo: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), *args], text=True, stderr=subprocess.STDOUT
        ).strip()
    except Exception as exc:
        return f"ERROR:{exc}"

def matching_lines(text: str, patterns: list[str]) -> list[str]:
    out = []
    for line in text.splitlines():
        if all(p.lower() in line.lower() for p in patterns):
            out.append(line)
    return out

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    repo = args.repo.resolve()
    missing = [p for p in REQUIRED if not (repo / p).exists()]
    report: dict[str, Any] = {
        "repo": str(repo),
        "missing_required": missing,
        "git_commit": git(repo, "rev-parse", "HEAD"),
        "git_status": git(repo, "status", "--short"),
        "files": {},
        "t3_v0006_v0007": {},
        "warnings": [],
    }
    for rel in REQUIRED:
        p = repo / rel
        if p.exists() and p.is_file():
            report["files"][rel] = {"bytes": p.stat().st_size, "sha256": sha256(p)}

    registry = (repo / "reports/SERVER_SCORE_REGISTRY.md")
    index = (repo / "submissions/INDEX.tsv")
    reg_text = registry.read_text(encoding="utf-8", errors="replace") if registry.exists() else ""
    idx_text = index.read_text(encoding="utf-8", errors="replace") if index.exists() else ""
    for version in ("v0006", "v0007"):
        reg_lines = matching_lines(reg_text, [version])
        idx_lines = matching_lines(idx_text, [version, "T3"])
        pending = any("score_pending" in x for x in idx_lines)
        numeric_score = any(re.search(r"\b\d{2}\.\d\b", x) for x in reg_lines + idx_lines)
        report["t3_v0006_v0007"][version] = {
            "registry_lines": reg_lines,
            "index_lines": idx_lines,
            "score_pending_in_index": pending,
            "numeric_score_detected": numeric_score,
        }
        if pending or not numeric_score:
            report["warnings"].append(
                f"{version}: local score synchronization may be incomplete; do not guess."
            )

    if missing:
        report["status"] = "BLOCKED_REQUIRED_FILES"
    elif report["warnings"]:
        report["status"] = "PASS_WITH_SCORE_SYNC_WARNINGS"
    else:
        report["status"] = "PASS"

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "out": str(args.out)}, ensure_ascii=False))
    return 0 if not missing else 2

if __name__ == "__main__":
    raise SystemExit(main())
