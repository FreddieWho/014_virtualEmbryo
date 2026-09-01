from pathlib import Path

import anndata as ad
import numpy as np

from scripts.t2_controls import run_control


def _write(path: Path, X, genes, coords):
    a = ad.AnnData(
        np.asarray(X, dtype=np.float32),
        obs={"celltype": ["A"] * len(X)},
        obsm={"spatial_3D": np.asarray(coords, dtype=np.float32)},
    )
    a.var_names = list(genes)
    a.write_h5ad(path)


def test_scale_ref_only_changes_expression(tmp_path):
    panel = tmp_path / "panel.txt"
    panel.write_text("g1\ng2\n")
    reference = tmp_path / "reference.h5ad"
    output = tmp_path / "scale.h5ad"
    coords = [[1, 2, 3], [4, 5, 6]]
    _write(reference, [[1, 2], [3, 4]], ["g1", "g2"], coords)

    run_control(
        task="embryo",
        control="ctrl_scale_ref",
        reference_path=reference,
        output_path=output,
        panel_path=panel,
    )
    result = ad.read_h5ad(output)
    assert np.array_equal(result.X, [[2, 4], [6, 8]])
    assert np.array_equal(result.obsm["spatial_3D"], coords)
    assert result.uns["ve_control"]["audit_only"] is True


def test_squashed_ref_preserves_center_and_expression(tmp_path):
    panel = tmp_path / "panel.txt"
    panel.write_text("g1\ng2\n")
    reference = tmp_path / "reference.h5ad"
    output = tmp_path / "squashed.h5ad"
    coords = [[0, 0, 0], [2, 4, 8], [4, 8, 16]]
    _write(reference, [[1, 2], [3, 4], [5, 6]], ["g1", "g2"], coords)

    run_control(
        task="embryo",
        control="ctrl_squashed_ref",
        reference_path=reference,
        output_path=output,
        panel_path=panel,
    )
    result = ad.read_h5ad(output)
    expected = (np.asarray(coords) - np.mean(coords, axis=0)) * [4, 1, 0.25] + np.mean(coords, axis=0)
    assert np.allclose(result.obsm["spatial_3D"], expected)
    assert np.array_equal(result.X, np.asarray([[1, 2], [3, 4], [5, 6]], dtype=np.float32))


def test_random_cube_uses_target_bbox_and_is_seeded(tmp_path):
    panel = tmp_path / "panel.txt"
    panel.write_text("g1\ng2\n")
    reference = tmp_path / "reference.h5ad"
    target = tmp_path / "target.h5ad"
    output_a = tmp_path / "random_a.h5ad"
    output_b = tmp_path / "random_b.h5ad"
    _write(reference, [[1, 2], [3, 4]], ["g1", "g2"], [[-100, -100, -100], [100, 100, 100]])
    target_coords = [[10, 20, 30], [12, 25, 34], [11, 22, 32]]
    _write(target, [[5, 6], [7, 8], [9, 10]], ["g1", "g2"], target_coords)

    kwargs = {
        "task": "embryo",
        "control": "ctrl_random_cube",
        "reference_path": reference,
        "target_path": target,
        "panel_path": panel,
        "seed": 7,
    }
    run_control(output_path=output_a, **kwargs)
    run_control(output_path=output_b, **kwargs)
    a = ad.read_h5ad(output_a)
    b = ad.read_h5ad(output_b)
    coords = np.asarray(a.obsm["spatial_3D"])
    assert np.array_equal(coords, b.obsm["spatial_3D"])
    assert np.all(coords >= np.min(target_coords, axis=0))
    assert np.all(coords <= np.max(target_coords, axis=0))
    assert np.array_equal(a.X, [[1, 2], [3, 4]])


def test_random_cube_requires_explicit_target(tmp_path):
    panel = tmp_path / "panel.txt"
    panel.write_text("g1\ng2\n")
    reference = tmp_path / "reference.h5ad"
    _write(reference, [[1, 2]], ["g1", "g2"], [[0, 0, 0]])
    try:
        run_control(
            task="embryo",
            control="ctrl_random_cube",
            reference_path=reference,
            output_path=tmp_path / "random.h5ad",
            panel_path=panel,
        )
    except ValueError as exc:
        assert "target_path" in str(exc)
    else:
        raise AssertionError("ctrl_random_cube must require an explicit target bbox")
