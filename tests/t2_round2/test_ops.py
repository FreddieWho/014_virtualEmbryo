"""Unit tests for scripts/t2_round2/ops.py pure operators.

Run: env LD_LIBRARY_PATH=/opt/anaconda3/lib python -m pytest -q --import-mode=importlib tests/t2_round2/test_ops.py
"""

from __future__ import annotations

import numpy as np
import pytest

from scripts.t2_round2 import ops


def test_rank_normalized_ties_and_order():
    v = np.array([3.0, 1.0, 1.0, 2.0])
    r = ops.rank_normalized(v)
    assert r[1] == r[2]  # ties share average rank
    assert r[1] < r[3] < r[0]
    assert 0.0 < r.min() and r.max() < 1.0


def test_empirical_quantile_endpoints_and_monotone():
    v = np.array([0.0, 0.0, 1.0, 2.0, 5.0])
    u = np.linspace(0.01, 0.99, 50)
    q = ops.empirical_quantile(v, u)
    assert np.all(np.diff(q) >= 0)  # monotone non-decreasing
    assert q[0] >= v.min() and q[-1] <= v.max()
    assert ops.empirical_quantile(v, np.array([1e-9]))[0] == v.min()
    assert ops.empirical_quantile(v, np.array([1 - 1e-9]))[0] == v.max()


def test_quantile_bridge_rank_preserving_and_nonnegative():
    rng = np.random.default_rng(0)
    left = rng.gamma(2.0, 1.0, size=200)
    right = rng.gamma(3.0, 1.0, size=250)
    parent = np.concatenate([rng.gamma(2.5, 1.0, size=180), [0.0, 0.0, 1.0, 1.0]])
    out = ops.quantile_bridge_map(parent, left, right, 0.5)
    assert out.shape == parent.shape
    assert (out >= 0).all()
    # ties preserved
    assert out[180] == out[181]
    assert out[182] == out[183]
    # rank order preserved (non-decreasing map): sorting parent sorts output the same way
    order = np.argsort(parent, kind="mergesort")
    assert np.all(np.diff(out[order]) >= 0)


def test_quantile_bridge_endpoints():
    left = np.arange(1.0, 101.0)
    right = left + 50.0
    parent = left[::3]
    out0 = ops.quantile_bridge_map(parent, left, right, 0.0)
    out1 = ops.quantile_bridge_map(parent, left, right, 1.0)
    # lam=0 equals left quantile map; lam=1 equals right's; right map > left map pointwise
    assert np.all(out1 >= out0)
    with pytest.raises(ValueError):
        ops.quantile_bridge_map(parent, left, right, 1.5)


def test_linfit_eval_recovers_line():
    t = np.array([6.75, 7.25, 8.0])
    y = 2.0 * t + 1.0
    assert ops.linfit_eval(t, y, 7.5) == pytest.approx(2.0 * 7.5 + 1.0, abs=1e-12)


def test_lagrange3_endpoints_and_midpoint_of_linear():
    t = np.array([8.25, 8.75, 9.5])
    w = ops.lagrange3_weights(t, 8.5)
    assert w.sum() == pytest.approx(1.0, abs=1e-12)
    assert w[0] == pytest.approx(0.4, abs=1e-9)
    assert w[1] == pytest.approx(2.0 / 3.0, abs=1e-9)
    assert w[2] == pytest.approx(-1.0 / 15.0, abs=1e-9)
    # endpoints reproduce values
    y = np.array([3.0, 5.0, 11.0])
    for i, ti in enumerate(t):
        assert ops.lagrange3_eval(t, y, ti) == pytest.approx(y[i], abs=1e-9)
    # linear data: quadratic collapses to the line, midpoint = mean of bracket means
    lin = 2.0 * t - 4.0
    assert ops.lagrange3_eval(t, lin, 8.5) == pytest.approx(2.0 * 8.5 - 4.0, abs=1e-9)


def test_share_series_predict_nonnegative_and_deterministic():
    t = np.array([8.25, 8.75, 9.5])
    s = np.array([0.10, 0.12, 0.15])
    p1 = ops.share_series_predict(t, s, 10.5)
    p2 = ops.share_series_predict(t, s, 10.5)
    assert p1 == p2 and p1 >= 0.0
    # zero share at one stage is handled
    s0 = np.array([0.0, 0.05, 0.10])
    assert ops.share_series_predict(t, s0, 10.5) >= 0.0


def test_shrink_weights_bounds_and_edges():
    shift = np.array([0.0, 1.0, -2.0, 5.0])
    se = np.array([1.0, 1.0, 1.0, 0.0])
    w = ops.shrink_weights(shift, se, C=2.0)
    assert w.shape == shift.shape
    assert ((w >= 0) & (w <= 1)).all()
    assert w[0] == 0.0  # zero shift
    assert w[3] == 0.0  # se==0 -> w=0 (frozen conservative rule)
    assert w[2] > w[1]  # larger |t| keeps more
    w0 = ops.shrink_weights(shift, np.ones(4), C=0.0)
    assert w0[1] == 1.0 and w0[0] == 0.0


def test_se_two_means():
    se = ops.se_two_means(np.array([4.0]), 4, np.array([4.0]), 4)
    assert se[0] == pytest.approx(np.sqrt(2.0))
    with pytest.raises(ValueError):
        ops.se_two_means(np.array([1.0]), 0, np.array([1.0]), 4)


def test_rms_and_scale_refit():
    rng = np.random.default_rng(1)
    coords = rng.normal(size=(500, 3)) * 10 + 5
    rms = ops.rms_radius(coords)
    target = rms * 1.3
    out, factor = ops.scale_to_rms(coords, target)
    assert factor == pytest.approx(1.3)
    assert ops.rms_radius(out) == pytest.approx(target, rel=1e-12)
    # centroid preserved
    assert np.allclose(out.mean(axis=0), coords.mean(axis=0))


def test_l1_target_log_rms_interp():
    t = np.array([7.25, 8.0])
    r = np.array([10.0, 20.0])
    # at 7.5: frac = 0.25/0.75 = 1/3
    want = np.log(10.0) + (1.0 / 3.0) * (np.log(20.0) - np.log(10.0))
    got = ops.l1_target_log_rms(t, r, 7.5)
    assert got == pytest.approx(want, abs=1e-12)
    with pytest.raises(ValueError):
        ops.l1_target_log_rms(t, r, 9.0)  # extrapolation not allowed on interp lane


def test_cosine_lineage_map_legality_and_determinism():
    cand = {"a": np.array([1.0, 0.0]), "b": np.array([0.0, 1.0])}
    orphans = {"x": np.array([0.9, 0.1]), "y": np.array([0.1, 0.9])}
    m1 = ops.cosine_lineage_map(list(orphans), cand, orphans)
    m2 = ops.cosine_lineage_map(list(orphans), cand, orphans)
    assert m1 == m2
    assert m1["x"] == "a" and m1["y"] == "b"
    assert all(v in cand for v in m1.values())


def test_library_scale_rank_and_nonnegative():
    X = np.array([[1.0, 1.0, 2.0], [0.0, 0.0, 0.0], [3.0, 0.0, 3.0]])
    lib = X.sum(axis=1)
    tgt = np.array([8.0, 0.0, 12.0])
    out = ops.apply_library_scale(X, lib, tgt)
    assert (out >= 0).all()
    assert out[0].sum() == pytest.approx(8.0)
    assert out[2].sum() == pytest.approx(12.0)
    assert (out[1] == 0).all()  # zero-library row untouched
    # within-row proportions preserved for scaled rows
    assert out[0, 0] == out[0, 1]


def test_compmix_cap_and_normalization():
    times = np.array([8.25, 8.75, 9.5])
    # type 0 explodes, type 1 vanishes, type 2 flat
    S = np.array([
        [0.01, 0.05, 0.20],
        [0.20, 0.05, 0.01],
        [0.10, 0.10, 0.10],
    ])
    ref = S[:, -1]
    out = ops.compmix_predict_shares(times, S, 10.5, ref, max_fold=2.0)
    assert out.sum() == pytest.approx(1.0, abs=1e-12)
    assert (out >= 0).all()
    # fold cap vs ref respected up to renormalization: capped pre-renorm values
    # type0 cannot exceed ref*2 / (sum of capped mins) -- check monotone cap effect:
    uncapped = np.array([ops.share_series_predict(times, S[i], 10.5) for i in range(3)])
    uncapped /= uncapped.sum()
    assert out[0] <= uncapped[0] + 1e-9  # cap must not increase the exploding type


def test_mass_counts_and_selection_replica_properties():
    ptypes = np.array(["b", "a", "a", "b", "c", "c", "c", "a"])
    pstates = sorted(set(ptypes.tolist()))
    pP = {s: float((ptypes == s).sum()) / len(ptypes) for s in pstates}
    pL = {"a": 0.5, "b": 0.3, "c": 0.2}
    pR = {"a": 0.4, "b": 0.6}
    shared = {"a", "b"}
    from scripts.t2_round2.common import mass_counts_bridge, select_rows, dedup_names
    counts, raw = mass_counts_bridge(pstates, pP, pL, pR, shared, 0.5, len(ptypes))
    assert sum(counts.values()) == len(ptypes)
    assert set(counts) == set(pstates)
    sel1 = select_rows(ptypes, counts, seed=42)
    sel2 = select_rows(ptypes, counts, seed=42)
    assert np.array_equal(sel1, sel2)  # deterministic
    assert len(sel1) == len(ptypes)
    # every selected row is a real parent row of the counted type
    for i in sel1:
        assert counts[ptypes[i]] >= 1
    names = dedup_names([ptypes[i] for i in sel1])
    assert len(set(names)) == len(names)
