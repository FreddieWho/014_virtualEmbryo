from __future__ import annotations

import json
import subprocess
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import pytest

from scripts import t2_j1_fgw_assignment as m


ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON = ROOT / ".venvs" / "ve-t1-ot" / "bin" / "python"


def _transport_plan(n: int, seed: int) -> np.ndarray:
    """Random near-uniform transport plan via Sinkhorn scaling (rows/cols 1/n)."""
    rng = np.random.default_rng(seed)
    T = rng.random((n, n))
    for _ in range(200):
        T *= (1.0 / n) / T.sum(axis=1, keepdims=True)
        T *= (1.0 / n) / T.sum(axis=0, keepdims=True)
    return T


# ---------------------------------------------------------------------------
# deterministic soft -> discrete assignment rule
# ---------------------------------------------------------------------------


def test_assignment_identity_plan_recovers_identity():
    n = 40
    placement, stats = m.assign_from_plan(np.eye(n) / n)
    assert np.array_equal(placement, np.arange(n))
    assert stats["conflicts"] == 0
    assert stats["mass_capture_ratio"] == pytest.approx(1.0)
    assert stats["n_moved_vs_parent"] == 0


def test_assignment_bijection_and_determinism():
    T = _transport_plan(60, seed=3)
    first, stats_first = m.assign_from_plan(T)
    second, stats_second = m.assign_from_plan(T)
    assert np.array_equal(np.sort(first), np.arange(len(first)))
    assert np.array_equal(first, second)
    assert stats_first == stats_second


def test_assignment_tie_break_lowest_row_index():
    n = 3
    T = np.full((n, n), 1.0 / (n * n))  # every entry tied
    placement, stats = m.assign_from_plan(T)
    # with all ties: margins are 0, visit order = position order; position j's
    # top-ranked row is row 0 (lowest index), so j walks down to the lowest
    # free row: placement = identity, conflicts counted for the walked positions
    assert np.array_equal(placement, np.arange(n))
    assert stats["conflicts"] == 2
    assert stats["max_rank_depth"] == 2


def test_assignment_conflict_resolution_and_count():
    """Two positions want row 0; the higher-margin position must win it."""
    n = 3
    base = np.asarray(
        [
            [0.50, 0.40, 0.10],
            [0.40, 0.35, 0.25],
            [0.10, 0.25, 0.65],
        ]
    )
    T1 = base / 3.0  # valid transport plan: all marginals are 1/3
    placement, stats = m.assign_from_plan(T1)
    # margins: col0=0.10, col1=0.05, col2=0.40 -> visit 2, 0, 1; col1 loses row 0
    assert placement.tolist() == [0, 1, 2]
    assert stats["conflicts"] == 1
    assert stats["max_rank_depth"] == 1

    flipped = np.asarray(
        [
            [0.40, 0.50, 0.10],
            [0.50, 0.35, 0.15],
            [0.10, 0.15, 0.75],
        ]
    )
    T2 = flipped / 3.0
    placement2, stats2 = m.assign_from_plan(T2)
    # col0 argmax = row1 (0.50), col1 argmax = row0 (0.50) -> no conflict
    assert placement2.tolist() == [1, 0, 2]
    assert stats2["conflicts"] == 0
    assert np.array_equal(np.sort(placement2), np.arange(n))


def test_assignment_fail_closed():
    n = 10
    good = _transport_plan(n, seed=5)
    bad_shape = np.full((n, n + 1), 1.0 / (n * (n + 1)))
    with pytest.raises(ValueError):
        m.assign_from_plan(bad_shape)
    nonfinite = good.copy()
    nonfinite[0, 0] = np.nan
    with pytest.raises(ValueError):
        m.assign_from_plan(nonfinite)
    negative = good.copy()
    negative[0, 0] = -1.0
    with pytest.raises(ValueError):
        m.assign_from_plan(negative)
    skewed = good.copy()
    skewed[:, 0] *= 1.1  # breaks the uniform marginal beyond tolerance
    with pytest.raises(ValueError):
        m.assign_from_plan(skewed)


# ---------------------------------------------------------------------------
# frozen pre-declaration
# ---------------------------------------------------------------------------


def test_config_freeze_refuses_drift(tmp_path):
    out_dir = tmp_path / "atom"
    result = m.command_config_freeze(out_dir)
    config_path = out_dir / "config_resolved.yaml"
    assert result["sha256"] == m.sha256_file(config_path)
    again = m.command_config_freeze(out_dir)
    assert again["status"] == "already_frozen"
    config_path.write_text("tampered: true\n", encoding="utf-8")
    with pytest.raises(RuntimeError):
        m.command_config_freeze(out_dir)


def test_config_contains_predeclared_audit_thresholds():
    text = m._config_text()
    assert "A1_bracket_span_days" in text
    assert "<= 0.75" in text
    assert ">= 10" in text
    assert "A3_cross_stage_probe" in text
    assert m.ASSIGNMENT_RULE_ID in text
    assert "lambda=0.500000" in text and "lambda=0.333333" in text


def test_parent_hash_lock():
    for spec in m.BOARD_SPECS.values():
        actual = m.sha256_file(ROOT / spec.parent_path)
        assert actual == spec.parent_sha256, spec.slug


def test_board_time_weights_and_limits():
    embryo = m.BOARD_SPECS["T2_embryo_val_interp"]
    heart = m.BOARD_SPECS["T2_heart_val_interp"]
    assert embryo.time_weight == pytest.approx(1.0 / 3.0)
    assert heart.time_weight == pytest.approx(0.5)
    assert heart.right_stage - heart.left_stage == pytest.approx(0.5)
    assert embryo.right_stage - embryo.left_stage == pytest.approx(0.75)


# ---------------------------------------------------------------------------
# toy fixture: structured stages + scrambled parent
# ---------------------------------------------------------------------------


def _write_toy_stage(path: Path, X: np.ndarray, coords: np.ndarray, labels, panel):
    obs = pd.DataFrame({"celltype": list(map(str, labels))},
                       index=[f"{path.stem}_{i:04d}" for i in range(len(X))])
    var = pd.DataFrame(index=list(panel))
    adata = ad.AnnData(X=np.asarray(X, dtype=np.float32), obs=obs, var=var)
    adata.obsm["spatial_3D"] = np.asarray(coords, dtype=np.float32)
    adata.uns["log1p"] = {}
    adata.write_h5ad(path)


def _toy_board(tmp_path: Path, *, n=120, g=12, n_stage=140, noise=0.05, seed=11):
    """Expression is a smooth function of position; parent pairing is scrambled.

    The cloud is an anisotropic ellipsoid so that per-stage PCA canonical
    frames are well-defined and the proper-flip selection can align the
    bracketing stages to the parent (an isotropic cloud leaves the PCA
    rotation unresolved and makes the reference frame arbitrary by
    construction).
    """
    rng = np.random.default_rng(seed)
    panel = [f"g{i}" for i in range(g)]
    panel_path = tmp_path / "panel.txt"
    panel_path.write_text("\n".join(panel) + "\n", encoding="utf-8")
    W = rng.normal(size=(3, g))
    aspect = np.asarray([3.0, 1.5, 0.5])
    coords = rng.normal(size=(n, 3)) * aspect
    X_true = np.abs(np.tanh(coords @ W) + noise * rng.normal(size=(n, g)))
    sigma = rng.permutation(n)
    labels = np.asarray(["A" if c[0] > 0 else "B" for c in coords], dtype=str)
    parent_path = tmp_path / "parent.h5ad"
    _write_toy_stage(parent_path, X_true[sigma], coords, labels, panel)

    stage_paths = {}
    for side, shift in (("left", -0.4), ("right", 0.4)):
        stage_coords = coords + 0.05 * rng.normal(size=(n, 3)) + shift * aspect
        extra = rng.normal(size=(n_stage - n, 3)) * aspect + shift * aspect
        stage_coords = np.concatenate([stage_coords, extra], axis=0)
        X_stage = np.abs(np.tanh((stage_coords - shift * aspect) @ W) + noise * rng.normal(size=(n_stage, g)))
        stage_labels = np.asarray(["A" if c[0] > 0 else "B" for c in stage_coords - shift * aspect], dtype=str)
        stage_path = tmp_path / f"stage_{side}.h5ad"
        _write_toy_stage(stage_path, X_stage, stage_coords, stage_labels, panel)
        stage_paths[side] = stage_path

    spec = m.BoardSpec(
        slug="TOY",
        board_key="embryo:val_interp",
        task="embryo",
        panel=str(panel_path),
        parent_path=str(parent_path),
        parent_sha256=m.sha256_file(parent_path),
        target_stage=7.5,
        left_stage=7.25,
        right_stage=8.0,
        left_path=str(stage_paths["left"]),
        right_path=str(stage_paths["right"]),
        min_cells=1,
        max_cells=100000,
        scorer_pseudo_target=str(stage_paths["right"]),
        scorer_pseudo_reference=str(stage_paths["left"]),
        scorer_truth_cells=n_stage,
        panel_genes=g,
        intended_version="v0000",
    )
    return {"spec": spec, "X_true": X_true, "sigma": sigma, "coords": coords,
            "labels": labels, "panel": panel}


def test_reference_time_weight_and_determinism(tmp_path):
    toy = _toy_board(tmp_path)
    spec = toy["spec"]
    parent = m.load_t2_input(Path(spec.parent_path), Path(spec.panel))
    z_target, _c, _r, _a = m.canonicalize(m._coords(parent, Path(spec.parent_path)))
    first = m.build_position_reference(spec, z_target)
    second = m.build_position_reference(spec, z_target)
    assert np.array_equal(first["g_hat"], second["g_hat"])
    assert first["meta"]["left"]["weight"] == pytest.approx(2.0 / 3.0)
    assert first["meta"]["right"]["weight"] == pytest.approx(1.0 / 3.0)
    # constant-expression stages make the weights directly readable
    assert np.isfinite(first["g_hat"]).all()


def test_audit_probe_sign_convention(tmp_path):
    """Identical stage -> pearson ~1; scrambled eval expression -> much lower."""
    toy = _toy_board(tmp_path, noise=0.01)
    spec = toy["spec"]
    panel_path = Path(spec.panel)
    support = m.load_stage_support(
        Path(spec.left_path), panel_path, board=spec.slug, side="left"
    )
    # eval on the SAME stage file: kNN self-regression of a smooth field is
    # strongly positive (k=32 smoothing caps it below 1 even without noise)
    same = m.single_stage_cross_probe(support, Path(spec.left_path), panel_path)
    assert same["nbhd_pearson"] > 0.6
    # scramble the eval expression: position information destroyed
    rng = np.random.default_rng(5)
    scrambled_path = tmp_path / "stage_scrambled.h5ad"
    left = ad.read_h5ad(spec.left_path)
    X = np.asarray(left.X)
    _write_toy_stage(
        scrambled_path,
        X[rng.permutation(len(X))],
        np.asarray(left.obsm["spatial_3D"]),
        np.asarray(left.obs["celltype"].astype(str)),
        toy["panel"],
    )
    scrambled = m.single_stage_cross_probe(support, scrambled_path, panel_path)
    assert scrambled["nbhd_pearson"] < 0.3
    assert scrambled["nbhd_pearson"] < same["nbhd_pearson"] - 0.3


def test_heart_gate_guard_blocks_without_audit(tmp_path):
    spec = m.BOARD_SPECS["T2_heart_val_interp"]
    with pytest.raises(RuntimeError):
        m._heart_gate_guard(tmp_path, spec.slug)
    m._heart_gate_guard(tmp_path, "T2_embryo_val_interp")  # embryo is not gated
    (tmp_path / "metrics").mkdir()
    (tmp_path / "metrics" / "reference_audit.json").write_text(
        json.dumps({"heart_verdict": "HOLD"}), encoding="utf-8"
    )
    with pytest.raises(RuntimeError):
        m._heart_gate_guard(tmp_path, spec.slug)
    (tmp_path / "metrics" / "reference_audit.json").write_text(
        json.dumps({"heart_verdict": "PROCEED"}), encoding="utf-8"
    )
    m._heart_gate_guard(tmp_path, spec.slug)


def test_writer_permutation_semantics(tmp_path):
    toy = _toy_board(tmp_path, n=60)
    spec = toy["spec"]
    parent_path = Path(spec.parent_path)
    parent = ad.read_h5ad(parent_path)
    rng = np.random.default_rng(17)
    placement = rng.permutation(parent.n_obs)
    out_path = tmp_path / "candidate" / "submission.h5ad"
    contract_io = m._contract_io()
    provenance = {"atom_id": m.ATOM, "board": "TOY"}
    contract_io.write_candidate_from_parent(
        parent_path=parent_path,
        output_path=out_path,
        expression=m._take_rows(parent.X, placement),
        row_names=[str(v) for v in parent.obs_names],
        normalization=m.NORMALIZATION,
        parent_sha256=spec.parent_sha256,
        metadata_updates={"ve_j1_fgw_assignment": json.dumps(provenance, sort_keys=True)},
    )
    candidate = ad.read_h5ad(out_path)
    assert np.array_equal(np.asarray(candidate.X), np.asarray(parent.X)[placement])
    assert candidate.obs.equals(parent.obs)                      # batch3 contract
    assert list(map(str, candidate.obs_names)) == list(map(str, parent.obs_names))
    assert np.array_equal(np.asarray(candidate.obsm["spatial_3D"]),
                          np.asarray(parent.obsm["spatial_3D"]))
    assert m._row_multiset_digest(candidate.X) == m._row_multiset_digest(parent.X)
    assert candidate.uns["ve_contract"]["normalization"] == m.NORMALIZATION
    assert "ve_j1_fgw_assignment" in candidate.uns
    with pytest.raises(FileExistsError):
        contract_io.write_candidate_from_parent(
            parent_path=parent_path,
            output_path=out_path,
            expression=m._take_rows(parent.X, placement),
            row_names=[str(v) for v in parent.obs_names],
            normalization=m.NORMALIZATION,
            parent_sha256=spec.parent_sha256,
            metadata_updates=None,
        )


# ---------------------------------------------------------------------------
# small end-to-end smoke through the real POT worker (budget: 1 small smoke)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not VENV_PYTHON.is_file(), reason="ve-t1-ot venv not installed")
def test_e2e_toy_pipeline_deterministic_and_recovers_structure(tmp_path):
    toy = _toy_board(tmp_path, n=120, noise=0.05)
    spec = toy["spec"]
    out_dir = tmp_path / "atom"
    hold_dir = out_dir / "intermediates" / "TOY"
    hold_dir.mkdir(parents=True)

    prepared = m.prepare_board(spec)
    assert prepared["M"].shape == (toy["coords"].shape[0],) * 2
    problem_path = hold_dir / "problem.npz"
    m._write_npz_atomic(
        problem_path,
        M=prepared["M"], C1=prepared["C1"], C2=prepared["C2"],
        p=prepared["p"], q=prepared["q"],
    )

    couplings = []
    for run in range(2):
        coupling_path = hold_dir / f"coupling_run{run}.npz"
        meta_path = hold_dir / f"solve_meta_run{run}.json"
        proc = subprocess.run(
            [
                str(VENV_PYTHON),
                "-m",
                "scripts.t2_j1_fgw_assignment",
                "solve-worker",
                "--problem",
                str(problem_path),
                "--coupling",
                str(coupling_path),
                "--meta",
                str(meta_path),
                "--board",
                "TOY",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            env=m._worker_env(),
            timeout=1800,
        )
        assert proc.returncode == 0, proc.stderr[-2000:]
        couplings.append(np.load(coupling_path)["T"].copy())
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        assert meta["backend"] == "POT"
        assert meta["epsilon"] == m.FGW_EPSILON and meta["alpha"] == m.FGW_ALPHA
    assert np.array_equal(couplings[0], couplings[1])  # worker determinism

    placement, stats = m.assign_from_plan(couplings[0])
    assert np.array_equal(np.sort(placement), np.arange(len(placement)))
    assert stats["conflicts"] >= 0

    # the candidate must beat the scrambled parent against the toy truth
    # (official NFS mirror, lower is better)
    parent_X = toy["X_true"][toy["sigma"]]
    candidate_X = parent_X[placement]
    nfs_parent = m._nfs_like(parent_X, toy["coords"], toy["X_true"], toy["coords"])
    nfs_candidate = m._nfs_like(candidate_X, toy["coords"], toy["X_true"], toy["coords"])
    assert nfs_candidate < nfs_parent

    # structure recovery (proxy-style): the soft plan's barycentric position
    # readout must place each row near the true position of its expression,
    # coords[sigma[i]] -- comparing against coords[i] would reward the
    # identity (still-scrambled) plan -- far better than a random coupling
    T = couplings[0]
    pos_hat = (T @ toy["coords"]) / T.sum(axis=1, keepdims=True)
    target = toy["coords"][toy["sigma"]]
    solved_err = float(np.median(np.linalg.norm(pos_hat - target, axis=1)))
    rng = np.random.default_rng(23)
    perm = rng.permutation(len(T))
    random_err = float(np.median(np.linalg.norm(target[perm] - target, axis=1)))
    assert solved_err < 0.7 * random_err

    # candidate write through the batch3 writer preserves the contract slots
    parent = ad.read_h5ad(spec.parent_path)
    out_path = tmp_path / "atom" / "candidates" / "TOY" / "submission.h5ad"
    contract_io = m._contract_io()
    contract_io.write_candidate_from_parent(
        parent_path=Path(spec.parent_path),
        output_path=out_path,
        expression=m._take_rows(parent.X, placement),
        row_names=[str(v) for v in parent.obs_names],
        normalization=m.NORMALIZATION,
        parent_sha256=spec.parent_sha256,
        metadata_updates={"ve_j1_fgw_assignment": json.dumps({"atom_id": m.ATOM})},
    )
    candidate = ad.read_h5ad(out_path)
    assert np.array_equal(np.asarray(candidate.X), np.asarray(parent.X)[placement])
    assert candidate.obs.equals(parent.obs)
    assert m._row_multiset_digest(candidate.X) == m._row_multiset_digest(parent.X)
