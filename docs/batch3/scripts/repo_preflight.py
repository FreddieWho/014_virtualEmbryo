#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
from pathlib import Path
from typing import Iterable


TARGET_NAMES = {
    "score_h5ad.py",
    "SERVER_SCORE_REGISTRY.md",
    "INDEX.tsv",
    "PHASE_REPORT_BATCH1_20260829.md",
    "active_atom.yaml",
    "active_task.yaml",
    "state_vocabulary.tsv",
    "state_crosswalk.tsv",
    "AUDIT_COMPLETE.json",
}

PACKAGES = [
    "anndata", "scanpy", "numpy", "scipy", "pandas", "h5py",
    "moscot", "POT", "wot", "pycpd", "spateo", "geomloss",
    "decoupler", "celloracle", "pertpy",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_info(repo: Path) -> dict:
    def run(*args: str) -> str | None:
        try:
            return subprocess.check_output(["git", "-C", str(repo), *args], text=True, stderr=subprocess.DEVNULL).strip()
        except Exception:
            return None
    return {
        "commit": run("rev-parse", "HEAD"),
        "branch": run("rev-parse", "--abbrev-ref", "HEAD"),
        "status": run("status", "--porcelain"),
    }


def package_versions() -> dict[str, str | None]:
    out = {}
    for name in PACKAGES:
        try:
            out[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            out[name] = None
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--max-files", type=int, default=200)
    args = ap.parse_args()

    repo = args.repo.resolve()
    if not repo.exists():
        raise SystemExit(f"repo does not exist: {repo}")

    matches = []
    for path in repo.rglob("*"):
        if not path.is_file():
            continue
        if path.name in TARGET_NAMES or "batch2" in str(path).lower() and path.suffix in {".md", ".yaml", ".json", ".tsv"}:
            try:
                rel = path.relative_to(repo)
                matches.append({
                    "path": str(rel),
                    "size": path.stat().st_size,
                    "sha256": sha256(path) if path.stat().st_size < 100 * 1024 * 1024 else None,
                })
            except OSError:
                continue
        if len(matches) >= args.max_files:
            break

    report = {
        "repo": str(repo),
        "git": git_info(repo),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "packages": package_versions(),
        "matches": sorted(matches, key=lambda x: x["path"]),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
