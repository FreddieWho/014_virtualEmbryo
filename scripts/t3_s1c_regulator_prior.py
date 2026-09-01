#!/usr/bin/env python3
"""Build an auditable CellOracle ``TFdict`` source-adapter prior for T3.

The locked promoter parquet is converted with CellOracle's native logic and is
never modified.  Only two explicitly contextual relations are added to a new
TFdict: Gata6 direct CollecTRI relations and the strict one-hop Ctnnb1->Pitx2
OmniPath relation.  The adapter is unsigned for inference purposes; source
database signs remain metadata and do not become KO effects or activity.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INTERFACES = ROOT / "docs" / "batch3" / "interfaces"
if str(INTERFACES) not in sys.path:
    sys.path.insert(0, str(INTERFACES))

from virtual_embryo_tools.directed_knowledge import (  # noqa: E402
    AuditedSnapshot,
    build_directed_paths,
    load_audited_snapshot,
)


ATOM = "T3-S1C-A-REGULATOR-PRIOR-BUILD-20260901-v1"
PARENT_ATOM = "T3-S1A-STATE-JOIN-20260901-v7"
RELATED_ATOM = "T3-S1B-STATE-JOIN-20260901-v3"
OUTPUT_DEFAULT = ROOT / "artifacts" / "tool_integration" / ATOM
SCRIPT_PATH = Path(__file__).resolve()
PANEL_PATH = ROOT / "data/gene_panel/T3__gata4.genes.txt"
BASE_GRN_PATH = (
    ROOT
    / "infra/external_data/sanitized/T3-S1A-STATE-JOIN/CELLORACLE/promoter_base_GRN"
    / "mm10_TFinfo_dataframe_gimmemotifsv5_fpr2_threshold_10_20210630.parquet"
)
BASE_GRN_SHA256 = "32de319419199f53bbdbf7c8545394a70052c7d14918d59b54c96593000dea40"
COLLECTRI_MANIFEST = ROOT / "infra/external_data/sanitized/T3-S1A-STATE-JOIN/COLLECTRI/snapshot_manifest.json"
OMNIPATH_MANIFEST = ROOT / "infra/external_data/sanitized/T3-S1A-STATE-JOIN/OMNIPATH/snapshot_manifest.json"
S1A_MANIFEST = ROOT / "artifacts/tool_integration/T3-S1A-STATE-JOIN-20260901-v7/metrics/artifact_manifest.stable.json"
S1B_MANIFEST = ROOT / "artifacts/tool_integration/T3-S1B-STATE-JOIN-20260901-v3/metrics/artifact_manifest.stable.json"
TARGETS = ("Gata4", "Gata6", "Ctnnb1")
SEED = 20260830


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def repo_relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def panel_genes(path: Path = PANEL_PATH) -> list[str]:
    genes = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(genes) != 500 or len(set(genes)) != 500:
        raise ValueError("T3 panel must contain exactly 500 unique genes")
    return genes


def base_tfdict(grn: pd.DataFrame) -> dict[str, list[str]]:
    """Mirror CellOracle 0.22.0 import_TF_data's matrix-to-TFdict rule."""
    if "peak_id" not in grn.columns or "gene_short_name" not in grn.columns:
        raise ValueError("CellOracle TF-info matrix requires peak_id and gene_short_name")
    tmp = grn.drop(["peak_id"], axis=1)
    tmp = tmp.groupby(by="gene_short_name").sum()
    return {
        str(gene): [str(column) for column in row[row > 0].index]
        for gene, row in tmp.iterrows()
    }


def tfdict_digest(tfdict: Mapping[str, Iterable[str]]) -> str:
    canonical = {
        str(gene): [str(regulator) for regulator in regulators]
        for gene, regulators in sorted(tfdict.items(), key=lambda item: str(item[0]))
    }
    payload = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _source_record(manifest_path: Path, snapshot: AuditedSnapshot) -> dict[str, Any]:
    return {
        "manifest_path": repo_relative(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "data_path": repo_relative(snapshot.data_path),
        "data_sha256": snapshot.sha256,
        "row_count": snapshot.row_count,
        "source_name": snapshot.source_name,
        "scope": "reused locked S1A audited snapshot; no new external download",
    }


def _edge_row(
    *,
    regulator: str,
    response: str,
    adapter_class: str,
    source_name: str,
    source_path: Path,
    hop_count: int,
    loader_eligible: bool,
    network_sign_status: str,
    provenance_suffix: str,
    exclusion_reason: str = "",
    pair_added: bool = False,
) -> dict[str, Any]:
    return {
        "regulator_gene": regulator,
        "response_gene": response,
        "adapter_class": adapter_class,
        "source_name": source_name,
        "source_record_key": f"{source_path}|{regulator}->{response}",
        "hop_count": hop_count,
        "loader_eligible": loader_eligible,
        "network_sign_status": network_sign_status,
        "activity_eligible": False,
        "signed_family_eligible": False,
        "state_scope": "GLOBAL_CONTEXTUAL",
        "pair_added": pair_added,
        "provenance": f"{source_name}|{source_path}|{provenance_suffix}",
        "exclusion_reason": exclusion_reason,
    }


def build_adapter_edges(
    collectri: AuditedSnapshot,
    omnipath: AuditedSnapshot,
    panel: list[str],
) -> list[dict[str, Any]]:
    """Select only the explicitly permitted one-hop source-adapter relations."""
    panel_set = set(panel)
    rows: list[dict[str, Any]] = []
    seen_gata6: set[str] = set()
    for edge in collectri.edges:
        if edge.source_gene != "Gata6" or edge.target_gene not in panel_set:
            continue
        pair_added = edge.target_gene not in seen_gata6
        seen_gata6.add(edge.target_gene)
        rows.append(
            _edge_row(
                regulator="Gata6",
                response=edge.target_gene,
                adapter_class="CUSTOM_DIRECT_TF_TARGET_SOURCE_ADAPTER",
                source_name=collectri.source_name,
                source_path=collectri.data_path,
                hop_count=1,
                loader_eligible=True,
                network_sign_status="RESOLVED" if edge.regulation_sign in (-1, 1) else "UNRESOLVED",
                provenance_suffix=f"{edge.source_gene}->{edge.target_gene}|direct_edge_presence_only",
                pair_added=pair_added,
            )
        )

    paths = build_directed_paths(omnipath, source_gene="Ctnnb1", max_hops=3, max_paths=5000)
    seen_ctnnb1: set[str] = set()
    for path in paths:
        response = str(path["response_gene"])
        hops = int(path["hops"])
        eligible = hops == 1 and response == "Pitx2" and len(path["path_nodes"]) == 2
        pair_added = eligible and response not in seen_ctnnb1
        if eligible:
            seen_ctnnb1.add(response)
        rows.append(
            _edge_row(
                regulator="Ctnnb1",
                response=response,
                adapter_class="CUSTOM_NON_TF_DIRECT_SIGNALING_SOURCE_ADAPTER",
                source_name=omnipath.source_name,
                source_path=omnipath.data_path,
                hop_count=hops,
                loader_eligible=eligible,
                network_sign_status=(
                    "RESOLVED" if int(path.get("ko_minus_wt_sign", 0) or 0) in (-1, 1) else "UNRESOLVED"
                ),
                provenance_suffix="->".join(str(node) for node in path["path_nodes"]),
                exclusion_reason="" if eligible else "CTNNB1_STRICT_ONE_HOP_PITX2_ONLY",
                pair_added=pair_added,
            )
        )
    return sorted(
        rows,
        key=lambda row: (
            str(row["regulator_gene"]),
            int(row["hop_count"]),
            str(row["response_gene"]),
            str(row["provenance"]),
        ),
    )


def augment_tfdict(
    base: Mapping[str, Iterable[str]],
    edge_rows: Iterable[Mapping[str, Any]],
) -> tuple[dict[str, list[str]], dict[str, Any]]:
    """Append only selected source relations; preserve native list order."""
    result = {str(gene): [str(regulator) for regulator in regulators] for gene, regulators in base.items()}
    selected = [row for row in edge_rows if bool(row.get("loader_eligible")) and bool(row.get("pair_added"))]
    for row in selected:
        regulator = str(row["regulator_gene"])
        response = str(row["response_gene"])
        if response not in result:
            raise ValueError(f"response gene {response!r} is absent from the native CellOracle TFdict")
        if regulator not in result[response]:
            result[response].append(regulator)
    return result, {
        "selected_unique_relation_count": len(selected),
        "selected_by_regulator": {
            regulator: len({str(row["response_gene"]) for row in selected if row["regulator_gene"] == regulator})
            for regulator in ("Gata6", "Ctnnb1")
        },
        "native_base_unchanged_outside_selected_relations": True,
    }


def capability_rows(
    base: Mapping[str, Iterable[str]],
    augmented: Mapping[str, Iterable[str]],
    edge_rows: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    edge_rows = list(edge_rows)
    for regulator in TARGETS:
        outgoing = {
            str(row["response_gene"])
            for row in edge_rows
            if row["regulator_gene"] == regulator and bool(row.get("loader_eligible")) and bool(row.get("pair_added"))
        }
        before = any(regulator in set(regulators) for regulators in base.values())
        after = any(regulator in set(regulators) for regulators in augmented.values())
        rows.append(
            {
                "regulator_gene": regulator,
                "source_membership_before": before,
                "source_membership_after": after,
                "response_rows_in_native_tfdict": sum(regulator in set(regulators) for regulators in base.values()),
                "selected_panel_response_count": len(outgoing),
                "adapter_class": (
                    "NATIVE_PROMOTER_TF_SOURCE"
                    if regulator == "Gata4"
                    else "CUSTOM_DIRECT_TF_TARGET_SOURCE_ADAPTER"
                    if regulator == "Gata6"
                    else "CUSTOM_NON_TF_DIRECT_SIGNALING_SOURCE_ADAPTER"
                ),
                "activity_eligible": False,
                "signed_family_eligible": False,
                "status": "PASS" if after else "BLOCKED_SOURCE_MEMBERSHIP",
            }
        )
    return rows


def write_tsv(path: Path, rows: Iterable[Mapping[str, Any]], fields: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in writer.fieldnames or ()})


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def _artifact_manifest(output_dir: Path) -> dict[str, Any]:
    files = []
    for path in sorted(output_dir.rglob("*")):
        if not path.is_file() or path.name == "artifact_manifest.stable.json":
            continue
        files.append({"path": path.relative_to(output_dir).as_posix(), "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    return {
        "schema": "ve.t3.s1c-a-regulator-prior-artifact-manifest.v1",
        "task": "T3-S1C-A-REGULATOR-PRIOR-BUILD",
        "atom": ATOM,
        "files": files,
    }


def run(*, output_dir: Path = OUTPUT_DEFAULT) -> dict[str, Any]:
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise FileExistsError(f"S1C-A output already exists: {output_dir}")
    output_dir.mkdir(parents=True)
    try:
        panel = panel_genes()
        for required in (BASE_GRN_PATH, S1A_MANIFEST, S1B_MANIFEST):
            if not required.is_file():
                raise FileNotFoundError(required)
        if sha256_file(BASE_GRN_PATH) != BASE_GRN_SHA256:
            raise ValueError("locked CellOracle promoter base-GRN SHA256 mismatch")
        base_grn = pd.read_parquet(BASE_GRN_PATH)
        base = base_tfdict(base_grn)
        before_gata4 = list(base.get("Gata4", []))
        collectri = load_audited_snapshot(
            COLLECTRI_MANIFEST,
            repo_root=ROOT,
            expected_source_name="CollecTRI",
            expected_dataset="collectri",
            expected_taxon_id=10090,
        )
        omnipath = load_audited_snapshot(
            OMNIPATH_MANIFEST,
            repo_root=ROOT,
            expected_source_name="OmniPath",
            expected_dataset="omnipath",
            expected_taxon_id=10090,
        )
        edge_rows = build_adapter_edges(collectri, omnipath, panel)
        augmented, augment_stats = augment_tfdict(base, edge_rows)
        capabilities = capability_rows(base, augmented, edge_rows)
        if not all(row["status"] == "PASS" for row in capabilities):
            raise ValueError("not all T3 regulators are source-compatible after adapter build")
        if list(augmented.get("Gata4", []))[: len(before_gata4)] != before_gata4:
            raise AssertionError("native Gata4 TFdict relations were removed or reordered")
        if augment_stats["selected_by_regulator"].get("Gata6") != 18:
            raise ValueError("Gata6 adapter must contain exactly 18 unique panel responses")
        if augment_stats["selected_by_regulator"].get("Ctnnb1") != 1:
            raise ValueError("Ctnnb1 adapter must contain exactly one strict direct response")

        inputs = output_dir / "inputs"
        grn = output_dir / "grn"
        metrics = output_dir / "metrics"
        input_lock = {
            "schema": "ve.t3.s1c-a-input-lock.v1",
            "atom": ATOM,
            "parent_atom": PARENT_ATOM,
            "related_atom": RELATED_ATOM,
            "seed": SEED,
            "target_truth_used": False,
            "panel": {"path": repo_relative(PANEL_PATH), "sha256": sha256_file(PANEL_PATH), "count": len(panel)},
            "parent_manifests": {
                "s1a": {"path": repo_relative(S1A_MANIFEST), "sha256": sha256_file(S1A_MANIFEST)},
                "s1b": {"path": repo_relative(S1B_MANIFEST), "sha256": sha256_file(S1B_MANIFEST)},
            },
            "base_grn": {"path": repo_relative(BASE_GRN_PATH), "sha256": sha256_file(BASE_GRN_PATH), "rows": len(base_grn), "columns": len(base_grn.columns)},
            "toolchain": {
                "CellOracle": importlib.metadata.version("celloracle"),
                "genomepy": importlib.metadata.version("genomepy"),
            },
            "sources": {
                "collectri": _source_record(COLLECTRI_MANIFEST, collectri),
                "omnipath": _source_record(OMNIPATH_MANIFEST, omnipath),
            },
            "new_external_download": False,
        }
        write_json(inputs / "input_lock.json", input_lock)
        write_json(
            grn / "augmented_tfdict.json",
            {
                "schema": "ve.t3.s1c-a-augmented-tfdict.v1",
                "atom": ATOM,
                "base_tfdict_digest": tfdict_digest(base),
                "augmented_tfdict_digest": tfdict_digest(augmented),
                "tfdict": augmented,
                "semantic_scope": "unsigned source adjacency for method compatibility; not causal sign or activity",
            },
        )
        write_tsv(
            grn / "regulator_edges.tsv",
            edge_rows,
            [
                "regulator_gene", "response_gene", "adapter_class", "source_name", "source_record_key",
                "hop_count", "loader_eligible", "network_sign_status", "activity_eligible",
                "signed_family_eligible", "state_scope", "pair_added", "provenance", "exclusion_reason",
            ],
        )
        write_json(
            metrics / "base_tfdict_equivalence.json",
            {
                "base_tfdict_digest": tfdict_digest(base),
                "augmented_tfdict_digest": tfdict_digest(augmented),
                "base_grn_sha256": sha256_file(BASE_GRN_PATH),
                "native_conversion": "CellOracle import_TF_data: drop peak_id; groupby gene_short_name; retain positive columns",
                "native_gata4_relations_preserved_as_prefix": list(augmented.get("Gata4", []))[: len(before_gata4)] == before_gata4,
                "added_relation_counts": augment_stats,
            },
        )
        write_tsv(
            metrics / "regulator_capability.tsv",
            capabilities,
            [
                "regulator_gene", "source_membership_before", "source_membership_after",
                "response_rows_in_native_tfdict", "selected_panel_response_count", "adapter_class",
                "activity_eligible", "signed_family_eligible", "status",
            ],
        )
        write_json(
            metrics / "source_schema_license_audit.json",
            {
                "schema": "ve.t3.s1c-a-source-audit.v1",
                "base_grn": {"path": repo_relative(BASE_GRN_PATH), "sha256": sha256_file(BASE_GRN_PATH), "schema": "CellOracle mm10 promoter TF-info parquet"},
                "collectri": _source_record(COLLECTRI_MANIFEST, collectri),
                "omnipath": _source_record(OMNIPATH_MANIFEST, omnipath),
                "panel": {"path": repo_relative(PANEL_PATH), "sha256": sha256_file(PANEL_PATH), "count": len(panel)},
                "license_note": "Existing S1A audited permits are reused; no new external data was downloaded by this atom.",
            },
        )
        gate = {
            "schema": "ve.t3.s1c-a-regulator-prior-gate.v1",
            "task": "T3-S1C-A-REGULATOR-PRIOR-BUILD",
            "atom": ATOM,
            "parent_atom": PARENT_ATOM,
            "status": "PASS",
            "network_availability": "AVAILABLE_CONTEXTUAL",
            "method_source_compatibility": "PASS",
            "biological_activity_status": "NOT_VALIDATED",
            "state_specificity_status": "NOT_EVALUATED",
            "signed_family_stability": "NOT_IDENTIFIABLE",
            "target_compatibility": {row["regulator_gene"]: row["status"] for row in capabilities},
            "candidate_generation": False,
            "server_submission": False,
            "blocks_submission": False,
            "outcome": "HOLD_AS_COMPONENT",
            "scientific_statement": "The adapter establishes source membership only; it does not establish direction, activity, state specificity, or causal validity.",
        }
        write_json(metrics / "gate_report.json", gate)
        result_text = (
            f"# {ATOM}\n\n"
            "Stage A completed as a method-compatibility component. Gata6 has 18 "
            "unique panel response relations from CollecTRI; Ctnnb1 has only the "
            "strict one-hop OmniPath Ctnnb1->Pitx2 relation. Multi-hop paths are "
            "retained as exclusions. No expression matrix was consumed.\n\n"
            "Biological activity, state specificity, signed-family stability and "
            "candidate admission remain unvalidated; no candidate or submission was created.\n"
        )
        (output_dir / "RESULT.md").write_text(result_text, encoding="utf-8")
        (output_dir / "METHOD_DISCLOSURE.md").write_text(
            "The native promoter parquet was not modified. The new TFdict is an "
            "unsigned contextual source-adjacency adapter; database regulation "
            "signs are metadata only and were not converted to KO effects.\n",
            encoding="utf-8",
        )
        completion = {
            "schema": "ve.t3.s1c-a-completion.v1",
            "task": "T3-S1C-A-REGULATOR-PRIOR-BUILD",
            "atom": ATOM,
            "parent_atom": PARENT_ATOM,
            "status": "PASS",
            "script": {"path": repo_relative(SCRIPT_PATH), "sha256": sha256_file(SCRIPT_PATH)},
            "selected_relation_counts": augment_stats["selected_by_regulator"],
            "biological_activity_status": "NOT_VALIDATED",
            "candidate_generation": False,
            "server_submission": False,
            "blocks_submission": False,
        }
        write_json(metrics / "completion_report.json", completion)
        manifest = _artifact_manifest(output_dir)
        write_json(metrics / "artifact_manifest.stable.json", manifest)
        return {"gate": gate, "completion": completion, "manifest": manifest}
    except Exception:
        shutil.rmtree(output_dir, ignore_errors=True)
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = run(output_dir=args.output)
    print(json.dumps(result["gate"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
