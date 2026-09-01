from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "docs/batch3/interfaces"))

from scripts.t3_s1b_state_join import (  # noqa: E402
    EXTERNAL_FAMILIES,
    _canonicalize_conflicts,
    _evaluate_biological_claim,
    build_state_mapping_audit,
    expand_contextual_evidence,
    leave_one_family_out,
)


def _state_rows() -> list[dict[str, str]]:
    return [
        {
            "condition_id": "GATA4_GATA6_VALIDATION_E875",
            "stage": "E8.75",
            "state": "parent_a",
            "matched_external_state": "external_a",
            "match_similarity": "0.9",
            "external_n": "10",
            "activity_gate_pass": "False",
            "gate_pass": "True",
            "lineage_gate": "0.8",
            "activity_evidence_status": "NOT_VALIDATED",
        },
        {
            "condition_id": "BETA_CATENIN_HIDDEN_E875",
            "stage": "E8.75",
            "state": "parent_a",
            "matched_external_state": "external_a",
            "match_similarity": "0.9",
            "external_n": "10",
            "activity_gate_pass": "False",
            "gate_pass": "True",
            "lineage_gate": "0.8",
            "activity_evidence_status": "NOT_VALIDATED",
        },
        {
            "condition_id": "GATA4_GATA6_VALIDATION_E875",
            "stage": "E8.75",
            "state": "parent_b",
            "matched_external_state": "external_a",
            "match_similarity": "0.7",
            "external_n": "10",
            "activity_gate_pass": "False",
            "gate_pass": "False",
            "lineage_gate": "0.4",
            "activity_evidence_status": "NOT_VALIDATED",
        },
    ]


def _vote(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "route_id": "GATA4_GATA6_VALIDATION_E875::L1_STRICT_AGREEMENT",
        "target_gene": "Gata4",
        "condition_id": "GATA4_GATA6_VALIDATION_E875",
        "stage": "E8.75",
        "state": "parent_a",
        "response_gene": "Acta2",
        "sign": 1,
        "rank_score": 0.8,
        "confidence": "",
        "evidence_family": "WT_CELLORACLE_REAL",
        "dosage_fraction": 0.0,
        "directness_score": "",
        "lineage_gate": 0.8,
        "provenance": "fixture",
        "conflict_flag": False,
        "evidence_channel": "BIOLOGICAL_MODEL",
        "independence_class": "BIOLOGICAL_MODEL",
        "activity_eligible": True,
    }
    row.update(overrides)
    return row


def test_state_mapping_records_collision_and_unmatched_projection() -> None:
    mapping, audit = build_state_mapping_audit(_state_rows())
    assert mapping["parent_a"]["matched_external_state"] == "external_a"
    assert audit["ambiguous_external_states"] == {"external_a": ["parent_a", "parent_b"]}
    assert audit["parent_state_count"] == 2
    assert audit["unmatched_external_states_excluded"] is True
    assert audit["project_external_state"]["unmatched"] == []


def test_external_evidence_is_global_context_and_cannot_be_activity_eligible() -> None:
    raw = [
        {
            "source_type": "edge",
            "source_name": "CollecTRI",
            "target_gene": "Gata4",
            "response_gene": "Acta2",
            "ko_minus_wt_sign": -1,
            "regulation_sign": 1,
            "hops": "",
            "path_nodes": "",
            "directness_score": 1.0,
            "conflict_flag": False,
            "provenance": "fixture-edge",
        }
    ]
    rows = expand_contextual_evidence(raw, build_state_mapping_audit(_state_rows())[0])
    assert rows
    assert {row["state_scope"] for row in rows} == {"GLOBAL_CONTEXTUAL"}
    assert {row["independence_class"] for row in rows} == {"SUPPORTING_KNOWLEDGE"}
    assert {row["activity_eligible"] for row in rows} == {False}
    assert {row["evidence_channel"] for row in rows} == {"EXTERNAL_CONTEXT"}
    assert EXTERNAL_FAMILIES == {"CURATED_TF_TARGET", "DIRECTED_SIGNALING"}


def test_conflict_zeroing_preserves_raw_sign_and_distinguishes_status() -> None:
    rows = [
        _vote(sign=1, evidence_family="WT_CELLORACLE_REAL", provenance="a"),
        _vote(sign=-1, evidence_family="OTHER_MODEL", provenance="b"),
        _vote(sign=0, evidence_family="WT_NETWORK_RANK_ONLY", provenance="unsigned"),
    ]
    canonical, audit = _canonicalize_conflicts(rows)
    signed = [row for row in canonical if row["provenance"] in {"a", "b"}]
    assert {row["raw_sign"] for row in signed} == {1, -1}
    assert {row["sign"] for row in signed} == {0}
    assert {row["conflict_status"] for row in signed} == {"CONFLICT"}
    assert any(row["status"] == "CONFLICT" for row in audit)
    unsigned = next(row for row in canonical if row["provenance"] == "unsigned")
    assert unsigned["conflict_status"] == "UNSIGNED"
    assert unsigned["sign"] == 0


def test_leave_one_family_out_does_not_count_external_context_as_independent() -> None:
    rows = [
        _vote(sign=1),
        _vote(
            sign=-1,
            evidence_family="CURATED_TF_TARGET",
            evidence_channel="EXTERNAL_CONTEXT",
            independence_class="SUPPORTING_KNOWLEDGE",
            activity_eligible=False,
        ),
        _vote(
            sign=1,
            evidence_family="DIRECTED_SIGNALING",
            evidence_channel="EXTERNAL_CONTEXT",
            independence_class="SUPPORTING_KNOWLEDGE",
            activity_eligible=False,
        ),
    ]
    state_rows = _state_rows()[:2]
    result = leave_one_family_out(rows, state_rows)
    assert result["leakage_guard"] == "FAMILY_NATIVE_RECOMPUTATION"
    assert result["per_target"]["Gata4"]["independent_biological_families"] == [
        "WT_CELLORACLE_REAL"
    ]
    assert result["per_target"]["Gata4"]["status"] == "NOT_IDENTIFIABLE"
    assert "CURATED_TF_TARGET" not in result["independent_families"]


def test_external_removal_cannot_change_biological_claim() -> None:
    model = [_vote(sign=1)]
    with_external = model + [
        _vote(
            sign=-1,
            evidence_family="CURATED_TF_TARGET",
            evidence_channel="EXTERNAL_CONTEXT",
            independence_class="SUPPORTING_KNOWLEDGE",
            activity_eligible=False,
        )
    ]
    state_rows = _state_rows()[:2]
    assert _evaluate_biological_claim(model, state_rows) == _evaluate_biological_claim(
        with_external, state_rows
    )
