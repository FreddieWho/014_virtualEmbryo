import json
from pathlib import Path

import anndata as ad
import numpy as np
import pytest

from scripts import t2_j1_pairing as j1


def _coords(n=20):
    return np.column_stack(
        (
            np.arange(n, dtype=np.float32),
            np.sin(np.arange(n, dtype=np.float32) * 0.37),
            np.cos(np.arange(n, dtype=np.float32) * 0.23),
        )
    )


def _fixture(n=20, g=4):
    rng = np.random.default_rng(11)
    X = rng.random((n, g), dtype=np.float32)
    a = ad.AnnData(
        X,
        obs={"celltype": np.asarray(["A" if i % 2 else "B" for i in range(n)])},
        obsm={"spatial_2D": _coords(n), "spatial_3D": _coords(n)},
        layers={"counts": np.round(X * 10).astype(np.float32), "log1p": X.copy()},
    )
    a.var_names = [f"g{i}" for i in range(g)]
    a.raw = a.copy()
    return a


def test_swap_delta_matches_full_recomputation():
    rng = np.random.default_rng(4)
    coords = _coords()
    z = rng.normal(size=(20, 5))
    desired = rng.normal(size=(20, 5))
    graph = j1._spatial_knn(coords)
    reverse = j1._reverse_neighbourhood(graph)
    assignment = np.arange(20, dtype=np.int64)
    neighbourhood = z[graph].mean(axis=1)
    residual = np.sum((neighbourhood - desired) ** 2, axis=1)
    delta, affected, new_m, new_r = j1._swap_delta(
        z=z,
        desired=desired,
        graph=graph,
        reverse=reverse,
        assignment=assignment,
        neighbourhood=neighbourhood,
        residual=residual,
        node_a=2,
        node_b=13,
    )
    trial = assignment.copy()
    trial[2], trial[13] = trial[13], trial[2]
    full_m = z[trial[graph]].mean(axis=1)
    full_r = np.sum((full_m - desired[trial]) ** 2, axis=1)
    assert np.isclose(delta, full_r.sum() - residual.sum())
    assert np.allclose(new_m, full_m[affected])
    assert np.allclose(new_r, full_r[affected])


def test_pairing_is_deterministic_and_respects_state_lane():
    rng = np.random.default_rng(5)
    z = rng.normal(size=(20, 5))
    desired = rng.normal(size=(20, 5))
    coords = _coords()
    labels = np.asarray(["A" if i % 2 else "B" for i in range(20)])
    names = np.asarray([f"cell-{i:03d}" for i in range(20)])
    first = j1.optimize_pairing(
        z, desired, coords, lane=j1.LANE_LATENT, labels=labels, obs_names=names, seed=7
    )
    second = j1.optimize_pairing(
        z, desired, coords, lane=j1.LANE_LATENT, labels=labels, obs_names=names, seed=7
    )
    assert np.array_equal(first["permutation"], second["permutation"])
    assert first["final_objective"] <= first["initial_objective"]
    assert first["proposal_count"] <= 10 * len(z)

    state = j1.optimize_pairing(
        z, desired, coords, lane=j1.LANE_STATE, labels=labels, obs_names=names, seed=7
    )
    assert np.array_equal(labels[state["permutation"]], labels)
    assert state["final_objective"] <= state["initial_objective"]


def test_reordered_output_moves_all_expression_row_aligned_objects(tmp_path: Path):
    parent = _fixture()
    permutation = np.asarray(list(range(1, 20)) + [0], dtype=np.int64)
    output_path = tmp_path / "prediction.h5ad"
    j1._write_reordered(
        parent,
        permutation,
        output_path,
        metadata={"target_used": False, "method": "test"},
    )
    candidate = ad.read_h5ad(output_path)
    checks = j1._check_output(
        parent,
        candidate,
        permutation,
        tmp_path / "parent.h5ad",
        output_path,
    )
    assert all(checks[key] for key in (
        "permutation_bijection",
        "expression_replay_exact",
        "layers_replay_exact",
        "raw_replay_exact",
        "obs_replay_exact",
        "coordinate_values_exact",
        "knn15_exact",
    ))
    assert candidate.obs_names.tolist() == parent.obs_names.tolist()
    assert np.array_equal(candidate.X, parent.X[permutation])
    assert np.array_equal(candidate.raw.X, parent.raw.X[permutation])


def test_state_hash_proposals_are_seeded_and_same_state_only():
    labels = np.asarray(["A"] * 10 + ["B"] * 10)
    names = np.asarray([f"cell-{i:03d}" for i in range(20)])
    a = j1._state_hash_proposals(names, labels, seed=9)
    b = j1._state_hash_proposals(names, labels, seed=9)
    c = j1._state_hash_proposals(names, labels, seed=10)
    assert all(np.array_equal(x, y) for x, y in zip(a, b))
    assert any(not np.array_equal(x, y) for x, y in zip(a, c))
    for row, candidates in enumerate(a):
        assert all(labels[candidate] == labels[row] for candidate in candidates)
        assert row not in set(candidates.tolist())


def test_frozen_a4_manifests_match_batch1_schema():
    root = Path("artifacts/atomic_batch1/B1-A4")
    if not root.exists():
        pytest.skip("B1-A4 artifacts are not present in this checkout")
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(Path("docs/batch1/templates/MANIFEST_SCHEMA.json").read_text())
    validator = jsonschema.Draft202012Validator(schema)
    manifests = sorted(root.glob("final/*/*/MANIFEST.json"))
    assert len(manifests) == 6
    for path in manifests:
        errors = sorted(validator.iter_errors(json.loads(path.read_text())), key=str)
        assert not errors, f"{path}: {errors}"

    final_schema = json.loads(Path("docs/batch1/templates/FINAL_SET_SCHEMA.json").read_text())
    final_errors = sorted(
        jsonschema.Draft202012Validator(final_schema).iter_errors(
            json.loads((root / "FINAL_SET_MANIFEST.json").read_text())
        ),
        key=str,
    )
    assert not final_errors, final_errors


def test_finalize_preflights_unique_lane_board_and_artifact_set(tmp_path: Path):
    atom_root = tmp_path / "atom"
    freeze_candidates = []
    for lane in j1.LANES:
        for board in j1.BOARD_ORDER:
            candidate_dir = atom_root / "final" / lane / board
            candidate_dir.mkdir(parents=True)
            artifact = candidate_dir / "prediction.h5ad"
            artifact.write_bytes(f"{lane}:{board}".encode())
            digest = j1.sha256_file(artifact)
            candidate_id = j1._candidate_id(lane, board)
            manifest = {
                "atom_id": j1.ATOM_ID,
                "lane_id": lane,
                "board": board,
                "candidate_id": candidate_id,
                "base_submission": "parent.h5ad",
                "sha256": digest,
                "output_file": str(artifact),
            }
            (candidate_dir / "MANIFEST.json").write_text(json.dumps(manifest))
            score_path = atom_root / "metrics" / lane / board / "local_or_official.json"
            score_path.parent.mkdir(parents=True, exist_ok=True)
            score_path.write_text(json.dumps({"status": "COMPLETE", "metrics": {"neighborhood_mmd": 1.0}}))
            freeze_candidates.append(
                {"lane_id": lane, "board": board, "candidate_id": candidate_id, "sha256": digest}
            )
    freeze = {"candidates": freeze_candidates}
    assert len(j1._prepare_finalize_candidates(atom_root, freeze)) == 6

    duplicate = {"candidates": freeze_candidates[:-1] + [freeze_candidates[0].copy()]}
    with pytest.raises(ValueError, match="repeats lane/board"):
        j1._prepare_finalize_candidates(atom_root, duplicate)


def test_submission_copy_is_exclusive_and_candidates_scoped(tmp_path: Path):
    project_root = tmp_path / "project"
    source = tmp_path / "source.h5ad"
    source.write_bytes(b"candidate")
    destination = project_root / "submissions" / "candidates" / "v1" / "submission.h5ad"
    j1._copy_submission_exclusive(source, destination, project_root)
    assert destination.read_bytes() == b"candidate"
    with pytest.raises(FileExistsError):
        j1._copy_submission_exclusive(source, destination, project_root)
    with pytest.raises(ValueError, match="escapes submissions/candidates"):
        j1._copy_submission_exclusive(
            source,
            project_root / "submissions" / "scored" / "submission.h5ad",
            project_root,
        )
