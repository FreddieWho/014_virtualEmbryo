from pathlib import Path

import anndata as ad
import numpy as np
import pytest
from scipy import sparse

from scripts.t3_shift_transfer import (
    _depth_match_indices,
    _normalize_log1p_rows,
    _sparsify_delta,
    run_shift_transfer,
)


def _write_source(path: Path, X, counts, genes, *, coords=True):
    obs = {"celltype": np.asarray(["A"] * len(X), dtype=str)}
    obsm = {}
    if coords:
        obsm["spatial_3D"] = np.arange(len(X) * 3, dtype=np.float32).reshape(len(X), 3)
    a = ad.AnnData(X, obs=obs, obsm=obsm)
    a.var_names = list(genes)
    a.layers["counts"] = counts
    a.write_h5ad(path)


def _log1p_10k(counts):
    counts = np.asarray(counts, dtype=np.float32)
    return np.log1p(counts * (10_000.0 / counts.sum(axis=1, keepdims=True))).astype(np.float32)


def test_depth_matching_and_sparsification_are_deterministic():
    wt, ko = _depth_match_indices(
        np.asarray([10, 20, 30, 40, 50, 60], dtype=float),
        np.asarray([11, 19, 31, 39, 51, 61], dtype=float),
        bins=3,
        seed=20260822,
    )[:2]
    wt2, ko2 = _depth_match_indices(
        np.asarray([10, 20, 30, 40, 50, 60], dtype=float),
        np.asarray([11, 19, 31, 39, 51, 61], dtype=float),
        bins=3,
        seed=20260822,
    )[:2]
    assert np.array_equal(wt, wt2)
    assert np.array_equal(ko, ko2)
    assert len(wt) == len(ko)

    kept, up, down = _sparsify_delta(np.asarray([-4.0, -3.0, -2.0, 1.0, 2.0, 3.0]), top_up=2, top_down=1)
    assert np.array_equal(kept, [-4.0, 0.0, 0.0, 0.0, 2.0, 3.0])
    assert up == [5, 4]
    assert down == [0]


def test_row_normalization_restores_implied_library_size():
    out = _normalize_log1p_rows(np.asarray([[0.0, 2.0], [4.0, 0.0]], dtype=float), 10_000.0)
    assert out.dtype == np.float32
    assert np.allclose(np.expm1(out).sum(axis=1), 10_000.0, rtol=1e-6, atol=1e-3)


def test_runner_rejects_carrier_below_board_minimum(tmp_path):
    genes = [line.strip() for line in Path("data/gene_panel/T3__gata4.genes.txt").read_text().splitlines() if line.strip()]
    carrier = tmp_path / "carrier.h5ad"
    counts_carrier = np.ones((2, 500), dtype=np.float32)
    carrier_X = _log1p_10k(counts_carrier)
    _write_source(carrier, carrier_X, counts_carrier, genes)

    # The production runner requires a 500-gene panel and the board's minimum
    # carrier size; this focused test exercises validation on smaller helpers.
    with pytest.raises(ValueError, match="outside"):
        run_shift_transfer(
            variant="official_norm",
            train_wt_path=carrier,
            train_ko_path=carrier,
            carrier_path=carrier,
            output_path=tmp_path / "out.h5ad",
        )


def test_runner_builds_both_presets_on_synthetic_board_data(tmp_path):
    genes = [line.strip() for line in Path("data/gene_panel/T3__gata4.genes.txt").read_text().splitlines() if line.strip()]
    levels = np.repeat(np.arange(1, 11, dtype=np.float32), 100)[:, None]
    wt_counts = np.repeat(levels, 500, axis=1)
    ko_counts = wt_counts.copy()
    mab = genes.index("Mab21l2")
    ko_counts[:, mab] += 1.0
    wt_path = tmp_path / "wt.h5ad"
    ko_path = tmp_path / "ko.h5ad"
    carrier_path = tmp_path / "carrier.h5ad"
    _write_source(wt_path, _log1p_10k(wt_counts), wt_counts, genes)
    _write_source(ko_path, _log1p_10k(ko_counts), ko_counts, genes)
    _write_source(carrier_path, _log1p_10k(wt_counts), wt_counts, genes)

    outputs = {}
    for variant in ("official_norm", "conservative"):
        output = tmp_path / f"{variant}.h5ad"
        outputs[variant] = run_shift_transfer(
            variant=variant,
            train_wt_path=wt_path,
            train_ko_path=ko_path,
            carrier_path=carrier_path,
            output_path=output,
        )
        result = ad.read_h5ad(output)
        values = result.X.toarray() if sparse.issparse(result.X) else np.asarray(result.X)
        assert result.shape == (1000, 500)
        assert np.isfinite(values).all() and (values >= 0).all()
        assert np.allclose(np.expm1(values).sum(axis=1), 10_000.0, rtol=1e-5, atol=1e-2)
    assert outputs["conservative"]["depth_match"] is True
    conservative = ad.read_h5ad(tmp_path / "conservative.h5ad")
    gata4 = conservative.var_names.get_loc("Gata4")
    assert np.array_equal(np.asarray(conservative.X)[:, gata4], np.zeros(1000, dtype=np.float32))


def test_scale_mismatch_is_not_silently_accepted(tmp_path):
    genes = [line.strip() for line in Path("data/gene_panel/T3__gata4.genes.txt").read_text().splitlines() if line.strip()]
    counts = np.ones((1000, 500), dtype=np.float32)
    bad_X = np.log1p(counts).astype(np.float32)
    path = tmp_path / "bad.h5ad"
    _write_source(path, bad_X, counts, genes)
    with pytest.raises(ValueError, match="counts-derived log1p"):
        run_shift_transfer(
            variant="official_norm",
            train_wt_path=path,
            train_ko_path=path,
            carrier_path=path,
            output_path=tmp_path / "out.h5ad",
        )
