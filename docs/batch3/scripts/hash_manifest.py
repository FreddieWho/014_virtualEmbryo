#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--repo-commit", default=None)
    ap.add_argument("--output", type=Path, default=None)
    args = ap.parse_args()

    root = args.root.resolve()
    output = args.output or root / "MANIFEST.json"
    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.resolve() == output.resolve():
            continue
        files.append({
            "path": str(path.relative_to(root)),
            "sha256": sha256(path),
            "size": path.stat().st_size,
            "role": None,
        })
    obj = {
        "task_id": args.task_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "repo_commit": args.repo_commit,
        "files": files,
    }
    output.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
