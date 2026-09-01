#!/usr/bin/env python3
"""Assess whether audited external edges can safely reinforce T3 prior stability.

This report compares edge-level signs with the existing model-family votes.  It
does not state-join the edges or promote them into the prior, because that
requires a separately validated S1B adapter and can expose real sign conflicts.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _source_file(path: Path, repo: Path) -> dict[str, Any]:
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    return {
        "path": str(path.relative_to(repo)),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def run(
    repo: Path,
    output_dir: Path,
    knowledge_dir: Path | None = None,
) -> dict[str, Any]:
    repo = Path(repo).resolve()
    output_dir = Path(output_dir).resolve()
    knowledge_dir = (
        repo / "artifacts/tool_integration/T3-S1B-KNOWLEDGE-PREFLIGHT-20260831-v3"
        if knowledge_dir is None
        else Path(knowledge_dir).resolve()
    )
    if output_dir.exists() and not output_dir.is_dir():
        raise NotADirectoryError(output_dir)
    if output_dir.is_dir() and any(output_dir.iterdir()):
        raise FileExistsError(
            f"refusing to overwrite existing preflight output directory: {output_dir}"
        )
    s1 = repo / "artifacts/tool_integration/T3-S1-PRIOR"
    gate_path = s1 / "metrics/gate_report.json"
    s1b = knowledge_dir
    stability_path = s1 / "metrics/stability.json"
    votes_path = s1 / "intermediates/source_votes.tsv"
    edges_path = s1b / "knowledge_edge_evidence.tsv"
    knowledge_summary_path = s1b / "summary.json"
    knowledge_manifest_path = s1b / "MANIFEST.json"
    stability = json.loads(stability_path.read_text(encoding="utf-8"))
    votes = read_tsv(votes_path)
    edges = read_tsv(edges_path)
    knowledge_summary = json.loads(
        knowledge_summary_path.read_text(encoding="utf-8")
    )
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)
    gate_snapshot_path = output_dir / "upstream_gate_snapshot.json"
    gate_snapshot_path.write_bytes(gate_path.read_bytes())

    signed_edges: dict[str, dict[str, set[int]]] = {}
    for row in edges:
        if row.get("target_gene") not in {"Gata4", "Gata6"}:
            continue
        if str(row.get("conflict_flag", "")).lower() == "true":
            continue
        sign = int(row.get("ko_minus_wt_sign", "0"))
        if sign == 0:
            continue
        signed_edges.setdefault(row["target_gene"], {}).setdefault(
            row["response_gene"], set()
        ).add(sign)

    comparisons: dict[str, dict[str, Any]] = {}
    for target in ("Gata4", "Gata6"):
        comparisons[target] = {}
        for family in ("WT_INFERRED_GRN_LOCAL", "WT_CONDITIONAL_NETWORK_LOCAL"):
            family_rows = [
                row
                for row in votes
                if row.get("target_gene") == target
                and row.get("condition_id") == "GATA4_GATA6_VALIDATION_E875"
                and row.get("evidence_family") == family
                and int(row.get("sign", "0")) != 0
            ]
            target_edges = signed_edges.get(target, {})
            overlap = [row for row in family_rows if row["response_gene"] in target_edges]
            same = [
                row for row in overlap if int(row["sign"]) in target_edges[row["response_gene"]]
            ]
            opposite = [
                row for row in overlap if -int(row["sign"]) in target_edges[row["response_gene"]]
            ]
            comparisons[target][family] = {
                "model_nonzero_rows": len(family_rows),
                "external_signed_gene_count": len(target_edges),
                "overlap_rows": len(overlap),
                "same_sign_rows": len(same),
                "opposite_sign_rows": len(opposite),
                "same_sign_fraction_of_overlap": (
                    len(same) / len(overlap) if overlap else None
                ),
            }

    result: dict[str, Any] = {
        "schema": "ve.t3.stability-preflight.v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "task": "T3-S1-STABILITY-PREFLIGHT",
        "status": "HOLD",
        "upstream_gate": {
            "path": str(gate_snapshot_path.relative_to(repo)),
            "sha256": sha256_file(gate_snapshot_path),
            "source_path": str(gate_path.relative_to(repo)),
            "source_sha256": sha256_file(gate_path),
            "task_id": gate.get("task_id"),
            "gate_id": gate.get("gate_id"),
            "status": gate.get("status", "NOT_AVAILABLE"),
            "outcome": gate.get("outcome", "NOT_AVAILABLE"),
        },
        "knowledge_preflight": {
            "path": str(knowledge_summary_path.relative_to(repo)),
            "manifest": str(knowledge_manifest_path.relative_to(repo)),
            "sha256": sha256_file(knowledge_summary_path),
            "status": knowledge_summary.get("status", "NOT_AVAILABLE"),
            "candidate_admission_status": knowledge_summary.get(
                "candidate_admission_status", "NOT_AVAILABLE"
            ),
        },
        "current_stability_status": stability.get("status"),
        "current_leave_one_out": stability.get("leave_one_out", {}),
        "external_snapshot_integration": "EDGE_LEVEL_ONLY_NOT_STATE_JOINED",
        "external_comparisons": comparisons,
        "decision": "NOT_READY_FOR_PRIOR_PROMOTION",
        "reason": [
            "strict two-family leave-one-out remains structurally non-identifiable",
            "external edge signs show target/family-specific discordance",
            "external edges have no validated state-specific activity assignment",
        ],
        "minimum_next_evidence": (
            "Run one fixed S1B state-join adapter with explicit conflict zeroing, "
            "then rerun leave-one-family-out before any candidate generation."
        ),
        "candidate_generation": False,
        "server_submission": False,
        "blocks_submission": False,
    }
    result_path = output_dir / "stability_preflight.json"
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    manifest = {
        "schema": "ve.t3.stability-preflight-manifest.v1",
        "task": "T3-S1-STABILITY-PREFLIGHT",
        "files": [
            {
                "path": result_path.name,
                "bytes": result_path.stat().st_size,
                "sha256": sha256_file(result_path),
            },
            {
                "path": gate_snapshot_path.name,
                "bytes": gate_snapshot_path.stat().st_size,
                "sha256": sha256_file(gate_snapshot_path),
            },
        ],
        "source_files": [
            _source_file(path, repo)
            for path in (
                stability_path,
                votes_path,
                edges_path,
                knowledge_summary_path,
                knowledge_manifest_path,
                gate_snapshot_path,
                Path(__file__).resolve(),
            )
        ],
    }
    (output_dir / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "artifacts/tool_integration/STABILITY-PREFLIGHT-20260831-v3"
        ),
    )
    parser.add_argument(
        "--knowledge-dir",
        type=Path,
        default=Path(
            "artifacts/tool_integration/T3-S1B-KNOWLEDGE-PREFLIGHT-20260831-v3"
        ),
    )
    args = parser.parse_args(argv)
    result = run(args.repo, args.output_dir, args.knowledge_dir)
    print(
        json.dumps(
            {
                "status": result["status"],
                "decision": result["decision"],
                "current_stability_status": result["current_stability_status"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
