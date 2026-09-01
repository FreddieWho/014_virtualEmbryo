from pathlib import Path

import anndata as ad
import numpy as np
from scipy import sparse

from scripts.t2_baseline import run_baseline, run_stage_shift


def _write(path: Path, X, genes, celltypes, *, coords=True):
    obs = {"celltype": np.asarray(celltypes, dtype=str)}
    obsm = {}
    if coords:
        obsm["spatial_3D"] = np.arange(len(celltypes) * 3, dtype=np.float32).reshape(
            len(celltypes), 3
        )
    if not sparse.issparse(X):
        X = np.asarray(X, dtype=np.float32)
    a = ad.AnnData(X, obs=obs, obsm=obsm)
    a.var_names = list(genes)
    a.write_h5ad(path)


def test_pseudobulk_shift_aligns_panel_and_preserves_geometry(tmp_path):
    panel = tmp_path / "panel.genes.txt"
    panel.write_text("g1\ng2\n")
    previous = tmp_path / "previous.h5ad"
    base = tmp_path / "base.h5ad"
    output = tmp_path / "prediction.h5ad"

    _write(
        previous,
        sparse.csr_matrix([[1, 2, 99], [1, 2, 99]], dtype=np.float32),
        ["g1", "g2", "unused"],
        ["A", "A"],
    )
    _write(
        base,
        sparse.csr_matrix([[2, 1, 88], [3, 5, 77]], dtype=np.float32),
        ["g1", "g2", "unused"],
        ["A", "B"],
    )

    summary = run_baseline(
        task="embryo",
        method="pseudobulk_shift",
        previous_path=previous,
        base_path=base,
        output_path=output,
        panel_path=panel,
    )

    result = ad.read_h5ad(output)
    assert result.var_names.tolist() == ["g1", "g2"]
    assert np.allclose(result.X, [[3, 0], [3, 5]])
    assert np.array_equal(result.obsm["spatial_3D"], ad.read_h5ad(base).obsm["spatial_3D"])
    assert summary["shifted_cells"] == 1


def test_copy_last_preserves_sparse_input_and_needs_no_previous(tmp_path):
    panel = tmp_path / "panel.genes.txt"
    panel.write_text("g1\ng2\n")
    base = tmp_path / "base.h5ad"
    output = tmp_path / "prediction.h5ad"
    _write(base, sparse.csr_matrix([[1, 0], [0, 2]], dtype=np.float32), ["g1", "g2"], ["A", "B"])

    summary = run_baseline(
        task="heart",
        method="copy_last",
        previous_path=None,
        base_path=base,
        output_path=output,
        panel_path=panel,
    )

    result = ad.read_h5ad(output)
    assert sparse.issparse(result.X)
    assert np.array_equal(result.X.toarray(), [[1, 0], [0, 2]])
    assert summary["shifted_cells"] == 0


def test_t2_requires_finite_three_column_spatial_coordinates(tmp_path):
    panel = tmp_path / "panel.genes.txt"
    panel.write_text("g1\ng2\n")
    base = tmp_path / "base.h5ad"
    output = tmp_path / "prediction.h5ad"
    _write(base, np.ones((1, 2), dtype=np.float32), ["g1", "g2"], ["A"], coords=False)

    try:
        run_baseline(
            task="embryo",
            method="copy_last",
            previous_path=None,
            base_path=base,
            output_path=output,
            panel_path=panel,
        )
    except ValueError as exc:
        assert "spatial_3D" in str(exc)
    else:
        raise AssertionError("missing spatial_3D must fail closed")


def test_stage_shift_supports_signed_interpolation_damp(tmp_path):
    panel = tmp_path / "panel.genes.txt"
    panel.write_text("g1\ng2\n")
    start = tmp_path / "start.h5ad"
    end = tmp_path / "end.h5ad"
    output = tmp_path / "prediction.h5ad"
    _write(start, [[1, 2], [1, 2]], ["g1", "g2"], ["A", "A"])
    _write(end, [[3, 4], [3, 4]], ["g1", "g2"], ["A", "A"])

    run_stage_shift(
        task="heart",
        shift_start_path=start,
        shift_end_path=end,
        base_path=end,
        output_path=output,
        panel_path=panel,
        damp=-0.5,
    )

    result = ad.read_h5ad(output)
    assert np.allclose(result.X, [[2, 3], [2, 3]])
    assert result.uns["ve_baseline"]["method"] == "pseudobulk_shift_stage_proxy"


def test_stage_shift_can_control_log1p_library_size(tmp_path):
    panel = tmp_path / "panel.genes.txt"
    panel.write_text("g1\ng2\n")
    start = tmp_path / "start.h5ad"
    end = tmp_path / "end.h5ad"
    base = tmp_path / "base.h5ad"
    output = tmp_path / "prediction.h5ad"
    _write(start, [[1, 1], [1, 1]], ["g1", "g2"], ["A", "A"])
    _write(end, [[2, 2], [2, 2]], ["g1", "g2"], ["A", "A"])
    _write(base, [[3, 3], [3, 3]], ["g1", "g2"], ["A", "A"])

    summary = run_stage_shift(
        task="heart",
        shift_start_path=start,
        shift_end_path=end,
        base_path=base,
        output_path=output,
        panel_path=panel,
        target_library_size=10_000.0,
    )

    result = ad.read_h5ad(output)
    X = np.asarray(result.X, dtype=np.float64)
    assert np.allclose(np.expm1(X).sum(axis=1), 10_000.0, rtol=1e-5)
    assert summary["normalization"] == "rowwise_log1p_library_size"
