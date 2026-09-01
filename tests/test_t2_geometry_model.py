from pathlib import Path

import anndata as ad
import numpy as np

from scripts.t2_geometry_model import run_source_geometry_shift


def _write(path: Path, coords, celltypes):
    a = ad.AnnData(
        np.asarray([[1, 2], [3, 4]], dtype=np.float32),
        obs={"celltype": np.asarray(celltypes, dtype=str)},
        obsm={"spatial_3D": np.asarray(coords, dtype=np.float32)},
    )
    a.var_names = ["g1", "g2"]
    a.write_h5ad(path)


def test_geometry_shift_preserves_expression_and_moves_centroids(tmp_path):
    panel = tmp_path / "panel.genes.txt"
    panel.write_text("g1\ng2\n")
    start = tmp_path / "start.h5ad"
    end = tmp_path / "end.h5ad"
    output = tmp_path / "prediction.h5ad"
    coords_start = [[0, 0, 0], [10, 0, 0]]
    coords_end = [[2, 0, 0], [14, 0, 0]]
    _write(start, coords_start, ["A", "B"])
    _write(end, coords_end, ["A", "B"])

    summary = run_source_geometry_shift(
        task="heart",
        shift_start_path=start,
        shift_end_path=end,
        base_path=end,
        output_path=output,
        panel_path=panel,
        damp=-0.5,
        centroid_weight=1.0,
    )

    result = ad.read_h5ad(output)
    assert np.array_equal(result.X, ad.read_h5ad(end).X)
    assert np.allclose(result.obsm["spatial_3D"], [[1, 0, 0], [12, 0, 0]], atol=1e-5)
    assert summary["centroid_weight"] == 1.0
    assert summary["fallback_celltypes"] == []
