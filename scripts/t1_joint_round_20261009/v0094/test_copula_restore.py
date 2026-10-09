import numpy as np
import unittest
from copula_restore import restore
from pair_diagnostics import uniform_pairs, pair_moments, compare_pair_moments, changed_pair_support


def fixture():
    rng = np.random.default_rng(8)
    T = rng.lognormal(size=(60, 31)).astype("float32")
    T[rng.random(T.shape) < .6] = 0
    P = T.copy()
    for g in range(P.shape[1]):
        P[:, g] = P[rng.permutation(len(P)), g]
    states = np.repeat(["a", "b", "singleton"], [29, 30, 1])
    return P, T, states


def test_operator_off_exact():
    P, T, s = fixture()
    O, d = restore(P, T, s, blend=0)
    assert np.array_equal(P, O) and d["operator_off_exact"]


def test_exact_state_gene_multisets():
    P, T, s = fixture()
    for shuffle in [False, True]:
        O, d = restore(P, T, s, shuffle_template=shuffle)
        for c in set(s):
            assert np.array_equal(np.sort(O[s == c], axis=0),
                                  np.sort(P[s == c], axis=0))
        assert d["on_transitions"] == d["off_transitions"]
        assert np.isfinite(O).all() and (O >= 0).all()
        assert np.array_equal(O[-1], P[-1])


def test_block_size_and_replay_invariance():
    P, T, s = fixture()
    for shuffle in [False, True]:
        A, da = restore(P, T, s, block_size=1, shuffle_template=shuffle)
        B, db = restore(P, T, s, block_size=15, shuffle_template=shuffle)
        assert np.array_equal(A, B) and da == db


def test_paired_identity_and_constant_template_fallback():
    P, T, s = fixture()
    O, _ = restore(P, P, s)
    assert np.array_equal(P, O)
    O, _ = restore(P, np.zeros_like(P), s)
    assert np.array_equal(P, O)


def test_correlated_template_is_not_module_monotone():
    # Distinct genes may have opposite ranks; a shared module sort cannot pass.
    T = np.array([[0, 3], [1, 2], [2, 1], [3, 0]], dtype="float32")
    P = np.array([[3, 3], [2, 2], [1, 1], [0, 0]], dtype="float32")
    O, _ = restore(P, T, np.array(["a"]*4), blend=1)
    assert np.array_equal(O, T)


def test_invalid_inputs():
    P, T, s = fixture()
    with unittest.TestCase().assertRaises(ValueError): restore(P, T[:-1], s)
    with unittest.TestCase().assertRaises(ValueError): restore(P, T, s, blend=1.1)
    T[0, 0] = np.nan
    with unittest.TestCase().assertRaises(ValueError): restore(P, T, s)


def test_pair_decomposition_and_fixed_marginal_metric_change():
    P, T, s = fixture()
    O, _ = restore(P, T, s)
    pairs = uniform_pairs(P.shape[1], n_pairs=200)
    p, o, t = [pair_moments(a, pairs, chunk_size=7) for a in (P, O, T)]
    d = compare_pair_moments(p, o, t)
    assert d["marginal_term_max_abs_change"] < 1e-12
    assert d["decomposition_max_abs_error"] < 1e-12
    assert abs(d["actual_variogram_change"] -
               d["fixed_marginal_predicted_variogram_change"]) < 1e-12
    assert np.all(p["joint_term"] <= p["loose_joint_upper_bound"]+1e-12)


def test_zero_gene_has_no_joint_leverage():
    X = np.array([[0., 4.], [0., 9.]])
    d = pair_moments(X, np.array([[0, 1]]))
    assert d["joint_term"][0] == 0
    assert d["loose_joint_upper_bound"][0] == 0


def test_exact_half_blend_ties_cross_dtype():
    P = np.array([[0],[0],[7],[0],[0]],dtype="float32")
    T = np.array([[7],[0],[0],[7],[0]],dtype="float32")
    labels = np.array(["a"]*5)
    a,_ = restore(P,T,labels)
    b,_ = restore(P.astype("float64"),T.astype("float64"),labels)
    assert np.array_equal(a,b)
    assert a[2,0] == 7  # exact tie preserves parent-value ordering


def test_actual_pair_support_zero_gene_invariance():
    P,T,s = fixture()
    P[:,0] = 0
    O,_ = restore(P,T,s)
    pairs = np.array([[0,1],[0,2],[1,2],[2,3]])
    d = changed_pair_support(P,O,pairs)
    assert d["sampled_pairs"] == 4
    assert d["pairs_with_a_globally_zero_gene"] == 2
    assert d["zero_gene_pair_max_moment_change"] < 1e-12


if __name__ == "__main__":
    import sys
    suite = unittest.TestSuite(unittest.FunctionTestCase(v) for k, v in
                               sorted(globals().items()) if k.startswith("test_"))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
