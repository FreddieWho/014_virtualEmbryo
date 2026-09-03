from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from scripts import t2_s3_shape_field as m


ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# analytic time coefficients
# ---------------------------------------------------------------------------


def test_board_coefficients_are_analytic():
    embryo = m.BOARD_SPECS["T2_embryo_val_interp"]
    assert m._board_coefficient(embryo) == pytest.approx(1.0 / 3.0)
    heart = m.BOARD_SPECS["T2_heart_val_interp"]
    assert m._board_coefficient(heart) == pytest.approx(0.5)
    extrap = m.BOARD_SPECS["T2_heart_val_extrap"]
    # raw 4/3 shrunk by the pre-declared rho=0.25 -> 1/3; never the interp slope
    assert m._board_coefficient(extrap) == pytest.approx(1.0 / 3.0)
    assert extrap.regime == "extrapolation"


def test_holdout_coefficients_are_analytic():
    expected = {
        "H1_embryo_regime_leave_E7.25_out": 0.4,
        "H2_heart_regime_leave_E8.25_out": 1.0 / 3.0,
        "H3_heart_regime_leave_E8.75_out": 0.4,
        "H4_extrap_leave_E9.5_out": 0.375,
    }
    for spec in m.HOLDOUT_SPECS:
        if spec.regime == "interpolation":
            value = m.interpolation_coefficient(
                target_stage=spec.truth_stage,
                base_stage=spec.base_stage,
                left_stage=spec.left_stage,
                right_stage=spec.right_stage,
            )
        else:
            value = m.extrapolation_coefficient(
                target_stage=spec.truth_stage,
                base_stage=spec.base_stage,
                left_stage=spec.left_stage,
                right_stage=spec.right_stage,
            )
        assert value == pytest.approx(expected[spec.name])


def test_coefficient_validation_fails_closed():
    with pytest.raises(ValueError):
        m.interpolation_coefficient(
            target_stage=9.0, base_stage=7.25, left_stage=7.25, right_stage=8.0
        )
    with pytest.raises(ValueError):
        m.extrapolation_coefficient(
            target_stage=9.0, base_stage=7.25, left_stage=7.25, right_stage=8.0
        )
    with pytest.raises(ValueError):
        m.extrapolation_coefficient(
            target_stage=10.5, base_stage=9.5, left_stage=8.75, right_stage=9.5, rho=1.5
        )


# ---------------------------------------------------------------------------
# canonical frame, proper flips, Gaussian motion model
# ---------------------------------------------------------------------------


def test_canonicalize_roundtrip():
    rng = np.random.default_rng(0)
    coords = rng.normal(size=(200, 3)) @ np.diag([3.0, 1.0, 0.5]) + np.array([7.0, -2.0, 1.0])
    z, center, rms, axes = m.canonicalize(coords)
    assert rms == pytest.approx(m.rms_radius(coords))
    restored = center + rms * (z @ axes.T)
    assert np.abs(restored - coords).max() < 1e-10
    assert np.abs(z.mean(axis=0)).max() < 1e-10
    assert m.rms_radius(z) == pytest.approx(1.0)


def test_best_proper_flip_recovers_mirror():
    rng = np.random.default_rng(1)
    reference = rng.normal(size=(400, 3)) @ np.diag([2.0, 1.0, 0.4])
    moving = reference * np.array([-1.0, 1.0, -1.0])  # det = +1 flip
    flip, scores = m.best_proper_flip(moving, reference)
    assert list(flip.astype(int)) == [-1, 1, -1]
    assert len(scores) == 4


def test_gaussian_field_eval_matches_motion_model():
    rng = np.random.default_rng(2)
    anchors = rng.normal(size=(50, 3))
    weights = rng.normal(size=(50, 3)) * 0.1
    points = rng.normal(size=(17, 3))
    beta = 1.0
    diff = points[:, None, :] - anchors[None, :, :]
    gram = np.exp(-np.sum(diff * diff, axis=2) / (2 * beta**2))
    expected = gram @ weights
    actual = m.gaussian_field_eval(points, anchors, weights, beta, chunk=8)
    assert np.abs(actual - expected).max() < 1e-12
    zero = m.gaussian_field_eval(points, anchors, np.zeros_like(weights), beta)
    assert np.abs(zero).max() == 0.0


def test_combine_fields_symmetric_and_endpoint_rules():
    rng = np.random.default_rng(3)
    points = rng.normal(size=(11, 3))
    anchors = rng.normal(size=(23, 3))
    fwd = {"anchors": anchors, "W": rng.normal(size=(23, 3)), "beta": 1.0}
    bwd = {"anchors": anchors + 0.05, "W": rng.normal(size=(23, 3)), "beta": 1.0}
    lam = 0.4
    u_f = m.gaussian_field_eval(points, fwd["anchors"], fwd["W"], 1.0)
    u_b = m.gaussian_field_eval(points, bwd["anchors"], bwd["W"], 1.0)
    combined = m.combine_fields(
        points, fwd=fwd, bwd=bwd, regime="interpolation", coefficient=lam
    )
    assert np.abs(combined - lam * 0.5 * (u_f - u_b)).max() < 1e-12
    endpoint = m.combine_fields(
        points, fwd=fwd, bwd=None, regime="extrapolation", coefficient=0.375
    )
    assert np.abs(endpoint - 0.375 * u_f).max() < 1e-12
    with pytest.raises(ValueError):
        m.combine_fields(points, fwd=fwd, bwd=None, regime="interpolation", coefficient=0.4)


# ---------------------------------------------------------------------------
# RMS re-lock, kNN topology, protected invariants
# ---------------------------------------------------------------------------


def test_deform_recenter_relock_restores_rms_and_center():
    rng = np.random.default_rng(4)
    coords = rng.normal(size=(300, 3)) * 50 + np.array([3.0, -1.0, 2.0])
    locked = m.rms_radius(coords)
    center = coords.mean(axis=0)
    displacement = rng.normal(size=coords.shape) * 3.0
    out, meta = m.deform_recenter_relock(coords, displacement, locked_rms=locked)
    assert m.rms_radius(out) == pytest.approx(locked, rel=m.RMS_RTOL, abs=m.RMS_ATOL)
    assert np.abs(out.mean(axis=0) - center).max() < 1e-8
    assert meta["relock_scale"] > 0
    with pytest.raises(ValueError):
        m.deform_recenter_relock(coords, displacement, locked_rms=-1.0)


def test_knn_overlap_and_topology_verdict():
    rng = np.random.default_rng(5)
    before = rng.normal(size=(120, 3))
    identical = m.knn_overlap(before, before.copy())
    assert identical["mean_overlap"] == pytest.approx(1.0)
    shuffled = before + rng.normal(size=before.shape) * 0.01
    moved = m.knn_overlap(before, shuffled)
    assert 0.0 < moved["mean_overlap"] <= 1.0
    assert m.topology_verdict(0.95, 0.90) == "PASS"
    assert m.topology_verdict(0.85, 0.90) == "DISRUPTIVE"
    assert m.topology_verdict(0.79, 0.90) == "CATASTROPHIC"


def test_expression_and_order_digests_detect_any_change(tmp_path):
    import anndata as ad

    rng = np.random.default_rng(6)
    x = rng.random((40, 12), dtype=np.float32)
    coords = rng.normal(size=(40, 3)).astype(np.float32)
    adata = ad.AnnData(X=x.copy())
    adata.obs_names = [f"cell{i}" for i in range(40)]
    adata.var_names = [f"g{i}" for i in range(12)]
    adata.obsm["spatial_3D"] = coords.copy()
    path = tmp_path / "toy.h5ad"
    adata.write_h5ad(path)
    loaded = ad.read_h5ad(path)
    assert m._matrix_digest(loaded.X) == m._matrix_digest(x)
    assert m._names_digest(loaded.var_names) == m._names_digest([f"g{i}" for i in range(12)])
    moved = loaded.copy()
    moved.obsm["spatial_3D"] = coords + 0.5  # geometry may change...
    assert m._matrix_digest(moved.X) == m._matrix_digest(x)  # ...expression must not
    tampered = x.copy()
    tampered[0, 0] += 1.0
    assert m._matrix_digest(tampered) != m._matrix_digest(x)
    reordered = [f"g{i}" for i in range(12)][::-1]
    assert m._names_digest(reordered) != m._names_digest([f"g{i}" for i in range(12)])


# ---------------------------------------------------------------------------
# pycpd worker: smoke + determinism (runs in the isolated tool venv)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not (ROOT / ".venvs" / "ve-t2-geometry" / "bin" / "python").is_file(),
    reason="ve-t2-geometry venv not installed",
)
def test_pycpd_worker_deterministic(tmp_path):
    rng = np.random.default_rng(7)
    left = rng.normal(size=(120, 3)) @ np.diag([2.0, 1.0, 0.5])
    # smooth non-rigid warp: not absorbable by the rigid polish
    right = left + 0.3 * np.sin(left[:, [1, 2, 0]]) + np.array([0.2, -0.1, 0.05])
    pair_dir = tmp_path / "intermediates" / "fields" / "E6.75__E8.0"
    pair_dir.mkdir(parents=True)
    np.savez(pair_dir / "landmarks.npz", left_lm=left, right_lm=right)
    env = {**os.environ, "OPENBLAS_NUM_THREADS": "4", "OMP_NUM_THREADS": "4"}
    outputs = []
    for _ in range(2):
        proc = subprocess.run(
            [
                str(ROOT / ".venvs" / "ve-t2-geometry" / "bin" / "python"),
                str(ROOT / "scripts" / "t2_s3_shape_field.py"),
                "fit-field",
                "--out-dir", str(tmp_path),
                "--pair", "E6.75__E8.0",
                "--direction", "fwd",
                "--backend", "pycpd",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            env=env,
            timeout=600,
        )
        assert proc.returncode == 0, proc.stderr[-2000:]
        bundle = np.load(pair_dir / "field_pycpd_fwd.npz")
        outputs.append(bundle["predicted_lm"].copy())
    assert np.array_equal(outputs[0], outputs[1])
    # the field must actually move the landmarks toward the target shape
    disp = np.load(pair_dir / "field_pycpd_fwd.npz")["displacement"]
    assert np.linalg.norm(disp, axis=1).mean() > 0.01


# ---------------------------------------------------------------------------
# stable manifest self-verify
# ---------------------------------------------------------------------------


def test_manifest_self_verify_and_tamper_detection(tmp_path):
    (tmp_path / "metrics").mkdir(parents=True)
    (tmp_path / "intermediates").mkdir()
    (tmp_path / "metrics" / "a.json").write_text('{"x": 1}\n', encoding="utf-8")
    (tmp_path / "intermediates" / "b.npy").write_bytes(b"payload")
    manifest = m.write_manifest(tmp_path)
    assert manifest["self_verify"]["ok"]
    verified = m.verify_manifest(tmp_path)
    assert verified["ok"] and verified["n_files"] == 2
    (tmp_path / "intermediates" / "b.npy").write_bytes(b"tampered")
    broken = m.verify_manifest(tmp_path)
    assert not broken["ok"]
    assert broken["mismatches"] == ["intermediates/b.npy"]


def test_registry_parents_match_board_specs():
    """Board specs must stay in lockstep with the P0 parent registry."""
    for spec in m.BOARD_SPECS.values():
        path = ROOT / spec.parent_path
        assert path.is_file(), f"missing parent {path}"
        assert m.sha256_file(path) == spec.parent_sha256, f"parent drift on {spec.slug}"


def test_stage_labels_match_field_pair_keys_and_files():
    assert m.stage_label(8.0) == "E8.0"
    assert m.stage_label(6.75) == "E6.75"
    assert m.stage_label(9.5) == "E9.5"
    for key, (left, right, _directions) in m.FIELD_PAIRS.items():
        assert key == m.pair_key(left, right)
    for stage, relative in m.STAGE_FILES.items():
        assert m.stage_label(stage) in relative, (stage, relative)
