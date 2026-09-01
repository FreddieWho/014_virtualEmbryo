from pathlib import Path

from virtual_embryo_tools.types import SignedPriorRecord


def test_signed_prior_validation() -> None:
    record = SignedPriorRecord(
        target_gene="Gata4",
        condition_id="example",
        stage="E8.75",
        state="mesoderm",
        response_gene="GeneA",
        sign=-1,
        rank_score=0.9,
        confidence=0.8,
        lineage_gate=0.7,
        source_families=("WT_GRN", "CURATED_EDGE"),
    )
    record.validate()


def test_conflict_must_be_zero() -> None:
    record = SignedPriorRecord(
        target_gene="Gata4",
        condition_id="example",
        stage="E8.75",
        state="mesoderm",
        response_gene="GeneA",
        sign=1,
        rank_score=0.9,
        confidence=0.8,
        lineage_gate=0.7,
        conflict_flag=True,
    )
    try:
        record.validate()
    except ValueError:
        return
    raise AssertionError("conflicting strict prior must not carry a non-zero sign")
