from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import yaml

from scripts import hx_dynamics_killtest as hx


# ---------------------------------------------------------------------------
# toy fixtures
# ---------------------------------------------------------------------------


def _toy_vocabulary() -> list[dict[str, str]]:
    return [
        {"fine_state": "A", "lineage": "l1", "n_cells_e85": "100", "n_cells_e95": "80"},
        {"fine_state": "B", "lineage": "l1", "n_cells_e85": "60", "n_cells_e95": "0"},
        {"fine_state": "C", "lineage": "l2", "n_cells_e85": "0", "n_cells_e95": "80"},
        {"fine_state": "D", "lineage": "l2", "n_cells_e85": "0", "n_cells_e95": "40"},
    ]


def _toy_mass_rows() -> list[dict[str, str]]:
    return [
        {"board": "T1:val", "state": "A", "shrunk_probability": "0.9"},
        {"board": "T1:pseudo_holdout", "state": "A", "shrunk_probability": "0.6"},
        {"board": "T1:pseudo_holdout", "state": "C", "shrunk_probability": "0.4"},
    ]


# ---------------------------------------------------------------------------
# arm vectors + metric
# ---------------------------------------------------------------------------


def test_parent_arm_is_observed_e85_composition() -> None:
    p = hx.parent_arm_vector(_toy_vocabulary())
    assert p == {"A": pytest.approx(100 / 160), "B": pytest.approx(60 / 160),
                 "C": 0.0, "D": 0.0}


def test_truth_is_observed_e95_composition() -> None:
    q = hx.truth_vector(_toy_vocabulary())
    assert q == {"A": pytest.approx(80 / 200), "B": 0.0,
                 "C": pytest.approx(80 / 200), "D": pytest.approx(40 / 200)}


def test_moscot_arm_uses_holdout_board_only_and_validates() -> None:
    p = hx.moscot_arm_vector(_toy_mass_rows(), _toy_vocabulary())
    assert sum(p.values()) == pytest.approx(1.0)
    assert p["A"] == pytest.approx(0.6) and p["C"] == pytest.approx(0.4)
    assert p["B"] == 0.0 and p["D"] == 0.0
    with pytest.raises(ValueError, match="outside vocabulary"):
        hx.moscot_arm_vector(
            [{"board": "T1:pseudo_holdout", "state": "ZZZ", "shrunk_probability": "1.0"}],
            _toy_vocabulary(),
        )
    with pytest.raises(ValueError, match="no T1:pseudo_holdout"):
        hx.moscot_arm_vector([{"board": "T1:val", "state": "A", "shrunk_probability": "1.0"}],
                             _toy_vocabulary())


def test_l1_metric_toy() -> None:
    states = ["A", "B", "C"]
    q = {"A": 0.5, "B": 0.25, "C": 0.25}
    assert hx.l1_distance(q, q, states) == pytest.approx(0.0)
    p = {"A": 1.0, "B": 0.0, "C": 0.0}
    assert hx.l1_distance(p, q, states) == pytest.approx(1.0)
    # missing keys are zero mass
    assert hx.l1_distance({"A": 0.5}, q, states) == pytest.approx(0.5)


def test_verdict_strict_rule() -> None:
    assert hx.verdict(0.5, 0.6, 0.7)["verdict"] == "SUPPORTED"
    assert hx.verdict(0.6, 0.6, 0.7)["verdict"] == "REJECT"  # tie is not strict
    assert hx.verdict(0.5, 0.4, 0.7)["verdict"] == "REJECT"
    assert hx.verdict(0.5, 0.6, 0.5)["verdict"] == "REJECT"


# ---------------------------------------------------------------------------
# assignment + weighted aggregation
# ---------------------------------------------------------------------------


def test_assign_to_states_nearest_and_tiebreak() -> None:
    centroids = np.array([[0.0, 0.0], [10.0, 0.0]])
    points = np.array([[0.1, 0.0], [9.9, 0.0], [5.0, 0.0]])
    idx = hx.assign_to_states(points, centroids)
    assert idx.tolist() == [0, 1, 0]  # exact tie -> lowest index
    with pytest.raises(ValueError):
        hx.assign_to_states(np.zeros((2, 3)), centroids)


def test_weighted_state_shares_growth_signal() -> None:
    assignments = np.array([0, 0, 1, 1])
    weights = np.array([1.0, 3.0, 1.0, 1.0])
    shares = hx.weighted_state_shares(assignments, weights, 3)
    assert shares.tolist() == pytest.approx([4 / 6, 2 / 6, 0.0])
    with pytest.raises(ValueError, match="non-negative"):
        hx.weighted_state_shares(assignments, np.array([1.0, -1.0, 1.0, 1.0]), 3)
    with pytest.raises(ValueError, match="zero"):
        hx.weighted_state_shares(assignments, np.zeros(4), 3)


def test_mioflow_arm_end_to_end_toy_aggregation() -> None:
    """Endpoints exactly at resolved centroids -> shares follow growth weights."""
    rng = np.random.default_rng(0)
    centroids = rng.normal(size=(2, 6))
    endpoints = np.vstack([centroids[0], centroids[0], centroids[1]])
    weights = np.array([2.0, 2.0, 1.0])
    idx = hx.assign_to_states(endpoints, centroids)
    shares = hx.weighted_state_shares(idx, weights, 2)
    assert shares.tolist() == pytest.approx([0.8, 0.2])


# ---------------------------------------------------------------------------
# real frozen artifacts (tiny files; structural assertions only)
# ---------------------------------------------------------------------------


def test_real_frozen_arms_support_and_normalisation() -> None:
    pre_vocab = hx.PRE_DIR / "intermediates" / "state_vocabulary.tsv"
    if not pre_vocab.is_file():
        pytest.skip("T1-PRE artifact absent")
    vocab = hx._read_tsv(pre_vocab)
    mass_rows = hx._read_tsv(hx.S2_STATE_MASS)
    states = sorted(row["fine_state"] for row in vocab)
    assert len(states) == 28
    q = hx.truth_vector(vocab)
    p_parent = hx.parent_arm_vector(vocab)
    p_moscot = hx.moscot_arm_vector(mass_rows, vocab)
    assert sum(q.values()) == pytest.approx(1.0, abs=1e-9)
    assert sum(p_parent.values()) == pytest.approx(1.0, abs=1e-9)
    assert sum(p_moscot.values()) == pytest.approx(1.0, abs=1e-9)
    # P1 boundary parity: moscot support = 14 crosswalk-resolved targets
    assert sum(1 for v in p_moscot.values() if v > 0) == 14
    # parent arm support = 18 E8.5 states
    assert sum(1 for v in p_parent.values() if v > 0) == 18
    # control-arm L1 values are deterministic from frozen artifacts
    assert 0.0 < hx.l1_distance(p_moscot, q, states) < 2.0
    assert 0.0 < hx.l1_distance(p_parent, q, states) < 2.0


def test_config_freezes_kill_metric_and_decision_rule() -> None:
    cfg_path = hx.OUTPUT_DEFAULT / "config_resolved.yaml"
    if not cfg_path.is_file():
        pytest.skip("config_resolved.yaml not written yet")
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    assert cfg["kill_metric"]["name"] == "holdout_state_mass_l1"
    assert "28 union fine_state" in cfg["kill_metric"]["definition"]
    assert "严格小于" in cfg["kill_metric"]["decision_rule"]
    assert cfg["budgets"]["mioflow_training_runs"] == 1
    assert cfg["budgets"]["holdout_evaluations"] == 1
    assert cfg["budgets"]["grid_search"] == 0
    assert cfg["scale_caps"]["cells_per_stage_max"] == 3000
    assert cfg["scale_caps"]["n_epochs"] == 100
    assert cfg["candidate_generation"] is False
    assert cfg["allow_server_submission"] is False
    assert cfg["allow_network"] is False


def test_seed_determinism_of_subsample() -> None:
    labels = np.array(["a"] * 50 + ["b"] * 30 + ["c"] * 20)
    shares = {"a": 0.5, "b": 0.3, "c": 0.2}
    seed = hx._derived_seed("hx", "subsample", "e85")
    i1 = hx.select_indices_by_shares(labels, shares, n_cells=40, seed=seed)
    i2 = hx.select_indices_by_shares(labels, shares, n_cells=40, seed=seed)
    assert np.array_equal(i1, i2)


def test_manifest_self_verify_roundtrip(tmp_path: Path) -> None:
    (tmp_path / "metrics").mkdir()
    (tmp_path / "metrics" / "x.json").write_text(json.dumps({"a": 1}), encoding="utf-8")
    manifest = hx.write_manifest(tmp_path)
    assert manifest["self_verify"]["ok"]
    payload = json.loads((tmp_path / "metrics" / "artifact_manifest.stable.json").read_text())
    assert payload["self_verify"]["ok"]
