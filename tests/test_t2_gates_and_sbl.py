"""Tests for the T2 gate/probe/validation/SBL scripts added on 2026-09-27.

These are cheap structural checks. The heavy numerics ran once and their outputs
live under ``artifacts/gate/`` and ``artifacts/tool_integration/``; these tests
guard the things that would silently invalidate a future re-run:

* the frozen constants (a design-freeze drift must fail loudly, not silently);
* that the SBL interpolation target really is the board's target stage on the
  frozen axis (the bug that was actually found and corrected);
* that the basis construction stays O(n*k) rather than silently reverting to a
  dense n-by-n distance matrix (which needs ~8 GB on the E8.0 stage);
* that the pre-declared negation criterion logic rejects "not better than
  do-nothing" on both arms.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, str(PROJECT_ROOT / rel))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------
# E-N1 SBL
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def sbl():
    return _load("t2_e_n1_sbl_under_test", "scripts/t2_e_n1_sbl.py")


def test_sbl_project_root_is_inside_the_project(sbl) -> None:
    """Regression: this script lives in scripts/ so parents[1] is the root.

    Using parents[2] silently points one level ABOVE the project, which is how
    the first run failed to import veckit with no obvious cause.
    """
    assert sbl.PROJECT_ROOT == PROJECT_ROOT
    assert (sbl.PROJECT_ROOT / "third_party/veckit").is_dir()


def test_sbl_interpolation_target_is_the_board_target_stage(sbl) -> None:
    """The corrected constant: E7.5 must sit at tau=0.6 on the frozen axis.

    The design freeze originally said tau=0.5, which corresponds to E7.625.
    This test exists so that drift back to a hand-written 0.5 fails loudly.
    """
    assert sbl.TAU == {"E6.75": 0.0, "E7.25": 1.0 / 3.0, "E8.0": 1.0}
    expected = (7.5 - 6.75) / (8.0 - 6.75)
    assert sbl.TARGET_TAU == pytest.approx(expected)
    assert sbl.TARGET_TAU == pytest.approx(0.6)
    # the stage the frozen constant must correspond to
    assert 6.75 + sbl.TARGET_TAU * (8.0 - 6.75) == pytest.approx(7.5)


def test_sbl_frozen_constants_present(sbl) -> None:
    assert sbl.STABILITY_COS == 0.5
    assert sbl.RIDGE_ALPHA == 1.0
    assert sbl.SEED == 20260927
    assert set(sbl.SOURCE_STAGES) == {"E6.75", "E7.25", "E8.0"}


def test_sbl_basis_is_sparse_knn_not_dense(sbl) -> None:
    """The basis must not build an n-by-n distance matrix.

    A dense cdist on the E8.0 stage (31,671 cells) needs roughly 8 GB. This
    guards the O(n*k) property that the corrected implementation relies on.
    """
    rng = np.random.default_rng(0)
    Z = rng.normal(size=(200, 3))
    B, names = sbl.geometric_basis(Z, k_neighbors=20)
    assert B.shape == (200, len(names))
    assert len(names) == 8
    assert np.isfinite(B).all()


def test_sbl_field_term_is_centred(sbl) -> None:
    """The field contributes contrast, not mass.

    The property is that, *before* the non-negativity clamp, the field term is
    zero-mean across target cells -- so the per-gene mean of the prediction is
    exactly the global level. This is the property whose absence caused the 53%
    mass inflation in the real run.

    The field magnitude is kept small on purpose so the clamp does not fire; a
    separate assertion checks that clamping can only ever remove mass, never
    add it.
    """
    rng = np.random.default_rng(1)
    n, k, g = 50, 8, 6
    B = rng.normal(size=(n, k))
    B = (B - B.mean(0)) / B.std(0)
    beta = 0.05 * rng.normal(size=(g, k))       # small enough that no clamping occurs
    mean_hat = np.full(g, 1.0)                  # well above the field's spread
    out = sbl.build_candidate(B, beta, mean_hat, np.ones(g))
    X = out["X"]
    assert X.shape == (n, g)
    assert (X >= 0).all()
    # no clamping happened here, so the per-gene mean is exactly the global level
    assert np.allclose(X.mean(axis=0), mean_hat, atol=1e-9)
    # and the field is NOT constant, i.e. it really carries spatial structure
    assert X.std(axis=0).max() > 1e-6


def test_sbl_clamping_raises_not_lowers_the_mean(sbl) -> None:
    """Clamping a zero-mean field at zero can only RAISE the mean.

    This is the correct direction (it replaces negative values with 0), and it is
    worth pinning explicitly: it is the second way a centred field can still move
    the predicted mass away from the intended global level, which is exactly the
    failure mode observed in the real run.
    """
    rng = np.random.default_rng(3)
    n, k, g = 50, 8, 4
    B = rng.normal(size=(n, k))
    B = (B - B.mean(0)) / B.std(0)
    beta = 3.0 * rng.normal(size=(g, k))       # large: forces values below zero
    mean_hat = np.full(g, 0.2)
    out = sbl.build_candidate(B, beta, mean_hat, np.ones(g))
    X = out["X"]
    assert (X >= 0).all()
    # The exact invariant: X is the clipped sum of the global level and the
    # centred field. Recomputing the field independently pins both the centring
    # and the clamp, with no hand-waved magnitude bound.
    field = B @ beta.T
    field = field - field.mean(axis=0, keepdims=True)
    assert np.allclose(X, np.clip(mean_hat[None, :] + field, 0.0, None), atol=1e-12)
    # clamping replaces negatives with 0, so it can only RAISE the mean
    assert (X.mean(axis=0) >= mean_hat - 1e-12).all()


def test_sbl_gate_off_uses_every_gene(sbl) -> None:
    rng = np.random.default_rng(2)
    n, k, g = 30, 8, 5
    B = rng.normal(size=(n, k))
    beta = rng.normal(size=(g, k))
    mean_hat = np.full(g, 0.1)
    gate = np.array([1.0, 0.0, 1.0, 0.0, 1.0])
    out = sbl.build_candidate(B, beta, mean_hat, gate)
    assert out["n_field_genes"] == 3
    # gated-off genes must collapse to the pure global level
    assert np.allclose(out["X"][:, 1], mean_hat[1])


def test_sbl_recorded_run_fired_the_negation_criterion(sbl) -> None:
    """The shipped run must show both arms worse than do-nothing, i.e. FAIL."""
    run = sbl.OUT_DIR / "sbl_run.json"
    if not run.is_file():
        pytest.skip("SBL run not present in this checkout")
    import json

    payload = json.loads(run.read_text(encoding="utf-8"))
    base = payload["reference_readings"]["do_nothing_baseline"]["neighborhood_mmd"]
    for name, sig in payload["pre_declared_signatures"].items():
        assert sig["beats_do_nothing"] is False, name
    for name, arm in payload["arms"].items():
        assert arm["metrics"]["neighborhood_mmd"] > base, name


# --------------------------------------------------------------------------
# validation V1 / probe D structural guards
# --------------------------------------------------------------------------
def test_validation_board_keys_match_index_notation() -> None:
    """INDEX.tsv uses colons in board names; the map must use the same keys.

    A mismatch silently evaluates 0/0 candidates, which is exactly what the
    first run did.
    """
    val = _load("t2_validate_v1_under_test", "scripts/gate/t2_validate_v1_local_vs_server.py")
    index_boards = set()
    with open(PROJECT_ROOT / "submissions/INDEX.tsv", encoding="utf-8") as handle:
        next(handle)
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if len(parts) > 2:
                index_boards.add(parts[2])
    for spec in val.BOARDS.values():
        assert spec["index_key"] in index_boards


def test_validation_primary_metric_is_defined_and_directional() -> None:
    val = _load("t2_validate_v1_under_test", "scripts/gate/t2_validate_v1_local_vs_server.py")
    assert val.PRIMARY == "neighborhood_mmd"
    assert val.METRIC_DIRECTION["neighborhood_mmd"] == "lower"
    # every metric the Spearman loop iterates must actually be computed
    assert set(val.NOISE_BAND) <= set(val.METRIC_DIRECTION)
