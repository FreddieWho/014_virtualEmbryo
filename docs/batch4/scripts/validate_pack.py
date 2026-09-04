#!/usr/bin/env python3
"""Validate Batch 4 pack hashes and parse machine-readable configs."""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path

try:
    import yaml
except Exception:
    yaml = None

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def main() -> int:
    root = Path(__file__).resolve().parents[1]
    manifest_path = root / "PACK_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    failures = []
    for item in manifest["files"]:
        p = root / item["path"]
        if not p.exists():
            failures.append(f"missing:{item['path']}")
            continue
        got = sha256(p)
        if got != item["sha256"]:
            failures.append(f"hash:{item['path']}:{got}")
    for rel in [
        "config/active_task.yaml",
        "config/task_manifest.yaml",
        "config/route_status.yaml",
        "config/score_targets.yaml",
    ]:
        p = root / rel
        if yaml is not None:
            try:
                yaml.safe_load(p.read_text(encoding="utf-8"))
            except Exception as exc:
                failures.append(f"yaml:{rel}:{exc}")
    if failures:
        print(json.dumps({"status": "FAIL", "failures": failures}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps({
        "status": "PASS",
        "files": len(manifest["files"]),
        "pack_version": manifest["pack_version"],
    }, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
