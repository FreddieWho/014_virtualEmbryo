from pathlib import Path

import anndata as ad
import numpy as np
import pytest
from scipy import sparse

from scripts.t1_mass_residual import (
    UNRESOLVED_STATE,
    balanced_donor_indices,
    canonicalize_shared_unresolved,
    fit_expression_centroids,
    forecast_state_mass,
    predict_expression_states,
)


def test_canonicalize_shared_unresolved_is_deterministic():
    labels = np.asarray(["A", "B", "C", "A"], dtype=str)
    result = canonicalize_shared_unresolved(labels, {"A", "C"})
    assert result.tolist() == ["A", UNRESOLVED_STATE, "C", "A"]


def test_forecast_state_mass_uses_observed_growth_and_exact_quota():
    previous = np.asarray(["A"] * 6 + ["B"] * 4, dtype=str)
    base = np.asarray(["A"] * 4 + ["B"] * 6, dtype=str)
    quotas, rows = forecast_state_mass(
        previous,
        base,
        n_cells=20,
        alpha=0.5,
        min_quota=1,
    )
    assert set(quotas) == {"A", "B"}
    assert sum(quotas.values()) == 20
    assert all(row["quota"] == quotas[row["state_id"]] for row in rows)
    assert all(np.isfinite(float(row["growth_clipped"])) for row in rows)


def test_forecast_state_mass_fails_when_previous_or_base_is_empty():
    with pytest.raises(ValueError, match="at least one state"):
        forecast_state_mass(np.asarray([], dtype=str), np.asarray(["A"]), n_cells=1)


def test_balanced_donor_indices_replays_full_vectors_with_bounded_multiplicity():
    banks = {"A": np.asarray([0, 1, 2]), "B": np.asarray([3, 4])}
    donors, details = balanced_donor_indices(
        banks,
        {"A": 8, "B": 1},
        seed=20260827,
    )
    assert len(donors) == 9
    assert set(donors[details["state_slices"]["A"]]).issubset({0, 1, 2})
    assert set(donors[details["state_slices"]["B"]]) == {3}
    counts = np.bincount(donors[details["state_slices"]["A"]], minlength=5)[:3]
    assert counts.max() - counts.min() <= 1


def test_expression_centroid_projection_is_sparse_safe_and_deterministic():
    X = sparse.csr_matrix(
        np.asarray(
            [
                [5.0, 0.0, 0.0],
                [4.0, 0.0, 0.0],
                [0.0, 5.0, 0.0],
                [0.0, 4.0, 0.0],
            ],
            dtype=np.float32,
        )
    )
    labels = np.asarray(["A", "A", "B", "B"], dtype=str)
    states = ["A", "B"]
    centroids = fit_expression_centroids(X, labels, states)
    first = predict_expression_states(X, centroids, states)
    second = predict_expression_states(X, centroids, states)
    assert first.tolist() == ["A", "A", "B", "B"]
    assert np.array_equal(first, second)

