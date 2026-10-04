"""Unit tests for T2 goal round (pure ops, no data files)."""
import numpy as np

from scripts.t2_round2 import common, ops


def test_share_trend_nonneg_and_sane():
    t = np.array([6.75, 7.25, 8.0])
    for series in ([0.1, 0.2, 0.15], [0.0, 0.05, 0.1], [0.5, 0.4, 0.45]):
        v = ops.share_series_predict(t, np.array(series), 7.5)
        assert np.isfinite(v) and v >= 0.0


def test_counts_conserve_and_deterministic():
    raw = {"a": 0.5, "b": 0.3, "c": 0.2}
    c1, _ = common.counts_from_raw(raw, ["a", "b", "c"], 5000)
    c2, _ = common.counts_from_raw(raw, ["a", "b", "c"], 5000)
    assert sum(c1.values()) == 5000 and c1 == c2
    pt = np.array(["a"] * 100 + ["b"] * 100 + ["c"] * 100)
    s1 = common.select_rows(pt, {"a": 50, "b": 50, "c": 50}, 20261001)
    s2 = common.select_rows(pt, {"a": 50, "b": 50, "c": 50}, 20261001)
    assert (s1 == s2).all() and len(s1) == 150


def test_shrink_c1_bounds_and_monotone():
    shift = np.array([0.0, 0.5, 2.0, 10.0])
    se = np.array([1.0, 1.0, 1.0, 1.0])
    w = ops.shrink_weights(shift, se, C=1.0)
    assert ((w >= 0) & (w <= 1)).all()
    assert (np.diff(w) >= 0).all()  # larger |t| -> less shrinkage
    # C=1 shrinks less than C=2 for the same finite t>0
    w2 = ops.shrink_weights(shift[1:], se[1:], C=2.0)
    assert (w[1:] > w2).all()


def test_shrink_zero_se_gives_zero():
    w = ops.shrink_weights(np.array([1.0]), np.array([0.0]), C=1.0)
    assert w[0] == 0.0


def test_dedup_pool_with_preduped_names():
    from scripts.t2_goal.run import dedup_names_pool
    # incumbent pools already contain __dupK names; output must stay unique
    # with minimal renaming (first occurrence keeps bare name).
    out = dedup_names_pool(["A", "A", "A__dup1", "B"], ["A", "B", "A__dup1"])
    assert out == ["A", "A__dup1", "A__dup1__dup1", "B"]
    assert len(set(out)) == len(out)
