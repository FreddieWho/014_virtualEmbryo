#!/usr/bin/env python3
"""Audit-only S1B state/context integration for the T3 prior committee.

This atom consumes the immutable S1A v7 outputs and the already audited full
mouse knowledge snapshots.  It deliberately keeps external edge/path
evidence out of the biological activity/sign gate.  No CellOracle or
scTenifold computation is rerun here, and no candidate is produced.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any, Iterable, Mapping

from virtual_embryo_tools.directed_knowledge import (
    build_directed_paths,
    build_tf_edge_evidence,
    load_audited_snapshot,
)


ROOT = Path(__file__).resolve().parents[1]
ATOM = "T3-S1B-STATE-JOIN-20260901-v3"
PARENT_ATOM = "T3-S1A-STATE-JOIN-20260901-v7"
PARENT_DEFAULT = ROOT / "artifacts/tool_integration" / PARENT_ATOM
OUTPUT_DEFAULT = ROOT / "artifacts/tool_integration" / ATOM
SCRIPT_PATH = Path(__file__).resolve()
COLLECTRI_MANIFEST = ROOT / "infra/external_data/sanitized/T3-S1A-STATE-JOIN/COLLECTRI/snapshot_manifest.json"
OMNIPATH_MANIFEST = ROOT / "infra/external_data/sanitized/T3-S1A-STATE-JOIN/OMNIPATH/snapshot_manifest.json"

EXACT_STAGE = "E8.75"
ROUTES = (
    "GATA4_GATA6_VALIDATION_E875::L1_STRICT_AGREEMENT",
    "GATA4_GATA6_VALIDATION_E875::L2_CONDITION_AWARE",
    "BETA_CATENIN_HIDDEN_E875::L1_STRICT_AGREEMENT",
    "BETA_CATENIN_HIDDEN_E875::L2_CONDITION_AWARE",
)
CONDITIONS = {
    "GATA4_GATA6_VALIDATION_E875": ("Gata4", "Gata6"),
    "BETA_CATENIN_HIDDEN_E875": ("Ctnnb1",),
}
EXTERNAL_FAMILIES = {"CURATED_TF_TARGET", "DIRECTED_SIGNALING"}
UNSIGNED_FAMILIES = {"WT_NETWORK_RANK_ONLY"}
BIOLOGICAL_FAMILIES = {"WT_CELLORACLE_REAL"}

REQUIRED_VOTE_FIELDS = (
    "target_gene",
    "condition_id",
    "stage",
    "state",
    "response_gene",
    "sign",
    "rank_score",
    "confidence",
    "evidence_family",
    "dosage_fraction",
    "directness_score",
    "lineage_gate",
    "provenance",
    "conflict_flag",
)
STATE_GATE_FIELDS = (
    "condition_id",
    "stage",
    "state",
    "lineage_gate",
    "p_mesp1_lineage",
    "gate_pass",
    "state_join_status",
    "state_sample_n",
    "activity_gate_pass",
    "target_gene",
    "target_expression",
    "tf_activity",
    "pathway_activity",
    "activity_evidence_status",
    "matched_external_state",
    "match_similarity",
    "external_n",
    "provenance",
)
RAW_EXTERNAL_FIELDS = (
    "source_type",
    "source_name",
    "target_gene",
    "response_gene",
    "regulation_sign",
    "ko_minus_wt_sign",
    "hops",
    "path_nodes",
    "directness_score",
    "conflict_flag",
    "confidence_status",
    "provenance",
)
JOINED_EXTERNAL_FIELDS = (
    "route_id",
    "target_gene",
    "condition_id",
    "stage",
    "state",
    "matched_external_state",
    "mapping_collision",
    "response_gene",
    "raw_sign",
    "canonical_sign",
    "sign",
    "sign_status",
    "rank_score",
    "confidence",
    "evidence_family",
    "dosage_fraction",
    "directness_score",
    "lineage_gate",
    "provenance",
    "conflict_flag",
    "source_type",
    "state_scope",
    "independence_class",
    "activity_eligible",
    "evidence_channel",
)
AUDIT_VOTE_FIELDS = (
    "route_id",
    *REQUIRED_VOTE_FIELDS,
    "raw_sign",
    "canonical_sign",
    "conflict_status",
    "evidence_channel",
    "independence_class",
    "activity_eligible",
)
CONFLICT_AUDIT_FIELDS = (
    "route_id",
    "evidence_channel",
    "target_gene",
    "condition_id",
    "stage",
    "state",
    "response_gene",
    "raw_signs",
    "families",
    "conflict",
    "canonical_sign",
    "status",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: Iterable[Mapping[str, Any]], fields: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    field_list = list(fields)
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=field_list,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in field_list})


def json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    token = str(value).strip().lower()
    if token in {"true", "1", "yes"}:
        return True
    if token in {"false", "0", "no", ""}:
        return False
    raise ValueError(f"invalid boolean token: {value!r}")


def _float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"non-finite numeric value: {value!r}")
    return result


def _route_slug(route_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", route_id).strip("_").lower()


def _route_condition(route_id: str) -> tuple[str, str]:
    condition, lane = route_id.split("::", 1)
    if route_id not in ROUTES or condition not in CONDITIONS:
        raise ValueError(f"unknown route: {route_id}")
    return condition, lane


def build_state_mapping_audit(
    state_rows: Iterable[Mapping[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Collapse the duplicated condition rows into one parent-state mapping.

    A parent state mapping to multiple external states is an input error.  An
    external state mapping to multiple parent states is retained as an audit
    collision and never treated as independent evidence.
    """
    mapping: dict[str, dict[str, Any]] = {}
    by_external: dict[str, list[str]] = defaultdict(list)
    for raw in state_rows:
        state = str(raw.get("state", "")).strip()
        external = str(raw.get("matched_external_state", "")).strip()
        if not state or not external:
            raise ValueError("state mapping contains an empty parent or external state")
        entry = {
            "matched_external_state": external,
            "match_similarity": _float_or_none(raw.get("match_similarity")),
            "external_n": int(raw.get("external_n", 0) or 0),
        }
        old = mapping.get(state)
        if old is not None and old["matched_external_state"] != external:
            raise ValueError(
                f"BLOCKED_INPUT_IDENTITY: parent state {state!r} maps to multiple external states"
            )
        mapping[state] = old or entry
        if state not in by_external[external]:
            by_external[external].append(state)
    collisions = {
        external: sorted(states)
        for external, states in sorted(by_external.items())
        if len(states) > 1
    }
    audit = {
        "schema": "ve.t3.s1b-state-join-audit.v1",
        "parent_state_count": len(mapping),
        "matched_external_state_count": len(by_external),
        "ambiguous_external_states": collisions,
        "projection": "recorded_parent_state_to_external_context_label",
        "unmatched_external_states_excluded": True,
        "project_external_state": {
            "matched": sorted(by_external),
            "unmatched": [],
        },
        "external_scope": "GLOBAL_CONTEXTUAL",
        "independence_class": "SUPPORTING_KNOWLEDGE",
        "activity_gate_effect": "NONE",
    }
    return mapping, audit


def _external_context_rows(raw_rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in raw_rows:
        source_type = str(raw.get("source_type", "")).strip()
        if source_type not in {"edge", "path"}:
            raise ValueError(f"unknown external evidence type: {source_type!r}")
        target = str(raw.get("target_gene", "")).strip()
        if source_type == "edge":
            if target not in {"Gata4", "Gata6"}:
                continue
            condition = "GATA4_GATA6_VALIDATION_E875"
            route_ids = [route for route in ROUTES if route.startswith(condition)]
        else:
            if target != "Ctnnb1":
                continue
            condition = "BETA_CATENIN_HIDDEN_E875"
            route_ids = [route for route in ROUTES if route.startswith(condition)]
        for route_id in route_ids:
            _, lane = _route_condition(route_id)
            max_hops = 2 if "L1" in lane else 3
            hops = int(raw.get("hops", 0) or 0) if source_type == "path" else 0
            if source_type == "path" and hops > max_hops:
                continue
            sign = int(raw.get("ko_minus_wt_sign", 0) or 0)
            if sign not in (-1, 0, 1):
                raise ValueError("external evidence sign must be -1, 0, or 1")
            rows.append(
                {
                    "route_id": route_id,
                    "target_gene": target,
                    "condition_id": condition,
                    "stage": EXACT_STAGE,
                    "response_gene": str(raw.get("response_gene", "")).strip(),
                    "state": "",
                    "matched_external_state": "",
                    "mapping_collision": False,
                    "raw_sign": sign,
                    "canonical_sign": sign,
                    "sign": sign,
                    "sign_status": "CONFLICT" if _bool(raw.get("conflict_flag", False)) else ("SIGNED" if sign else "ZERO_RESPONSE"),
                    "rank_score": (
                        0.8
                        if source_type == "edge" and sign
                        else 1.0 / max(1, hops)
                        if source_type == "path"
                        else 0.0
                    ),
                    "confidence": "",
                    "evidence_family": "CURATED_TF_TARGET" if source_type == "edge" else "DIRECTED_SIGNALING",
                    "dosage_fraction": 0.5 if target == "Gata6" else 0.0,
                    "directness_score": raw.get("directness_score", "") if source_type == "edge" else "",
                    "lineage_gate": "",
                    "provenance": str(raw.get("provenance", "")),
                    "conflict_flag": _bool(raw.get("conflict_flag", False)),
                    "source_type": source_type,
                    "state_scope": "GLOBAL_CONTEXTUAL",
                    "independence_class": "SUPPORTING_KNOWLEDGE",
                    "activity_eligible": False,
                    "evidence_channel": "EXTERNAL_CONTEXT",
                    "hops": hops if source_type == "path" else "",
                    "path_nodes": raw.get("path_nodes", "") if source_type == "path" else "",
                    "regulation_sign": raw.get("regulation_sign", ""),
                }
            )
    return rows


def expand_contextual_evidence(
    raw_rows: Iterable[Mapping[str, Any]],
    state_mapping: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Project state-free external knowledge onto parent states as context only."""
    if not state_mapping:
        raise ValueError("cannot project external evidence without a state mapping")
    base_rows = _external_context_rows(raw_rows)
    collision_counts: Counter[str] = Counter(
        str(entry.get("matched_external_state", "")) for entry in state_mapping.values()
    )
    output: list[dict[str, Any]] = []
    for base in base_rows:
        for state in sorted(state_mapping):
            external = str(state_mapping[state]["matched_external_state"])
            row = dict(base)
            row["state"] = state
            row["matched_external_state"] = external
            row["mapping_collision"] = collision_counts[external] > 1
            output.append(row)
    return sorted(
        output,
        key=lambda row: (
            str(row["route_id"]),
            str(row["target_gene"]),
            str(row["state"]),
            str(row["response_gene"]),
            str(row["provenance"]),
        ),
    )


def _raw_external_evidence(collectri: Any, omnipath: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target in ("Gata4", "Gata6"):
        for row in build_tf_edge_evidence(collectri, target_gene=target):
            rows.append(
                {
                    "source_type": "edge",
                    "source_name": row["source_name"],
                    "target_gene": target,
                    "response_gene": row["response_gene"],
                    "regulation_sign": row.get("regulation_sign", ""),
                    "ko_minus_wt_sign": row["ko_minus_wt_sign"],
                    "hops": "",
                    "path_nodes": "",
                    "directness_score": row.get("directness_score", ""),
                    "conflict_flag": row.get("conflict_flag", False),
                    "confidence_status": row.get("confidence_status", ""),
                    "provenance": row["provenance"],
                }
            )
    for row in build_directed_paths(
        omnipath, source_gene="Ctnnb1", max_hops=3, max_paths=5000
    ):
        rows.append(
            {
                "source_type": "path",
                "source_name": omnipath.source_name,
                "target_gene": "Ctnnb1",
                "response_gene": row["response_gene"],
                "regulation_sign": "",
                "ko_minus_wt_sign": row["ko_minus_wt_sign"],
                "hops": row["hops"],
                "path_nodes": "->".join(str(node) for node in row["path_nodes"]),
                "directness_score": "",
                "conflict_flag": row.get("conflict_flag", False),
                "confidence_status": "UNRESOLVED_PATH_DIRECTION" if row.get("conflict_flag") else "UNCALIBRATED_EXTERNAL_EVIDENCE",
                "provenance": row["provenance"],
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            str(row["source_type"]),
            str(row["target_gene"]),
            str(row["response_gene"]),
            int(row["hops"] or 0),
            str(row["path_nodes"]),
            str(row["provenance"]),
        ),
    )


def _vote_group_key(row: Mapping[str, Any]) -> tuple[str, str, str, str, str, str, str]:
    return (
        str(row.get("route_id", "")),
        str(row.get("evidence_channel", "BIOLOGICAL_MODEL")),
        str(row.get("target_gene", "")),
        str(row.get("condition_id", "")),
        str(row.get("stage", "")),
        str(row.get("state", "")),
        str(row.get("response_gene", "")),
    )


def _is_unsigned(row: Mapping[str, Any]) -> bool:
    return str(row.get("evidence_family", "")) in UNSIGNED_FAMILIES or str(
        row.get("independence_class", "")
    ) == "UNSIGNED_RANK"


def _canonicalize_conflicts(
    rows: Iterable[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Zero only derived conflicting contributions and retain raw signs/status."""
    materialized = [dict(row) for row in rows]
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in materialized:
        row["raw_sign"] = int(row.get("raw_sign", row.get("sign", 0)) or 0)
        groups[_vote_group_key(row)].append(row)
    audit: list[dict[str, Any]] = []
    for key in sorted(groups):
        group = groups[key]
        signed = {
            int(row["raw_sign"])
            for row in group
            if int(row["raw_sign"]) in (-1, 1) and not _is_unsigned(row)
        }
        conflict = {-1, 1}.issubset(signed) or any(
            _bool(row.get("conflict_flag", False)) and not _is_unsigned(row)
            for row in group
        )
        canonical_sign = 0 if conflict else next(iter(signed), 0)
        for row in group:
            raw_sign = int(row["raw_sign"])
            if _is_unsigned(row) and raw_sign == 0:
                status = "UNSIGNED"
                row["sign"] = 0
            elif conflict:
                status = "CONFLICT"
                row["sign"] = 0
                row["conflict_flag"] = True
            elif raw_sign == 0 and _bool(row.get("conflict_flag", False)):
                status = "CONFLICT"
                row["sign"] = 0
                row["conflict_flag"] = True
            elif raw_sign == 0:
                status = "ZERO_RESPONSE"
                row["sign"] = 0
            else:
                status = "SIGNED"
                row["sign"] = raw_sign
            row["canonical_sign"] = int(row["sign"])
            row["conflict_status"] = status
        audit.append(
            {
                "route_id": key[0],
                "evidence_channel": key[1],
                "target_gene": key[2],
                "condition_id": key[3],
                "stage": key[4],
                "state": key[5],
                "response_gene": key[6],
                "raw_signs": ";".join(str(int(row["raw_sign"])) for row in group),
                "families": ";".join(sorted({str(row.get("evidence_family", "")) for row in group})),
                "conflict": bool(conflict),
                "canonical_sign": int(canonical_sign if conflict else next(iter(signed), 0)),
                "status": "CONFLICT" if conflict else "UNSIGNED" if all(_is_unsigned(row) for row in group) else "SIGNED" if signed else "ZERO_RESPONSE",
            }
        )
    return materialized, audit


def _model_only(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in rows
        if str(row.get("evidence_channel", "BIOLOGICAL_MODEL")) == "BIOLOGICAL_MODEL"
        and str(row.get("evidence_family", "")) not in EXTERNAL_FAMILIES
    ]


def _relevant_states(rows: Iterable[Mapping[str, Any]], state_rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    conditions = {str(row.get("condition_id", "")) for row in rows}
    if not conditions:
        return [dict(row) for row in state_rows]
    return [dict(row) for row in state_rows if str(row.get("condition_id", "")) in conditions]


def _evaluate_biological_claim(
    rows: Iterable[Mapping[str, Any]],
    state_rows: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Evaluate only biological-model rows; external rows are structurally ignored."""
    model_rows = _model_only(rows)
    relevant = _relevant_states(model_rows, state_rows)
    activity_values = [_bool(row.get("activity_gate_pass", False)) for row in relevant]
    activity_pass = bool(activity_values) and all(activity_values)
    targets = sorted({str(row.get("target_gene", "")) for row in model_rows})
    per_target: dict[str, Any] = {}
    for target in targets:
        target_rows = [row for row in model_rows if str(row.get("target_gene")) == target]
        families = sorted(
            {
                str(row.get("evidence_family"))
                for row in target_rows
                if int(row.get("sign", 0) or 0) in (-1, 1)
                and str(row.get("evidence_family")) in BIOLOGICAL_FAMILIES
            }
        )
        conflicts = sum(
            str(row.get("conflict_status", "")) == "CONFLICT" for row in target_rows
        )
        if not families:
            status = "NOT_IDENTIFIABLE"
        elif conflicts:
            status = "CONFLICT"
        elif not activity_pass:
            status = "HOLD_ACTIVITY_NOT_VALIDATED"
        elif len(families) < 2:
            status = "NOT_IDENTIFIABLE_INSUFFICIENT_BIOLOGICAL_FAMILIES"
        else:
            status = "PASS"
        per_target[target] = {
            "independent_biological_families": families,
            "signed_rows": sum(int(row.get("sign", 0) or 0) in (-1, 1) for row in target_rows),
            "unsigned_rows": sum(_is_unsigned(row) for row in target_rows),
            "conflict_rows": conflicts,
            "status": status,
        }
    return {
        "status": "PASS" if activity_pass and all(item["status"] == "PASS" for item in per_target.values()) else "HOLD",
        "activity_gate_pass": activity_pass,
        "activity_evidence_status": "VALIDATED" if activity_pass else "NOT_VALIDATED",
        "per_target": per_target,
    }


def leave_one_family_out(
    rows: Iterable[Mapping[str, Any]],
    state_rows: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Recompute each fold from native biological rows, before any selection."""
    model_rows = _model_only(rows)
    relevant_states = _relevant_states(model_rows, state_rows)
    native, _ = _canonicalize_conflicts(model_rows)
    full = _evaluate_biological_claim(native, relevant_states)
    families = sorted(
        {
            str(row.get("evidence_family"))
            for row in model_rows
            if str(row.get("evidence_family")) in BIOLOGICAL_FAMILIES
            and int(row.get("raw_sign", row.get("sign", 0)) or 0) in (-1, 1)
        }
    )
    folds: dict[str, Any] = {}
    for family in families:
        held_out = [
            dict(row)
            for row in model_rows
            if str(row.get("evidence_family")) != family
        ]
        fold_rows, _ = _canonicalize_conflicts(held_out)
        folds[family] = _evaluate_biological_claim(fold_rows, relevant_states)
    per_target: dict[str, Any] = {}
    for target, value in full["per_target"].items():
        target_folds = {
            family: fold["per_target"].get(target, {"status": "NOT_IDENTIFIABLE"})
            for family, fold in folds.items()
        }
        per_target[target] = {
            **value,
            "loo": target_folds,
            "independent_biological_families": value["independent_biological_families"],
            "status": value["status"] if len(value["independent_biological_families"]) >= 2 else "NOT_IDENTIFIABLE",
        }
    status = "PASS" if per_target and all(item["status"] == "PASS" for item in per_target.values()) else "NOT_IDENTIFIABLE"
    return {
        "schema": "ve.t3.s1b-family-lofo.v1",
        "status": status,
        "leakage_guard": "FAMILY_NATIVE_RECOMPUTATION",
        "selection_recomputed_before_gate": True,
        "independent_families": families,
        "full_claim": full,
        "per_target": per_target,
        "folds": folds,
        "external_context_families_excluded": sorted(EXTERNAL_FAMILIES),
        "external_context_invariance": True,
        "notes": [
            "External edge/path rows are supporting knowledge and are not independent biological model families.",
            "Unsigned rank rows do not enter signed-family LOFO.",
            "Activity remains NOT_VALIDATED; LOFO does not establish biological replicates or in vivo activity.",
        ],
    }


def _parent_vote_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
    values: list[Any] = []
    for field in ("route_id", *REQUIRED_VOTE_FIELDS):
        value = row.get(field, "")
        if field == "sign":
            value = int(value or 0)
        elif field in {"rank_score", "confidence", "dosage_fraction", "directness_score", "lineage_gate"}:
            parsed = _float_or_none(value)
            value = None if parsed is None else round(parsed, 12)
        elif field == "conflict_flag":
            value = _bool(value)
        else:
            value = str(value)
        values.append(value)
    return tuple(values)


def _validate_parent_manifest(parent_dir: Path, gate: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
    stable_path = parent_dir / "metrics/artifact_manifest.stable.json"
    if not stable_path.is_file():
        raise ValueError("BLOCKED_INPUT_IDENTITY: parent stable manifest is missing")
    expected_hashes = {
        str(route.get("artifact_manifest_sha256", ""))
        for route in gate.get("routes", [])
        if route.get("artifact_manifest_sha256")
    }
    actual_stable_hash = sha256_file(stable_path)
    if expected_hashes and actual_stable_hash not in expected_hashes:
        raise ValueError("BLOCKED_INPUT_IDENTITY: parent stable manifest hash disagrees with gate")
    manifest = json.loads(stable_path.read_text(encoding="utf-8"))
    if manifest.get("task") != "T3-S1A-STATE-JOIN":
        raise ValueError("BLOCKED_INPUT_IDENTITY: parent manifest task is not S1A")
    entries = manifest.get("files")
    if not isinstance(entries, list) or not entries:
        raise ValueError("BLOCKED_INPUT_IDENTITY: parent manifest has no file entries")
    for entry in entries:
        rel = Path(str(entry.get("path", "")))
        path = (parent_dir / rel).resolve()
        if parent_dir.resolve() not in path.parents:
            raise ValueError("BLOCKED_INPUT_IDENTITY: parent manifest path escapes atom")
        if not path.is_file():
            raise ValueError(f"BLOCKED_INPUT_IDENTITY: missing parent artifact {rel}")
        if path.stat().st_size != int(entry.get("bytes", -1)):
            raise ValueError(f"BLOCKED_INPUT_IDENTITY: byte mismatch for parent artifact {rel}")
        if sha256_file(path) != str(entry.get("sha256", "")):
            raise ValueError(f"BLOCKED_INPUT_IDENTITY: hash mismatch for parent artifact {rel}")
    return manifest, actual_stable_hash


def _validate_parent_inputs(parent_dir: Path) -> dict[str, Any]:
    gate_path = parent_dir / "metrics/gate_report.v2.repaired.json"
    if not gate_path.is_file():
        raise ValueError("BLOCKED_INPUT_IDENTITY: repaired parent gate is missing")
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    route_ids = [str(route.get("route_id", "")) for route in gate.get("routes", [])]
    if sorted(route_ids) != sorted(ROUTES):
        raise ValueError("BLOCKED_INPUT_IDENTITY: parent routes do not match the four locked routes")
    if gate.get("candidate_generation") is not False or gate.get("server_submission") is not False:
        raise ValueError("BLOCKED_INPUT_IDENTITY: parent gate has an enabled downstream action")
    manifest, stable_hash = _validate_parent_manifest(parent_dir, gate)

    state_path = parent_dir / "intermediates/state_gate.tsv"
    source_path = parent_dir / "intermediates/source_votes.tsv"
    state_rows = read_tsv(state_path)
    source_rows = read_tsv(source_path)
    if tuple(state_rows[0]) != STATE_GATE_FIELDS if state_rows else True:
        raise ValueError("BLOCKED_INPUT_IDENTITY: parent state_gate schema changed")
    expected_source_fields = ("route_id", *REQUIRED_VOTE_FIELDS)
    if tuple(source_rows[0]) != expected_source_fields if source_rows else True:
        raise ValueError("BLOCKED_INPUT_IDENTITY: parent source_votes schema changed")
    for row in state_rows:
        if str(row.get("stage")) != EXACT_STAGE:
            raise ValueError("BLOCKED_INPUT_IDENTITY: parent state gate stage changed")
        if _bool(row.get("activity_gate_pass", False)):
            raise ValueError("BLOCKED_INPUT_IDENTITY: S1B input activity gate is unexpectedly true")
    mapping, mapping_audit = build_state_mapping_audit(state_rows)
    if len(state_rows) != len(mapping) * len({str(row.get("condition_id")) for row in state_rows}):
        raise ValueError("BLOCKED_INPUT_IDENTITY: duplicated or missing condition/state rows")
    if not source_rows:
        raise ValueError("BLOCKED_INPUT_IDENTITY: parent source_votes is empty")
    for row in source_rows:
        if row.get("route_id") not in ROUTES:
            raise ValueError("BLOCKED_INPUT_IDENTITY: parent source_votes contains an unknown route")
        if row.get("stage") != EXACT_STAGE or row.get("state") not in mapping:
            raise ValueError("BLOCKED_INPUT_IDENTITY: parent source vote identity changed")
        if int(row.get("sign", 0)) not in (-1, 0, 1):
            raise ValueError("BLOCKED_INPUT_IDENTITY: parent source vote sign is invalid")

    deployment_path = parent_dir / "deployment/DEPLOYMENT_MANIFEST.json"
    if not deployment_path.is_file():
        raise ValueError("BLOCKED_INPUT_IDENTITY: locked local deployment manifest is missing")
    deployment = json.loads(deployment_path.read_text(encoding="utf-8"))
    if deployment.get("status") != "READY_FOR_EXACT_INPUT_RUN":
        raise ValueError("BLOCKED_INPUT_IDENTITY: local deployment is not the locked exact-input deployment")

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
    gate_snapshots = gate.get("source_snapshots", {})
    for name, snapshot in (("CollecTRI", collectri), ("OmniPath", omnipath)):
        declared = gate_snapshots.get(name, {})
        if str(declared.get("sha256", "")) != snapshot.sha256 or int(declared.get("row_count", -1)) != snapshot.row_count:
            raise ValueError(f"BLOCKED_INPUT_IDENTITY: {name} snapshot disagrees with parent gate")
    return {
        "parent_dir": parent_dir,
        "gate": gate,
        "stable_manifest": manifest,
        "stable_manifest_path": parent_dir / "metrics/artifact_manifest.stable.json",
        "stable_manifest_sha256": stable_hash,
        "state_path": state_path,
        "source_path": source_path,
        "state_rows": state_rows,
        "source_rows": source_rows,
        "state_mapping": mapping,
        "state_mapping_audit": mapping_audit,
        "collectri": collectri,
        "omnipath": omnipath,
        "deployment_path": deployment_path,
        "deployment": deployment,
    }


def _decorate_model_rows(source_rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for raw in source_rows:
        row = dict(raw)
        family = str(row.get("evidence_family", ""))
        if family in EXTERNAL_FAMILIES:
            continue
        row["sign"] = int(row.get("sign", 0) or 0)
        row["raw_sign"] = row["sign"]
        row["evidence_channel"] = "UNSIGNED_RANK" if family in UNSIGNED_FAMILIES else "BIOLOGICAL_MODEL"
        row["independence_class"] = "UNSIGNED_RANK" if family in UNSIGNED_FAMILIES else "BIOLOGICAL_MODEL"
        row["activity_eligible"] = family in BIOLOGICAL_FAMILIES
        output.append(row)
    return output


def _compare_external_rows(
    parent_rows: Iterable[Mapping[str, Any]],
    generated_rows: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    parent_external = [
        row for row in parent_rows if str(row.get("evidence_family", "")) in EXTERNAL_FAMILIES
    ]
    generated = list(generated_rows)
    parent_counter = Counter(_parent_vote_key(row) for row in parent_external)
    generated_counter = Counter(_parent_vote_key(row) for row in generated)
    missing = parent_counter - generated_counter
    unexpected = generated_counter - parent_counter
    return {
        "status": "PASS" if not missing and not unexpected else "BLOCKED_INPUT_IDENTITY",
        "parent_external_rows": len(parent_external),
        "generated_external_rows": len(generated),
        "missing_rows": int(sum(missing.values())),
        "unexpected_rows": int(sum(unexpected.values())),
        "parent_family_counts": dict(sorted(Counter(str(row.get("evidence_family")) for row in parent_external).items())),
        "generated_family_counts": dict(sorted(Counter(str(row.get("evidence_family")) for row in generated).items())),
    }


def _source_vote_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        [dict(row) for row in rows],
        key=lambda row: (
            str(row.get("route_id", "")),
            str(row.get("target_gene", "")),
            str(row.get("condition_id", "")),
            str(row.get("stage", "")),
            str(row.get("state", "")),
            str(row.get("response_gene", "")),
            str(row.get("evidence_family", "")),
            str(row.get("provenance", "")),
        ),
    )


def _route_state_vector(
    route_id: str,
    model_rows: Iterable[Mapping[str, Any]],
    contextual_rows: Iterable[Mapping[str, Any]],
    state_rows: Iterable[Mapping[str, Any]],
    stability: Mapping[str, Any],
    selected_records: int,
) -> dict[str, Any]:
    condition, lane = _route_condition(route_id)
    targets = CONDITIONS[condition]
    route_states = sorted(
        {str(row.get("state", "")) for row in state_rows if str(row.get("condition_id")) == condition}
    )
    state_lookup = {
        str(row.get("state")): row
        for row in state_rows
        if str(row.get("condition_id")) == condition
    }
    route_model = [row for row in model_rows if str(row.get("route_id")) == route_id]
    route_context = [row for row in contextual_rows if str(row.get("route_id")) == route_id]
    claim = _evaluate_biological_claim(route_model, [state_lookup[state] for state in route_states])
    matrix: list[dict[str, Any]] = []
    target_summary: dict[str, Any] = {}
    for target in targets:
        target_model = [row for row in route_model if str(row.get("target_gene")) == target]
        target_context = [row for row in route_context if str(row.get("target_gene")) == target]
        signed = [row for row in target_model if int(row.get("sign", 0) or 0) in (-1, 1)]
        rank = [row for row in target_model if _is_unsigned(row)]
        target_stability = stability.get("per_target", {}).get(target, {})
        context_conflict = sum(str(row.get("conflict_status")) == "CONFLICT" for row in target_context)
        target_summary[target] = {
            "biological_model_families": sorted({str(row.get("evidence_family")) for row in signed}),
            "biological_signed_rows": len(signed),
            "unsigned_rank_rows": len(rank),
            "contextual_rows": len(target_context),
            "contextual_signed_rows": sum(int(row.get("sign", 0) or 0) in (-1, 1) for row in target_context),
            "contextual_conflict_rows": context_conflict,
            "contextual_directness_rows": sum(row.get("directness_score", "") not in ("", None) for row in target_context),
            "stability_status": target_stability.get("status", "NOT_IDENTIFIABLE"),
            "biological_activity_status": "NOT_VALIDATED",
            "context_affects_biological_gate": False,
        }
        for state in route_states:
            state_row = state_lookup[state]
            state_model = [row for row in target_model if str(row.get("state")) == state]
            raw_signs = [int(row.get("raw_sign", row.get("sign", 0)) or 0) for row in state_model]
            statuses = {str(row.get("conflict_status", "")) for row in state_model}
            if "CONFLICT" in statuses:
                conflict_status = "CONFLICT"
            elif any(_is_unsigned(row) for row in state_model) and not any(sign for sign in raw_signs):
                conflict_status = "UNSIGNED"
            elif any(sign for sign in raw_signs):
                conflict_status = "SIGNED"
            else:
                conflict_status = "NO_SIGN"
            if not state_model or not any(sign for sign in raw_signs):
                final = "NOT_IDENTIFIABLE"
            elif conflict_status == "CONFLICT":
                final = "CONFLICT"
            elif not _bool(state_row.get("activity_gate_pass", False)):
                final = "HOLD_ACTIVITY_NOT_VALIDATED"
            elif not _bool(state_row.get("gate_pass", False)):
                final = "HOLD_LINEAGE_GATE"
            else:
                final = "PASS"
            matrix.append(
                {
                    "target_gene": target,
                    "state": state,
                    "input_valid": True,
                    "route_applicable": True,
                    "claim_eligible": final == "PASS",
                    "raw_direction": ";".join(str(sign) for sign in raw_signs if sign),
                    "raw_rank": len([row for row in state_model if _is_unsigned(row)]),
                    "conflict_status": conflict_status,
                    "stability_status": target_stability.get("status", "NOT_IDENTIFIABLE"),
                    "final_claim_status": final,
                }
            )

    blockers: list[str] = []
    if any(not _bool(row.get("activity_gate_pass", False)) for row in state_lookup.values()):
        blockers.append("STATE_ACTIVITY_NOT_VALIDATED")
    if selected_records == 0:
        blockers.append("NO_SELECTED_SIGNED_RECORDS")
    if stability.get("status") != "PASS":
        blockers.append("EVIDENCE_FAMILY_STABILITY_NOT_IDENTIFIABLE")
    for target in targets:
        summary = target_summary[target]
        if not summary["biological_model_families"]:
            blockers.append(f"{target}:SIGNED_MODEL_NOT_IDENTIFIABLE")
        if target == "Gata4" and "L1" in lane and summary["contextual_directness_rows"]:
            blockers.append("Gata4:DIRECTNESS_CONTEXT_ONLY")
        if target == "Ctnnb1" and summary["contextual_rows"]:
            blockers.append("Ctnnb1:SIGNALING_CONTEXT_ONLY")
    return {
        "route_id": route_id,
        "condition_id": condition,
        "lane": lane,
        "status": "HOLD",
        "outcome": "HOLD_AS_COMPONENT",
        "blocks_submission": False,
        "candidate_generation": False,
        "server_submission": False,
        "blockers": sorted(set(blockers)),
        "biological_claim": claim,
        "unsigned_rank_claim": {
            "status": "DESCRIPTIVE_ONLY_UNSIGNED",
            "rows": sum(_is_unsigned(row) for row in route_model),
            "affects_biological_gate": False,
        },
        "contextual_support": {
            "status": "GLOBAL_CONTEXTUAL_ONLY" if route_context else "NO_CONTEXT_ROWS",
            "rows": len(route_context),
            "signed_rows": sum(int(row.get("sign", 0) or 0) in (-1, 1) for row in route_context),
            "conflict_rows": sum(str(row.get("conflict_status")) == "CONFLICT" for row in route_context),
            "state_scope": "GLOBAL_CONTEXTUAL",
            "independence_class": "SUPPORTING_KNOWLEDGE",
            "affects_biological_gate": False,
        },
        "biological_activity_status": "NOT_VALIDATED",
        "selected_records": selected_records,
        "evidence_family_leave_one_out": stability.get("status", "NOT_IDENTIFIABLE"),
        "evidence_family_stability": stability,
        "target_summary": target_summary,
        "state_claim_vector": matrix,
    }


def _write_stable_manifest(output_dir: Path, implementation_sha256: str) -> Path:
    excluded = {
        "metrics/artifact_manifest.stable.json",
        "metrics/gate_report.v2.json",
        "run.log",
    }
    files: list[dict[str, Any]] = []
    for path in sorted(output_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(output_dir).as_posix()
        if rel in excluded or ".tmp-" in rel or rel.endswith(".part"):
            continue
        files.append({"path": rel, "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    manifest = {
        "schema": "ve.t3.s1b-artifact-manifest.v1",
        "task": ATOM,
        "parent_atom": PARENT_ATOM,
        "implementation_sha256": implementation_sha256,
        "note": "Stable S1B audit manifest; gate report and run.log are intentionally not self-referenced.",
        "files": files,
    }
    path = output_dir / "metrics/artifact_manifest.stable.json"
    json_write(path, manifest)
    return path


def _write_blocked(output_dir: Path, exc: Exception) -> None:
    if output_dir.exists() and any(output_dir.iterdir()):
        return
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "ve.t3.s1b-blocker.v1",
        "atom": ATOM,
        "status": "BLOCKED_INPUT_IDENTITY",
        "reason": str(exc),
        "candidate_generation": False,
        "server_submission": False,
        "blocks_submission": False,
    }
    json_write(output_dir / "metrics/blocker.json", payload)
    (output_dir / "RESULT.md").write_text(
        f"# {ATOM}\n\n状态：`BLOCKED_INPUT_IDENTITY`\n\n原因：{exc}\n\n未生成候选，未提交服务器。\n",
        encoding="utf-8",
    )


def run_s1b(
    output_dir: Path = OUTPUT_DEFAULT,
    parent_dir: Path = PARENT_DEFAULT,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    parent_dir = Path(parent_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        existing = {
            path.relative_to(output_dir).as_posix()
            for path in output_dir.rglob("*")
            if path.is_file()
        }
        if existing == {"metrics/blocker.json", "RESULT.md"}:
            (output_dir / "metrics/blocker.json").rename(
                output_dir / "metrics/previous_blocker.json"
            )
        else:
            raise FileExistsError(f"refusing to overwrite non-empty output atom: {output_dir}")
    inputs = _validate_parent_inputs(parent_dir)
    implementation_sha256 = sha256_file(SCRIPT_PATH)
    raw_external = _raw_external_evidence(inputs["collectri"], inputs["omnipath"])
    contextual = expand_contextual_evidence(raw_external, inputs["state_mapping"])
    generated_required = [dict(row) for row in contextual]
    comparison = _compare_external_rows(inputs["source_rows"], generated_required)
    if comparison["status"] != "PASS":
        raise ValueError(
            "BLOCKED_INPUT_IDENTITY: regenerated external rows disagree with parent source_votes "
            f"({comparison['missing_rows']} missing, {comparison['unexpected_rows']} unexpected)"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "intermediates").mkdir(parents=True, exist_ok=True)
    (output_dir / "metrics").mkdir(parents=True, exist_ok=True)
    model_rows = _decorate_model_rows(inputs["source_rows"])
    model_rows, model_conflicts = _canonicalize_conflicts(model_rows)
    contextual, contextual_conflicts = _canonicalize_conflicts(contextual)
    all_rows = _source_vote_rows([*model_rows, *contextual])

    write_tsv(output_dir / "intermediates/raw_external_evidence.tsv", raw_external, RAW_EXTERNAL_FIELDS)
    write_tsv(output_dir / "intermediates/state_joined_evidence.tsv", contextual, JOINED_EXTERNAL_FIELDS)
    write_tsv(output_dir / "intermediates/state_gate.tsv", inputs["state_rows"], STATE_GATE_FIELDS)
    write_tsv(
        output_dir / "intermediates/conflict_audit.tsv",
        [*model_conflicts, *contextual_conflicts],
        CONFLICT_AUDIT_FIELDS,
    )
    write_tsv(output_dir / "intermediates/source_votes.tsv", all_rows, AUDIT_VOTE_FIELDS)
    json_write(output_dir / "metrics/external_row_identity.json", comparison)
    mapping_audit = dict(inputs["state_mapping_audit"])
    mapping_audit.update(
        {
            "parent_atom": PARENT_ATOM,
            "external_raw_rows": len(raw_external),
            "state_joined_rows": len(contextual),
            "contextual_conflict_rows": sum(item["status"] == "CONFLICT" for item in contextual_conflicts),
            "candidate_generation": False,
            "server_submission": False,
            "blocks_submission": False,
            "biological_activity_status": "NOT_VALIDATED",
        }
    )
    json_write(output_dir / "metrics/state_join_audit.json", mapping_audit)

    parent_refs = {
        "parent_atom": PARENT_ATOM,
        "implementation": {
            "path": "scripts/t3_s1b_state_join.py",
            "sha256": implementation_sha256,
            "source_control_status": "NO_INITIAL_COMMIT_BRANCH_UNKNOWN",
        },
        "parent_stable_manifest": str(inputs["stable_manifest_path"]),
        "parent_stable_manifest_sha256": inputs["stable_manifest_sha256"],
        "parent_state_gate": {"path": str(inputs["state_path"]), "sha256": sha256_file(inputs["state_path"])},
        "parent_source_votes": {"path": str(inputs["source_path"]), "sha256": sha256_file(inputs["source_path"])},
        "local_deployment": {
            "path": str(inputs["deployment_path"]),
            "sha256": sha256_file(inputs["deployment_path"]),
            "status": inputs["deployment"].get("status"),
        },
        "external_snapshots": {
            "CollecTRI": {
                "manifest": str(COLLECTRI_MANIFEST),
                "data": str(inputs["collectri"].data_path),
                "sha256": inputs["collectri"].sha256,
                "row_count": inputs["collectri"].row_count,
            },
            "OmniPath": {
                "manifest": str(OMNIPATH_MANIFEST),
                "data": str(inputs["omnipath"].data_path),
                "sha256": inputs["omnipath"].sha256,
                "row_count": inputs["omnipath"].row_count,
            },
        },
        "new_external_download": False,
    }
    json_write(output_dir / "inputs/input_lock.json", parent_refs)
    json_write(
        output_dir / "TOOL_VERSIONS.json",
        {
            "schema": "ve.t3.s1b-tool-versions.v1",
            "atom": ATOM,
            "reuse": "S1A v7 CellOracle/scTenifold outputs; no method rerun",
            "external_loader": "virtual_embryo_tools.directed_knowledge.load_audited_snapshot",
            "prior_committee": "virtual_embryo_tools.perturb_prior_committee.combine_prior_votes",
            "deployment_manifest": parent_refs["local_deployment"],
            "implementation": parent_refs["implementation"],
        },
    )
    (output_dir / "config_resolved.yaml").write_text(
        f"""atom: {ATOM}
parent_atom: T3-S1A-STATE-JOIN-20260901-v7
seed: 20260830
reuse_exact_parent_state_and_method_outputs: true
allow_external_downloads: false
external_scope: GLOBAL_CONTEXTUAL
external_activity_eligible: false
external_independence_class: SUPPORTING_KNOWLEDGE
require_state_activity: true
candidate_generation: false
server_submission: false
blocks_submission: false
""",
        encoding="utf-8",
    )
    (output_dir / "METHOD_DISCLOSURE.md").write_text(
        """# T3-S1B 方法披露

本 atom 只消费已锁定的 S1A v7 状态 gate、方法输出和本地全量小鼠 CollecTRI/OmniPath 快照。
外部 edge/path 没有状态特异 activity 注释，因此只写入 `GLOBAL_CONTEXTUAL` / `SUPPORTING_KNOWLEDGE` 通道，
不改变 `activity_gate_pass`、CellOracle applicability、signed biological claim 或独立 family 数。
冲突审计保留 raw sign；派生 canonical sign 在冲突时归零并标记 `CONFLICT`，不解释为 inactive。
LOFO 从 family-native biological rows 删除 family 后重新做 conflict/claim 评估；external 与 unsigned rank 不计作 signed biological family。
本 atom 不下载新数据、不重跑 CellOracle/scTenifold、不生成 H5AD、不调用 scorer、不提交服务器。
""",
        encoding="utf-8",
    )

    from virtual_embryo_tools.perturb_prior_committee import combine_prior_votes

    route_outputs: dict[str, Any] = {}
    route_stability: dict[str, Any] = {}
    for route_id in ROUTES:
        route_model = [row for row in model_rows if row.get("route_id") == route_id]
        condition, lane = _route_condition(route_id)
        vote_path = output_dir / f"intermediates/votes_{_route_slug(route_id)}.tsv"
        write_tsv(vote_path, route_model, ["route_id", *REQUIRED_VOTE_FIELDS])
        prior_path = output_dir / f"intermediates/prior_{_route_slug(route_id)}.json"
        evidence_path = output_dir / f"intermediates/evidence_{_route_slug(route_id)}.tsv"
        records = combine_prior_votes(
            vote_tables=[vote_path],
            state_gate_path=output_dir / "intermediates/state_gate.tsv",
            lane=lane,
            output_json=prior_path,
            evidence_tsv=evidence_path,
            config={
                "min_independent_families": 2 if "L1" in lane else 1,
                "max_nonzero_fraction": 0.10 if "L1" in lane else 0.25,
                "panel_size": 500,
                "dosage_fractions": {"Gata4": 0.0, "Gata6": 0.5, "Ctnnb1": 0.0},
                "require_state_activity": True,
                "directness_required_targets": [],
                "signaling_path_required_targets": [],
            },
        )
        selected = sum(record.sign != 0 for record in records)
        stability = leave_one_family_out(route_model, inputs["state_rows"])
        route_stability[route_id] = stability
        route_outputs[route_id] = {
            "prior": str(prior_path.relative_to(output_dir)),
            "evidence": str(evidence_path.relative_to(output_dir)),
            "votes": str(vote_path.relative_to(output_dir)),
            "record_count": len(records),
            "selected_records": selected,
        }

    route_reports = [
        _route_state_vector(
            route_id,
            model_rows,
            contextual,
            inputs["state_rows"],
            route_stability[route_id],
            route_outputs[route_id]["selected_records"],
        )
        for route_id in ROUTES
    ]
    json_write(output_dir / "metrics/stability_s1b.json", {"schema": "ve.t3.s1b-stability.v1", "routes": route_stability})
    json_write(
        output_dir / "metrics/state_join_audit.json",
        {**mapping_audit, "route_outputs": route_outputs},
    )
    completion = {
        "schema": "ve.t3.s1b-completion.v1",
        "atom": ATOM,
        "parent_atom": PARENT_ATOM,
        "implementation": parent_refs["implementation"],
        "status": "HOLD",
        "outcome": "HOLD_AS_COMPONENT",
        "candidate_generation": False,
        "server_submission": False,
        "blocks_submission": False,
        "biological_activity_status": "NOT_VALIDATED",
        "external_context_status": "AUDITED_GLOBAL_CONTEXTUAL",
        "route_count": len(route_reports),
        "external_raw_rows": len(raw_external),
        "external_state_joined_rows": len(contextual),
        "new_external_download": False,
        "core_computation": "NOT_RUN_BY_DESIGN_REUSED_LOCKED_S1A_OUTPUTS",
        "route_outputs": route_outputs,
    }
    json_write(output_dir / "COMPLETION_REPORT.json", completion)
    (output_dir / "COMPLETION_REPORT.md").write_text(
        f"""# {ATOM}

- 状态：`HOLD` / `HOLD_AS_COMPONENT`
- 父版本：`{PARENT_ATOM}`
- 外部证据：{len(raw_external)} 条 raw，{len(contextual)} 条状态上下文投影；仅 `GLOBAL_CONTEXTUAL`。
- 生物 activity：`NOT_VALIDATED`；未由外部证据提升。
- LOFO：从 family-native 行重算；external/unsigned 不计为独立 signed biological family。
- 候选生成：`false`；服务器提交：`false`。
""",
        encoding="utf-8",
    )
    (output_dir / "RESULT.md").write_text(
        f"""# {ATOM}

结论：`HOLD_AS_COMPONENT`。

S1B 已完成 full-snapshot identity check、状态映射/碰撞审计、外部证据 contextual 化、冲突归零审计和四路 claim-state gate。
当前不能进入正式候选生成：activity 未验证，且没有可识别的独立 signed biological family 稳定性。

外部 edge/path 只作为 supporting knowledge；没有改变 activity、sign、applicability 或候选 gate。

本结果未生成 H5AD，未运行 scorer，未提交服务器。实现脚本 SHA256：`{implementation_sha256}`。
""",
        encoding="utf-8",
    )
    (output_dir / "run.log").write_text(
        "S1B audit-only run\nnew_external_download=false\ncelloracle_rerun=false\nsctenifold_rerun=false\ncandidate_generation=false\nserver_submission=false\n",
        encoding="utf-8",
    )
    stable_path = _write_stable_manifest(output_dir, implementation_sha256)
    stable_hash = sha256_file(stable_path)
    gate_report = {
        "schema": "ve.t3.s1b-route-gate.v1",
        "task_id": ATOM,
        "status": "HOLD",
        "outcome": "HOLD_AS_COMPONENT",
        "blocks_submission": False,
        "candidate_generation": False,
        "server_submission": False,
        "biological_activity_status": "NOT_VALIDATED",
        "artifact_manifest_path": str(stable_path.relative_to(output_dir)),
        "artifact_manifest_sha256": stable_hash,
        "parent_atom": PARENT_ATOM,
        "implementation": parent_refs["implementation"],
        "routes": route_reports,
        "state_mapping_audit": mapping_audit,
        "external_row_identity": comparison,
        "evidence_paths": [
            "inputs/input_lock.json",
            "intermediates/raw_external_evidence.tsv",
            "intermediates/state_joined_evidence.tsv",
            "intermediates/conflict_audit.tsv",
            "intermediates/source_votes.tsv",
            "metrics/stability_s1b.json",
            "metrics/state_join_audit.json",
        ],
    }
    json_write(output_dir / "metrics/gate_report.v2.json", gate_report)
    return {
        "atom": ATOM,
        "output_dir": str(output_dir),
        "status": "HOLD",
        "outcome": "HOLD_AS_COMPONENT",
        "stable_manifest_sha256": stable_hash,
        "route_count": len(route_reports),
        "candidate_generation": False,
        "server_submission": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--parent-dir", type=Path, default=PARENT_DEFAULT)
    args = parser.parse_args()
    try:
        result = run_s1b(args.output_dir, args.parent_dir)
    except Exception as exc:  # pragma: no cover - CLI failure receipt
        _write_blocked(args.output_dir, exc)
        print(json.dumps({"status": "BLOCKED_INPUT_IDENTITY", "reason": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
