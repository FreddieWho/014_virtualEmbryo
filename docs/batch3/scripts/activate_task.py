#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _repo_relative(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _check_route_gate(args: argparse.Namespace) -> dict[str, str] | None:
    if args.task != "T3-S1B-GENERATE":
        if args.route_id or args.gate_report:
            raise SystemExit("--route-id/--gate-report are only valid for T3-S1B-GENERATE")
        return None
    if not args.route_id:
        raise SystemExit("T3-S1B-GENERATE requires --route-id")
    repo_root = args.pack_root.parent.parent
    report = args.gate_report or (
        repo_root / "artifacts" / "tool_integration" / "T3-S1A-STATE-JOIN-20260831-v1" / "metrics" / "gate_report.v2.json"
    )
    import sys
    sys.path.insert(0, str(args.pack_root / "interfaces"))
    from virtual_embryo_tools.route_gate import load_route_gate, validate_route_binding

    try:
        validated = load_route_gate(report, route_id=args.route_id)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    report = report.resolve()
    route = validated["route"]
    repo_root = args.pack_root.parent.parent.resolve()
    artifact_root = report.parent.parent.resolve()
    binding = {
        "route_id": route["route_id"],
        "gate_report": _repo_relative(report, repo_root),
        "gate_report_sha256": _sha256(report),
        "prior_path": _repo_relative(artifact_root / route["prior_path"], repo_root),
        "prior_sha256": route["prior_sha256"],
        "evidence_path": _repo_relative(artifact_root / route["evidence_path"], repo_root),
        "evidence_sha256": route["evidence_sha256"],
        "artifact_manifest_path": _repo_relative(artifact_root / route["artifact_manifest_path"], repo_root),
        "artifact_manifest_sha256": route["artifact_manifest_sha256"],
        "gate_outcome": validated["report"]["outcome"],
    }
    try:
        validate_route_binding(binding, repo_root=repo_root)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    return binding


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--pack-root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--route-id")
    ap.add_argument("--gate-report", type=Path)
    args = ap.parse_args()

    root = args.pack_root.resolve()
    args.pack_root = root
    binding = _check_route_gate(args)
    source = root / "config" / "active_templates" / f"{args.task}.yaml"
    target = root / "config" / "active_task.yaml"
    if not source.exists():
        available = sorted(p.stem for p in (root / "config" / "active_templates").glob("*.yaml"))
        raise SystemExit(f"unknown task {args.task!r}; available: {', '.join(available)}")
    if binding is None:
        shutil.copyfile(source, target)
    else:
        # The active config is a signed-by-hash handoff.  S1B consumers must
        # revalidate this binding before reading any prior or generating data.
        text = source.read_text(encoding="utf-8")
        text += "\n" + "\n".join([
            "route_id: " + json.dumps(binding["route_id"]),
            "route_gate_report: " + json.dumps(binding["gate_report"]),
            "route_gate_report_sha256: " + binding["gate_report_sha256"],
            "prior_path: " + json.dumps(binding["prior_path"]),
            "prior_sha256: " + binding["prior_sha256"],
            "evidence_path: " + json.dumps(binding["evidence_path"]),
            "evidence_sha256: " + binding["evidence_sha256"],
            "artifact_manifest_path: " + json.dumps(binding["artifact_manifest_path"]),
            "artifact_manifest_sha256: " + binding["artifact_manifest_sha256"],
            "route_gate_outcome: " + binding["gate_outcome"],
        ]) + "\n"
        target.write_text(text, encoding="utf-8")
    print(f"activated {args.task}: {target}")


if __name__ == "__main__":
    main()
