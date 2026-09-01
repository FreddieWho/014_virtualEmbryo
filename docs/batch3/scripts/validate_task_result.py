#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED = [
    "RESULT.md", "COMPLETION_REPORT.md", "config_resolved.yaml",
    "TOOL_VERSIONS.json", "MANIFEST.json", "run.log",
    "metrics/protected_checks.json",
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact", type=Path, required=True)
    args = ap.parse_args()
    root = args.artifact.resolve()
    missing = [name for name in REQUIRED if not (root / name).exists()]
    if missing:
        raise SystemExit("missing required files: " + ", ".join(missing))
    json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
    json.loads((root / "metrics/protected_checks.json").read_text(encoding="utf-8"))
    print("OK", root)


if __name__ == "__main__":
    main()
