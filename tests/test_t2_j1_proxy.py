from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from scripts import t2_j1_proxy as m


ROOT = Path(__file__).resolve().parents[1]


def _toy_cloud(n=300, g=20, seed=7):
    """Structured toy: expression is a smooth function of position plus noise."""
    rng = np.random.default_rng(seed)
    coords = rng.normal(size=(n, 3))
    W = rng.normal(size=(3, g))
    X = np.tanh(coords @ W) + 0.2 * rng.normal(size=(n, g))
    labels = np.asarray(["A" if c[0] > 0 else "B" for c in coords], dtype=str)
    return np.abs(X), coords, labels


# ---------------------------------------------------------------------------
# official NFS-like neighbour definition consistency
# ---------------------------------------------------------------------------


def test_knn_mirror_matches_official_definition():
    """Our pseudobulk must equal veckit _knn_neighborhood_pb verbatim semantics.

    Reference below is a verbatim copy of third_party/veckit/T2/metrics.py
    ``_knn_neighborhood_pb`` (k nearest spatial neighbours, self-inclusive).
    """
    from sklearn.neighbors import NearestNeighbors

    X, coords, _ = _toy_cloud()
    _, idx = NearestNeighbors(n_neighbors=m.KNN_K).fit(coords).kneighbors(coords)
    official = X[idx].mean(1)
    ours = m.knn_neighbourhood_pseudobulk(X, coords)
    assert np.array_equal(ours, official)
    # self-inclusion is part of the official definition
    graph = m._spatial_knn(coords, k=m.KNN_K)
    assert np.array_equal(graph[:, 0], np.arange(len(coords)))


def test_nfs_like_sign_convention():
    """NFS-like: truth vs truth ~ 0; a broken pairing must score worse."""
    X, coords, _ = _toy_cloud()
    rng = np.random.default_rng(3)
    perm = rng.permutation(len(X))
    perfect = m.nfs_like(X, X, coords)
    broken = m.nfs_like(X[perm], X, coords)
    assert perfect < 0.01  # unbiased estimator, near zero
    assert broken > perfect


def test_neighbourhood_pearson_bounds():
    X, coords, _ = _toy_cloud()
    assert m.neighbourhood_pearson(X, X, coords) == pytest.approx(1.0)
    rng = np.random.default_rng(5)
    shuffled = m.neighbourhood_pearson(X[rng.permutation(len(X))], X, coords)
    assert shuffled < 0.9


# ---------------------------------------------------------------------------
# readout / objective semantics
# ---------------------------------------------------------------------------


def test_barycentric_readout_identity_and_permutation():
    X, _, _ = _toy_cloud(n=40, g=6)
    n = len(X)
    identity = np.eye(n) / n
    assert np.allclose(m.barycentric_expression(identity, X), X)
    rng = np.random.default_rng(9)
    placement = rng.permutation(n)  # placement[j] = row placed at position j
    T = np.zeros((n, n))
    T[placement, np.arange(n)] = 1.0 / n
    assert np.allclose(m.barycentric_expression(T, X), X[placement])
    with pytest.raises(ValueError):
        m.barycentric_expression(-identity, X)


def test_fgw_loss_permutation_matches_dense():
    rng = np.random.default_rng(12)
    n = 25
    M = rng.random((n, n))
    C1 = rng.random((n, n)); C1 = (C1 + C1.T) / 2
    C2 = rng.random((n, n)); C2 = (C2 + C2.T) / 2
    placement = rng.permutation(n)
    T = np.zeros((n, n))
    T[placement, np.arange(n)] = 1.0 / n
    dense = m.fgw_loss(M, C1, C2, T, alpha=0.5)
    fast = m.fgw_loss_permutation(M, C1, C2, placement, alpha=0.5)
    assert dense["linear"] == pytest.approx(fast["linear"], rel=1e-10)
    assert dense["gw"] == pytest.approx(fast["gw"], rel=1e-10)
    assert dense["total"] == pytest.approx(fast["total"], rel=1e-10)
    with pytest.raises(ValueError):
        m.fgw_loss_permutation(M, C1, C2, np.zeros(n, dtype=np.int64), alpha=0.5)


def test_shuffle_within_label_semantics():
    labels = np.asarray(["B", "A", "B", "A", "C", "C"], dtype=str)
    order = m.shuffle_within_label(labels, 123)
    assert sorted(order.tolist()) == list(range(6))
    for label in ("A", "B", "C"):
        group = set(np.flatnonzero(labels == label).tolist())
        assert set(order[list(group)].tolist()) == group
    assert np.array_equal(order, m.shuffle_within_label(labels, 123))
    assert not np.array_equal(order, m.shuffle_within_label(labels, 124))


def test_max_normalise_and_pairwise():
    A = np.asarray([[0.0, 2.0], [2.0, 0.0]])
    normed = m.max_normalise(A)
    assert normed.max() == pytest.approx(1.0)
    with pytest.raises(ValueError):
        m.max_normalise(np.zeros((3, 3)))
    feats = np.asarray([[0.0, 0.0], [3.0, 4.0]])
    D = m.pairwise_euclidean(feats)
    assert D[0, 1] == pytest.approx(5.0)
    assert D[0, 0] == pytest.approx(0.0)


def test_holdout_spec_requires_interior_stage():
    assert m.HOLDOUT_BY_NAME["H1_embryo_leave_E7.25_out"].time_weight == pytest.approx(0.4)
    assert m.HOLDOUT_BY_NAME["H2_heart_leave_E8.75_out"].time_weight == pytest.approx(0.4)
    bad = m.HoldoutSpec("bad", "embryo", 6.75, 6.75, 8.0, m.PANEL_EMBRYO)
    with pytest.raises(ValueError):
        _ = bad.time_weight


def test_scrambled_reference_arm_keeps_structure_breaks_position():
    """Scrambled arm: C1/C2 identical to full, M row-position mapping permuted."""
    X, coords, labels = _toy_cloud(n=80, g=6)

    class _Spec:
        name = "TOY"
        holdout_stage = 7.25

    n = len(X)
    prepared = {
        "spec": _Spec(),
        "seed": 777,
        "X_broken": X,
        "coords": coords,
        "labels": labels,
        "g_hat": X + 0.1,  # stand-in reference
        "label_vocabulary": ["A", "B"],
        "label_ref": np.full((n, 2), 0.5),
    }
    full = m.build_arm_problem(prepared, m.ARM_FULL)
    scrambled = m.build_arm_problem(prepared, m.ARM_SCRAMBLED)
    gw_only = m.build_arm_problem(prepared, m.ARM_GW_ONLY)
    assert np.array_equal(full["C1"], scrambled["C1"])
    assert np.array_equal(full["C2"], scrambled["C2"])
    assert not np.array_equal(full["M"], scrambled["M"])
    # the scrambled M is a column permutation of the full M
    assert np.allclose(
        np.sort(full["M"], axis=1), np.sort(scrambled["M"], axis=1)
    )
    assert np.array_equal(full["M"], gw_only["M"])
    assert np.array_equal(full["C1"], gw_only["C1"])
    assert m.ARM_ALPHA[m.ARM_GW_ONLY] == 1.0
    assert m.ARM_FULL not in m.ARM_ALPHA  # candidate objective keeps alpha=0.5


# ---------------------------------------------------------------------------
# random baseline determinism
# ---------------------------------------------------------------------------


def _toy_prepared(seed=42, n=60, g=8):
    X, coords, labels = _toy_cloud(n=n, g=g, seed=seed)
    rng = np.random.default_rng(seed + 1)
    sigma = rng.permutation(n)

    class _Spec:
        name = "TOY"

    return {
        "spec": _Spec(),
        "seed": 4242,
        "n_cells": n,
        "X_true": X,
        "X_broken": X[sigma],
        "coords": coords,
        "labels": labels,
    }


def test_random_baseline_deterministic_and_varied():
    prepared = _toy_prepared()
    first = m._random_baseline(prepared)
    second = m._random_baseline(prepared)
    assert [d["seed"] for d in first] == [d["seed"] for d in second]
    assert [d["nfs_like"] for d in first] == [d["nfs_like"] for d in second]
    assert len({d["nfs_like"] for d in first}) > 1  # draws genuinely differ
    perms = {tuple(d["permutation"].tolist()) for d in first}
    assert len(perms) == len(first)


# ---------------------------------------------------------------------------
# spec freeze
# ---------------------------------------------------------------------------


def test_objective_spec_freeze_refuses_drift(tmp_path):
    out_dir = tmp_path / "atom"
    result = m.command_spec(out_dir)
    spec_path = out_dir / "intermediates" / "objective_spec.yaml"
    assert result["sha256"] == m.sha256_file(spec_path)
    again = m.command_spec(out_dir)
    assert again["status"] == "already_frozen"
    spec_path.write_text("tampered: true\n", encoding="utf-8")
    with pytest.raises(RuntimeError):
        m.command_spec(out_dir)


# ---------------------------------------------------------------------------
# gate logic on synthetic rows
# ---------------------------------------------------------------------------


def _synthetic_holdout_result(
    name, *, full_nfs, label_nfs, scrambled_nfs, random_nfs, gw_only_nfs=0.07
):
    rows = []
    for method, nfs in (
        (m.ARM_IDENTITY, random_nfs[0]),
        (m.ARM_FULL, full_nfs),
        (m.ARM_LABEL, label_nfs),
        (m.ARM_SHUFFLED, full_nfs),  # exact symmetry control
        (m.ARM_SCRAMBLED, scrambled_nfs),
        (m.ARM_GW_ONLY, gw_only_nfs),
    ):
        rows.append(
            {
                "method": method,
                "n_cells": 100,
                "nfs_like": nfs,
                "nbhd_pearson": 0.5,
                "fgw_objective_total": 0.01 if method == m.ARM_FULL else "",
                "fgw_objective_linear": "",
                "fgw_objective_gw": "",
                "solver_iter": "",
                "effective_sources": "",
                "wall_seconds": "",
            }
        )
    return {
        "holdout": name,
        "tissue": "toy",
        "n_cells": 100,
        "rows": rows,
        "objective_check": {
            "identity": {"total": 0.5},
            "random_couplings": [{"total": 0.4}, {"total": 0.6}],
        },
        "row_order_invariance": {"abs_nfs_diff": 0.0, "pass": True},
        "random_baseline_draws": [
            {"draw": i, "seed": i, "nfs_like": v, "nbhd_pearson": 0.1}
            for i, v in enumerate(random_nfs)
        ],
    }


def test_gate_pass_and_reject_logic():
    rng = np.random.default_rng(0)
    random_nfs = list(0.10 + 0.01 * rng.random(64))
    good = [
        _synthetic_holdout_result(
            "H1", full_nfs=0.05, label_nfs=0.08, scrambled_nfs=0.09, random_nfs=random_nfs
        ),
        _synthetic_holdout_result(
            "H2", full_nfs=0.06, label_nfs=0.09, scrambled_nfs=0.10, random_nfs=random_nfs
        ),
    ]
    gate = m.evaluate_gate(good)
    assert gate["verdict"] == "J1_PROXY_PASS"
    assert all(gate["criteria"].values())

    # sign flip in one holdout: full no longer beats random there
    bad = [
        good[0],
        _synthetic_holdout_result(
            "H2", full_nfs=0.20, label_nfs=0.09, scrambled_nfs=0.10, random_nfs=random_nfs
        ),
    ]
    gate = m.evaluate_gate(bad)
    assert gate["verdict"] == "REJECT"
    assert not gate["criteria"]["beats_random_everywhere"]
    assert not gate["criteria"]["same_direction"]

    # label-only null explains the gain -> REJECT via beyond_labels
    label_explains = [
        _synthetic_holdout_result(
            "H1", full_nfs=0.05, label_nfs=0.04, scrambled_nfs=0.09, random_nfs=random_nfs
        ),
        _synthetic_holdout_result(
            "H2", full_nfs=0.06, label_nfs=0.09, scrambled_nfs=0.10, random_nfs=random_nfs
        ),
    ]
    gate = m.evaluate_gate(label_explains)
    assert gate["verdict"] == "REJECT"
    assert not gate["criteria"]["beyond_labels"]

    # scrambled reference keeps the gain -> improvement is not expression-driven
    artifact = [
        _synthetic_holdout_result(
            "H1", full_nfs=0.05, label_nfs=0.08, scrambled_nfs=0.05, random_nfs=random_nfs
        ),
        _synthetic_holdout_result(
            "H2", full_nfs=0.06, label_nfs=0.09, scrambled_nfs=0.06, random_nfs=random_nfs
        ),
    ]
    gate = m.evaluate_gate(artifact)
    assert gate["verdict"] == "REJECT"
    assert not gate["criteria"]["information_dependence"]

    # invariance control broken -> REJECT
    broken = [dict(good[0]), dict(good[1])]
    broken[0]["row_order_invariance"] = {"abs_nfs_diff": 1e-3, "pass": False}
    gate = m.evaluate_gate(broken)
    assert gate["verdict"] == "REJECT"
    assert not gate["criteria"]["row_order_invariance"]


# ---------------------------------------------------------------------------
# POT FGW worker: determinism + structured recovery (ve-t1-ot subprocess)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not (ROOT / ".venvs" / "ve-t1-ot" / "bin" / "python").is_file(),
    reason="ve-t1-ot venv not installed",
)
def test_pot_fgw_worker_deterministic_and_recovers_structure(tmp_path):
    rng = np.random.default_rng(21)
    n = 150
    coords = rng.normal(size=(n, 3))
    W = rng.normal(size=(3, 8))
    X = np.tanh(coords @ W) + 0.2 * rng.normal(size=(n, 8))
    C1 = m.max_normalise(m.pairwise_euclidean(X))
    C2 = m.max_normalise(m.pairwise_euclidean(coords))
    M = m.max_normalise(((X[:, None] - X[None]) ** 2).sum(-1))
    p = np.full(n, 1.0 / n)
    q = np.full(n, 1.0 / n)
    hold_dir = tmp_path / "intermediates" / "TOY"
    hold_dir.mkdir(parents=True)
    np.savez(hold_dir / "problem_fgw_full.npz", M=M, C1=C1, C2=C2, p=p, q=q)

    env = m._worker_env()
    couplings = []
    for _ in range(2):
        proc = subprocess.run(
            [
                str(ROOT / ".venvs" / "ve-t1-ot" / "bin" / "python"),
                "-m",
                "scripts.t2_j1_proxy",
                "solve",
                "--out-dir",
                str(tmp_path),
                "--holdout",
                "TOY",
                "--arm",
                "fgw_full",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            env=env,
            timeout=900,
        )
        assert proc.returncode == 0, proc.stderr[-2000:]
        couplings.append(np.load(hold_dir / "coupling_fgw_full.npz")["T"].copy())
    assert np.array_equal(couplings[0], couplings[1])

    # the solved coupling must recover position structure far better than random
    T = couplings[0]
    pos_hat = (T @ coords) / T.sum(1, keepdims=True)
    solved_err = float(np.median(np.linalg.norm(pos_hat - coords, axis=1)))
    perm = rng.permutation(n)
    random_err = float(np.median(np.linalg.norm(coords[perm] - coords, axis=1)))
    assert solved_err < 0.7 * random_err
    meta = json.loads((hold_dir / "solve_meta_fgw_full.json").read_text(encoding="utf-8"))
    assert meta["backend"] == "POT" and meta["epsilon"] == m.FGW_EPSILON


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
