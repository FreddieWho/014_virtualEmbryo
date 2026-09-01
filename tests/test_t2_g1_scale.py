from pathlib import Path

import anndata as ad
import numpy as np

from scripts import t2_g1_scale as g1


def _write(path: Path, coords, *, genes=("g1", "g2")):
    n_obs = len(coords)
    a = ad.AnnData(
        np.arange(n_obs * len(genes), dtype=np.float32).reshape(n_obs, len(genes)) + 1,
        obs={"celltype": np.asarray(["A"] * n_obs, dtype=str)},
        obsm={"spatial_3D": np.asarray(coords, dtype=np.float32)},
    )
    a.var_names = list(genes)
    a.write_h5ad(path)


def test_formal_and_trend_log_rms_fits_are_deterministic():
    formal = g1._fit_target_log_rms(
        g1.LANE_FORMAL,
        [7.25, 8.0],
        [2.0, 2.0 * np.e],
        7.5,
    )
    assert formal["fit"] == "strict_linear_interpolation"
    assert np.isclose(formal["target_log_rms"], np.log(2.0) + (1.0 / 3.0) * np.log(np.e))

    trend = g1._fit_target_log_rms(
        g1.LANE_TREND,
        [6.75, 7.25, 8.0],
        np.exp([1.0, 1.5, 2.25]),
        7.5,
    )
    assert trend["fit"] == "ordinary_least_squares"
    assert np.isclose(trend["target_log_rms"], 1.75)


def test_run_g1_scale_changes_only_uniform_coordinates(tmp_path, monkeypatch):
    panel = tmp_path / "panel.genes.txt"
    panel.write_text("g1\ng2\n")
    start = tmp_path / "start.h5ad"
    middle = tmp_path / "middle.h5ad"
    end = tmp_path / "end.h5ad"
    output = tmp_path / "prediction.h5ad"
    coords = np.asarray(
        [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 2.0, 0.0], [4.0, 3.0, 5.0]],
        dtype=np.float32,
    )
    _write(start, coords)
    _write(middle, coords * 2.0)
    _write(end, coords * 4.0)

    monkeypatch.setitem(
        g1.BOARD_SPECS,
        "test_board",
        g1.BoardSpec(
            slug="test_board",
            official_key="T2:test:interp",
            task="heart",
            panel="panel.genes.txt",
            target_stage=0.5,
            source_stages=((0.0, "start.h5ad"), (1.0, "middle.h5ad"), (2.0, "end.h5ad")),
            base_submission="end.h5ad",
            min_cells=2,
            max_cells=100,
        ),
    )
    result = g1.run_g1_scale(
        lane=g1.LANE_FORMAL,
        board="test_board",
        output_path=output,
        project_root=tmp_path,
    )

    base = ad.read_h5ad(end)
    candidate = ad.read_h5ad(output)
    base_coords = np.asarray(base.obsm["spatial_3D"], dtype=np.float64)
    candidate_coords = np.asarray(candidate.obsm["spatial_3D"], dtype=np.float64)
    base_center = base_coords.mean(axis=0)
    expected = base_center + result["model"]["scale_factor"] * (base_coords - base_center)
    assert np.allclose(candidate_coords, expected, rtol=1e-6, atol=1e-6)
    assert np.array_equal(candidate.X, base.X)
    assert candidate.obs_names.tolist() == base.obs_names.tolist()
    assert candidate.var_names.tolist() == base.var_names.tolist()
    assert result["protected_checks"]["expression_checksum_unchanged"]
    assert result["protected_checks"]["knn15_exact"]


def test_l1_rejects_pre_first_stage_extrapolation():
    try:
        g1._fit_target_log_rms(g1.LANE_FORMAL, [1.0, 2.0], [1.0, 2.0], 0.5)
    except ValueError as exc:
        assert "pre-first-stage" in str(exc)
    else:
        raise AssertionError("pre-first-stage L1 extrapolation must fail closed")


def test_run_batch1_a1_freezes_two_lanes_and_six_manifests(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    panel_dir = data_dir / "gene_panel"
    panel_dir.mkdir(parents=True)
    (panel_dir / "index.json").write_text("{}")
    (panel_dir / "panel.genes.txt").write_text("g1\ng2\n")
    for name, multiplier in (("start", 1.0), ("middle", 2.0), ("end", 4.0)):
        _write(tmp_path / f"{name}.h5ad", np.asarray([[0, 0, 0], [1, 0, 0], [0, 2, 0], [4, 3, 5]]) * multiplier)

    board_names = ("board_a", "board_b", "board_c")
    specs = {
        name: g1.BoardSpec(
            slug=name,
            official_key=f"T2:{name}:interp",
            task="heart",
            panel="data/gene_panel/panel.genes.txt",
            target_stage=0.5,
            source_stages=((0.0, "start.h5ad"), (1.0, "middle.h5ad"), (2.0, "end.h5ad")),
            base_submission="end.h5ad",
            min_cells=2,
            max_cells=100,
        )
        for name in board_names
    }
    monkeypatch.setattr(g1, "BOARD_ORDER", board_names)
    monkeypatch.setattr(g1, "BOARD_SPECS", specs)

    result = g1.run_batch1_a1(
        atom_root=tmp_path / "artifacts" / "B1-A1",
        project_root=tmp_path,
    )

    assert len(result["candidates"]) == 6
    assert {item["lane_id"] for item in result["candidates"]} == set(g1.LANES)
    assert {item["board"] for item in result["candidates"]} == set(board_names)
    freeze = result["final_set_manifest"]
    assert freeze["expected_final_artifacts"] == 6
    assert len(freeze["candidates"]) == 6
    assert freeze["score_status"] == "score_pending"
