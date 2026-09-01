from pathlib import Path

import anndata as ad
import numpy as np
import pytest

from scripts import t1_temporal_model as m
from scripts.t1_temporal_model import (
    extrapolate_shares,
    run_t1_shift,
    select_indices_by_shares,
)


def _write(path: Path, X, celltypes):
    a = ad.AnnData(
        np.asarray(X, dtype=np.float32),
        obs={"celltype": np.asarray(celltypes, dtype=str)},
    )
    a.var_names = ["g1", "g2"]
    a.write_h5ad(path)


def _panel(tmp_path: Path) -> Path:
    panel = tmp_path / "panel.genes.txt"
    panel.write_text("g1\ng2\n")
    return panel


def _relax_board(monkeypatch):
    config = dict(m.BOARD_CONFIG[("T1", "val")])
    config["min_cells"] = 1
    monkeypatch.setitem(m.BOARD_CONFIG, ("T1", "val"), config)


def test_shrunk_shift_mixes_type_and_global_delta_with_global_fallback(tmp_path, monkeypatch):
    _relax_board(monkeypatch)
    prev = tmp_path / "prev.h5ad"
    base = tmp_path / "base.h5ad"
    output = tmp_path / "prediction.h5ad"
    _write(prev, [[1, 1], [3, 3]], ["A", "A"])          # A mean [2, 2]
    _write(base, [[3, 3], [5, 5], [10, 10]], ["A", "A", "B"])  # A mean [4, 4]; B unmapped

    summary = run_t1_shift(
        board="val",
        previous_path=prev,
        base_path=base,
        output_path=output,
        n_cells=3,
        seed=7,
        damp=1.0,
        celltype_weight=0.5,
        unmapped_delta="global",
        composition_extrap="none",
        panel_path=_panel(tmp_path),
    )

    # global delta = [6, 6] - [2, 2] = [4, 4]; A: 0.5*[2, 2] + 0.5*[4, 4] = [3, 3]; B: [4, 4]
    result = ad.read_h5ad(output)
    assert np.allclose(result.X, [[6, 6], [8, 8], [14, 14]])
    assert not result.obsm.keys(), "T1 output must not carry obsm"
    assert summary["metadata"]["fallback_celltypes"] == ["B"]
    assert summary["metadata"]["target_used"] is False
    assert summary["diagnostics"]["shifted_cells"] == 3


def test_official_reference_switches_reproduce_plain_pseudobulk_shift(tmp_path, monkeypatch):
    _relax_board(monkeypatch)
    prev = tmp_path / "prev.h5ad"
    base = tmp_path / "base.h5ad"
    output = tmp_path / "prediction.h5ad"
    _write(prev, [[1, 1], [3, 3]], ["A", "A"])
    _write(base, [[3, 3], [5, 5], [10, 10]], ["A", "A", "B"])

    run_t1_shift(
        board="val",
        previous_path=prev,
        base_path=base,
        output_path=output,
        n_cells=3,
        seed=7,
        celltype_weight=1.0,
        unmapped_delta="zero",
        composition_extrap="none",
        panel_path=_panel(tmp_path),
    )

    result = ad.read_h5ad(output)
    # A shifts by [2, 2]; B has no counterpart and stays put (official behaviour).
    assert np.allclose(result.X, [[5, 5], [7, 7], [10, 10]])


def test_shift_is_clipped_at_zero(tmp_path, monkeypatch):
    _relax_board(monkeypatch)
    prev = tmp_path / "prev.h5ad"
    base = tmp_path / "base.h5ad"
    output = tmp_path / "prediction.h5ad"
    _write(prev, [[5, 5]], ["A"])
    _write(base, [[1, 1], [2, 2]], ["A", "A"])  # A delta = [1.5, 1.5] - [5, 5] = [-3.5, -3.5]

    run_t1_shift(
        board="val",
        previous_path=prev,
        base_path=base,
        output_path=output,
        n_cells=2,
        seed=7,
        celltype_weight=1.0,
        composition_extrap="none",
        panel_path=_panel(tmp_path),
    )

    result = ad.read_h5ad(output)
    assert np.allclose(result.X, [[0, 0], [0, 0]])
    assert (np.asarray(result.X) >= 0).all()


def test_extrapolate_shares_only_extrapolates_shared_types():
    shares = extrapolate_shares({"A": 0.5, "B": 0.5}, {"A": 0.25, "B": 0.5, "C": 0.25}, floor=0.001)
    assert shares["A"] == pytest.approx(0.001 / 0.751)
    assert shares["B"] == pytest.approx(0.5 / 0.751)
    assert shares["C"] == pytest.approx(0.25 / 0.751)  # unmapped type keeps last-stage share
    assert sum(shares.values()) == pytest.approx(1.0)


def test_select_indices_by_shares_hits_target_allocation_and_is_deterministic():
    rng = np.random.default_rng(0)
    celltypes = np.array(["A"] * 800 + ["B"] * 200)
    shares = {"A": 0.5, "B": 0.5}
    first = select_indices_by_shares(celltypes, shares, n_cells=100, seed=11)
    second = select_indices_by_shares(celltypes, shares, n_cells=100, seed=11)
    assert np.array_equal(first, second)
    assert (celltypes[first] == "A").sum() == 50
    assert (celltypes[first] == "B").sum() == 50
    third = select_indices_by_shares(celltypes, shares, n_cells=100, seed=12)
    assert not np.array_equal(first, third)


def test_select_indices_by_shares_clips_to_availability_and_redistributes():
    celltypes = np.array(["A"] * 800 + ["B"] * 200)
    indices = select_indices_by_shares(celltypes, {"A": 0.99, "B": 0.01}, n_cells=1000, seed=3)
    assert len(indices) == 1000
    assert (celltypes[indices] == "A").sum() == 800  # clipped to availability
    assert (celltypes[indices] == "B").sum() == 200  # deficit redistributed


def test_missing_panel_gene_fails_closed(tmp_path, monkeypatch):
    _relax_board(monkeypatch)
    prev = tmp_path / "prev.h5ad"
    base = tmp_path / "base.h5ad"
    _write(prev, [[1, 1]], ["A"])
    _write(base, [[1, 1]], ["A"])
    panel = tmp_path / "panel.genes.txt"
    panel.write_text("g1\ng_missing\n")

    with pytest.raises(ValueError, match="missing panel genes"):
        run_t1_shift(
            board="val",
            previous_path=prev,
            base_path=base,
            output_path=tmp_path / "prediction.h5ad",
            n_cells=1,
            seed=7,
            panel_path=panel,
        )


def test_same_seed_reproduces_prediction_matrix(tmp_path, monkeypatch):
    _relax_board(monkeypatch)
    prev = tmp_path / "prev.h5ad"
    base = tmp_path / "base.h5ad"
    _write(prev, [[1, 1], [3, 3]], ["A", "A"])
    _write(base, [[3, 3], [5, 5], [7, 7], [9, 9]], ["A", "A", "B", "B"])

    outputs = []
    for name in ("run1.h5ad", "run2.h5ad"):
        out = tmp_path / name
        run_t1_shift(
            board="val",
            previous_path=prev,
            base_path=base,
            output_path=out,
            n_cells=2,
            seed=99,
            celltype_weight=0.5,
            composition_extrap="none",
            panel_path=_panel(tmp_path),
        )
        outputs.append(np.asarray(ad.read_h5ad(out).X))
    assert np.allclose(outputs[0], outputs[1])
