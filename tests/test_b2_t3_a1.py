from __future__ import annotations

import numpy as np

from scripts.b2_t3_a1_signed_prior import apply_program, robust_sd, stratified_indices


def test_stratified_selection_is_deterministic_and_bounded():
    labels = np.array(["a"] * 8 + ["b"] * 5 + ["c"] * 3)
    first = stratified_indices(labels, 9, 20260829)
    second = stratified_indices(labels, 9, 20260829)
    assert np.array_equal(first, second)
    assert len(first) == 9
    assert len(set(first.tolist())) == 9
    assert set(labels[first]) == {"a", "b", "c"}


def test_robust_sd_uses_mad_and_is_finite_for_constant_values():
    assert robust_sd(np.array([1.0, 2.0, 3.0, 4.0, 100.0])) < 3.0
    assert robust_sd(np.ones(5)) == 0.0


def test_lineage_gate_zeroes_target_and_preserves_non_gate_cells():
    # Panel positions are intentionally tiny here; the production caller uses
    # the released 500-gene panel.
    X = np.array([
        [1.5, np.log1p(4.0), 0.4],
        [1.5, np.log1p(4.0), 0.4],
    ], dtype=np.float64)
    states = np.array(["responding", "blocked"])
    gates = {
        "responding": {"p_mesp1_lineage": 0.75, "responds": True},
        "blocked": {"p_mesp1_lineage": 0.25, "responds": False},
    }
    program = {"responding": {"Effector": {"delta": -0.1}}}
    updated, meta = apply_program(
        X,
        states,
        gates,
        {"Gata4": 0, "Gata6": 1, "Effector": 2},
        program,
        lane="test",
        include_gata6_dose=True,
    )
    assert updated[0, 0] == 0.0
    assert np.isclose(updated[0, 1], np.log1p(2.0))
    assert np.isclose(updated[0, 2], 0.4 - 0.075)
    assert np.array_equal(updated[1], X[1].astype(np.float32))
    assert set(meta["changed_genes"]) == {"Effector", "Gata4", "Gata6"}


def test_mab21l2_target_is_zeroed_without_zeroing_gata4():
    X = np.array([[1.2, 0.8, 2.0]], dtype=np.float64)
    updated, meta = apply_program(
        X,
        np.array(["responding"]),
        {"responding": {"p_mesp1_lineage": 1.0, "responds": True}},
        {"Gata4": 0, "Mab21l2": 1, "Effector": 2, "Gata6": 3},
        {"responding": {"Effector": {"delta": 0.1}}},
        lane="kill",
        include_gata6_dose=False,
        perturbation_target="Mab21l2",
    )
    assert np.isclose(updated[0, 0], X[0, 0])
    assert updated[0, 1] == 0.0
    assert updated[0, 2] > X[0, 2]
    assert "Mab21l2" in meta["changed_genes"]
