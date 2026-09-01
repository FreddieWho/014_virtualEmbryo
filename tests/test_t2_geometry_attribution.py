from pathlib import Path

import anndata as ad
import numpy as np

from scripts.t2_geometry_attribution import replace_geometry


def _write(path: Path, X, coords):
    a = ad.AnnData(
        np.asarray(X, dtype=np.float32),
        obs={"celltype": ["A"] * len(X)},
        obsm={"spatial_3D": np.asarray(coords, dtype=np.float32)},
    )
    a.var_names = ["g1", "g2"]
    a.write_h5ad(path)


def test_replace_geometry_keeps_expression_and_replaces_only_coordinates(tmp_path):
    expression = tmp_path / "expression.h5ad"
    geometry = tmp_path / "geometry.h5ad"
    output = tmp_path / "output.h5ad"
    _write(expression, [[1, 2], [3, 4]], [[1, 1, 1], [2, 2, 2]])
    _write(geometry, [[9, 9], [9, 9]], [[7, 8, 9], [10, 11, 12]])

    summary = replace_geometry(expression, geometry, output, label="oracle_geometry")
    result = ad.read_h5ad(output)
    assert np.array_equal(result.X, [[1, 2], [3, 4]])
    assert np.array_equal(result.obsm["spatial_3D"], [[7, 8, 9], [10, 11, 12]])
    assert summary["geometry_label"] == "oracle_geometry"
