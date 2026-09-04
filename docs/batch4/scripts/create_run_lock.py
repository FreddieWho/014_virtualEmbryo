#!/usr/bin/env python3
"""Create a pre-run lock snapshot for one Batch 4 active task.

This script is intentionally read-only with respect to project code. It writes
only into the requested run-lock output directory.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path

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

def parse_active_task(text: str) -> str:
    for line in text.splitlines():
        if line.strip().startswith("active_task:"):
            return line.split(":", 1)[1].strip()
    raise ValueError("active_task missing")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--pack", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--provider", required=True)
    ap.add_argument("--effort", required=True)
    ap.add_argument("--harness", required=True)
    args = ap.parse_args()

    repo, pack, out = args.repo.resolve(), args.pack.resolve(), args.out.resolve()
    active = pack / "config/active_task.yaml"
    controller = pack / "01_CODEX_CONTROLLER_PROMPT.md"
    manifest = pack / "config/task_manifest.yaml"
    if not all(p.exists() for p in (active, controller, manifest)):
        raise FileNotFoundError("pack entry files missing")
    task_id = parse_active_task(active.read_text(encoding="utf-8"))
    prompt_candidates = list((pack / "prompts").glob("*.md"))
    task_prompt = None
    manifest_text = manifest.read_text(encoding="utf-8")
    for p in prompt_candidates:
        if task_id in p.read_text(encoding="utf-8", errors="ignore").splitlines()[0]:
            task_prompt = p
            break
    if task_prompt is None:
        # P0 and closeout names may not match first heading exactly; use manifest lookup.
        m = None
        for line in manifest_text.splitlines():
            if task_id in line:
                m = True
            elif m and "prompt:" in line:
                rel = line.split("prompt:", 1)[1].strip()
                task_prompt = repo / rel
                break
    if task_prompt is None or not task_prompt.exists():
        raise FileNotFoundError(f"task prompt not resolved for {task_id}")

    dirty = git(repo, "status", "--porcelain=v1")
    dirty_digest = hashlib.sha256(dirty.encode()).hexdigest()
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    run_id = f"{task_id}-{now.replace(':','').replace('+00:00','Z')}"
    lock = {
        "run_id": run_id,
        "task_id": task_id,
        "track": "Agent Team",
        "lock_time_utc": now,
        "git": {
            "commit": git(repo, "rev-parse", "HEAD"),
            "dirty": bool(dirty),
            "dirty_digest": dirty_digest,
            "dirty_status": dirty.splitlines(),
        },
        "prompts": {
            "controller_path": str(controller.relative_to(repo) if controller.is_relative_to(repo) else controller),
            "controller_sha256": sha256(controller),
            "task_path": str(task_prompt.relative_to(repo) if task_prompt.is_relative_to(repo) else task_prompt),
            "task_sha256": sha256(task_prompt),
            "active_task_sha256": sha256(active),
            "task_manifest_sha256": sha256(manifest),
        },
        "model": {"provider": args.provider, "model": args.model, "effort": args.effort},
        "harness": {"path_or_commit": args.harness},
        "permissions": {
            "network": False,
            "external_downloads": task_id == "B4-T1-R2-LATE-PROGRAM-BRIDGE",
            "server_submission": False,
        },
        "random": {"seed": 20260904},
        "configuration_locked": True,
        "human_midrun_steering": False,
    }
    out.mkdir(parents=True, exist_ok=False)
    (out / "RUN_LOCK.yaml").write_text(
        json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out / "PROMPT_SHA256.tsv").write_text(
        "kind\tpath\tsha256\n"
        f"controller\t{controller}\t{sha256(controller)}\n"
        f"task\t{task_prompt}\t{sha256(task_prompt)}\n"
        f"active\t{active}\t{sha256(active)}\n"
        f"manifest\t{manifest}\t{sha256(manifest)}\n",
        encoding="utf-8",
    )
    print(json.dumps({"run_id": run_id, "out": str(out)}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
