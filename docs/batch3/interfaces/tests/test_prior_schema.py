from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


def _validator() -> Draft202012Validator:
    schema_path = Path(__file__).resolve().parents[2] / "schemas/prior.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def _payload(sign: int, conflict: bool) -> dict[str, object]:
    return {
        "schema_version": "ve.t3.signed-prior.v2",
        "condition_ids": ["validation"],
        "lane": "L1_STRICT_AGREEMENT",
        "sign_definition": "KO_MINUS_MATCHED_WT",
        "records": [{
            "target_gene": "Gata4",
            "condition_id": "validation",
            "stage": "E8.75_target",
            "state": "mesoderm",
            "response_gene": "A",
            "sign": sign,
            "rank_score": 0.8,
            "confidence": 0.8,
            "lineage_gate": 0.8,
            "dosage_fraction": 0.0,
            "source_families": ["toy"],
            "directness_score": 0.8,
            "conflict_flag": conflict,
            "provenance": ["toy"],
        }],
        "metadata": {},
    }


def test_schema_rejects_nonzero_conflict_record() -> None:
    errors = list(_validator().iter_errors(_payload(sign=1, conflict=True)))
    assert errors


def test_schema_accepts_zero_conflict_record() -> None:
    assert not list(_validator().iter_errors(_payload(sign=0, conflict=True)))
