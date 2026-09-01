import json
from pathlib import Path

import anndata as ad
import numpy as np
import pytest

from scripts.t3_signed_response import (
    EffectBudget,
    SignedPrior,
    _json_write,
    _manifest,
    _budget_from_signed_effects,
    _prepare_output,
    apply_signed_residual,
    build_signed_prior,
    build_state_gates,
    residual_vector,
    refresh_self_score_manifests,
    select_support,
)


def _budget(values):
    values = np.asarray(values, dtype=float)
    return _budget_from_signed_effects(values, np.arange(len(values)))


def _adata(X, genes, labels=None):
    if labels is None:
        labels = ["A"] * len(X)
    out = ad.AnnData(
        np.asarray(X, dtype=np.float32),
        obs={"celltype": np.asarray(labels, dtype=str)},
        obsm={"spatial_3D": np.arange(len(X) * 3, dtype=np.float32).reshape(-1, 3)},
    )
    out.var_names = list(genes)
    out.layers["counts"] = np.ones(out.shape, dtype=np.float32)
    out.layers["log1p"] = out.X.copy()
    return out


def test_wt_prior_uses_opposite_correlation_sign():
    target = np.arange(12, dtype=float)
    positive = target * 2.0 + 1.0
    negative = target[::-1] * 1.5 + 2.0
    mixed = np.array([0, 4, 1, 5, 2, 6, 3, 7, 8, 9, 10, 11], dtype=float)
    constant = np.ones(12, dtype=float)
    wt = _adata(np.column_stack([target, positive, negative, mixed, constant]), ["Gata4", "up", "down", "mixed", "constant"])

    prior = build_signed_prior(wt, lane_id="L1_CELL_LEVEL_SPEARMAN", target_gene="Gata4")

    assert prior.rho[1] > 0
    assert prior.rho[2] < 0
    assert prior.confidence[4] == 0
    assert (-prior.rho[1]) < 0  # positive WT correlation predicts KO down-regulation
    assert (-prior.rho[2]) > 0  # negative WT correlation predicts KO up-regulation


def test_state_pseudobulk_prior_is_distinct_and_deterministic():
    labels = ["A"] * 4 + ["B"] * 4 + ["C"] * 4
    target = np.array([1] * 4 + [2] * 4 + [3] * 4, dtype=float)
    gene_a = np.array([1] * 4 + [4] * 4 + [9] * 4, dtype=float)
    gene_b = np.array([9] * 4 + [4] * 4 + [1] * 4, dtype=float)
    gene_c = np.arange(12, dtype=float)
    wt = _adata(np.column_stack([target, gene_a, gene_b, gene_c]), ["Gata4", "a", "b", "c"], labels)

    first = build_signed_prior(wt, lane_id="L2_STATE_PSEUDOBULK_SPEARMAN", target_gene="Gata4")
    second = build_signed_prior(wt, lane_id="L2_STATE_PSEUDOBULK_SPEARMAN", target_gene="Gata4")

    assert np.array_equal(first.rho, second.rho)
    assert first.method == "state_pseudobulk_spearman"
    assert first.rho[1] > 0
    assert first.rho[2] < 0


def test_effect_budget_is_invariant_to_training_delta_sign():
    effects = np.array([-0.8, 0.3, 0.5, -1.2, 0.9])
    positive = _budget_from_signed_effects(effects, np.arange(5))
    flipped = _budget_from_signed_effects(-effects, np.arange(5))

    assert positive.n_de == flipped.n_de
    assert np.array_equal(positive.abs_effects, flipped.abs_effects)
    assert positive.median_abs_effect == pytest.approx(flipped.median_abs_effect)
    assert positive.q90_abs_effect == pytest.approx(flipped.q90_abs_effect)


def test_support_is_exactly_training_de_count_minus_target_and_keeps_both_signs():
    prior = SignedPrior(
        lane_id="L1_CELL_LEVEL_SPEARMAN",
        method="cell_level_spearman",
        target_gene="g0",
        rho=np.array([0.0, 0.9, -0.8, 0.7, -0.6, 0.01]),
        confidence=np.array([0.0, 0.9, 0.8, 0.7, 0.6, 0.01]),
        threshold=0.05,
        eligible_indices=np.array([1, 2, 3, 4]),
        support_indices=np.empty(0, dtype=np.int64),
    )
    selected = select_support(prior, _budget([0.2, 0.3, 0.4, 0.5, 0.6]))

    assert len(selected.support_indices) == 4
    assert set(selected.support_indices) == {1, 2, 3, 4}
    assert np.any(-selected.rho[selected.support_indices] > 0)
    assert np.any(-selected.rho[selected.support_indices] < 0)
    assert np.array_equal(selected.support_indices, np.array([1, 2, 3, 4]))


def test_state_gates_are_normalized_to_target_activity():
    wt = _adata(
        [[4, 1], [2, 1], [0, 1], [1, 1]],
        ["Gata4", "g1"],
        ["A", "A", "B", "B"],
    )
    gates, metadata = build_state_gates(wt, target_gene="Gata4")

    assert gates["A"] == pytest.approx(1.0)
    assert gates["B"] == pytest.approx(1.0 / 6.0)
    assert all(0.0 <= value <= 1.0 for value in gates.values())
    assert metadata["state_counts"] == {"A": 2, "B": 2}


def test_apply_preserves_non_response_genes_and_zeroes_target():
    genes = ["Gata4", "up", "down", "untouched"]
    carrier = _adata([[2, 1, 2, 7], [1, 4, 1, 8]], genes, ["A", "B"])
    prior = SignedPrior(
        lane_id="L1_CELL_LEVEL_SPEARMAN",
        method="cell_level_spearman",
        target_gene="Gata4",
        rho=np.array([0.0, -0.5, 0.5, 0.0]),
        confidence=np.array([0.0, 0.5, 0.5, 0.0]),
        threshold=0.1,
        eligible_indices=np.array([1, 2]),
        support_indices=np.array([1, 2]),
    )
    budget = _budget([0.2, 0.3, 0.4])

    prediction, diagnostics = apply_signed_residual(
        carrier, prior=prior, gates={"A": 1.0, "B": 0.5}, budget=budget
    )

    assert np.all(prediction[:, 0] == 0)
    assert np.array_equal(prediction[:, 3], carrier.X[:, 3])
    assert prediction[0, 1] > carrier.X[0, 1]
    assert prediction[0, 2] < carrier.X[0, 2]
    assert diagnostics["support_count"] == 2
    assert diagnostics["target_zeroed"] is True


def test_output_clears_stale_layers_and_keeps_coordinates(tmp_path):
    carrier = _adata([[1, 2], [3, 4]], ["Gata4", "g1"])
    prior = SignedPrior(
        lane_id="L1_CELL_LEVEL_SPEARMAN",
        method="cell_level_spearman",
        target_gene="Gata4",
        rho=np.array([0.0, -0.5]),
        confidence=np.array([0.0, 0.5]),
        threshold=0.1,
        eligible_indices=np.array([1]),
        support_indices=np.array([1]),
    )
    budget = EffectBudget(
        n_de=2,
        abs_effects=np.array([0.2, 0.3]),
        median_abs_effect=0.3,
        q90_abs_effect=0.29,
    )
    prediction, diagnostics = apply_signed_residual(
        carrier, prior=prior, gates={"A": 1.0}, budget=budget
    )
    output = tmp_path / "prediction.h5ad"
    written = _prepare_output(
        carrier,
        prediction,
        prior=prior,
        budget=budget,
        gate_metadata={"states": ["A"], "state_counts": {"A": 2}, "activity": {"A": 1.0}, "gates": {"A": 1.0}},
        diagnostics=diagnostics,
        output_path=output,
        source_wt_path=Path("wt.h5ad"),
        source_ko_path=Path("ko.h5ad"),
        carrier_path=Path("carrier.h5ad"),
    )
    reloaded = ad.read_h5ad(output)

    assert list(written.layers.keys()) == []
    assert list(reloaded.layers.keys()) == []
    assert np.array_equal(reloaded.obsm["spatial_3D"], carrier.obsm["spatial_3D"])


def test_missing_carrier_state_fails_closed():
    carrier = _adata([[1, 2]], ["Gata4", "g1"], ["unseen"])
    prior = SignedPrior(
        lane_id="L1_CELL_LEVEL_SPEARMAN",
        method="cell_level_spearman",
        target_gene="Gata4",
        rho=np.array([0.0, -0.5]),
        confidence=np.array([0.0, 0.5]),
        threshold=0.1,
        eligible_indices=np.array([1]),
        support_indices=np.array([1]),
    )
    with pytest.raises(ValueError, match="absent from gate table"):
        apply_signed_residual(carrier, prior=prior, gates={"A": 1.0}, budget=_budget([0.2, 0.3, 0.4]))


def test_manifest_normalizes_partial_artifact_path(tmp_path):
    output = tmp_path / "artifacts/atomic_batch1/B1-A2.partial/final/L1_CELL_LEVEL_SPEARMAN/T3_gata4/prediction.h5ad"
    candidate = _adata([[1, 2], [3, 4]], ["Gata4", "g1"])
    output.parent.mkdir(parents=True)
    candidate.write_h5ad(output)
    prior = SignedPrior(
        lane_id="L1_CELL_LEVEL_SPEARMAN",
        method="cell_level_spearman",
        target_gene="Gata4",
        rho=np.array([0.0, -0.5]),
        confidence=np.array([0.0, 0.5]),
        threshold=0.1,
        eligible_indices=np.array([1]),
        support_indices=np.array([1]),
    )
    manifest = _manifest(
        lane_id=prior.lane_id,
        candidate_id="B1-A2-L1-T3_gata4",
        output_path=output,
        base_submission="baseline-001/T3_gata4/v0001",
        checks={"all_core_invariants": True},
        prior=prior,
        budget=_budget([0.2, 0.3, 0.4]),
        self_score_path=tmp_path / "missing.json",
        project_root=tmp_path,
    )
    assert ".partial" not in manifest["output_file"]
    assert manifest["output_file"].startswith("artifacts/atomic_batch1/B1-A2/final/")


def test_refresh_self_scores_updates_existing_manifest(tmp_path):
    artifact = tmp_path / "B1-A2"
    manifest_path = artifact / "final/L1_CELL_LEVEL_SPEARMAN/T3_gata4/MANIFEST.json"
    prediction_path = manifest_path.parent / "prediction.h5ad"
    score_path = artifact / "metrics/mab21l2_self_prediction/L1_CELL_LEVEL_SPEARMAN/candidate.json"
    manifest = {
        "lane_id": "L1_CELL_LEVEL_SPEARMAN",
        "candidate_id": "B1-A2-L1-T3_gata4",
        "sha256": "abc",
        "protected_checks": {"all_core_invariants": True},
        "primary_metrics": {"DES": None, "DCS": None, "PSS": None, "status": "score_pending"},
    }
    _json_write(manifest_path, manifest)
    prediction = _adata([[1, 2], [3, 4]], ["Gata4", "g1"])
    prediction.write_h5ad(prediction_path)
    _json_write(score_path, {"metrics": {"de_score": -0.1, "de_direction": -0.2, "severity_slope": -3.0}})
    _json_write(
        artifact / "FINAL_SET_MANIFEST.json",
        {
            "atom_id": "B1-A2",
            "candidates": [{"manifest": "final/L1_CELL_LEVEL_SPEARMAN/T3_gata4/MANIFEST.json"}],
        },
    )
    refresh_self_score_manifests(artifact, project_root=tmp_path)
    refreshed = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert refreshed["primary_metrics"]["DES"] == -0.1
    assert refreshed["primary_metrics"]["DCS"] == -0.2
    assert "DES=-0.1" in (artifact / "RESULT.md").read_text(encoding="utf-8")
