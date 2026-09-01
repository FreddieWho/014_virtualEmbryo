#!/usr/bin/env python3
"""Build the T3-S1 signed-prior bundle from audited local evidence.

The runner is deliberately prior-only.  It adapts the immutable B2 evidence
into the Batch 3 schema, records unavailable or not-yet-integrated external
knowledge explicitly, and stops before H5AD/candidate generation or server
scoring.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPO_DEFAULT = Path(__file__).resolve().parents[1]
B2_RELATIVE = Path("artifacts/atomic_batch2/B2-T3-A1")
P0_HASH_RELATIVE = Path("artifacts/tool_integration/P0-LOCK/metrics/batch2_reuse_hashes_20260831.tsv")
TASK_INPUT_LOCK_RELATIVE = Path("docs/batch3/config/T3_S1_INPUT_LOCK.json")
KNOWLEDGE_PREFLIGHT_RELATIVE = Path(
    "artifacts/tool_integration/T3-S1B-KNOWLEDGE-PREFLIGHT-20260831-v3/summary.json"
)
VALIDATION_CONDITION = "GATA4_GATA6_VALIDATION_E875"
BETA_CONDITION = "BETA_CATENIN_HIDDEN_E875"
CONTEXT_STAGE = "E6.5-E8.5_WT_CONTEXT"
DOSAGE_FRACTIONS = {"Gata4": 0.0, "Gata6": 0.5, "CTNNB1": 0.0}
VOTE_FIELDS = [
    "target_gene", "condition_id", "stage", "state", "response_gene", "sign",
    "rank_score", "confidence", "evidence_family", "directness_score",
    "dosage_fraction", "lineage_gate", "provenance", "conflict_flag",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "pass"}


def as_float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    result = float(value)
    if not 0.0 <= result <= 1.0:
        raise ValueError(f"expected a probability/score in [0,1], got {value!r}")
    return result


def locked_hashes(repo: Path) -> dict[str, str]:
    path = repo / P0_HASH_RELATIVE
    if not path.is_file():
        raise FileNotFoundError(path)
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        digest, relative = line.split(None, 1)
        result[relative] = digest
    return result


def task_locked_hashes(repo: Path) -> dict[str, str]:
    path = repo / TASK_INPUT_LOCK_RELATIVE
    if not path.is_file():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    files = payload.get("files")
    if not isinstance(files, dict) or not files:
        raise ValueError(f"invalid task input lock: {path}")
    return {str(relative): str(digest) for relative, digest in files.items()}


def verify_small_locked_inputs(repo: Path, required: list[str]) -> dict[str, Any]:
    locks = locked_hashes(repo)
    locks.update(task_locked_hashes(repo))
    checked: dict[str, Any] = {}
    for relative in required:
        path = repo / relative
        expected = locks.get(relative)
        if expected is None:
            raise KeyError(f"missing P0 hash lock for {relative}")
        if not path.is_file():
            raise FileNotFoundError(path)
        actual = sha256_file(path)
        checked[relative] = {
            "expected_sha256": expected,
            "actual_sha256": actual,
            "match": actual == expected,
        }
        if actual != expected:
            raise ValueError(f"locked input hash mismatch: {relative}")
    return checked


def directness_by_gene(rows: list[dict[str, str]]) -> dict[str, float]:
    result: dict[str, float] = {}
    for row in rows:
        gene = row.get("gene", "")
        if gene:
            # B2's `score` is an enrichment scale and can exceed one.  The
            # normalized `weight` is the contract-compatible directness score.
            raw = row.get("weight", "") or row.get("score", "")
            value = float(raw) if raw not in (None, "") else 0.0
            value = min(1.0, max(0.0, value))
            result[gene] = max(result.get(gene, 0.0), value)
    return result


def build_standard_votes(
    b2: Path,
    output: Path,
    *,
    knowledge_status: str = "BLOCKED_EXTERNAL_DATA",
) -> dict[str, Any]:
    prior_rows = read_tsv(b2 / "prior_votes.tsv")
    direct_rows = read_tsv(b2 / "directness_panel.tsv")
    lineage_rows = read_tsv(b2 / "lineage_gate.tsv")
    directness = directness_by_gene(direct_rows)
    standard: list[dict[str, Any]] = []
    base_keys: dict[tuple[str, str], dict[str, str]] = {}
    model_fields = (
        ("celloracle_sign", "celloracle_confidence", "WT_INFERRED_GRN_LOCAL"),
        ("sctenifold_sign", "sctenifold_confidence", "WT_CONDITIONAL_NETWORK_LOCAL"),
    )
    for row in prior_rows:
        target = row.get("target", "")
        if target not in {"Gata4", "Gata6"}:
            continue
        state = row["official_state"]
        gene = row["gene"]
        base_keys[(state, gene)] = row
        for sign_field, confidence_field, family in model_fields:
            standard.append(
                {
                    "target_gene": target,
                    "condition_id": VALIDATION_CONDITION,
                    "stage": CONTEXT_STAGE,
                    "state": state,
                    "response_gene": gene,
                    "sign": int(row[sign_field]),
                    "rank_score": as_float(row[confidence_field]),
                    "confidence": as_float(row[confidence_field]),
                    "evidence_family": family,
                    "directness_score": directness.get(gene, as_float(row.get("directness_weight"), 0.0)),
                    "dosage_fraction": DOSAGE_FRACTIONS[target],
                    "lineage_gate": as_float(row.get("p_mesp1_lineage"), 0.0),
                    "provenance": (
                        "B2-T3-A1|prior_votes.tsv|"
                        f"{family}|source_archive_not_executed"
                    ),
                    "conflict_flag": as_bool(row.get("conflict_or_one_vote", False)),
                }
            )

    beta_evidence_family = (
        "EXTERNAL_KNOWLEDGE_AUDITED_NOT_INTEGRATED"
        if knowledge_status == "AUDITED_PASS"
        else "BLOCKED_EXTERNAL_DATA"
    )
    beta_provenance = (
        "audited_panel_scoped_CollecTRI_OmniPath_snapshot_present_but_not_consumed_by_S1_prior_runner"
        if knowledge_status == "AUDITED_PASS"
        else "no_local_CollecTRI_or_OmniPath_directed_signaling_snapshot"
    )
    for (state, gene), row in sorted(base_keys.items()):
        standard.append(
            {
                "target_gene": "CTNNB1",
                "condition_id": BETA_CONDITION,
                "stage": CONTEXT_STAGE,
                "state": state,
                "response_gene": gene,
                "sign": 0,
                "rank_score": 0.0,
                "confidence": 0.0,
                "evidence_family": beta_evidence_family,
                "directness_score": "",
                "dosage_fraction": DOSAGE_FRACTIONS["CTNNB1"],
                "lineage_gate": as_float(row.get("p_mesp1_lineage"), 0.0),
                "provenance": beta_provenance,
                "conflict_flag": False,
            }
        )
    write_tsv(output, standard, VOTE_FIELDS)
    return {
        "input_rows": len(prior_rows),
        "standard_rows": len(standard),
        "validation_rows": sum(row["condition_id"] == VALIDATION_CONDITION for row in standard),
        "beta_blocked_rows": sum(row["condition_id"] == BETA_CONDITION for row in standard),
        "genes": len({row["response_gene"] for row in standard}),
        "states": len({row["state"] for row in standard}),
    }


def build_standard_gate(b2: Path, output: Path) -> dict[str, Any]:
    rows = read_tsv(b2 / "lineage_gate.tsv")
    by_state: dict[str, dict[str, str]] = {}
    for row in rows:
        state = row.get("official_state", "")
        if state:
            by_state[state] = row
    standard: list[dict[str, Any]] = []
    for condition in (VALIDATION_CONDITION, BETA_CONDITION):
        for state, row in sorted(by_state.items()):
            probability = as_float(row.get("p_mesp1_lineage"), 0.0)
            standard.append(
                {
                    "condition_id": condition,
                    "stage": CONTEXT_STAGE,
                    "state": state,
                    "lineage_gate": probability,
                    "p_mesp1_lineage": probability,
                    "gate_pass": as_bool(row.get("responds", False)),
                    "target_expression": "",
                    "tf_activity": "",
                    "pathway_activity": "",
                    "activity_evidence_status": "NOT_AVAILABLE_IN_LOCKED_B2_GATE",
                    "activity_evidence": "B2-T3-A1/lineage_gate.tsv contains lineage marker probability only",
                    "provenance": "B2-T3-A1|lineage_gate.tsv|continuous_marker_probability",
                    "evidence": row.get("evidence", ""),
                }
            )
    fields = [
        "condition_id", "stage", "state", "lineage_gate", "p_mesp1_lineage",
        "gate_pass", "target_expression", "tf_activity", "pathway_activity",
        "activity_evidence_status", "activity_evidence", "provenance", "evidence",
    ]
    write_tsv(output, standard, fields)
    return {
        "rows": len(standard),
        "states": len(by_state),
        "passed": sum(as_bool(row["gate_pass"]) for row in standard),
    }


def merge_evidence(path_l1: Path, path_l2: Path, output: Path) -> None:
    rows: list[dict[str, Any]] = []
    for lane, path in (("L1_STRICT_AGREEMENT", path_l1), ("L2_CONDITION_AWARE", path_l2)):
        for row in read_tsv(path):
            rows.append({"lane": lane, **row})
    fields = ["lane"] + [field for field in rows[0] if field != "lane"] if rows else ["lane"]
    write_tsv(output, rows, fields)


def tf_edge_to_ko_minus_wt(edge_sign: int, *, wt_tf: float = 1.0, ko_tf: float = 0.0) -> int:
    """Convert a signed TF edge into a KO-minus-matched-WT response sign."""
    if edge_sign not in (-1, 1):
        raise ValueError("toy TF edge sign must be activating (+1) or repressing (-1)")
    if not (0.0 <= ko_tf <= 1.0 and 0.0 <= wt_tf <= 1.0) or ko_tf == wt_tf:
        raise ValueError("toy TF activities must be distinct values in [0, 1]")
    # A repressor has target activity 1 - TF activity; an activator has
    # target activity equal to TF activity.  This is the same sign transform
    # used whenever an edge-based source is adapted to the prior schema.
    wt_target = wt_tf if edge_sign == 1 else 1.0 - wt_tf
    ko_target = ko_tf if edge_sign == 1 else 1.0 - ko_tf
    delta = ko_target - wt_target
    return 1 if delta > 0 else -1 if delta < 0 else 0


def sign_convention_report() -> dict[str, Any]:
    cases = []
    for edge_type, edge_sign in (("activating", 1), ("repressing", -1)):
        expected = -edge_sign
        observed = tf_edge_to_ko_minus_wt(edge_sign)
        cases.append(
            {
                "edge_type": edge_type,
                "tf_target_edge_sign": edge_sign,
                "expected_ko_minus_wt": expected,
                "observed_ko_minus_wt": observed,
                "pass": observed == expected,
            }
        )
    return {
        "status": "PASS" if all(case["pass"] for case in cases) else "FAIL",
        "definition": "KO_MINUS_MATCHED_WT",
        "positive_means": "KO expression/activity is higher than matched WT",
        "transform": "tf_edge_to_ko_minus_wt",
        "cases": cases,
    }


def known_ko_report(b2: Path) -> dict[str, Any]:
    identity = json.loads((b2 / "kill_test/identity_score.json").read_text(encoding="utf-8"))
    pipeline = json.loads((b2 / "kill_test/pipeline_score.json").read_text(encoding="utf-8"))
    identity_metrics = identity.get("metrics", {})
    pipeline_metrics = pipeline.get("metrics", {})
    de_identity = float(identity_metrics.get("de_score", 0.0))
    de_pipeline = float(pipeline_metrics.get("de_score", 0.0))
    direction_identity = float(identity_metrics.get("de_direction", 0.0))
    direction_pipeline = float(pipeline_metrics.get("de_direction", 0.0))
    return {
        "status": "PASS_VALIDATION_ONLY"
        if de_pipeline > de_identity or direction_pipeline > direction_identity
        else "HOLD_VALIDATION_ONLY",
        "target": "Mab21l2",
        "target_used_for_gata4_or_beta_sign": False,
        "source_only": True,
        "comparison": {
            "de_score_like": {"identity": de_identity, "adapter": de_pipeline},
            "de_direction_like": {"identity": direction_identity, "adapter": direction_pipeline},
            "adapter_not_below_identity_on_both": (
                de_pipeline >= de_identity and direction_pipeline >= direction_identity
            ),
        },
        "identity_evidence": "B2-T3-A1/kill_test/identity_score.json",
        "adapter_evidence": "B2-T3-A1/kill_test/pipeline_score.json",
        "limitations": [
            "Mab21l2 is validation-only and cannot choose Gata4/Gata6/CTNNB1 signs",
            "DES/DCS were not available; de_score/de_direction are explicitly like-for-like diagnostics",
        ],
    }


def stability_report(source_votes: Path) -> dict[str, Any]:
    rows = read_tsv(source_votes)
    groups: dict[tuple[str, str, str, str, str], dict[str, set[int]]] = defaultdict(lambda: defaultdict(set))
    for row in rows:
        if row["evidence_family"] in {"BLOCKED_EXTERNAL_DATA", "BLOCKED_TOOLCHAIN"}:
            continue
        sign = int(row["sign"])
        if sign:
            groups[
                (row["target_gene"], row["condition_id"], row["stage"], row["state"], row["response_gene"])
            ][row["evidence_family"]].add(sign)
    complete = sum(
        len(families) >= 2 and len({sign for signs in families.values() for sign in signs}) == 1
        for families in groups.values()
    )
    families = sorted({family for group in groups.values() for family in group})
    leave_one_out = {}
    for removed in families:
        retained = 0
        for group in groups.values():
            remaining = {family: signs for family, signs in group.items() if family != removed}
            if len(remaining) >= 2 and len({sign for signs in remaining.values() for sign in signs}) == 1:
                retained += 1
        leave_one_out[removed] = {"consensus_groups": retained, "denominator": complete}
    return {
        "status": "PASS_WITH_SENSITIVITY" if complete else "NOT_TESTABLE",
        "analysis": "one evidence-family leave-one-out; no seed/grid search",
        "groups": len(groups),
        "complete_consensus_groups": complete,
        "families": families,
        "leave_one_out": leave_one_out,
        "interpretation": "removing either of the two model families removes strict two-family identifiability",
    }


def cap_metrics(records: list[Any], panel_size: int, fraction: float) -> dict[str, Any]:
    grouped: dict[tuple[str, str, str, str], list[Any]] = defaultdict(list)
    for record in records:
        grouped[(record.target_gene, record.condition_id, record.stage, record.state)].append(record)
    violations = []
    cap = max(1, int(panel_size * fraction))
    for key, group in grouped.items():
        selected = sum(record.sign != 0 for record in group)
        if selected > cap:
            violations.append({"group": key, "selected": selected, "cap": cap})
    return {"status": "PASS" if not violations else "FAIL", "cap": cap, "violations": violations}


def write_gate_report(
    artifact: Path,
    *,
    deployment: dict[str, Any],
    sign_report: dict[str, Any],
    known_report: dict[str, Any],
    stability: dict[str, Any],
    l1_records: list[Any],
    l2_records: list[Any],
    gate_summary: dict[str, Any],
    knowledge_preflight_status: str = "NOT_RUN",
    knowledge_preflight_evidence: str | None = None,
) -> dict[str, Any]:
    knowledge_blocked = deployment.get("knowledge_snapshots", {}).get("status") == "BLOCKED_EXTERNAL_DATA"
    celloracle_importable = deployment.get("tools", {}).get("CellOracle_import", {}).get("importable", False)
    sct_source_match = deployment.get("tools", {}).get("scTenifoldKnk_import", {}).get("source_version_match", False)
    celloracle_errors = [
        line.strip()
        for line in str(deployment.get("tools", {}).get("CellOracle_import", {}).get("stderr", "")).splitlines()
        if "ModuleNotFoundError:" in line or "ImportError:" in line
    ]
    celloracle_value = (
        "source import passed"
        if celloracle_importable
        else "source installed but import blocked"
        + (f"; {celloracle_errors[-1]}" if celloracle_errors else "")
    )
    gata4_l1_selected = [
        record
        for record in l1_records
        if record.target_gene == "Gata4" and record.sign != 0
    ]
    gata4_directness_ok = bool(gata4_l1_selected) and all(
        record.directness_score is not None and record.directness_score > 0.0
        for record in gata4_l1_selected
    )
    stability_leave_one_out_failed = any(
        result.get("denominator", 0) > 0 and result.get("consensus_groups", 0) == 0
        for result in stability.get("leave_one_out", {}).values()
    )
    criteria = [
        {
            "name": "sign_convention",
            "result": "PASS" if sign_report["status"] == "PASS" else "FAIL",
            "value": sign_report["definition"],
            "evidence": "metrics/sign_convention_test.json",
        },
        {
            "name": "independent_sign_models",
            "result": "PASS" if any(len(record.source_families) >= 2 and record.sign != 0 for record in l1_records + l2_records) else "FAIL",
            "value": "two local model families represented; upstream package execution separate",
            "evidence": "intermediates/source_votes.tsv",
        },
        {
            "name": "lineage_state_gate",
            "result": "PASS" if gate_summary.get("passed", 0) else "FAIL",
            "value": gate_summary,
            "evidence": "intermediates/state_gate.tsv",
        },
        {
            "name": "conflict_zero_in_selected_records",
            "result": "PASS" if all(not record.conflict_flag for record in l1_records + l2_records if record.sign != 0) else "FAIL",
            "value": "selected nonzero records only",
            "evidence": "intermediates/evidence.tsv",
        },
        {
            "name": "L1_cap",
            "result": cap_metrics(l1_records, 500, 0.10)["status"],
            "value": cap_metrics(l1_records, 500, 0.10),
            "evidence": "intermediates/prior_L1.json",
        },
        {
            "name": "L2_cap",
            "result": cap_metrics(l2_records, 500, 0.25)["status"],
            "value": cap_metrics(l2_records, 500, 0.25),
            "evidence": "intermediates/prior_L2.json",
        },
        {
            "name": "known_KO_adapter_validation_only",
            "result": "PASS" if known_report["status"] == "PASS_VALIDATION_ONLY" else "BLOCKED",
            "value": known_report["comparison"],
            "evidence": "metrics/known_ko_adapter_check.json",
        },
        {
            "name": "Gata4_directness",
            "result": "PASS" if gata4_directness_ok else "FAIL",
            "value": {
                "lane": "L1_STRICT_AGREEMENT",
                "selected_nonzero_records": len(gata4_l1_selected),
                "requirement": "positive directness score or audited signed edge",
                "implemented_evidence": "positive directness score",
            },
            "evidence": "intermediates/evidence_L1.tsv",
        },
        {
            "name": "stability",
            "result": "BLOCKED" if (
                stability["status"] == "NOT_TESTABLE" or stability_leave_one_out_failed
            ) else "PASS",
            "value": stability,
            "evidence": "metrics/stability.json",
        },
        {
            "name": "CellOracle_import",
            "result": "PASS" if celloracle_importable else "BLOCKED",
            "value": celloracle_value,
            "evidence": "deployment/deployment_report.json",
        },
        {
            "name": "scTenifoldKnk_source_version",
            "result": "PASS" if sct_source_match else "BLOCKED",
            "value": "source 1.1 requires scTenifoldNet >=1.4; local fallback is 1.0.2/1.3",
            "evidence": "deployment/deployment_report.json",
        },
        {
            "name": "CollecTRI_OmniPath_snapshot_audit",
            "result": "BLOCKED" if knowledge_blocked else "PASS",
            "value": "required beta-catenin knowledge snapshot integrity",
            "evidence": "deployment/deployment_report.json",
        },
        {
            "name": "CollecTRI_OmniPath_directed_signaling_integration",
            # The S1 runner is prior-only.  A separate preflight may consume
            # the snapshots, but it must not be confused with this runner
            # having joined the evidence to state gates or prior records.
            "result": "NOT_RUN",
            "value": {
                "prior_runner_consumption": "NOT_RUN",
                "separate_preflight_status": knowledge_preflight_status,
                "scientific_validation_status": "NOT_RUN",
            },
            "evidence": knowledge_preflight_evidence or "not_run",
        },
    ]
    blockers = [
        criterion["name"]
        for criterion in criteria
        if criterion["result"] in {"BLOCKED", "FAIL", "NOT_RUN"}
    ]
    status = "HOLD" if blockers else "PASS"
    report = {
        "task_id": "T3-S1-PRIOR",
        "gate_id": "T3-S1-PRIOR-GATE",
        "status": status,
        "outcome": "HOLD_AS_COMPONENT" if status == "HOLD" else "PRIOR_GATE_PASS",
        "criteria": criteria,
        "evidence_paths": [
            "intermediates/source_votes.tsv",
            "intermediates/evidence.tsv",
            "intermediates/state_gate.tsv",
            "metrics/sign_convention_test.json",
            "metrics/known_ko_adapter_check.json",
            "metrics/stability.json",
            "deployment/deployment_report.json",
        ],
        "notes": (
            "This bundle is prior/gate evidence only. It is not an H5AD, server submission, "
            "leaderboard result, or mechanistic claim. blocks_submission: false."
        ),
        "route_admission": {
            "Gata4_Gata6": {
                "status": "HOLD",
                "blockers": [
                    name for name in blockers if name in {
                        "stability", "independent_sign_models", "lineage_state_gate",
                        "conflict_zero_in_selected_records", "L1_cap", "Gata4_directness",
                    }
                ],
                "candidate_generation": False,
            },
            "CTNNB1": {
                "status": "HOLD",
                "blockers": [
                    name for name in blockers if name in {
                        "CollecTRI_OmniPath_snapshot_audit",
                        "CollecTRI_OmniPath_directed_signaling_integration",
                        "stability",
                    }
                ],
                "candidate_generation": False,
            },
        },
    }
    path = artifact / "metrics/gate_report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def write_text_outputs(artifact: Path, deployment: dict[str, Any], hashes: dict[str, Any], summary: dict[str, Any], gate_report: dict[str, Any], known: dict[str, Any], stability: dict[str, Any], knowledge_preflight_status: str = "NOT_RUN") -> None:
    tools = deployment.get("tools", {})
    celloracle_importable = tools.get("CellOracle_import", {}).get("importable", False)
    velocyto_importable = tools.get("velocyto_import", {}).get("importable", False)
    sct_source_match = tools.get("scTenifoldKnk_import", {}).get("source_version_match", False)
    knowledge_status = deployment.get("knowledge_snapshots", {}).get("status", "UNKNOWN")
    celloracle_status = "SOURCE_PRESENT_IMPORTABLE" if celloracle_importable else "SOURCE_PRESENT_IMPORT_BLOCKED"
    celloracle_errors = [
        line.strip()
        for line in str(tools.get("CellOracle_import", {}).get("stderr", "")).splitlines()
        if "ModuleNotFoundError:" in line or "ImportError:" in line
    ]
    celloracle_note = (
        "local velocyto import passed"
        if velocyto_importable
        else "local velocyto import unavailable"
    )
    if celloracle_errors:
        celloracle_note += f"; {celloracle_errors[-1]}"
    sct_status = "SOURCE_PRESENT_VERSION_PASS" if sct_source_match else "SOURCE_PRESENT_VERSION_BLOCKED"
    sct_note = (
        "source scTenifoldNet requirement satisfied"
        if sct_source_match
        else "scTenifoldNet local version does not satisfy source 1.1"
    )
    knowledge_note = (
        "audited panel-scoped snapshots are present; a separate directed-evidence preflight is "
        f"{knowledge_preflight_status}, but this prior-only runner does not consume it, so "
        "beta-catenin remains zero pending state-joined S1B validation"
        if knowledge_status == "AUDITED_PASS"
        else "requires separately audited local snapshot"
    )
    config = (
        "task: T3-S1-PRIOR\n"
        "seed: 20260830\n"
        "active_task_required: T3-S1-PRIOR\n"
        "sign_definition: KO_MINUS_MATCHED_WT\n"
        f"validation_condition: {VALIDATION_CONDITION}\n"
        f"beta_condition: {BETA_CONDITION}\n"
        f"stage_context: {CONTEXT_STAGE}\n"
        "network_used: false\n"
        "external_downloads_used: false\n"
        "server_submission: false\n"
        "candidate_generation: false\n"
        "stop_after: prior_and_gate_written\n"
        "source_policy: B2 hash-locked sanitized evidence only\n"
    )
    (artifact / "config_resolved.yaml").write_text(config, encoding="utf-8")
    data_rows = [
        ["E-MTAB-6967", "sanitized WT expression; model input", "E-MTAB-6967", "PASS", "False", "B2 hash-locked input"],
        ["E-MTAB-11763", "metadata-only fallback; not model input", "E-MTAB-11763", "PASS_METADATA_ONLY_NO_PROCESSED_SNAPSHOT", "False", "not used for expression"],
        ["GSE52123", "E12.5 WT GATA4 ChIP directness only", "GSE52123", "PASS", "False", "directness cannot determine sign"],
        ["REACTOME", "audited pathway provenance/filter context; no sign", "ReactomePathways", "PASS", "False", "B2 component only"],
        ["GO", "audited ontology provenance/filter context; no sign", "go-basic/MOUSE", "PASS", "False", "B2 component only"],
        ["CELLORACLE", "pinned source archive; no pretrained model", "7948870a3b70f7d228e54734e1fa9ed3291fc23b", celloracle_status, "False", celloracle_note],
        ["SCTENIFOLDKNK", "pinned source archive; no pretrained model", "d635a5855295b4ee75909438b09b2ea27ce3437c", sct_status, "False", sct_note],
        ["CollecTRI", "required directed TF-target knowledge", "local snapshot", knowledge_status, "False", knowledge_note],
        ["OmniPath", "required directed signaling knowledge", "local snapshot", knowledge_status, "False", knowledge_note],
    ]
    write_tsv(
        artifact / "DATA_SOURCES_USED.tsv",
        ({"source_id": row[0], "role": row[1], "accession": row[2], "status": row[3], "target_used": row[4], "notes": row[5]} for row in data_rows),
        ["source_id", "role", "accession", "status", "target_used", "notes"],
    )
    disclosure = f"""# T3-S1-PRIOR method disclosure

- Parent evidence: immutable `artifacts/atomic_batch2/B2-T3-A1/`; small TSV inputs were re-hashed against the P0 lock.
- Expression context: sanitized E-MTAB-6967 WT only. E-MTAB-11763 remains metadata-only; no raw/quarantine records were read.
- The runner adapts two auditable B2 WT-only model columns into independent evidence families. It does not claim that the upstream packages generated the B2 votes.
- CellOracle 0.22.0 source deployment status is `{celloracle_status}` (`{celloracle_note}`). scTenifoldKnk source 1.1 status is `{sct_status}` (`{sct_note}`); any 1.0.2/1.3 copy remains version-mismatched and validation-only.
- CollecTRI and OmniPath snapshot audit status is `{knowledge_status}`; the separate directed-evidence preflight is `{knowledge_preflight_status}`. The current prior-only adapter does not consume that preflight, so beta-catenin rows carry `EXTERNAL_KNOWLEDGE_AUDITED_NOT_INTEGRATED` and sign zero; no TF-only substitute is used.
- Gata4/Gata6 target channels carry explicit dosage fractions: Gata4 `0.0`, Gata6 `0.5`; dosage is metadata and does not scale the sign or expression amplitude.
- The locked B2 lineage table supplies lineage probability and marker-program provenance only; target expression, TF activity, and pathway activity are recorded as `NOT_AVAILABLE_IN_LOCKED_B2_GATE`, not imputed.
- Sign is always `KO - matched WT`; directness contributes eligibility only and never determines sign. Mab21l2 is validation-only.
- L1 cap is 10% of the 500-gene panel; L2 cap is 25%. Conflict rows and failed lineage gates are zeroed.
- Stability is `{stability['status']}`: removing either model family removes all strict two-family consensus groups, so the gate remains conservative.
- This task ends at prior/gate. No H5AD, candidate, scorer call, upload, or leaderboard claim is produced.

Gate outcome: `{gate_report['outcome']}`.
"""
    (artifact / "METHOD_DISCLOSURE.md").write_text(disclosure, encoding="utf-8")
    completion = f"""# T3-S1-PRIOR completion report

- Task: `T3-S1-PRIOR`
- Parent: `P0-LOCK`; reused B2-T3-A1 evidence without modifying the parent.
- Standard vote rows: {summary['vote']['standard_rows']}; lineage rows: {summary['gate']['rows']}.
- L1/L2 prior JSON and evidence tables were written; sign convention and validation-only known-KO checks were written.
- Deployment: `{deployment['overall_status']}`; external directed-signaling knowledge: `{deployment['knowledge_snapshots']['status']}`.
- Gate: `{gate_report['status']}` / `{gate_report['outcome']}`.
- Core limitation: CellOracle import status is `{celloracle_status}`, exact scTenifoldKnk 1.1 status is `{sct_status}`, and directed-signaling knowledge status is `{knowledge_status}`.
- `blocks_submission: false`; no candidate generation or server submission was attempted.

Input hash checks:
```json
{json.dumps(hashes, ensure_ascii=False, indent=2)}
```

Known-KO adapter status: `{known['status']}`. Stability status: `{stability['status']}`.
"""
    (artifact / "COMPLETION_REPORT.md").write_text(completion, encoding="utf-8")
    result = f"""# T3-S1-PRIOR RESULT

## Decision

`{gate_report['outcome']}`. The prior/gate bundle is an auditable component, not a biological or leaderboard conclusion.

## What is available

- Gata4/Gata6 validation-condition state×gene records derived from hash-locked B2 WT-only evidence.
- L1 strict-agreement and L2 condition-aware rankings with deterministic caps and conflict zeroing.
- KO-WT sign test, validation-only Mab21l2 adapter check, lineage gate, and one family leave-one-out stability diagnostic.

## Blocking risks

- CellOracle import status: `{celloracle_status}` (`{celloracle_note}`); local `velocyto` status is `{'PASS' if velocyto_importable else 'BLOCKED'}`.
- Exact scTenifoldKnk 1.1 status: `{sct_status}`; version-mismatched fallback is not treated as equivalent.
- CollecTRI/OmniPath snapshot audit status: `{knowledge_status}`; directed-evidence preflight status: `{knowledge_preflight_status}`. Neither is state-joined into this prior-only adapter, so beta-catenin rows remain `sign=0` pending S1B integration and validation.
- Stability status: `{stability['status']}`; one-family leave-one-out removes all strict consensus groups and keeps the gate at `HOLD`.

## Stop boundary

No H5AD, candidate, local scorer, server request, submission ID, or leaderboard score was created by this task.
"""
    (artifact / "RESULT.md").write_text(result, encoding="utf-8")


def write_manifest(artifact: Path, repo: Path) -> None:
    files = []
    for path in sorted(p for p in artifact.rglob("*") if p.is_file() and p.name != "MANIFEST.json"):
        files.append({"path": str(path.relative_to(artifact)), "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    source_files = []
    for relative in (
        "scripts/t3_s1_prior.py",
        "scripts/t3_prior_local_deployment.py",
        "scripts/t3_s1b_knowledge_preflight.py",
        "scripts/batch3_contract_preflight.py",
        "scripts/t3_stability_preflight.py",
        "docs/batch3/interfaces/virtual_embryo_tools/contract_io.py",
        "docs/batch3/interfaces/virtual_embryo_tools/directed_knowledge.py",
        "docs/batch3/schemas/prior.schema.json",
        str(TASK_INPUT_LOCK_RELATIVE),
        "docs/batch3/config/T3_S1_LOCAL_DEPENDENCY_LOCK.json",
    ):
        path = repo / relative
        if path.is_file():
            source_files.append(
                {"path": relative, "bytes": path.stat().st_size, "sha256": sha256_file(path)}
            )
    manifest = {
        "schema": "ve.t3.s1-prior.manifest.v1",
        "task": "T3-S1-PRIOR",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "candidate_generation": False,
        "server_submission": False,
        "source_files": source_files,
        "files": files,
    }
    (artifact / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=REPO_DEFAULT)
    parser.add_argument("--artifact", type=Path, default=None)
    args = parser.parse_args()
    repo = args.repo.resolve()
    artifact = (args.artifact or repo / "artifacts/tool_integration/T3-S1-PRIOR").resolve()
    b2 = repo / B2_RELATIVE
    artifact.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(repo / "docs/batch3/interfaces"))
    from virtual_embryo_tools.perturb_prior_committee import combine_prior_votes

    active_config = (repo / "docs/batch3/config/active_task.yaml").read_text(encoding="utf-8")
    if "active_task: T3-S1-PRIOR" not in active_config:
        raise RuntimeError("active task is not T3-S1-PRIOR")
    if "allow_external_downloads: false" not in active_config or "allow_server_submission: false" not in active_config:
        raise RuntimeError("task policy is not fail-closed for downloads/submission")
    required_hash_inputs = [
        "artifacts/atomic_batch2/B2-T3-A1/prior_votes.tsv",
        "artifacts/atomic_batch2/B2-T3-A1/directness_panel.tsv",
        "artifacts/atomic_batch2/B2-T3-A1/response_program.tsv",
        "artifacts/atomic_batch2/B2-T3-A1/lineage_gate.tsv",
        "artifacts/atomic_batch2/B2-T3-A1/kill_test/identity_score.json",
        "artifacts/atomic_batch2/B2-T3-A1/kill_test/pipeline_score.json",
    ]
    hashes = verify_small_locked_inputs(repo, required_hash_inputs)
    deployment_path = artifact / "deployment/deployment_report.json"
    deployment = json.loads(deployment_path.read_text(encoding="utf-8")) if deployment_path.is_file() else {
        "overall_status": "MISSING",
        "knowledge_snapshots": {"status": "BLOCKED_EXTERNAL_DATA"},
        "tools": {},
    }
    knowledge_status = deployment.get("knowledge_snapshots", {}).get("status", "UNKNOWN")
    knowledge_preflight_path = repo / KNOWLEDGE_PREFLIGHT_RELATIVE
    knowledge_preflight_status = "NOT_RUN"
    if knowledge_preflight_path.is_file():
        try:
            preflight = json.loads(knowledge_preflight_path.read_text(encoding="utf-8"))
            knowledge_preflight_status = str(
                preflight.get(
                    "status",
                    preflight.get("integration_status", "NOT_RUN"),
                )
            )
        except (OSError, json.JSONDecodeError, TypeError):
            knowledge_preflight_status = "PRESENT_BUT_NOT_PARSEABLE"
    vote_summary = build_standard_votes(
        b2,
        artifact / "intermediates/source_votes.tsv",
        knowledge_status=knowledge_status,
    )
    gate_summary = build_standard_gate(b2, artifact / "intermediates/state_gate.tsv")
    l1_tmp = artifact / "intermediates/evidence_L1.tsv"
    l2_tmp = artifact / "intermediates/evidence_L2.tsv"
    l1_records = combine_prior_votes(
        vote_tables=[artifact / "intermediates/source_votes.tsv"],
        state_gate_path=artifact / "intermediates/state_gate.tsv",
        lane="L1_STRICT_AGREEMENT",
        output_json=artifact / "intermediates/prior_L1.json",
        evidence_tsv=l1_tmp,
        config={
            "min_independent_families": 2,
            "max_nonzero_fraction": 0.10,
            "panel_size": 500,
            "directness_required_targets": ["Gata4"],
            # A zero-valued fallback means no audited occupancy evidence.  L1
            # requires positive directness unless an audited signed edge is
            # added; this adapter currently implements the former only.
            "directness_threshold": 1e-12,
            "dosage_fractions": DOSAGE_FRACTIONS,
        },
    )
    l2_records = combine_prior_votes(
        vote_tables=[artifact / "intermediates/source_votes.tsv"],
        state_gate_path=artifact / "intermediates/state_gate.tsv",
        lane="L2_CONDITION_AWARE",
        output_json=artifact / "intermediates/prior_L2.json",
        evidence_tsv=l2_tmp,
        config={
            "min_independent_families": 1,
            "max_nonzero_fraction": 0.25,
            "panel_size": 500,
            "dosage_fractions": DOSAGE_FRACTIONS,
        },
    )
    merge_evidence(l1_tmp, l2_tmp, artifact / "intermediates/evidence.tsv")
    sign_report = sign_convention_report()
    known_report = known_ko_report(b2)
    stability = stability_report(artifact / "intermediates/source_votes.tsv")
    (artifact / "metrics/sign_convention_test.json").write_text(json.dumps(sign_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (artifact / "metrics/known_ko_adapter_check.json").write_text(json.dumps(known_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (artifact / "metrics/stability.json").write_text(json.dumps(stability, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    gate_report = write_gate_report(
        artifact,
        deployment=deployment,
        sign_report=sign_report,
        known_report=known_report,
        stability=stability,
        l1_records=l1_records,
        l2_records=l2_records,
        gate_summary=gate_summary,
        knowledge_preflight_status=knowledge_preflight_status,
        knowledge_preflight_evidence=(
            str(knowledge_preflight_path.relative_to(repo))
            if knowledge_preflight_path.is_relative_to(repo)
            else str(knowledge_preflight_path)
        ),
    )
    summary = {"vote": vote_summary, "gate": gate_summary}
    write_text_outputs(
        artifact,
        deployment,
        hashes,
        summary,
        gate_report,
        known_report,
        stability,
        knowledge_preflight_status=knowledge_preflight_status,
    )
    log = {
        "task": "T3-S1-PRIOR",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "source_votes": vote_summary,
        "state_gate": gate_summary,
        "l1_records": len(l1_records),
        "l2_records": len(l2_records),
        "gate": gate_report["outcome"],
        "candidate_generation": False,
        "server_submission": False,
        "stop_after": "prior_and_gate_written",
    }
    (artifact / "run.log").write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_manifest(artifact, repo)
    print(json.dumps({"status": gate_report["outcome"], "artifact": str(artifact), "l1_nonzero": sum(r.sign != 0 for r in l1_records), "l2_nonzero": sum(r.sign != 0 for r in l2_records)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
