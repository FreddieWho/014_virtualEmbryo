from __future__ import annotations

from pathlib import Path

from virtual_embryo_tools.directed_knowledge import (
    AuditedSnapshot,
    DirectedEdge,
    build_directed_paths,
    build_tf_edge_evidence,
    load_audited_snapshot,
)


def _edge(
    source: str,
    target: str,
    *,
    stimulation: bool = False,
    inhibition: bool = False,
    consensus_direction: bool = True,
    consensus_stimulation: bool = False,
    consensus_inhibition: bool = False,
) -> DirectedEdge:
    return DirectedEdge(
        source=source,
        target=target,
        source_gene=source,
        target_gene=target,
        is_directed=True,
        is_stimulation=stimulation,
        is_inhibition=inhibition,
        consensus_direction=consensus_direction,
        consensus_stimulation=consensus_stimulation,
        consensus_inhibition=consensus_inhibition,
    )


def _snapshot(*edges: DirectedEdge) -> AuditedSnapshot:
    return AuditedSnapshot(
        manifest_path=Path("manifest.json"),
        data_path=Path("edges.tsv"),
        source_name="toy",
        sha256="toy",
        row_count=len(edges),
        panel_path=Path("panel.txt"),
        panel_genes=frozenset({"Gata4", "A", "B"}),
        edges=tuple(edges),
    )


def test_tf_edge_sign_is_flipped_to_ko_minus_wt_and_conflicts_fail_closed() -> None:
    snapshot = _snapshot(
        _edge("Gata4", "A", stimulation=True, consensus_stimulation=True),
        _edge("Gata4", "B", inhibition=True, consensus_inhibition=True),
        _edge(
            "Gata4",
            "A",
            stimulation=True,
            inhibition=True,
            consensus_direction=False,
        ),
    )

    rows = build_tf_edge_evidence(snapshot, target_gene="Gata4")
    by_gene = {(row["response_gene"], row["provenance"]): row for row in rows}
    signs = sorted(row["ko_minus_wt_sign"] for row in rows)
    assert signs == [-1, 0, 1]
    assert sum(bool(row["conflict_flag"]) for row in rows) == 1
    assert all(row["target_gene"] == "Gata4" for row in by_gene.values())
    assert all(row["confidence"] is None for row in rows)
    assert {row["confidence_status"] for row in rows} == {
        "UNCALIBRATED_EXTERNAL_EVIDENCE",
        "UNRESOLVED_DIRECTION",
    }


def test_directed_paths_are_bounded_and_flip_path_sign() -> None:
    snapshot = _snapshot(
        _edge("Ctnnb1", "A", stimulation=True, consensus_stimulation=True),
        _edge("A", "B", inhibition=True, consensus_inhibition=True),
    )

    paths = build_directed_paths(snapshot, source_gene="Ctnnb1", max_hops=2)
    assert [(row["response_gene"], row["hops"]) for row in paths] == [
        ("A", 1),
        ("B", 2),
    ]
    assert paths[0]["ko_minus_wt_sign"] == -1
    assert paths[1]["ko_minus_wt_sign"] == 1


def test_locked_snapshots_are_consumed_after_content_audit() -> None:
    root = Path(__file__).resolve().parents[4]
    base = root / "infra/external_data/sanitized/T3/B2-T3-A1"
    collectri = load_audited_snapshot(
        base / "COLLECTRI/snapshot_manifest.json",
        repo_root=root,
        expected_source_name="CollecTRI",
        expected_dataset="collectri",
        expected_taxon_id=10090,
    )
    omnipath = load_audited_snapshot(
        base / "OMNIPATH/snapshot_manifest.json",
        repo_root=root,
        expected_source_name="OmniPath",
        expected_dataset="omnipath",
        expected_taxon_id=10090,
    )

    assert len(build_tf_edge_evidence(collectri, target_gene="Gata4")) == 21
    assert len(build_tf_edge_evidence(collectri, target_gene="Gata6")) == 18
    paths = build_directed_paths(omnipath, source_gene="Ctnnb1", max_hops=2)
    assert [row["response_gene"] for row in paths] == ["Pitx2"]
    assert paths[0]["ko_minus_wt_sign"] == -1
