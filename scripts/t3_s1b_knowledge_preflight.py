#!/usr/bin/env python3
"""Run the bounded T3-S1B directed-knowledge integration preflight.

The preflight consumes the already audited local CollecTRI and OmniPath
snapshots and writes edge/path evidence only.  It deliberately does not join
the evidence to state gates, choose a prior top-k, create an H5AD, score a
candidate, or submit to the server.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping


INTERFACE_ROOT = Path(__file__).resolve().parents[1] / "docs" / "batch3" / "interfaces"
if str(INTERFACE_ROOT) not in sys.path:
    sys.path.insert(0, str(INTERFACE_ROOT))

from virtual_embryo_tools.directed_knowledge import (  # noqa: E402
    build_directed_paths,
    build_tf_edge_evidence,
    load_audited_snapshot,
    snapshot_summary,
)


EDGE_FIELDS = [
    "source_name",
    "target_gene",
    "response_gene",
    "regulation_sign",
    "ko_minus_wt_sign",
    "conflict_flag",
    "directness_score",
    "confidence",
    "confidence_status",
    "provenance",
]
PATH_FIELDS = [
    "source_gene",
    "response_gene",
    "hops",
    "path_nodes",
    "regulation_signs",
    "ko_minus_wt_sign",
    "conflict_flag",
    "provenance",
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_tsv(path: Path, fields: list[str], rows: Iterable[Mapping[str, Any]]) -> None:
    import csv

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for row in rows:
            serialised = dict(row)
            for field in ("path_nodes", "regulation_signs"):
                if field in serialised and isinstance(serialised[field], (list, tuple)):
                    serialised[field] = ";".join(str(value) for value in serialised[field])
            writer.writerow({field: serialised.get(field, "") for field in fields})


def _route_summary(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "rows_consumed": len(rows),
        "signed_rows": sum(int(row.get("ko_minus_wt_sign", 0)) != 0 for row in rows),
        "conflict_rows": sum(bool(row.get("conflict_flag", False)) for row in rows),
        "response_genes": sorted({str(row["response_gene"]) for row in rows}),
        "ko_minus_wt_sign_counts": {
            str(sign): sum(int(row.get("ko_minus_wt_sign", 0)) == sign for row in rows)
            for sign in (-1, 0, 1)
        },
    }


def _path_summary(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "paths_consumed": len(rows),
        "signed_paths": sum(int(row.get("ko_minus_wt_sign", 0)) != 0 for row in rows),
        "conflict_paths": sum(bool(row.get("conflict_flag", False)) for row in rows),
        "response_genes": sorted({str(row["response_gene"]) for row in rows}),
        "ko_minus_wt_sign_counts": {
            str(sign): sum(int(row.get("ko_minus_wt_sign", 0)) == sign for row in rows)
            for sign in (-1, 0, 1)
        },
    }


def _source_file(path: Path, repo: Path) -> dict[str, Any]:
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    return {
        "path": str(path.relative_to(repo)),
        "bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def _upstream_gate(repo: Path) -> tuple[Path, dict[str, Any]]:
    gate_path = repo / "artifacts/tool_integration/T3-S1-PRIOR/metrics/gate_report.json"
    if not gate_path.is_file():
        return gate_path, {
            "status": "NOT_AVAILABLE",
            "outcome": "NOT_AVAILABLE",
        }
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    return gate_path, {
        "path": str(gate_path.relative_to(repo)),
        "sha256": _sha256(gate_path),
        "task_id": gate.get("task_id"),
        "gate_id": gate.get("gate_id"),
        "status": gate.get("status", "NOT_AVAILABLE"),
        "outcome": gate.get("outcome", "NOT_AVAILABLE"),
    }


def run_preflight(repo: Path, output_dir: Path) -> dict[str, Any]:
    repo = Path(repo).resolve()
    output_dir = Path(output_dir).resolve()
    if output_dir.exists() and not output_dir.is_dir():
        raise NotADirectoryError(output_dir)
    if output_dir.is_dir() and any(output_dir.iterdir()):
        raise FileExistsError(
            f"refusing to overwrite existing preflight output directory: {output_dir}"
        )
    base = repo / "infra" / "external_data" / "sanitized" / "T3" / "B2-T3-A1"
    collectri = load_audited_snapshot(
        base / "COLLECTRI" / "snapshot_manifest.json",
        repo_root=repo,
        expected_source_name="CollecTRI",
        expected_dataset="collectri",
        expected_taxon_id=10090,
    )
    omnipath = load_audited_snapshot(
        base / "OMNIPATH" / "snapshot_manifest.json",
        repo_root=repo,
        expected_source_name="OmniPath",
        expected_dataset="omnipath",
        expected_taxon_id=10090,
    )
    upstream_gate_path, upstream_gate = _upstream_gate(repo)
    output_dir.mkdir(parents=True, exist_ok=True)
    upstream_gate_snapshot_path: Path | None = None
    if upstream_gate_path.is_file():
        upstream_gate_snapshot_path = output_dir / "upstream_gate_snapshot.json"
        upstream_gate_snapshot_path.write_bytes(upstream_gate_path.read_bytes())
        upstream_gate = {
            **upstream_gate,
            "source_path": upstream_gate.pop("path"),
            "source_sha256": upstream_gate["sha256"],
            "path": str(upstream_gate_snapshot_path.relative_to(repo)),
            "sha256": _sha256(upstream_gate_snapshot_path),
        }

    # These are edge-level evidence rows.  They intentionally have no state
    # assignment; state-specific joining remains part of the separately gated
    # S1B adapter.
    tf_rows = [
        row
        for target in ("Gata4", "Gata6")
        for row in build_tf_edge_evidence(collectri, target_gene=target)
    ]
    beta_paths = build_directed_paths(
        omnipath, source_gene="Ctnnb1", max_hops=2, max_paths=5000
    )

    edge_path = output_dir / "knowledge_edge_evidence.tsv"
    path_path = output_dir / "beta_directed_paths.tsv"
    summary_path = output_dir / "summary.json"
    manifest_path = output_dir / "MANIFEST.json"
    _write_tsv(edge_path, EDGE_FIELDS, tf_rows)
    _write_tsv(path_path, PATH_FIELDS, beta_paths)

    summary: dict[str, Any] = {
        "schema": "ve.t3.s1b.knowledge-preflight.v1",
        "task": "T3-S1B-KNOWLEDGE-PREFLIGHT",
        "status": "COMPONENT_PASS",
        "component_integrity_status": "PASS",
        "candidate_admission_status": (
            "NOT_RUN" if upstream_gate.get("status") == "PASS" else "HOLD"
        ),
        "upstream_gate": upstream_gate,
        "candidate_generation": False,
        "server_submission": False,
        "seed": "not_used",
        "snapshot_audit_status": "AUDITED_PASS",
        "integration_status": "PASS",
        "scientific_validation_status": "NOT_RUN",
        "snapshots": {
            "CollecTRI": snapshot_summary(collectri),
            "OmniPath": snapshot_summary(omnipath),
        },
        "routes": {
            "Gata4": {
                "evidence_family": "CURATED_TF_TARGET",
                "source": "CollecTRI",
                **_route_summary([row for row in tf_rows if row["target_gene"] == "Gata4"]),
            },
            "Gata6": {
                "evidence_family": "CURATED_TF_TARGET",
                "source": "CollecTRI",
                **_route_summary([row for row in tf_rows if row["target_gene"] == "Gata6"]),
            },
            "CTNNB1": {
                "evidence_family": "DIRECTED_SIGNALING",
                "source": "OmniPath",
                "max_hops": 2,
                **_path_summary(beta_paths),
            },
        },
        "evidence_paths": [
            "knowledge_edge_evidence.tsv",
            "beta_directed_paths.tsv",
        ],
        "not_run": [
            "state_gate_join",
            "cell_state_or_pathway_activity_validation",
            "prior_committee_consumption",
            "response_top_k_or_amplitude_selection",
            "H5AD_candidate_generation",
            "local_scorer",
            "server_submission",
        ],
        "interpretation": (
            "Snapshot integrity and directed evidence consumption passed. "
            "The external component is not state-joined and therefore remains "
            "outside candidate admission; this is not a scientific validation "
            "or candidate-generation result."
        ),
        "blocks_submission": False,
    }
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    files = [edge_path, path_path, summary_path]
    if upstream_gate_snapshot_path is not None:
        files.append(upstream_gate_snapshot_path)
    manifest = {
        "schema": "ve.t3.s1b.knowledge-preflight-manifest.v1",
        "task": "T3-S1B-KNOWLEDGE-PREFLIGHT",
        "candidate_generation": False,
        "server_submission": False,
        "upstream_gate": upstream_gate,
        "source_snapshots": [
            {
                "source": snapshot.source_name,
                "manifest": str(snapshot.manifest_path.relative_to(repo)),
                "data": str(snapshot.data_path.relative_to(repo)),
                "sha256": snapshot.sha256,
                "rows": snapshot.row_count,
            }
            for snapshot in (collectri, omnipath)
        ],
        "source_files": [
            _source_file(collectri.manifest_path, repo),
            _source_file(omnipath.manifest_path, repo),
            _source_file(collectri.panel_path, repo),
            _source_file(
                repo / "docs/batch3/interfaces/virtual_embryo_tools/directed_knowledge.py",
                repo,
            ),
            *(
                [_source_file(upstream_gate_snapshot_path, repo)]
                if upstream_gate_snapshot_path is not None
                else []
            ),
        ],
        "runner": {
            "path": str(Path(__file__).resolve().relative_to(repo)),
            "sha256": _sha256(Path(__file__).resolve()),
        },
        "files": [
            {
                "path": str(path.relative_to(output_dir)),
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
            for path in files
        ],
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "artifacts/tool_integration/T3-S1B-KNOWLEDGE-PREFLIGHT-20260831-v3"
        ),
    )
    args = parser.parse_args(argv)
    summary = run_preflight(args.repo, args.output_dir)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
