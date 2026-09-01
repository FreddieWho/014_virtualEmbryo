from pathlib import Path

import anndata as ad
import numpy as np

from scripts.t2_expression_model import run_shrunk_stage_shift


def _write(path: Path, X, celltypes):
    a = ad.AnnData(
        np.asarray(X, dtype=np.float32),
        obs={"celltype": np.asarray(celltypes, dtype=str)},
        obsm={"spatial_3D": np.arange(len(celltypes) * 3, dtype=np.float32).reshape(-1, 3)},
    )
    a.var_names = ["g1", "g2"]
    a.write_h5ad(path)


def test_shrunk_shift_mixes_celltype_and_global_delta_and_preserves_geometry(tmp_path):
    panel = tmp_path / "panel.genes.txt"
    panel.write_text("g1\ng2\n")
    start = tmp_path / "start.h5ad"
    end = tmp_path / "end.h5ad"
    output = tmp_path / "prediction.h5ad"
    _write(start, [[1, 1], [5, 5]], ["A", "B"])
    _write(end, [[3, 3], [6, 6]], ["A", "B"])

    summary = run_shrunk_stage_shift(
        task="heart",
        shift_start_path=start,
        shift_end_path=end,
        base_path=end,
        output_path=output,
        panel_path=panel,
        damp=1.0,
        celltype_weight=0.5,
    )

    result = ad.read_h5ad(output)
    assert np.allclose(result.X, [[4.75, 4.75], [7.25, 7.25]])
    assert np.array_equal(result.obsm["spatial_3D"], ad.read_h5ad(end).obsm["spatial_3D"])
    assert summary["celltype_weight"] == 0.5
    assert summary["fallback_celltypes"] == []


def test_shrunk_shift_can_restore_log1p_library_size(tmp_path):
    panel = tmp_path / "panel.genes.txt"
    panel.write_text("g1\ng2\n")
    start = tmp_path / "start.h5ad"
    end = tmp_path / "end.h5ad"
    output = tmp_path / "prediction.h5ad"
    _write(start, [[1, 1], [5, 5]], ["A", "B"])
    _write(end, [[3, 3], [6, 6]], ["A", "B"])

    summary = run_shrunk_stage_shift(
        task="heart",
        shift_start_path=start,
        shift_end_path=end,
        base_path=end,
        output_path=output,
        panel_path=panel,
        damp=1.0,
        celltype_weight=0.5,
        target_library_size=10000.0,
    )

    result = ad.read_h5ad(output)
    totals = np.expm1(np.asarray(result.X)).sum(axis=1)
    assert np.allclose(totals, 10000.0, rtol=1e-5, atol=1e-3)
    assert summary["normalization"] == "rowwise_log1p_library_size"
