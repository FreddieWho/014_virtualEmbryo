import numpy as np

from scripts.t2_pseudo_holdout import select_indices


def test_stratified_indices_are_fixed_seed_exact_size_and_balanced():
    celltypes = np.asarray(["A"] * 8 + ["B"] * 4 + ["C"] * 2)
    first = select_indices(celltypes, n_cells=10, seed=17, strategy="stratified")
    second = select_indices(celltypes, n_cells=10, seed=17, strategy="stratified")

    assert np.array_equal(first, second)
    assert len(first) == 10
    assert len(np.unique(first)) == 10
    counts = {key: int(np.sum(celltypes[first] == key)) for key in ["A", "B", "C"]}
    assert counts == {"A": 6, "B": 3, "C": 1}


def test_first_strategy_is_explicit_and_rejects_invalid_size():
    celltypes = np.asarray(["A", "B", "A"])
    assert np.array_equal(select_indices(celltypes, n_cells=2, seed=1, strategy="first"), [0, 1])
    try:
        select_indices(celltypes, n_cells=4, seed=1, strategy="stratified")
    except ValueError as exc:
        assert "n_cells" in str(exc)
    else:
        raise AssertionError("oversampling must fail closed")
