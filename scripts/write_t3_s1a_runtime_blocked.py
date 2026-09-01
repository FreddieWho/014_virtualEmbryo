#!/usr/bin/env python3
"""Freeze an interrupted T3-S1A exact-stage run without fabricating a gate."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    output = Path(__file__).resolve().parents[1] / "artifacts/tool_integration/T3-S1A-STATE-JOIN-20260831-v5"
    if not output.is_dir():
        raise FileNotFoundError(output)
    protected = [
        output / "COMPLETION_REPORT.json",
        output / "COMPLETION_REPORT.md",
        output / "RESULT.md",
        output / "run.log",
        output / "metrics/runtime_blocked.json",
    ]
    existing = [str(path) for path in protected if path.exists()]
    if existing:
        raise FileExistsError(f"refusing to overwrite existing handoff files: {existing}")

    data_audit_path = output / "metrics/data_audit.json"
    state_gate_path = output / "intermediates/state_gate.tsv"
    state_activity_path = output / "intermediates/state_activity.tsv"
    if not data_audit_path.is_file() or not state_gate_path.is_file() or not state_activity_path.is_file():
        raise FileNotFoundError("v5 exact-stage audit/state artifacts are incomplete")

    completed = []
    for target in ("Gata4", "Gata6", "Ctnnb1"):
        vote = output / f"celloracle/{target}_votes.tsv"
        sampling = output / f"celloracle/{target}_state_sampling.tsv"
        if vote.is_file() and sampling.is_file():
            completed.append({
                "target": target,
                "status": "PASS_REAL_API_OUTPUT",
                "votes": {"path": str(vote.relative_to(output)), "sha256": sha256(vote)},
                "state_sampling": {"path": str(sampling.relative_to(output)), "sha256": sha256(sampling)},
            })

    runtime = {
        "schema": "ve.t3.s1a-runtime-block.v1",
        "task": "T3-S1A-STATE-JOIN",
        "atom": output.name,
        "status": "BLOCKED_RUNTIME",
        "blocked_at": datetime.now(timezone.utc).isoformat(),
        "blocker": "BLOCKED_RUNTIME_CELLORACLE_TARGET_PROPAGATION",
        "stop_reason": "Gata6 exact-stage CellOracle simulate_shift exceeded the bounded observation window; the process was interrupted before Gata6/Ctnnb1 and before scTenifold.",
        "input_audit": {
            "data_audit": {"path": str(data_audit_path.relative_to(output)), "sha256": sha256(data_audit_path)},
            "state_gate": {"path": str(state_gate_path.relative_to(output)), "sha256": sha256(state_gate_path)},
            "state_activity": {"path": str(state_activity_path.relative_to(output)), "sha256": sha256(state_activity_path)},
        },
        "celloracle": {
            "method": "real CellOracle 0.22.0 API",
            "status": "PARTIAL_BLOCKED_RUNTIME",
            "completed_targets": completed,
            "not_completed_targets": [target for target in ("Gata4", "Gata6", "Ctnnb1") if target not in {item["target"] for item in completed}],
            "base_grn_sha256": "32de319419199f53bbdbf7c8545394a70052c7d14918d59b54c96593000dea40",
            "gene_cap": 2000,
            "n_propagation": 3,
        },
        "scTenifoldNet_scTenifoldKnk": {
            "status": "NOT_RUN_IN_THIS_ATOM",
            "reason": "The main runner executes scTenifold after CellOracle; the atom was stopped before that stage.",
        },
        "route_gate": {
            "status": "NOT_GENERATED",
            "reason": "No complete route prior/evidence bundle exists; no gate_report.v2.json is claimed.",
        },
        "candidate_generation": False,
        "server_submission": False,
        "blocks_submission": False,
        "scientific_validation": "NOT_RUN",
    }
    runtime_path = output / "metrics/runtime_blocked.json"
    runtime_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_path.write_text(json.dumps(runtime, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    completion = {
        "task": "T3-S1A-STATE-JOIN",
        "status": "BLOCKED_RUNTIME",
        "global_status": "BLOCKED",
        "candidate_generation": False,
        "server_submission": False,
        "blocks_submission": False,
        "route_gate": "NOT_GENERATED",
        "core_computation_status": {
            "input_audit": "PASS",
            "state_join": "PASS",
            "CellOracle": "PARTIAL_BLOCKED_RUNTIME",
            "scTenifoldNet_scTenifoldKnk": "NOT_RUN_IN_THIS_ATOM",
        },
        "completed_evidence": completed,
        "limitations": [
            "Gata6 and Ctnnb1 CellOracle targets did not complete within the bounded runtime window",
            "scTenifold was not run in this atom",
            "no complete route-specific prior/gate, H5AD, candidate, scorer, server score, or leaderboard claim",
        ],
    }
    (output / "COMPLETION_REPORT.json").write_text(json.dumps(completion, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "COMPLETION_REPORT.md").write_text(
        "# T3-S1A completion report\n\n"
        "- Status: `BLOCKED_RUNTIME`\n"
        "- Input audit/state join: `PASS`\n"
        "- CellOracle: `PARTIAL_BLOCKED_RUNTIME` (Gata4 output exists; Gata6/Ctnnb1 incomplete)\n"
        "- scTenifoldNet/scTenifoldKnk: `NOT_RUN_IN_THIS_ATOM`\n"
        "- Route gate: `NOT_GENERATED`\n"
        "- Candidate generation/server submission: `false`\n"
        "- `blocks_submission: false`\n",
        encoding="utf-8",
    )
    (output / "RESULT.md").write_text(
        "# T3-S1A result\n\n"
        "Core status: `BLOCKED_RUNTIME`. The official E8.75 input and state join passed, and real CellOracle Gata4 output was produced. The exact-stage Gata6/Ctnnb1 propagation did not complete within the bounded runtime window; scTenifold and route gate were not run in this atom. No candidate, scorer, server submission, or leaderboard claim was produced.\n",
        encoding="utf-8",
    )
    (output / "run.log").write_text(
        "status=BLOCKED_RUNTIME\n"
        "blocker=BLOCKED_RUNTIME_CELLORACLE_TARGET_PROPAGATION\n"
        "input_audit=PASS\n"
        "state_join=PASS\n"
        "candidate_generation=false\n"
        "server_submission=false\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "BLOCKED_RUNTIME", "runtime_report": str(runtime_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
