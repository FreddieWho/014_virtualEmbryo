from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from scripts.t3_s1_prior import sign_convention_report, tf_edge_to_ko_minus_wt
from virtual_embryo_tools.lineage_state_gate import build_lineage_state_gate
from virtual_embryo_tools.perturb_prior_committee import combine_prior_votes
from virtual_embryo_tools.types import SignedPriorRecord


VOTE_FIELDS = [
    "target_gene",
    "condition_id",
    "stage",
    "state",
    "response_gene",
    "sign",
    "rank_score",
    "confidence",
    "evidence_family",
    "directness_score",
    "dosage_fraction",
    "lineage_gate",
    "provenance",
    "conflict_flag",
]


def write_tsv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def vote(
    gene: str,
    family: str,
    sign: int,
    *,
    target: str = "Gata4",
    condition: str = "validation",
    state: str = "mesoderm",
    score: float = 0.9,
    confidence: float | None = 0.8,
    directness: float | None = 0.8,
    dosage_fraction: float = 0.0,
) -> dict[str, object]:
    return {
        "target_gene": target,
        "condition_id": condition,
        "stage": "E8.75_target",
        "state": state,
        "response_gene": gene,
        "sign": sign,
        "rank_score": score,
        "confidence": confidence,
        "evidence_family": family,
        "directness_score": "" if directness is None else directness,
        "dosage_fraction": dosage_fraction,
        "lineage_gate": 0.8,
        "provenance": f"toy:{family}",
        "conflict_flag": False,
    }


def gate(path: Path, *, condition: str = "validation", state: str = "mesoderm") -> None:
    write_tsv(
        path,
        [
            {
                "condition_id": condition,
                "stage": "E8.75_target",
                "state": state,
                "lineage_gate": 0.8,
                "gate_pass": True,
                "provenance": "toy:lineage",
            }
        ],
        ["condition_id", "stage", "state", "lineage_gate", "gate_pass", "provenance"],
    )


def test_strict_committee_enforces_sign_independence_conflict_and_cap(tmp_path: Path) -> None:
    votes = tmp_path / "votes.tsv"
    write_tsv(
        votes,
        [
            vote("A", "WT_INFERRED_GRN", 1, score=0.99),
            vote("A", "WT_CONDITIONAL_NETWORK", 1, score=0.98),
            vote("B", "WT_INFERRED_GRN", 1, score=0.97),
            vote("B", "WT_CONDITIONAL_NETWORK", -1, score=0.96),
            vote("C", "WT_INFERRED_GRN", 1, score=0.95),
            vote("D", "WT_INFERRED_GRN", 1, score=0.94),
            vote("D", "WT_CONDITIONAL_NETWORK", 1, score=0.93),
        ],
        VOTE_FIELDS,
    )
    state_gate = tmp_path / "state_gate.tsv"
    gate(state_gate)
    output = tmp_path / "prior.json"
    evidence = tmp_path / "evidence.tsv"

    records = combine_prior_votes(
        vote_tables=[votes],
        state_gate_path=state_gate,
        lane="L1_STRICT_AGREEMENT",
        output_json=output,
        evidence_tsv=evidence,
        config={
            "min_independent_families": 2,
            "max_nonzero_fraction": 0.25,
            "panel_size": 4,
            "directness_required": True,
            "directness_threshold": 0.0,
        },
    )
    by_gene = {record.response_gene: record for record in records}
    assert by_gene["A"].sign == 1
    assert by_gene["D"].sign == 0  # deterministic cap keeps higher-ranked A only
    assert by_gene["B"].sign == 0
    assert by_gene["B"].conflict_flag is True
    assert by_gene["C"].sign == 0
    assert len(by_gene["A"].source_families) == 2
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["condition_ids"] == ["validation"]
    assert payload["sign_definition"] == "KO_MINUS_MATCHED_WT"


def test_missing_lineage_gate_is_fail_closed(tmp_path: Path) -> None:
    votes = tmp_path / "votes.tsv"
    write_tsv(votes, [vote("A", "WT_INFERRED_GRN", 1)], VOTE_FIELDS)
    missing_gate = tmp_path / "missing.tsv"
    write_tsv(
        missing_gate,
        [],
        ["condition_id", "stage", "state", "lineage_gate", "gate_pass", "provenance"],
    )
    records = combine_prior_votes(
        vote_tables=[votes],
        state_gate_path=missing_gate,
        lane="L2_CONDITION_AWARE",
        output_json=tmp_path / "prior.json",
        evidence_tsv=tmp_path / "evidence.tsv",
        config={"min_independent_families": 1, "max_nonzero_fraction": 0.25},
    )
    assert records[0].sign == 0
    assert records[0].lineage_gate == 0.0


def test_gate_pass_cannot_override_missing_lineage_probability(tmp_path: Path) -> None:
    votes = tmp_path / "votes.tsv"
    write_tsv(votes, [vote("A", "WT_INFERRED_GRN", 1)], VOTE_FIELDS)
    gate_path = tmp_path / "gate.tsv"
    write_tsv(
        gate_path,
        [{
            "condition_id": "validation",
            "stage": "E8.75_target",
            "state": "mesoderm",
            "lineage_gate": "",
            "gate_pass": True,
        }],
        ["condition_id", "stage", "state", "lineage_gate", "gate_pass"],
    )
    with pytest.raises(ValueError, match="gate_pass=true"):
        combine_prior_votes(
            vote_tables=[votes],
            state_gate_path=gate_path,
            lane="L2_CONDITION_AWARE",
            output_json=tmp_path / "prior.json",
            evidence_tsv=tmp_path / "evidence.tsv",
            config={"min_independent_families": 1, "max_nonzero_fraction": 0.25},
        )


def test_dosage_fraction_is_preserved_per_target_channel(tmp_path: Path) -> None:
    votes = tmp_path / "votes.tsv"
    write_tsv(
        votes,
        [vote("A", "WT_INFERRED_GRN", 1, target="Gata6", dosage_fraction=0.5)],
        VOTE_FIELDS,
    )
    gate_path = tmp_path / "gate.tsv"
    gate(gate_path)
    output = tmp_path / "prior.json"
    records = combine_prior_votes(
        vote_tables=[votes],
        state_gate_path=gate_path,
        lane="L2_CONDITION_AWARE",
        output_json=output,
        evidence_tsv=tmp_path / "evidence.tsv",
        config={
            "min_independent_families": 1,
            "max_nonzero_fraction": 0.25,
            "dosage_fractions": {"Gata6": 0.5},
        },
    )
    assert records[0].dosage_fraction == 0.5
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["records"][0]["dosage_fraction"] == 0.5


def test_uncalibrated_confidence_remains_null_in_prior_record(tmp_path: Path) -> None:
    votes = tmp_path / "votes.tsv"
    write_tsv(votes, [vote("A", "CURATED_TF_TARGET", 1, confidence=None)], VOTE_FIELDS)
    gate_path = tmp_path / "gate.tsv"
    gate(gate_path)
    output = tmp_path / "prior.json"
    records = combine_prior_votes(
        vote_tables=[votes],
        state_gate_path=gate_path,
        lane="L2_CONDITION_AWARE",
        output_json=output,
        evidence_tsv=tmp_path / "evidence.tsv",
        config={"min_independent_families": 1, "max_nonzero_fraction": 0.25},
    )
    assert records[0].confidence is None
    assert json.loads(output.read_text(encoding="utf-8"))["records"][0]["confidence"] is None


def test_signed_prior_accepts_missing_calibrated_confidence() -> None:
    record = SignedPriorRecord(
        target_gene="Gata4",
        condition_id="validation",
        stage="E8.75_target",
        state="mesoderm",
        response_gene="A",
        sign=0,
        rank_score=0.5,
        confidence=None,
        lineage_gate=0.5,
    )
    record.validate()


def test_toy_sign_transform_executes_activating_and_repressing_edges() -> None:
    report = sign_convention_report()
    assert report["status"] == "PASS"
    assert [case["observed_ko_minus_wt"] for case in report["cases"]] == [-1, 1]
    with pytest.raises(ValueError):
        tf_edge_to_ko_minus_wt(0)


def test_lineage_gate_writer_does_not_infer_unknown_states(tmp_path: Path) -> None:
    output = tmp_path / "state_gate.tsv"
    build_lineage_state_gate(
        wt_data=None,
        state_labels=["mesoderm", "unknown_state"],
        output_path=output,
        config={"condition_id": "validation", "stage": "E8.75_target"},
    )
    rows = list(csv.DictReader(output.open(encoding="utf-8"), delimiter="\t"))
    assert len(rows) == 2
    assert all(row["gate_pass"] == "False" for row in rows)
    assert all(row["lineage_gate"] == "0.0" for row in rows)
