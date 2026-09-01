from __future__ import annotations

import pandas as pd
import pytest

from scripts.t3_s1c_regulator_prior import (
    augment_tfdict,
    base_tfdict,
    build_adapter_edges,
    tfdict_digest,
)


class Edge:
    def __init__(self, source_gene: str, target_gene: str, sign: int | None = 1):
        self.source_gene = source_gene
        self.target_gene = target_gene
        self.source = source_gene
        self.target = target_gene
        self.regulation_sign = sign


class Snapshot:
    def __init__(self, source_name: str, edges: tuple[Edge, ...], panel_genes: frozenset[str]):
        self.source_name = source_name
        self.data_path = f"{source_name}.tsv"
        self.edges = edges
        self.panel_genes = panel_genes


def test_base_tfdict_matches_positive_celloracle_matrix_rule():
    frame = pd.DataFrame(
        {
            "peak_id": ["p1", "p2", "p3"],
            "gene_short_name": ["Gata4", "Gata4", "Pitx2"],
            "Tbx5": [1, 0, 0],
            "Isl1": [0, 2, 0],
            "Gata4": [1, 0, 1],
        }
    )
    assert base_tfdict(frame) == {"Gata4": ["Tbx5", "Isl1", "Gata4"], "Pitx2": ["Gata4"]}


def test_adapter_selects_gata6_direct_edges_and_only_strict_ctnnb1_path():
    panel = frozenset({"Gata4", "Gata6", "Pitx2", "Nkx2-5"})
    collectri = Snapshot(
        "CollecTRI",
        (Edge("Gata6", "Gata4"), Edge("Gata6", "Gata4"), Edge("Gata6", "Nkx2-5")),
        panel,
    )
    omnipath = Snapshot(
        "OmniPath",
        (Edge("Ctnnb1", "Pitx2"), Edge("Ctnnb1", "Nkx2-5"), Edge("Nkx2-5", "Gata4")),
        panel,
    )
    rows = build_adapter_edges(collectri, omnipath, list(panel))
    selected = {(r["regulator_gene"], r["response_gene"]) for r in rows if r["loader_eligible"] and r["pair_added"]}
    assert selected == {("Gata6", "Gata4"), ("Gata6", "Nkx2-5"), ("Ctnnb1", "Pitx2")}
    assert any(r["response_gene"] == "Nkx2-5" and not r["loader_eligible"] for r in rows if r["regulator_gene"] == "Ctnnb1")
    assert all(r["activity_eligible"] is False and r["signed_family_eligible"] is False for r in rows)


def test_augment_preserves_native_relations_and_is_deterministic():
    base = {"Gata4": ["Tbx5"], "Gata6": ["Isl1"], "Ctnnb1": [], "Pitx2": ["Tbx5"], "Nkx2-5": []}
    rows = [
        {"regulator_gene": "Gata6", "response_gene": "Pitx2", "loader_eligible": True, "pair_added": True},
        {"regulator_gene": "Ctnnb1", "response_gene": "Pitx2", "loader_eligible": True, "pair_added": True},
        {"regulator_gene": "Ctnnb1", "response_gene": "Nkx2-5", "loader_eligible": False, "pair_added": False},
    ]
    augmented, stats = augment_tfdict(base, rows)
    assert base["Pitx2"] == ["Tbx5"]
    assert augmented["Pitx2"] == ["Tbx5", "Gata6", "Ctnnb1"]
    assert stats["selected_unique_relation_count"] == 2
    assert tfdict_digest(augmented) == tfdict_digest({"Gata4": ["Tbx5"], "Gata6": ["Isl1"], "Ctnnb1": [], "Pitx2": ["Tbx5", "Gata6", "Ctnnb1"], "Nkx2-5": []})


def test_augment_fails_closed_for_missing_response_gene():
    with pytest.raises(ValueError, match="absent from the native CellOracle TFdict"):
        augment_tfdict(
            {"Gata4": []},
            [{"regulator_gene": "Gata6", "response_gene": "Missing", "loader_eligible": True, "pair_added": True}],
        )
