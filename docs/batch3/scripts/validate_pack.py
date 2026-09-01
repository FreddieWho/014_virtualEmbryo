#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


REQUIRED = [
    "00_START_HERE.md",
    "01_AGENT_CONTROLLER_PROMPT.md",
    "config/active_task.yaml",
    "config/task_manifest.yaml",
    "prompts/P0_LOCK_SCORER_ANCHORS_TOOLCHAIN.md",
    "prompts/T3_S1_PRIOR_COMMITTEE.md",
    "prompts/T1_S2_MOSCOT_DECODER.md",
    "prompts/T2_S3_SHAPE_FIELD.md",
    "schemas/prior.schema.json",
]


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    missing = [p for p in REQUIRED if not (root / p).exists()]
    if missing:
        raise SystemExit("missing: " + ", ".join(missing))
    for path in (root / "schemas").glob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))
    print(f"OK: {root} ({sum(1 for p in root.rglob('*') if p.is_file())} files)")


if __name__ == "__main__":
    main()
