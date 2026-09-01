from __future__ import annotations

import os
import json

import pandas as pd
import pytest
import anndata as ad
import numpy as np

from scripts.t3_s1a_state_join import (
    _assess_route,
    _aggregate_method_status,
    _align_metadata,
    _gate_result,
    _celloracle_target_capabilities,
    _is_transient_runtime_artifact,
    _write_artifact_manifest,
    _run_celloracle_target_isolated,
    _method_vote_rows,
    _selected_gene_stability,
    _build_state_response_support,
    CELLORACLE_TARGET_START_METHOD,
    REQUIRED_VOTE_FIELDS,
    panel_genes,
    _resolve_gene_symbols,
    exact_stage_and_firewall,
)
from virtual_embryo_tools.types import SignedPriorRecord


def _record(*, target: str = "Ctnnb1", family: tuple[str, ...] = ("DIRECTED_SIGNALING",)):
    return SignedPriorRecord(
        target_gene=target,
        condition_id="BETA_CATENIN_HIDDEN_E875",
        stage="E8.75",
        state="mesoderm",
        response_gene="Pitx2",
        sign=-1,
        rank_score=0.8,
        confidence=None,
        lineage_gate=0.8,
        source_families=family,
    )


def test_metadata_first_filter_keeps_only_exact_e875_wt() -> None:
    frame = pd.DataFrame(
        {
            "cell": ["a", "b", "c", "d"],
            "stage": ["E8.75", "E8.5-E8.75", "E8.75", "E8.75"],
            "genotype": ["WT", "WT", "Ctnnb1 KO", "control"],
        }
    )
    mask, report = exact_stage_and_firewall(frame)
    assert mask.tolist() == [True, False, False, True]
    assert report["kept_rows"] == 2
    assert report["forbidden_records_remaining"] == 0


def test_metadata_without_condition_is_blocked() -> None:
    with pytest.raises(ValueError, match="no genotype/condition"):
        exact_stage_and_firewall(pd.DataFrame({"stage": ["E8.75"]}))


def test_metadata_without_condition_can_use_explicit_source_attestation() -> None:
    mask, report = exact_stage_and_firewall(
        pd.DataFrame({"stage": ["E8.75", "E8.5"]}),
        source_wt_attested=True,
        wt_evidence="publication.html:E8.5-E9.5",
    )
    assert mask.tolist() == [True, False]
    assert report["wt_status"] == "PASS_SOURCE_ATTESTED"
    assert report["wt_attestation"]["used"] is True


def test_empty_condition_is_not_silently_treated_as_wt() -> None:
    with pytest.raises(ValueError, match="auditable WT"):
        exact_stage_and_firewall(pd.DataFrame({"stage": ["E8.75"], "condition": [""]}))


def test_metadata_join_accepts_exact_obs_identifier_column() -> None:
    source = ad.AnnData(
        X=np.asarray([[1.0], [2.0]]),
        obs=pd.DataFrame({"cell": ["cell_0", "cell_1"]}, index=["0", "1"]),
    )
    metadata = pd.DataFrame({"cell": ["cell_1", "cell_0"], "stage": ["E8.75", "E8.75"]})
    aligned = _align_metadata(source, metadata)
    assert aligned["stage"].tolist() == ["E8.75", "E8.75"]
    assert aligned["cell"].tolist() == ["cell_0", "cell_1"]


def test_gene_id_mapping_requires_complete_panel_resolution(tmp_path) -> None:
    panel = panel_genes()
    ids = [f"ENSMUSG{index:011d}" for index in range(500)]
    metadata_path = tmp_path / "metadata_genes.csv"
    pd.DataFrame({"ensembl_id": ids, "gene_symbol": panel}).to_csv(metadata_path, index=False)
    resolved, report = _resolve_gene_symbols(ids, metadata_path)
    assert resolved == panel
    assert report["panel_overlap_after"] == 500


def test_method_summary_preserves_partial_failure() -> None:
    assert _aggregate_method_status(
        [{"status": "PASS"}, {"status": "BLOCKED_TOOLCHAIN"}]
    ) == "PARTIAL"
    assert _aggregate_method_status(
        [{"status": "PASS"}, {"status": "NOT_APPLICABLE_BASE_GRN_TARGET_ABSENT"}]
    ) == "PASS"
    assert _gate_result("PARTIAL") == "FAIL"
    assert _gate_result("BLOCKED_NO_PANEL_EVIDENCE") == "BLOCKED"


@pytest.mark.skipif(not hasattr(os, "fork"), reason="target worker uses Linux fork isolation")
def test_celloracle_target_worker_isolated_checkpoint(tmp_path) -> None:
    class FakeAdata:
        def __init__(self) -> None:
            self.var_names = np.asarray(panel_genes(), dtype=object)
            self.obs = pd.DataFrame({"state": ["mesoderm"] * 4})
            self.obs_names = pd.Index(["cell_0", "cell_1", "cell_2", "cell_3"])
            self.layers = {}

    class FakeOracle:
        def __init__(self) -> None:
            self.adata = FakeAdata()

        def simulate_shift(self, **kwargs) -> None:
            assert kwargs["perturb_condition"] == {"Gata4": 0.0}
            self.adata.layers["delta_X"] = np.zeros((4, 500), dtype=float)

    log: list[str] = []
    result = _run_celloracle_target_isolated(
        FakeOracle(), "Gata4", tmp_path, [4, 500], 1, log
    )
    assert result["status"] == "PASS"
    assert result["runtime"]["start_method"] == CELLORACLE_TARGET_START_METHOD
    assert (tmp_path / "celloracle/Gata4_checkpoint.json").is_file()
    assert (tmp_path / "celloracle/Gata4_votes.tsv").is_file()
    assert (tmp_path / "celloracle/Gata4_state_sampling.tsv").is_file()


def test_artifact_manifest_excludes_transient_runtime_files(tmp_path) -> None:
    stable = tmp_path / "stable.txt"
    stable.write_text("stable\n", encoding="utf-8")
    for name in ("cache.db-shm", "cache.db-wal", ".output.tmp-123", "partial.part"):
        (tmp_path / name).write_text("transient\n", encoding="utf-8")
    assert _is_transient_runtime_artifact(tmp_path / "cache.db-shm") is True
    manifest = _write_artifact_manifest(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    paths = {entry["path"] for entry in payload["files"]}
    assert "stable.txt" in paths
    assert not any("cache.db-" in path or ".tmp-" in path or path.endswith(".part") for path in paths)


def test_celloracle_capability_requires_tf_source_column() -> None:
    base_grn = pd.DataFrame(
        {"gene_short_name": ["Gata4", "Gata6"], "Gata4": [1, 0]}
    )
    capabilities = _celloracle_target_capabilities(base_grn)
    assert capabilities["Gata4"]["perturbable"] is True
    assert capabilities["Gata6"]["gene_row_present"] is True
    assert capabilities["Gata6"]["tf_source_column_present"] is False
    assert capabilities["Gata6"]["perturbable"] is False
    assert capabilities["Ctnnb1"]["gene_row_present"] is False


def test_method_votes_project_external_states_through_state_join(tmp_path) -> None:
    path = tmp_path / "votes.tsv"
    pd.DataFrame([
        {
            "target_gene": "Gata4", "condition_id": "", "stage": "",
            "state": "external_a", "response_gene": "Acta2", "sign": 1,
            "rank_score": 0.9, "confidence": "", "evidence_family": "WT_CELLORACLE_REAL",
            "dosage_fraction": 0.0, "directness_score": "", "lineage_gate": "",
            "provenance": "fixture", "conflict_flag": False,
        },
        {
            "target_gene": "Gata4", "condition_id": "", "stage": "",
            "state": "unmatched_external", "response_gene": "B", "sign": 1,
            "rank_score": 0.8, "confidence": "", "evidence_family": "WT_CELLORACLE_REAL",
            "dosage_fraction": 0.0, "directness_score": "", "lineage_gate": "",
            "provenance": "fixture", "conflict_flag": False,
        },
    ], columns=REQUIRED_VOTE_FIELDS).to_csv(path, sep="\t", index=False)
    rows = _method_vote_rows(
        path,
        "Gata4",
        "GATA4_GATA6_VALIDATION_E875",
        ["parent_a"],
        state_mapping={"parent_a": {"matched_external_state": "external_a"}},
    )
    assert [(row["state"], row["response_gene"]) for row in rows] == [("parent_a", "Acta2")]


def test_selected_gene_stability_excludes_non_applicable_celloracle_target() -> None:
    result = _selected_gene_stability(
        ("Gata4", "Gata6"),
        {
            "CellOracle": {
                "targets": {
                    "Gata4": {"status": "PASS"},
                    "Gata6": {"status": "NOT_APPLICABLE_BASE_GRN_REGULATOR_ABSENT"},
                }
            }
        },
        {"Gata4": {"status": "PASS", "agreement_fraction": 0.99}},
    )
    assert result["status"] == "PASS"
    assert result["applicable_targets"] == ["Gata4"]
    assert result["not_applicable_targets"] == ["Gata6"]
    assert result["per_target"]["Gata6"]["status"].startswith("NOT_APPLICABLE")


def test_state_response_support_is_modelled_not_biological_activity(tmp_path) -> None:
    response = tmp_path / "Gata4_state_response.tsv"
    coverage = tmp_path / "Gata4_state_coverage.tsv"
    sample_response = tmp_path / "Gata4_sample_state_response.tsv"
    sampling = tmp_path / "Gata4_state_sampling.tsv"
    pd.DataFrame([{
        "target_gene": "Gata4", "state": "external_a", "response_gene": "Acta2",
        "n_cells": 4, "n_samples": 2, "sample_ids": "s1;s2", "effect": 0.2, "sign": 1,
    }]).to_csv(response, sep="\t", index=False)
    pd.DataFrame([{
        "target_gene": "Gata4", "state": "external_a", "n_cells": 4, "n_samples": 2,
        "sample_ids": "s1;s2", "cell_id_count": 4, "cell_id_unique": True, "cell_id_sha256": "a" * 64,
    }]).to_csv(coverage, sep="\t", index=False)
    pd.DataFrame([{"target_gene": "Gata4", "state": "external_a", "sample": "s1", "n_cells": 4}]).to_csv(
        sample_response, sep="\t", index=False
    )
    pd.DataFrame([{
        "target_gene": "Gata4", "state": "external_a", "response_gene": "Acta2",
        "n_first": 2, "n_second": 2, "effect_first": 0.1, "effect_second": 0.2,
        "sign_first": 1, "sign_second": 1, "sign_agree": True,
    }]).to_csv(sampling, sep="\t", index=False)
    result = _build_state_response_support(
        {
            "CellOracle": {
                "targets": {
                    "Gata4": {
                        "status": "PASS",
                        "state_response_output": str(response),
                        "state_coverage_output": str(coverage),
                        "sample_state_response_output": str(sample_response),
                        "state_sampling_output": str(sampling),
                    },
                    "Gata6": {"status": "NOT_APPLICABLE_BASE_GRN_REGULATOR_ABSENT"},
                    "Ctnnb1": {"status": "NOT_APPLICABLE_BASE_GRN_REGULATOR_ABSENT"},
                }
            }
        },
        tmp_path,
        {"state_mappings": {"parent_a": {"matched_external_state": "external_a"}}},
    )
    assert result["status"] == "PASS_STATE_RESPONSE_SUPPORT"
    assert result["biological_activity_status"] == "NOT_VALIDATED"
    assert result["targets"]["Gata4"]["claim"] == "MODELLED_STATE_RESPONSE_ONLY"


def test_beta_routes_require_state_and_stability_evidence() -> None:
    method = {
        "CellOracle": {"status": "NOT_APPLICABLE"},
        "scTenifoldNet/scTenifoldKnk": {
            "targets": {"Ctnnb1": {"status": "PASS_UNSIGNED_RANK_ONLY"}},
        },
    }
    stability = {}
    l1 = _assess_route(
        "BETA_CATENIN_HIDDEN_E875::L1_STRICT_AGREEMENT",
        [_record()], method, stability,
    )
    l2 = _assess_route(
        "BETA_CATENIN_HIDDEN_E875::L2_CONDITION_AWARE",
        [_record()], method, stability,
    )
    assert l1["status"] == "BLOCKED"
    assert "Ctnnb1:INSUFFICIENT_INDEPENDENT_SIGN_FAMILIES" in l1["blockers"]
    assert l2["status"] == "BLOCKED"
    assert l2["candidate_generation"] is False
    assert "STATE_ACTIVITY_NOT_VALIDATED" in l2["blockers"]
    assert "SELECTED_GENE_STABILITY_NOT_IDENTIFIABLE" in l2["blockers"]
