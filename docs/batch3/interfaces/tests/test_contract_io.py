from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import pytest

from virtual_embryo_tools.contract_io import (
    validate_h5ad_contract,
    write_candidate_from_parent,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fixture_root(tmp_path: Path) -> tuple[Path, Path, list[str]]:
    root = tmp_path / "repo"
    panel_dir = root / "data" / "gene_panel"
    panel_dir.mkdir(parents=True)
    genes = ["G1", "G2", "G3"]
    (panel_dir / "panel.txt").write_text("\n".join(genes) + "\n", encoding="utf-8")
    (panel_dir / "index.json").write_text(
        json.dumps(
            {
                "T3:gata4": {
                    "task": "T3",
                    "key": "T3:gata4",
                    "genes_file": "panel.txt",
                    "n_genes": 3,
                    "min_cells": 1,
                    "max_cells": 10,
                    "needs_coords": True,
                    "obs_required": [],
                    "obsm_required": ["spatial_3D"],
                }
            }
        ),
        encoding="utf-8",
    )
    lock = root / "artifacts" / "scorer_lock.json"
    lock.parent.mkdir(parents=True)
    lock.write_text(
        json.dumps(
            {
                "schema": "test-lock",
                "contract_snapshot": {
                    "board_index": {"path": "data/gene_panel/index.json"}
                },
            }
        ),
        encoding="utf-8",
    )
    return root, lock, genes


def _write_parent(path: Path, genes: list[str]) -> None:
    matrix = np.array([[0.0, 1.0, 2.0], [2.0, 0.5, 0.0]], dtype=np.float32)
    obj = ad.AnnData(
        X=matrix,
        obs=pd.DataFrame({"celltype": ["a", "b"]}, index=["c1", "c2"]),
        var=pd.DataFrame(index=genes),
        obsm={
            "spatial_3D": np.array(
                [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float32
            )
        },
        uns={
            "ve_contract": {
                "schema": "ve.contract.v1",
                "normalization": "log_normalized",
            }
        },
    )
    obj.write_h5ad(path)


def test_validate_h5ad_contract_passes_and_does_not_mutate_input(tmp_path: Path) -> None:
    _, lock, genes = _fixture_root(tmp_path)
    candidate = tmp_path / "candidate.h5ad"
    _write_parent(candidate, genes)
    before = _sha256(candidate)

    report = validate_h5ad_contract(
        candidate,
        task="T3",
        board="gata4",
        scorer_lock=lock,
        parent_path=candidate,
        parent_sha256=before,
    )

    assert report["status"] == "PASS"
    assert report["valid"] is True
    assert report["checks"]["gene_order"]["exact_order"] is True
    assert report["checks"]["serialisation_round_trip"]["status"] == "PASS"
    assert _sha256(candidate) == before


def test_validate_h5ad_contract_rejects_gene_order_and_negative_values(
    tmp_path: Path,
) -> None:
    _, lock, genes = _fixture_root(tmp_path)
    parent = tmp_path / "parent.h5ad"
    candidate = tmp_path / "invalid.h5ad"
    _write_parent(parent, genes)
    obj = ad.AnnData(
        X=np.array([[0.0, -1.0, 2.0]], dtype=np.float32),
        var=pd.DataFrame(index=list(reversed(genes))),
        obsm={"spatial_3D": np.zeros((1, 3), dtype=np.float32)},
    )
    obj.write_h5ad(candidate)

    report = validate_h5ad_contract(
        candidate,
        task="T3",
        board="gata4",
        scorer_lock=lock,
        parent_path=parent,
        parent_sha256=_sha256(parent),
    )

    assert report["status"] == "FAIL"
    assert any("var_names" in error for error in report["errors"])
    assert any("negative" in error for error in report["errors"])


def test_validate_h5ad_contract_rejects_missing_required_spatial_coordinates(
    tmp_path: Path,
) -> None:
    _, lock, genes = _fixture_root(tmp_path)
    parent = tmp_path / "parent.h5ad"
    candidate = tmp_path / "missing-spatial.h5ad"
    _write_parent(parent, genes)
    obj = ad.AnnData(
        X=np.zeros((1, 3), dtype=np.float32),
        var=pd.DataFrame(index=genes),
    )
    obj.write_h5ad(candidate)

    report = validate_h5ad_contract(
        candidate,
        task="T3",
        board="gata4",
        scorer_lock=lock,
        parent_path=parent,
        parent_sha256=_sha256(parent),
    )

    assert report["status"] == "FAIL"
    assert any("required obsm" in error for error in report["errors"])


def test_write_candidate_is_atomic_preserves_parent_and_validates_roundtrip(
    tmp_path: Path,
) -> None:
    _, lock, genes = _fixture_root(tmp_path)
    parent = tmp_path / "parent.h5ad"
    output = tmp_path / "nested" / "candidate.h5ad"
    _write_parent(parent, genes)
    before = _sha256(parent)
    expression = np.array([[0.25, 1.0, 2.0], [2.0, 0.5, 0.0]], dtype=np.float64)

    write_candidate_from_parent(
        parent_path=parent,
        output_path=output,
        expression=expression,
        row_names=["c1", "c2"],
        normalization="log_normalized",
        metadata_updates={"route": "preflight"},
        parent_sha256=_sha256(parent),
    )

    assert output.exists()
    assert _sha256(parent) == before
    report = validate_h5ad_contract(
        output,
        task="T3",
        board="gata4",
        scorer_lock=lock,
        parent_path=parent,
        parent_sha256=_sha256(parent),
    )
    assert report["status"] == "PASS"
    written = ad.read_h5ad(output)
    assert written.uns["route"] == "preflight"
    np.testing.assert_array_equal(written.X, expression.astype(np.float32))
    np.testing.assert_array_equal(written.obsm["spatial_3D"], np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float32))

    with pytest.raises(FileExistsError):
        write_candidate_from_parent(
            parent_path=parent,
            output_path=output,
            parent_sha256=_sha256(parent),
        )


def test_write_candidate_rejects_invalid_expression_without_output(tmp_path: Path) -> None:
    _, _, genes = _fixture_root(tmp_path)
    parent = tmp_path / "parent.h5ad"
    output = tmp_path / "candidate.h5ad"
    _write_parent(parent, genes)

    with pytest.raises(ValueError, match="non-negative"):
        write_candidate_from_parent(
            parent_path=parent,
            output_path=output,
            expression=np.array([[0.0, -1.0, 0.0], [0.0, 0.0, 0.0]]),
            row_names=["c1", "c2"],
            normalization="log_normalized",
            parent_sha256=_sha256(parent),
        )
    assert not output.exists()


def test_validate_h5ad_contract_rejects_parent_row_permutation(tmp_path: Path) -> None:
    _, lock, genes = _fixture_root(tmp_path)
    parent = tmp_path / "parent.h5ad"
    candidate = tmp_path / "permuted.h5ad"
    _write_parent(parent, genes)
    source = ad.read_h5ad(parent)
    source = source[[1, 0]].copy()
    source.write_h5ad(candidate)

    report = validate_h5ad_contract(
        candidate,
        task="T3",
        board="gata4",
        scorer_lock=lock,
        parent_path=parent,
        parent_sha256=_sha256(parent),
    )

    assert report["status"] == "FAIL"
    assert any("obs_names/order" in error for error in report["errors"])
    assert any("spatial_3D" in error for error in report["errors"])


def test_write_candidate_requires_row_identity_for_replacements(tmp_path: Path) -> None:
    _, _, genes = _fixture_root(tmp_path)
    parent = tmp_path / "parent.h5ad"
    output = tmp_path / "candidate.h5ad"
    _write_parent(parent, genes)

    with pytest.raises(ValueError, match="row_names"):
        write_candidate_from_parent(
            parent_path=parent,
            output_path=output,
            expression=np.zeros((2, 3), dtype=np.float32),
            normalization="log_normalized",
            parent_sha256=_sha256(parent),
        )
    assert not output.exists()


def test_write_candidate_publication_is_no_clobber_under_race(tmp_path: Path) -> None:
    _, _, genes = _fixture_root(tmp_path)
    parent = tmp_path / "parent.h5ad"
    output = tmp_path / "candidate.h5ad"
    _write_parent(parent, genes)
    expression = np.zeros((2, 3), dtype=np.float32)

    def attempt() -> str:
        try:
            write_candidate_from_parent(
                parent_path=parent,
                output_path=output,
                expression=expression,
                row_names=["c1", "c2"],
                normalization="log_normalized",
                parent_sha256=_sha256(parent),
            )
        except FileExistsError:
            return "exists"
        return "published"

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = sorted(executor.map(lambda _: attempt(), range(2)))

    assert outcomes == ["exists", "published"]
    assert output.exists()
    assert not list(tmp_path.glob(".candidate.h5ad.*"))
