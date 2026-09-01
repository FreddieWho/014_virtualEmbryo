#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--task", required=True)
    ap.add_argument("--artifact-root", default="artifacts/tool_integration")
    args = ap.parse_args()

    root = args.repo.resolve() / args.artifact_root / args.task
    for rel in [
        "inputs", "intermediates", "submissions", "metrics", "discovery", "locks"
    ]:
        (root / rel).mkdir(parents=True, exist_ok=True)
    for name in ["run.log", "RESULT.md", "COMPLETION_REPORT.md"]:
        p = root / name
        if not p.exists():
            p.write_text("", encoding="utf-8")
    print(root)


if __name__ == "__main__":
    main()
