#!/usr/bin/env python3
"""Source-only T2 J1 expression/coordinate pairing for B1-A4.

The runner learns a small source-only latent neighbourhood model and changes
only the hard row-to-coordinate permutation of an existing T2 submission.
It never accepts a target path and never changes expression values, cell count,
gene order, or coordinate values.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

import anndata as ad
import numpy as np
from scipy import sparse
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge
from sklearn.neighbors import NearestNeighbors

try:
    from .t2_baseline import load_t2_input, read_panel
except ImportError:  # direct ``python scripts/t2_j1_pairing.py`` execution
    from t2_baseline import load_t2_input, read_panel


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ATOM_ID = "B1-A4"
SCORER_VERSION = "veckit@46d41e63f42a9aab815db20b742feeccd249cb17"
SEED = 20260827
PCA_COMPONENTS = 30
K_NEIGHBOURS = 15
PROPOSALS_PER_NODE = 10
LANE_LATENT = "L1_LATENT_KNN10"
LANE_STATE = "L2_STATE_HASH10"
LANES = (LANE_LATENT, LANE_STATE)
BOARD_ORDER = (
    "T2_embryo_val_interp",
    "T2_heart_val_interp",
    "T2_heart_val_extrap",
)


@dataclass(frozen=True)
class BoardSpec:
    slug: str
    official_key: str
    tissue: str
    panel: str
    target_stage: float
    source_stages: tuple[tuple[float, str], ...]
    parent_submission: str
    root_submission: str
    parent_sha256: str
    root_sha256: str
    min_cells: int
    max_cells: int
    submission_paths: tuple[str, str]
    score_proxy: str


BOARD_SPECS: dict[str, BoardSpec] = {
    "T2_embryo_val_interp": BoardSpec(
        slug="T2_embryo_val_interp",
        official_key="T2:embryo:val_interp",
        tissue="embryo",
        panel="data/gene_panel/T2__embryo__val_interp.genes.txt",
        target_stage=7.5,
        source_stages=(
            (6.75, "data/E6.75.h5ad"),
            (7.25, "data/E7.25.h5ad"),
            (8.0, "data/E8.0.h5ad"),
        ),
        parent_submission=(
            "submissions/candidates/T2_embryo_val_interp/"
            "v0002_g1_formal_log_rms/submission.h5ad"
        ),
        root_submission="submissions/scored/baseline-001/T2_embryo_val_interp/submission.h5ad",
        parent_sha256="392c470e4af35797ad27c100e773c1a7695c989baed95c911fceb0b5d7965fd4",
        root_sha256="ee1549ba74d9c2bb545140230c88539d941b4c206241ef133872067a0820bcf8",
        min_cells=583,
        max_cells=5000,
        submission_paths=(
            "submissions/candidates/T2_embryo_val_interp/"
            "v0004_b1_a4_latent_knn10/submission.h5ad",
            "submissions/candidates/T2_embryo_val_interp/"
            "v0005_b1_a4_state_hash10/submission.h5ad",
        ),
        score_proxy="T2_embryo_interp_proxy",
    ),
    "T2_heart_val_interp": BoardSpec(
        slug="T2_heart_val_interp",
        official_key="T2:heart:val_interp",
        tissue="heart",
        panel="data/gene_panel/T2__heart__val_interp.genes.txt",
        target_stage=8.5,
        source_stages=(
            (8.25, "data/E8.25_late.h5ad"),
            (8.75, "data/E8.75.h5ad"),
            (9.5, "data/E9.5.h5ad"),
        ),
        parent_submission=(
            "submissions/candidates/T2_heart_val_interp/"
            "v0003_g1_formal_log_rms/submission.h5ad"
        ),
        root_submission="submissions/scored/submission-002/T2_heart_val_interp/submission.h5ad",
        parent_sha256="f8a4da854bf9e01e25503b59fddb70bae242c0382b38cc0f3984bf80cd751424",
        root_sha256="402b0a893672e9ce267af0a39bcdf8e00975cdf3dc7dca00fab80858ae2d08b4",
        min_cells=1000,
        max_cells=17616,
        submission_paths=(
            "submissions/candidates/T2_heart_val_interp/"
            "v0005_b1_a4_latent_knn10/submission.h5ad",
            "submissions/candidates/T2_heart_val_interp/"
            "v0006_b1_a4_state_hash10/submission.h5ad",
        ),
        score_proxy="T2_heart_interp_proxy",
    ),
    "T2_heart_val_extrap": BoardSpec(
        slug="T2_heart_val_extrap",
        official_key="T2:heart:val_extrap",
        tissue="heart",
        panel="data/gene_panel/T2__heart__val_extrap.genes.txt",
        target_stage=10.5,
        source_stages=(
            (8.25, "data/E8.25_late.h5ad"),
            (8.75, "data/E8.75.h5ad"),
            (9.5, "data/E9.5.h5ad"),
        ),
        parent_submission="submissions/scored/baseline-001/T2_heart_val_extrap/submission.h5ad",
        root_submission="submissions/scored/baseline-001/T2_heart_val_extrap/submission.h5ad",
        parent_sha256="f30beba62da673bb4c980d92eec2bc9ea03696e5c2b65414307c2e0402bd7504",
        root_sha256="f30beba62da673bb4c980d92eec2bc9ea03696e5c2b65414307c2e0402bd7504",
        min_cells=1000,
        max_cells=25179,
        submission_paths=(
            "submissions/candidates/T2_heart_val_extrap/"
            "v0004_b1_a4_latent_knn10/submission.h5ad",
            "submissions/candidates/T2_heart_val_extrap/"
            "v0005_b1_a4_state_hash10/submission.h5ad",
        ),
        score_proxy="T2_heart_extrap_proxy",
    ),
}


@dataclass
class TissueModel:
    tissue: str
    panel_path: Path
    pca: PCA
    score_center: np.ndarray
    score_scale: np.ndarray
    regressor: Ridge
    time_center: float
    time_scale: float
    n_fit_per_stage: int
    stage_records: list[dict[str, Any]]

    @property
    def n_components(self) -> int:
        return int(self.pca.n_components_)

    def encode(self, X: Any) -> np.ndarray:
        dense = _dense_float32(X)
        scores = np.asarray(self.pca.transform(dense), dtype=np.float64)
        return (scores - self.score_center) / self.score_scale

    def predict_neighbourhood(self, z: np.ndarray, target_stage: float) -> np.ndarray:
        tau = (float(target_stage) - self.time_center) / self.time_scale
        features = np.column_stack(
            (z, np.full(len(z), tau, dtype=np.float64))
        )
        result = np.asarray(self.regressor.predict(features), dtype=np.float64)
        if result.shape != z.shape or not np.isfinite(result).all():
            raise ValueError("Ridge neighbourhood prediction is invalid")
        return result


def _resolve(project_root: Path, path: str | Path) -> Path:
    value = Path(path)
    return value if value.is_absolute() else Path(project_root) / value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _matrix_digest(value: Any) -> str:
    digest = hashlib.sha256()
    if sparse.issparse(value):
        matrix = value.tocsr(copy=True)
        matrix.sum_duplicates()
        matrix.sort_indices()
        digest.update(b"sparse_csr")
        digest.update(str(matrix.shape).encode("utf-8"))
        digest.update(matrix.dtype.str.encode("utf-8"))
        for part in (matrix.indptr, matrix.indices, matrix.data):
            digest.update(np.ascontiguousarray(part).tobytes(order="C"))
    else:
        array = np.ascontiguousarray(np.asarray(value))
        digest.update(b"dense")
        digest.update(str(array.shape).encode("utf-8"))
        digest.update(array.dtype.str.encode("utf-8"))
        digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def _row_multiset_digest(value: Any) -> str:
    array = _dense_float32(value)
    row_hashes = sorted(
        hashlib.sha256(np.ascontiguousarray(row).tobytes(order="C")).hexdigest()
        for row in array
    )
    return hashlib.sha256("\n".join(row_hashes).encode("utf-8")).hexdigest()


def _names_digest(names: Iterable[Any]) -> str:
    return hashlib.sha256(
        "\n".join(str(name) for name in names).encode("utf-8")
    ).hexdigest()


def _dense_float32(value: Any) -> np.ndarray:
    if sparse.issparse(value):
        value = value.toarray()
    result = np.asarray(value, dtype=np.float32)
    if result.ndim != 2 or not np.isfinite(result).all() or (result < 0).any():
        raise ValueError("expression matrix must be finite, non-negative and 2D")
    return result


def _coords(adata: ad.AnnData, path: Path) -> np.ndarray:
    if "spatial_3D" not in adata.obsm:
        raise ValueError(f"{path}: missing obsm['spatial_3D']")
    value = adata.obsm["spatial_3D"]
    if sparse.issparse(value):
        value = value.toarray()
    result = np.asarray(value, dtype=np.float64)
    if result.ndim != 2 or result.shape[0] != adata.n_obs or result.shape[1] < 3:
        raise ValueError(f"{path}: invalid spatial_3D shape {result.shape}")
    result = result[:, :3]
    if not np.isfinite(result).all():
        raise ValueError(f"{path}: spatial_3D is not finite")
    if len(np.unique(result, axis=0)) != len(result):
        raise ValueError(f"{path}: duplicate spatial_3D points are unsupported")
    return result


def _labels(adata: ad.AnnData, path: Path) -> np.ndarray:
    if "celltype" not in adata.obs:
        raise ValueError(f"{path}: obs['celltype'] is required for J1")
    values = adata.obs["celltype"]
    if values.isna().any():
        raise ValueError(f"{path}: obs['celltype'] contains missing values")
    result = np.asarray(values.astype(str), dtype=str)
    if result.ndim != 1 or len(result) != adata.n_obs or (result == "").any():
        raise ValueError(f"{path}: invalid celltype values")
    return result


def _spatial_knn(coords: np.ndarray, k: int = K_NEIGHBOURS) -> np.ndarray:
    if len(coords) < k:
        raise ValueError(f"need at least {k} cells for the fixed spatial graph")
    model = NearestNeighbors(n_neighbors=k, algorithm="auto").fit(coords)
    _, indices = model.kneighbors(coords, return_distance=True)
    indices = np.asarray(indices, dtype=np.int64)
    if indices.shape != (len(coords), k) or not np.array_equal(indices[:, 0], np.arange(len(coords))):
        raise ValueError("spatial graph is not the expected self-inclusive kNN graph")
    return indices


def _knn_fingerprint(coords: np.ndarray, k: int = K_NEIGHBOURS) -> str:
    return _matrix_digest(_spatial_knn(coords, k))


def _matrix_equal(left: Any, right: Any) -> bool:
    if sparse.issparse(left) or sparse.issparse(right):
        if not sparse.issparse(left) or not sparse.issparse(right):
            return False
        a = left.tocsr(copy=True)
        b = right.tocsr(copy=True)
        a.sum_duplicates()
        b.sum_duplicates()
        a.sort_indices()
        b.sort_indices()
        return (
            a.shape == b.shape
            and a.dtype == b.dtype
            and np.array_equal(a.indptr, b.indptr)
            and np.array_equal(a.indices, b.indices)
            and np.array_equal(a.data, b.data)
        )
    return np.array_equal(np.asarray(left), np.asarray(right))


def _take_rows(value: Any, indices: np.ndarray) -> Any:
    if sparse.issparse(value):
        return value[indices].copy()
    return np.array(np.asarray(value)[indices], copy=True)


def _balanced_indices(labels: np.ndarray, n_cells: int, seed: int) -> np.ndarray:
    labels = np.asarray(labels, dtype=str)
    if n_cells < 1 or n_cells > len(labels):
        raise ValueError("invalid balanced sample size")
    if n_cells == len(labels):
        return np.arange(len(labels), dtype=np.int64)
    groups = sorted(np.unique(labels).tolist())
    group_indices = {group: np.flatnonzero(labels == group) for group in groups}
    counts = np.asarray([len(group_indices[group]) for group in groups], dtype=np.float64)
    exact = counts * float(n_cells) / float(len(labels))
    take = np.floor(exact).astype(np.int64)
    remainder = int(n_cells - int(take.sum()))
    fractions = exact - take
    order = sorted(range(len(groups)), key=lambda i: (-fractions[i], groups[i]))
    for index in order[:remainder]:
        take[index] += 1
    rng = np.random.default_rng(int(seed))
    selected: list[np.ndarray] = []
    for index, group in enumerate(groups):
        selected.append(
            np.asarray(
                rng.choice(group_indices[group], size=int(take[index]), replace=False),
                dtype=np.int64,
            )
        )
    return np.sort(np.concatenate(selected).astype(np.int64))


def _derived_seed(seed: int, *parts: Any) -> int:
    text = "|".join([str(seed), *(str(part) for part in parts)])
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "little") % (2**32)


def _stage_infos(tissue: str) -> list[tuple[float, str]]:
    values = [
        spec.source_stages
        for spec in BOARD_SPECS.values()
        if spec.tissue == tissue
    ]
    if not values or any(item != values[0] for item in values[1:]):
        raise ValueError(f"inconsistent source-stage definition for {tissue}")
    return list(values[0])


def fit_tissue_model(
    tissue: str,
    *,
    project_root: Path = PROJECT_ROOT,
    seed: int = SEED,
) -> TissueModel:
    if tissue not in {"embryo", "heart"}:
        raise ValueError(f"unsupported tissue {tissue!r}")
    board = next(spec for spec in BOARD_SPECS.values() if spec.tissue == tissue)
    project_root = Path(project_root).resolve()
    panel_path = _resolve(project_root, board.panel)
    panel = read_panel(panel_path)
    loaded: list[tuple[float, Path, ad.AnnData, np.ndarray]] = []
    for stage, relative in _stage_infos(tissue):
        path = _resolve(project_root, relative)
        source = load_t2_input(path, panel_path)
        labels = _labels(source, path)
        _coords(source, path)
        if [str(name) for name in source.var_names] != panel:
            raise ValueError(f"{path}: panel order mismatch after loading")
        loaded.append((float(stage), path, source, labels))
    n_fit = min(int(source.n_obs) for _, _, source, _ in loaded)
    if n_fit < PCA_COMPONENTS + 1:
        raise ValueError("not enough stage-balanced cells for the fixed PCA")

    fit_parts: list[np.ndarray] = []
    stage_records: list[dict[str, Any]] = []
    selected_indices: dict[str, np.ndarray] = {}
    for stage, path, source, labels in loaded:
        indices = _balanced_indices(
            labels,
            n_fit,
            _derived_seed(seed, tissue, stage, "fit-selection"),
        )
        selected_indices[str(path)] = indices
        fit_parts.append(_dense_float32(source.X)[indices])
        stage_records.append(
            {
                "stage": float(stage),
                "path": path.resolve().relative_to(project_root).as_posix(),
                "n_obs": int(source.n_obs),
                "n_selected": int(len(indices)),
                "selected_indices_sha256": _matrix_digest(indices),
                "selected_obs_names_sha256": _names_digest(source.obs_names[indices]),
            }
        )

    fit_matrix = np.concatenate(fit_parts, axis=0)
    pca = PCA(
        n_components=min(PCA_COMPONENTS, fit_matrix.shape[1], fit_matrix.shape[0] - 1),
        svd_solver="randomized",
        random_state=int(seed),
    ).fit(fit_matrix)
    fit_scores = np.asarray(pca.transform(fit_matrix), dtype=np.float64)
    score_center = fit_scores.mean(axis=0)
    score_scale = fit_scores.std(axis=0)
    if not np.isfinite(score_scale).all() or (score_scale <= 1e-12).any():
        raise ValueError("PCA score has a zero or non-finite standard deviation")

    times = np.asarray([item[0] for item in loaded], dtype=np.float64)
    time_center = float(times.mean())
    time_scale = float(times.std())
    if not np.isfinite(time_scale) or time_scale <= 0:
        raise ValueError("observed stage times must have positive spread")

    design_parts: list[np.ndarray] = []
    target_parts: list[np.ndarray] = []
    for stage, path, source, _ in loaded:
        z = (
            np.asarray(pca.transform(_dense_float32(source.X)), dtype=np.float64)
            - score_center
        ) / score_scale
        coords = _coords(source, path)
        graph = _spatial_knn(coords)
        neighbourhood = z[graph].mean(axis=1)
        indices = selected_indices[str(path)]
        tau = (float(stage) - time_center) / time_scale
        design_parts.append(
            np.column_stack((z[indices], np.full(len(indices), tau, dtype=np.float64)))
        )
        target_parts.append(neighbourhood[indices])

    design = np.concatenate(design_parts, axis=0)
    targets = np.concatenate(target_parts, axis=0)
    regressor = Ridge(
        alpha=1.0,
        fit_intercept=True,
        solver="cholesky",
    ).fit(design, targets)
    if not np.isfinite(regressor.coef_).all() or not np.isfinite(regressor.intercept_).all():
        raise ValueError("Ridge fit produced non-finite coefficients")

    for _, _, source, _ in loaded:
        del source
    return TissueModel(
        tissue=tissue,
        panel_path=panel_path,
        pca=pca,
        score_center=np.asarray(score_center, dtype=np.float64),
        score_scale=np.asarray(score_scale, dtype=np.float64),
        regressor=regressor,
        time_center=time_center,
        time_scale=time_scale,
        n_fit_per_stage=n_fit,
        stage_records=stage_records,
    )


def save_tissue_model(model: TissueModel, output_dir: Path, project_root: Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    arrays_path = output_dir / f"{model.tissue}_model.npz"
    np.savez_compressed(
        arrays_path,
        pca_components=model.pca.components_,
        pca_mean=model.pca.mean_,
        pca_explained_variance=model.pca.explained_variance_,
        score_center=model.score_center,
        score_scale=model.score_scale,
        ridge_coef=model.regressor.coef_,
        ridge_intercept=model.regressor.intercept_,
        time_center=np.asarray([model.time_center]),
        time_scale=np.asarray([model.time_scale]),
    )
    selection_path = output_dir / f"{model.tissue}_fit_selection.tsv"
    with selection_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(
            ["stage", "path", "n_obs", "n_selected", "selected_indices_sha256", "selected_obs_names_sha256"]
        )
        for record in model.stage_records:
            writer.writerow(
                [
                    record["stage"],
                    record["path"],
                    record["n_obs"],
                    record["n_selected"],
                    record["selected_indices_sha256"],
                    record["selected_obs_names_sha256"],
                ]
            )
    metadata = {
        "atom_id": ATOM_ID,
        "tissue": model.tissue,
        "panel": model.panel_path.resolve().relative_to(project_root).as_posix(),
        "panel_gene_count": len(read_panel(model.panel_path)),
        "n_components": model.n_components,
        "pca_solver": "randomized",
        "ridge": {"alpha": 1.0, "fit_intercept": True, "solver": "cholesky"},
        "time_center": model.time_center,
        "time_scale": model.time_scale,
        "n_fit_per_stage": model.n_fit_per_stage,
        "stage_records": model.stage_records,
        "target_used": False,
        "arrays_file": arrays_path.resolve().relative_to(project_root).as_posix(),
        "arrays_sha256": sha256_file(arrays_path),
        "selection_file": selection_path.resolve().relative_to(project_root).as_posix(),
        "selection_sha256": sha256_file(selection_path),
    }
    metadata_path = output_dir / f"{model.tissue}_model.json"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return metadata


def _latent_proposals(z: np.ndarray, limit: int = PROPOSALS_PER_NODE) -> list[np.ndarray]:
    n = len(z)
    if n < 2:
        return [np.empty(0, dtype=np.int64) for _ in range(n)]
    count = min(n, limit + 1)
    model = NearestNeighbors(n_neighbors=count, algorithm="auto").fit(z)
    distances, indices = model.kneighbors(z, return_distance=True)
    result: list[np.ndarray] = []
    for row in range(n):
        ordered = sorted(
            (
                (float(distance), int(candidate))
                for distance, candidate in zip(distances[row], indices[row])
                if int(candidate) != row
            ),
            key=lambda item: (item[0], item[1]),
        )
        result.append(np.asarray([candidate for _, candidate in ordered[:limit]], dtype=np.int64))
    return result


def _state_hash_proposals(
    obs_names: Sequence[Any], labels: np.ndarray, seed: int, limit: int = PROPOSALS_PER_NODE
) -> list[np.ndarray]:
    labels = np.asarray(labels, dtype=str)
    keys = [
        hashlib.sha256(f"{seed}|{name}".encode("utf-8")).hexdigest()
        for name in obs_names
    ]
    result = [np.empty(0, dtype=np.int64) for _ in range(len(labels))]
    for state in sorted(np.unique(labels).tolist()):
        members = [int(index) for index in np.flatnonzero(labels == state)]
        members.sort(key=lambda index: (keys[index], index))
        if len(members) < 2:
            continue
        for position, row in enumerate(members):
            candidates: list[int] = []
            for distance in range(1, limit // 2 + 1):
                candidates.append(members[(position - distance) % len(members)])
            for distance in range(1, limit - len(candidates) + 1):
                candidates.append(members[(position + distance) % len(members)])
            result[row] = np.asarray(
                list(dict.fromkeys(candidate for candidate in candidates if candidate != row))[:limit],
                dtype=np.int64,
            )
    return result


def _reverse_neighbourhood(graph: np.ndarray) -> list[np.ndarray]:
    reverse: list[list[int]] = [[] for _ in range(len(graph))]
    for center, neighbours in enumerate(graph):
        for node in neighbours:
            reverse[int(node)].append(int(center))
    return [np.asarray(values, dtype=np.int64) for values in reverse]


def _swap_delta(
    *,
    z: np.ndarray,
    desired: np.ndarray,
    graph: np.ndarray,
    reverse: list[np.ndarray],
    assignment: np.ndarray,
    neighbourhood: np.ndarray,
    residual: np.ndarray,
    node_a: int,
    node_b: int,
) -> tuple[float, np.ndarray, np.ndarray, np.ndarray]:
    affected = np.unique(
        np.concatenate((reverse[node_a], reverse[node_b], np.asarray([node_a, node_b], dtype=np.int64)))
    )
    donor_a = int(assignment[node_a])
    donor_b = int(assignment[node_b])
    delta_z = z[donor_b] - z[donor_a]
    contains_a = np.any(graph[affected] == node_a, axis=1)
    contains_b = np.any(graph[affected] == node_b, axis=1)
    updated_neighbourhood = neighbourhood[affected] + (
        contains_a.astype(np.float64) - contains_b.astype(np.float64)
    )[:, None] * delta_z / float(graph.shape[1])
    updated_desired = desired[assignment[affected]].copy()
    updated_desired[affected == node_a] = desired[donor_b]
    updated_desired[affected == node_b] = desired[donor_a]
    updated_residual = np.sum((updated_neighbourhood - updated_desired) ** 2, axis=1)
    delta = float(np.sum(updated_residual) - np.sum(residual[affected]))
    return delta, affected, updated_neighbourhood, updated_residual


def optimize_pairing(
    z: np.ndarray,
    desired: np.ndarray,
    coords: np.ndarray,
    *,
    lane: str,
    labels: np.ndarray,
    obs_names: Sequence[Any],
    seed: int = SEED,
) -> dict[str, Any]:
    if lane not in LANES:
        raise ValueError(f"unsupported lane {lane!r}")
    z = np.asarray(z, dtype=np.float64)
    desired = np.asarray(desired, dtype=np.float64)
    if z.ndim != 2 or desired.shape != z.shape or not np.isfinite(z).all() or not np.isfinite(desired).all():
        raise ValueError("latent and desired arrays must have the same finite 2D shape")
    if len(coords) != len(z) or len(labels) != len(z) or len(obs_names) != len(z):
        raise ValueError("pairing inputs have inconsistent row counts")
    graph = _spatial_knn(np.asarray(coords, dtype=np.float64))
    reverse = _reverse_neighbourhood(graph)
    proposals = (
        _latent_proposals(z)
        if lane == LANE_LATENT
        else _state_hash_proposals(obs_names, labels, seed)
    )
    assignment = np.arange(len(z), dtype=np.int64)
    inverse = assignment.copy()
    neighbourhood = z[graph].mean(axis=1)
    residual = np.sum((neighbourhood - desired[assignment]) ** 2, axis=1)
    initial_sum = float(np.sum(residual))
    visit_order = np.lexsort((np.arange(len(z), dtype=np.int64), -residual))
    proposal_count = 0
    accepted = 0
    accepted_deltas: list[float] = []
    for node_a_raw in visit_order:
        node_a = int(node_a_raw)
        donor_a = int(assignment[node_a])
        best: tuple[float, int, np.ndarray, np.ndarray, np.ndarray] | None = None
        for donor_b_raw in proposals[donor_a]:
            donor_b = int(donor_b_raw)
            node_b = int(inverse[donor_b])
            if node_b == node_a:
                continue
            proposal_count += 1
            delta, affected, updated_m, updated_r = _swap_delta(
                z=z,
                desired=desired,
                graph=graph,
                reverse=reverse,
                assignment=assignment,
                neighbourhood=neighbourhood,
                residual=residual,
                node_a=node_a,
                node_b=node_b,
            )
            if best is None or delta < best[0] or (delta == best[0] and donor_b < best[1]):
                best = (delta, donor_b, affected, updated_m, updated_r)
        if best is None:
            continue
        old_sum = float(np.sum(residual))
        tolerance = 1e-12 * max(1.0, abs(old_sum))
        if best[0] >= -tolerance:
            continue
        donor_b = best[1]
        node_b = int(inverse[donor_b])
        donor_a = int(assignment[node_a])
        assignment[node_a], assignment[node_b] = donor_b, donor_a
        inverse[donor_b], inverse[donor_a] = node_a, node_b
        neighbourhood[best[2]] = best[3]
        residual[best[2]] = best[4]
        accepted += 1
        accepted_deltas.append(float(best[0]))

    final_neighbourhood = z[assignment[graph]].mean(axis=1)
    final_residual = np.sum((final_neighbourhood - desired[assignment]) ** 2, axis=1)
    final_sum = float(np.sum(final_residual))
    if not np.array_equal(np.sort(assignment), np.arange(len(z), dtype=np.int64)):
        raise AssertionError("pairing assignment is not a bijection")
    if not np.allclose(final_sum, float(np.sum(residual)), rtol=2e-10, atol=2e-10):
        raise AssertionError("incremental pairing objective disagrees with full recomputation")
    if proposal_count > PROPOSALS_PER_NODE * len(z):
        raise AssertionError("pairing proposal budget exceeded")
    return {
        "lane_id": lane,
        "permutation": assignment,
        "inverse_permutation": inverse,
        "initial_objective_sum": initial_sum,
        "final_objective_sum": final_sum,
        "initial_objective": initial_sum / len(z),
        "final_objective": final_sum / len(z),
        "accepted_swaps": accepted,
        "proposal_count": proposal_count,
        "proposal_limit": PROPOSALS_PER_NODE * len(z),
        "accepted_delta_sum": float(np.sum(accepted_deltas)) if accepted_deltas else 0.0,
        "graph_k": K_NEIGHBOURS,
        "target_used": False,
    }


def _assert_parent_lineage(
    parent: ad.AnnData,
    root: ad.AnnData,
    parent_path: Path,
    root_path: Path,
) -> dict[str, Any]:
    parent_coords = _coords(parent, parent_path)
    root_coords = _coords(root, root_path)
    if parent.n_obs != root.n_obs or parent.n_vars != root.n_vars:
        raise ValueError("immediate parent and pre-A1 root have different shapes")
    if list(map(str, parent.obs_names)) != list(map(str, root.obs_names)):
        raise ValueError("immediate parent and root obs order differ")
    if list(map(str, parent.var_names)) != list(map(str, root.var_names)):
        raise ValueError("immediate parent and root var order differ")
    if not _matrix_equal(parent.X, root.X):
        raise ValueError("immediate parent and root expression matrices differ")
    if _knn_fingerprint(parent_coords) != _knn_fingerprint(root_coords):
        raise ValueError("immediate parent and root 15-NN graphs differ")
    return {
        "root_expression_hash": _matrix_digest(root.X),
        "parent_expression_hash": _matrix_digest(parent.X),
        "root_coordinate_hash": _matrix_digest(root_coords),
        "parent_coordinate_hash": _matrix_digest(parent_coords),
        "root_knn15_hash": _knn_fingerprint(root_coords),
        "parent_knn15_hash": _knn_fingerprint(parent_coords),
        "x_equal": True,
        "obs_order_equal": True,
        "var_order_equal": True,
        "knn15_equal": True,
    }


def _write_reordered(
    parent: ad.AnnData,
    permutation: np.ndarray,
    output_path: Path,
    *,
    metadata: dict[str, Any],
) -> None:
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite candidate {output_path}")
    permutation = np.asarray(permutation, dtype=np.int64)
    if not np.array_equal(np.sort(permutation), np.arange(parent.n_obs, dtype=np.int64)):
        raise ValueError("cannot write a non-bijective permutation")
    if len(parent.obsp):
        raise ValueError("unknown pairwise obsp fields require explicit row semantics")
    known_obsm = {"spatial_2D", "spatial_3D"}
    unknown_obsm = set(parent.obsm.keys()) - known_obsm
    if unknown_obsm:
        raise ValueError(f"unknown obsm fields cannot be classified safely: {sorted(unknown_obsm)}")

    output = parent.copy()
    output.X = _take_rows(parent.X, permutation)
    donor_obs = parent.obs.iloc[permutation].copy()
    donor_obs.index = parent.obs_names.copy()
    output.obs = donor_obs
    for key in parent.layers.keys():
        layer = parent.layers[key]
        if getattr(layer, "shape", (None,))[0] != parent.n_obs:
            raise ValueError(f"layer {key!r} is not row-aligned")
        output.layers[key] = _take_rows(layer, permutation)
    if parent.raw is not None:
        raw = parent.raw.to_adata()[permutation].copy()
        raw.obs_names = parent.obs_names.copy()
        output.raw = raw
    for key in parent.obsm.keys():
        output.obsm[key] = parent.obsm[key].copy()
    output.uns["ve_j1_pairing"] = metadata
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output.write_h5ad(output_path)


def _check_output(
    parent: ad.AnnData,
    candidate: ad.AnnData,
    permutation: np.ndarray,
    parent_path: Path,
    candidate_path: Path,
) -> dict[str, Any]:
    permutation = np.asarray(permutation, dtype=np.int64)
    expression_exact = _matrix_equal(candidate.X, _take_rows(parent.X, permutation))
    layers_exact = True
    for key in parent.layers.keys():
        layers_exact = layers_exact and key in candidate.layers and _matrix_equal(
            candidate.layers[key], _take_rows(parent.layers[key], permutation)
        )
    raw_exact = True
    if parent.raw is not None:
        raw_exact = candidate.raw is not None and _matrix_equal(
            candidate.raw.X,
            _take_rows(parent.raw.X, permutation),
        )
    obs_exact = list(map(str, candidate.obs_names)) == list(map(str, parent.obs_names))
    if obs_exact:
        for key in parent.obs.columns:
            if key not in candidate.obs:
                obs_exact = False
                break
            expected = parent.obs[key].iloc[permutation].astype(str).to_numpy()
            actual = candidate.obs[key].astype(str).to_numpy()
            if not np.array_equal(expected, actual):
                obs_exact = False
                break
    coords_exact = True
    for key in parent.obsm.keys():
        coords_exact = coords_exact and key in candidate.obsm and np.array_equal(
            np.asarray(candidate.obsm[key]), np.asarray(parent.obsm[key])
        )
    parent_coords = _coords(parent, parent_path)
    candidate_coords = _coords(candidate, candidate_path)
    checks = {
        "permutation_bijection": np.array_equal(
            np.sort(permutation), np.arange(parent.n_obs, dtype=np.int64)
        ),
        "expression_replay_exact": bool(expression_exact),
        "expression_multiset_base": _row_multiset_digest(parent.X),
        "expression_multiset_candidate": _row_multiset_digest(candidate.X),
        "expression_multiset_exact": _row_multiset_digest(parent.X) == _row_multiset_digest(candidate.X),
        "layers_replay_exact": bool(layers_exact),
        "raw_replay_exact": bool(raw_exact),
        "obs_replay_exact": bool(obs_exact),
        "obs_order_unchanged": list(map(str, candidate.obs_names)) == list(map(str, parent.obs_names)),
        "var_order_unchanged": list(map(str, candidate.var_names)) == list(map(str, parent.var_names)),
        "coordinate_values_exact": bool(coords_exact),
        "coordinate_hash_base": _matrix_digest(parent_coords),
        "coordinate_hash_candidate": _matrix_digest(candidate_coords),
        "spatial_shape_unchanged": list(parent_coords.shape) == list(candidate_coords.shape),
        "knn15_fingerprint_base": _knn_fingerprint(parent_coords),
        "knn15_fingerprint_candidate": _knn_fingerprint(candidate_coords),
        "knn15_exact": _knn_fingerprint(parent_coords) == _knn_fingerprint(candidate_coords),
        "n_obs_unchanged": parent.n_obs == candidate.n_obs,
        "n_vars_unchanged": parent.n_vars == candidate.n_vars,
        "target_used": False,
    }
    if not all(
        checks[key]
        for key in (
            "permutation_bijection",
            "expression_replay_exact",
            "expression_multiset_exact",
            "layers_replay_exact",
            "raw_replay_exact",
            "obs_replay_exact",
            "obs_order_unchanged",
            "var_order_unchanged",
            "coordinate_values_exact",
            "spatial_shape_unchanged",
            "knn15_exact",
            "n_obs_unchanged",
            "n_vars_unchanged",
        )
    ):
        raise AssertionError(f"J1 output invariant failed: {checks}")
    return checks


def _candidate_id(lane: str, board: str) -> str:
    return f"{ATOM_ID}-{lane}-{board}"


def _relative(project_root: Path, path: Path) -> str:
    return path.resolve().relative_to(Path(project_root).resolve()).as_posix()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def _write_json_atomic(path: Path, value: Any) -> None:
    """Write one workflow JSON without exposing a truncated file to readers."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _copy_submission_exclusive(source: Path, destination: Path, project_root: Path) -> None:
    """Copy a candidate with no-clobber semantics and a candidates-only boundary."""
    source = Path(source)
    destination = Path(destination)
    candidates_root = (Path(project_root) / "submissions" / "candidates").resolve()
    resolved_parent = destination.parent.resolve()
    if resolved_parent != candidates_root and candidates_root not in resolved_parent.parents:
        raise ValueError(f"submission destination escapes submissions/candidates: {destination}")
    if destination.is_symlink():
        raise FileExistsError(f"refusing symlink submission destination {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    created = False
    try:
        with source.open("rb") as source_handle, destination.open("xb") as destination_handle:
            created = True
            shutil.copyfileobj(source_handle, destination_handle, length=1024 * 1024)
        shutil.copystat(source, destination)
    except Exception:
        if created and destination.exists() and not destination.is_symlink():
            destination.unlink()
        raise


def run_board_lane(
    *,
    lane: str,
    board: str,
    model: TissueModel,
    output_path: Path,
    project_root: Path = PROJECT_ROOT,
    seed: int = SEED,
) -> dict[str, Any]:
    if board not in BOARD_SPECS:
        raise ValueError(f"unknown board {board!r}")
    spec = BOARD_SPECS[board]
    project_root = Path(project_root).resolve()
    panel_path = _resolve(project_root, spec.panel)
    parent_path = _resolve(project_root, spec.parent_submission)
    root_path = _resolve(project_root, spec.root_submission)
    if not parent_path.exists() or not root_path.exists():
        raise FileNotFoundError("J1 parent or root file is missing")
    parent_sha = sha256_file(parent_path)
    root_sha = sha256_file(root_path)
    if spec.parent_sha256 and parent_sha != spec.parent_sha256:
        raise ValueError(f"{parent_path}: parent SHA256 mismatch")
    if spec.root_sha256 and root_sha != spec.root_sha256:
        raise ValueError(f"{root_path}: root SHA256 mismatch")
    parent = load_t2_input(parent_path, panel_path)
    root = load_t2_input(root_path, panel_path)
    if not spec.min_cells <= parent.n_obs <= spec.max_cells:
        raise ValueError(f"{parent_path}: n_obs outside board limits")
    lineage = _assert_parent_lineage(parent, root, parent_path, root_path)
    labels = _labels(parent, parent_path)
    coords = _coords(parent, parent_path)
    z = model.encode(parent.X)
    desired = model.predict_neighbourhood(z, spec.target_stage)
    pairing = optimize_pairing(
        z,
        desired,
        coords,
        lane=lane,
        labels=labels,
        obs_names=parent.obs_names,
        seed=seed,
    )
    permutation = pairing["permutation"]
    metadata = {
        "atom_id": ATOM_ID,
        "lane_id": lane,
        "board": board,
        "official_board_key": spec.official_key,
        "tissue": spec.tissue,
        "parent_submission": _relative(project_root, parent_path),
        "parent_sha256": parent_sha,
        "root_submission": _relative(project_root, root_path),
        "root_sha256": root_sha,
        "panel": _relative(project_root, panel_path),
        "panel_gene_count": parent.n_vars,
        "target_stage": float(spec.target_stage),
        "source_stages": [float(stage) for stage, _ in spec.source_stages],
        "method": "hard_expression_coordinate_permutation",
        "proposal_rule": "latent_knn10" if lane == LANE_LATENT else "state_hash10",
        "graph_k": K_NEIGHBOURS,
        "seed": int(seed),
        "source_only": True,
        "target_used": False,
        "lineage": lineage,
        "pairing_objective": {
            key: value
            for key, value in pairing.items()
            if key not in {"permutation", "inverse_permutation"}
        },
    }
    _write_reordered(parent, permutation, output_path, metadata=metadata)
    checked = load_t2_input(output_path, panel_path)
    checks = _check_output(parent, checked, permutation, parent_path, output_path)
    pairing_path = output_path.parent / "pairing_objective.json"
    pairing_json = {
        **metadata,
        **{
            key: value
            for key, value in pairing.items()
            if key not in {"permutation", "inverse_permutation"}
        },
        "permutation": permutation.tolist(),
    }
    _write_json(pairing_path, pairing_json)
    permutation_path = output_path.parent / "permutation.npy"
    np.save(permutation_path, permutation.astype(np.int64))
    permutation_tsv = output_path.parent / "permutation.tsv"
    with permutation_tsv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["node_index", "node_obs_name", "donor_index", "donor_obs_name"])
        for node, donor in enumerate(permutation):
            writer.writerow([node, str(parent.obs_names[node]), int(donor), str(parent.obs_names[int(donor)])])

    candidate_id = _candidate_id(lane, board)
    manifest = {
        **metadata,
        "candidate_id": candidate_id,
        "task": "T2",
        "base_submission": _relative(project_root, parent_path),
        "final_candidate": True,
        "score_required": True,
        "attempt_id": None,
        "output_file": _relative(project_root, output_path),
        "submission_file": None,
        "sha256": sha256_file(output_path),
        "n_obs": int(checked.n_obs),
        "n_vars": int(checked.n_vars),
        "gene_order_hash": _names_digest(checked.var_names),
        "expression_multiset_hash": checks["expression_multiset_candidate"],
        "coordinate_hash": checks["coordinate_hash_candidate"],
        "official_index_hash": sha256_file(project_root / "data" / "gene_panel" / "index.json"),
        "scorer_version": SCORER_VERSION,
        "primary_metrics": {"neighborhood_mmd": {"status": "NOT_RUN"}},
        "protected_checks": checks,
        "recommend_submit": True,
        "score_status": "score_pending",
        "model_file": _relative(project_root, output_path.parent.parent.parent.parent / "models" / f"{spec.tissue}_model.json"),
        "pairing_file": _relative(project_root, pairing_path),
        "permutation_file": _relative(project_root, permutation_path),
        "permutation_tsv": _relative(project_root, permutation_tsv),
        "notes": "A4 J1 pairing candidate; local public score and server score are recorded separately.",
    }
    manifest_path = output_path.parent / "MANIFEST.json"
    _write_json(manifest_path, manifest)
    return {
        "manifest": manifest,
        "checks": checks,
        "pairing": pairing,
        "output_path": str(output_path.resolve()),
        "manifest_path": str(manifest_path.resolve()),
    }


def _initial_result(atom_root: Path, candidates: list[dict[str, Any]]) -> str:
    lines = [
        "# B1-A4 RESULT",
        "",
        "## Status",
        "- status: SCORE_PENDING",
        "- overall decision: PER_BOARD",
        "- task: T2",
        "- final lanes: L1_LATENT_KNN10 + L2_STATE_HASH10",
        "- boards: T2_embryo_val_interp / T2_heart_val_interp / T2_heart_val_extrap",
        "- final artifacts: 6",
        "- local public proxy scores: 0/6",
        "- server scores: 0/6",
        "- submission mode: manual_user_upload",
        "",
        "## Final candidates",
        "| Lane | Board | Candidate ID | SHA256 | Local NFS | Server status | Decision |",
        "|---|---|---|---|---:|---|---|",
    ]
    for item in candidates:
        m = item["manifest"]
        lines.append(
            f"| {m['lane_id']} | {m['board']} | {m['candidate_id']} | {m['sha256']} | NOT_RUN | score_pending | awaiting_server_score |"
        )
    lines.extend(
        [
            "",
            "## Atom",
            "- optimized atom: J1 expression-coordinate joint neighbourhood",
            "- primary metric: neighborhood_mmd (NFS; lower raw is better)",
            "- protected metrics: DES, DCS, MMD, CSS, SDD, ODS, TSR",
            "- hypothesis: a source-only hard permutation can improve local expression-coordinate neighbourhood alignment while preserving both marginals.",
            "",
            "## Change",
            "L1 uses the ten nearest expression-latent donors. L2 uses ten deterministic same-celltype hash neighbours. Both use the same 15-NN graph, PCA/Ridge model and strict-decrease swap ledger.",
            "",
            "## Protected checks",
            "| Candidate ID | permutation | X/layers/raw/obs replay | coordinate exact | 15-NN exact | target used |",
            "|---|---|---|---|---|---|",
        ]
    )
    for item in candidates:
        m = item["manifest"]
        c = m["protected_checks"]
        lines.append(
            f"| {m['candidate_id']} | {c['permutation_bijection']} | "
            f"{c['expression_replay_exact'] and c['layers_replay_exact'] and c['raw_replay_exact'] and c['obs_replay_exact']} | "
            f"{c['coordinate_values_exact']} | {c['knn15_exact']} | {c['target_used']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "All six contract-valid artifacts are ready for manual upload; lane/board promotion remains unresolved until server scores are returned.",
            "",
            "## Only next action",
            "等待用户人工上传六个 artifact 并回填 submission ID 和服务器分数。",
        ]
    )
    result_path = atom_root / "RESULT.md"
    result_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(result_path.resolve())


def run_batch1_a4(
    *,
    atom_root: Path = PROJECT_ROOT / "artifacts" / "atomic_batch1" / ATOM_ID,
    project_root: Path = PROJECT_ROOT,
    seed: int = SEED,
    materialize_submissions: bool = True,
) -> dict[str, Any]:
    project_root = Path(project_root).resolve()
    atom_root = Path(atom_root)
    if atom_root.exists():
        existing = {item.name for item in atom_root.iterdir()}
        unexpected = existing - {"exploration"}
        if unexpected:
            raise FileExistsError(f"A4 atom root already contains final artifacts: {sorted(unexpected)}")
    if materialize_submissions:
        for board in BOARD_ORDER:
            for destination in BOARD_SPECS[board].submission_paths:
                if _resolve(project_root, destination).exists():
                    raise FileExistsError(f"refusing to overwrite submission {destination}")

    models_dir = atom_root / "models"
    models: dict[str, TissueModel] = {}
    model_metadata: dict[str, dict[str, Any]] = {}
    for tissue in ("embryo", "heart"):
        model = fit_tissue_model(tissue, project_root=project_root, seed=seed)
        models[tissue] = model
        model_metadata[tissue] = save_tissue_model(model, models_dir, project_root)

    candidates: list[dict[str, Any]] = []
    for lane_index, lane in enumerate(LANES):
        for board in BOARD_ORDER:
            output_path = atom_root / "final" / lane / board / "prediction.h5ad"
            record = run_board_lane(
                lane=lane,
                board=board,
                model=models[BOARD_SPECS[board].tissue],
                output_path=output_path,
                project_root=project_root,
                seed=seed,
            )
            manifest = record["manifest"]
            local_path = atom_root / "metrics" / lane / board / "local_or_official.json"
            _write_json(
                local_path,
                {
                    "status": "NOT_RUN",
                    "score_type": "public_pseudo_holdout",
                    "server_score": False,
                    "target_used_for_generation": False,
                    "candidate_id": manifest["candidate_id"],
                    "proxy_name": BOARD_SPECS[board].score_proxy,
                    "raw_metrics": {},
                    "notes": "Populate only after the fixed public scorer is run once.",
                },
            )
            manifest["local_score_file"] = _relative(project_root, local_path)
            manifest["local_score_source"] = "public_pseudo_holdout"
            _write_json(output_path.parent / "MANIFEST.json", manifest)
            candidates.append(record)

    if len(candidates) != 6:
        raise AssertionError(f"B1-A4 requires six candidates, got {len(candidates)}")
    if len({record["manifest"]["sha256"] for record in candidates}) != 6:
        raise ValueError("B1-A4 final candidates are not six distinct artifacts")

    submission_records = []
    if materialize_submissions:
        for lane_index, lane in enumerate(LANES):
            for board in BOARD_ORDER:
                record = next(
                    item for item in candidates
                    if item["manifest"]["lane_id"] == lane and item["manifest"]["board"] == board
                )
                source = Path(record["output_path"])
                destination = _resolve(project_root, BOARD_SPECS[board].submission_paths[lane_index])
                _copy_submission_exclusive(source, destination, project_root)
                if sha256_file(source) != sha256_file(destination):
                    raise AssertionError(f"submission copy hash mismatch: {destination}")
                record["manifest"]["submission_file"] = _relative(project_root, destination)
                _write_json(Path(record["manifest_path"]), record["manifest"])
                submission_records.append(
                    {
                        "candidate_id": record["manifest"]["candidate_id"],
                        "lane_id": lane,
                        "board": board,
                        "artifact": record["manifest"]["output_file"],
                        "submission_file": _relative(project_root, destination),
                        "sha256": record["manifest"]["sha256"],
                    }
                )

    final_manifest = {
        "atom_id": ATOM_ID,
        "final_lanes": list(LANES),
        "boards": list(BOARD_ORDER),
        "expected_final_artifacts": 6,
        "exploration_attempt_budget": 4,
        "exploration_attempts": [],
        "submission_mode": "manual_user_upload",
        "all_scores_required": True,
        "score_status": "score_pending",
        "target_used": False,
        "candidates": [
            {
                "candidate_id": record["manifest"]["candidate_id"],
                "lane_id": record["manifest"]["lane_id"],
                "board": record["manifest"]["board"],
                "manifest": record["manifest"]["output_file"].replace("/prediction.h5ad", "/MANIFEST.json"),
                "output_file": record["manifest"]["output_file"],
                "submission_file": record["manifest"].get("submission_file"),
                "sha256": record["manifest"]["sha256"],
            }
            for record in candidates
        ],
    }
    _write_json(atom_root / "FINAL_SET_MANIFEST.json", final_manifest)
    _write_json(
        atom_root / "config_resolved.yaml",
        {
            "atom_id": ATOM_ID,
            "seed": int(seed),
            "final_lanes": list(LANES),
            "boards": list(BOARD_ORDER),
            "final_artifact_count": 6,
            "exploration_attempt_budget": 4,
            "final_generation_budget": 6,
            "final_score_budget": 6,
            "submission_mode": "manual_user_upload",
            "auto_submit": False,
            "scorer_version": SCORER_VERSION,
            "models": model_metadata,
        },
    )
    result_path = _initial_result(atom_root, candidates)
    (atom_root / "run.log").write_text(
        json.dumps(
            {
                "atom_id": ATOM_ID,
                "status": "GENERATED_SCORE_PENDING",
                "candidate_count": 6,
                "submission_records": submission_records,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "atom_id": ATOM_ID,
        "status": "SCORE_PENDING",
        "candidates": [record["manifest"] for record in candidates],
        "final_set_manifest": str((atom_root / "FINAL_SET_MANIFEST.json").resolve()),
        "result": result_path,
    }


def _nfs_like(
    pred_X: Any,
    pred_coords: np.ndarray,
    true_X: Any,
    true_coords: np.ndarray,
) -> float:
    """The scorer's current raw neighbourhood-MMD calculation, locally exposed for one check."""
    veckit_root = PROJECT_ROOT / "third_party" / "veckit"
    if str(veckit_root) not in sys.path:
        sys.path.insert(0, str(veckit_root))
    from common.core_metrics import mmd_unbiased

    pred_matrix = _dense_float32(pred_X)
    true_matrix = _dense_float32(true_X)
    pred_graph = _spatial_knn(np.asarray(pred_coords, dtype=np.float64))
    true_graph = _spatial_knn(np.asarray(true_coords, dtype=np.float64))
    pred_neighbourhood = pred_matrix[pred_graph].mean(axis=1)
    true_neighbourhood = true_matrix[true_graph].mean(axis=1)
    return float(mmd_unbiased(pred_neighbourhood, true_neighbourhood, n=2000, seed=0))


def run_functional_check(
    *,
    output_dir: Path = PROJECT_ROOT / "artifacts" / "atomic_batch1" / ATOM_ID / "exploration" / "attempt-001",
    project_root: Path = PROJECT_ROOT,
    seed: int = SEED,
) -> dict[str, Any]:
    """Run the single fixed 512-cell within-state scramble/recovery check."""
    project_root = Path(project_root).resolve()
    model = fit_tissue_model("embryo", project_root=project_root, seed=seed)
    panel_path = _resolve(project_root, BOARD_SPECS["T2_embryo_val_interp"].panel)
    source_path = _resolve(project_root, "data/E7.25.h5ad")
    source = load_t2_input(source_path, panel_path)
    labels = _labels(source, source_path)
    indices = _balanced_indices(labels, 512, _derived_seed(seed, "functional-check", "E7.25"))
    truth_X = _dense_float32(source.X)[indices]
    truth_coords = _coords(source, source_path)[indices]
    truth_labels = labels[indices]
    truth_names = np.asarray([str(value) for value in source.obs_names[indices]], dtype=str)
    scrambled_order = np.arange(len(indices), dtype=np.int64)
    rng = np.random.default_rng(_derived_seed(seed, "functional-check", "scramble"))
    for state in sorted(np.unique(truth_labels).tolist()):
        group = np.flatnonzero(truth_labels == state)
        shuffled = group.copy()
        rng.shuffle(shuffled)
        scrambled_order[group] = shuffled
    scrambled_X = truth_X[scrambled_order]
    scrambled_labels = truth_labels[scrambled_order]
    z = model.encode(scrambled_X)
    desired = model.predict_neighbourhood(z, 7.25)
    rows: dict[str, Any] = {
        "atom_id": ATOM_ID,
        "attempt_id": "attempt-001",
        "stage": 7.25,
        "n_cells": 512,
        "scramble": "within_celltype_fixed_seed",
        "seed": int(seed),
        "target_used": False,
        "results": {},
    }
    baseline_nfs = _nfs_like(scrambled_X, truth_coords, truth_X, truth_coords)
    for lane in LANES:
        pairing = optimize_pairing(
            z,
            desired,
            truth_coords,
            lane=lane,
            labels=scrambled_labels,
            obs_names=truth_names,
            seed=seed,
        )
        candidate_X = scrambled_X[pairing["permutation"]]
        candidate_nfs = _nfs_like(candidate_X, truth_coords, truth_X, truth_coords)
        rows["results"][lane] = {
            "initial_objective": pairing["initial_objective"],
            "final_objective": pairing["final_objective"],
            "accepted_swaps": pairing["accepted_swaps"],
            "proposal_count": pairing["proposal_count"],
            "baseline_nfs": baseline_nfs,
            "candidate_nfs": candidate_nfs,
            "objective_decreased": pairing["final_objective"] < pairing["initial_objective"],
            "nfs_improved": candidate_nfs < baseline_nfs,
        }
    output_dir = Path(output_dir)
    _write_json(output_dir / "functional_check.json", rows)
    if not all(item["objective_decreased"] for item in rows["results"].values()):
        raise AssertionError("functional check: at least one lane did not lower its objective")
    if not any(item["nfs_improved"] for item in rows["results"].values()):
        raise AssertionError("functional check: neither lane improved neighbourhood MMD")
    return rows


def _commit_json_updates(updates: Sequence[tuple[Path, Any]]) -> None:
    """Stage a validated JSON update set, then replace each file without truncation."""
    staged: list[tuple[Path, Path]] = []
    try:
        for index, (path, value) in enumerate(updates):
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_name(f".{path.name}.{os.getpid()}.{index}.tmp")
            temporary.write_text(
                json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            staged.append((temporary, path))
        for temporary, path in staged:
            os.replace(temporary, path)
    finally:
        for temporary, _ in staged:
            if temporary.exists():
                temporary.unlink()


def _prepare_finalize_candidates(atom_root: Path, freeze: dict[str, Any]) -> list[dict[str, Any]]:
    atom_root = Path(atom_root)
    items = freeze.get("candidates")
    expected_pairs = {(lane, board) for lane in LANES for board in BOARD_ORDER}
    if not isinstance(items, list) or len(items) != len(expected_pairs):
        raise ValueError("B1-A4 final set must contain exactly six candidates")

    prepared: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, str]] = set()
    seen_hashes: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("B1-A4 final set contains a non-object candidate")
        lane = str(item.get("lane_id", ""))
        board = str(item.get("board", ""))
        pair = (lane, board)
        if pair not in expected_pairs:
            raise ValueError(f"B1-A4 final set has unexpected lane/board pair: {pair}")
        if pair in seen_pairs:
            raise ValueError(f"B1-A4 final set repeats lane/board pair: {pair}")
        seen_pairs.add(pair)
        candidate_id = _candidate_id(lane, board)
        if item.get("candidate_id") != candidate_id:
            raise ValueError(f"B1-A4 freeze candidate ID mismatch for {pair}")

        manifest_path = atom_root / "final" / lane / board / "MANIFEST.json"
        score_path = atom_root / "metrics" / lane / board / "local_or_official.json"
        artifact_path = atom_root / "final" / lane / board / "prediction.h5ad"
        if not manifest_path.exists() or not score_path.exists() or not artifact_path.exists():
            raise FileNotFoundError(f"B1-A4 freeze input missing for {pair}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("candidate_id") != candidate_id:
            raise ValueError(f"{manifest_path}: candidate ID does not match freeze")
        if manifest.get("lane_id") != lane or manifest.get("board") != board:
            raise ValueError(f"{manifest_path}: lane/board does not match freeze")
        if not manifest.get("base_submission"):
            raise ValueError(f"{manifest_path}: missing base_submission")
        artifact_sha = sha256_file(artifact_path)
        if manifest.get("sha256") != artifact_sha:
            raise ValueError(f"{manifest_path}: artifact SHA256 mismatch")
        if item.get("sha256") != artifact_sha:
            raise ValueError(f"{manifest_path}: freeze SHA256 mismatch")
        seen_hashes.add(artifact_sha)

        score = json.loads(score_path.read_text(encoding="utf-8"))
        if score.get("status") not in {"COMPLETE", "complete"}:
            # score_h5ad.py emits the canonical {meta, metrics} payload but no
            # workflow status field. Enrich it only after all six inputs pass.
            if not isinstance(score.get("metrics"), dict):
                raise ValueError(f"{score_path}: fixed public scorer has not completed")
            score["status"] = "COMPLETE"
            score["score_type"] = "public_pseudo_holdout"
            score["server_score"] = False
            score["target_used_for_generation"] = False
        metrics = score.get("metrics")
        if not isinstance(metrics, dict) or "neighborhood_mmd" not in metrics:
            raise ValueError(f"{score_path}: missing neighborhood_mmd")
        try:
            neighborhood_mmd = float(metrics["neighborhood_mmd"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{score_path}: neighborhood_mmd is not numeric") from exc
        if not np.isfinite(neighborhood_mmd):
            raise ValueError(f"{score_path}: neighborhood_mmd is not finite")
        manifest["primary_metrics"] = {
            "neighborhood_mmd": neighborhood_mmd,
            "source": "public_pseudo_holdout",
            "status": "COMPLETE",
        }
        manifest["score_status"] = "score_pending"
        prepared.append(
            {
                "manifest": manifest,
                "manifest_path": manifest_path,
                "score": score,
                "score_path": score_path,
            }
        )
    if seen_pairs != expected_pairs:
        raise ValueError(f"B1-A4 final set does not cover exactly 2 lanes × 3 boards: {seen_pairs}")
    if len(seen_hashes) != len(expected_pairs):
        raise ValueError("B1-A4 final candidates are not six distinct artifacts")
    return prepared


def finalize_scores(atom_root: Path) -> dict[str, Any]:
    atom_root = Path(atom_root)
    freeze = json.loads((atom_root / "FINAL_SET_MANIFEST.json").read_text(encoding="utf-8"))
    candidates = _prepare_finalize_candidates(atom_root, freeze)
    updates: list[tuple[Path, Any]] = []
    for item in candidates:
        updates.append((item["score_path"], item["score"]))
        updates.append((item["manifest_path"], item["manifest"]))
    freeze["local_score_status"] = "complete"
    freeze["local_score_count"] = 6
    freeze["score_status"] = "score_pending"
    updates.append((atom_root / "FINAL_SET_MANIFEST.json", freeze))
    _commit_json_updates(updates)
    lines = [
        "# B1-A4 RESULT",
        "",
        "## Status",
        "- status: SCORE_PENDING",
        "- overall decision: PER_BOARD",
        "- task: T2",
        "- final lanes: L1_LATENT_KNN10 + L2_STATE_HASH10",
        "- boards: T2_embryo_val_interp / T2_heart_val_interp / T2_heart_val_extrap",
        "- final artifacts: 6",
        "- local public proxy scores: 6/6",
        "- server scores: 0/6",
        "- submission mode: manual_user_upload",
        "",
        "## Final candidates",
        "| Lane | Board | Candidate ID | SHA256 | Local NFS | Server status | Decision |",
        "|---|---|---|---|---:|---|---|",
    ]
    for item in candidates:
        m = item["manifest"]
        lines.append(
            f"| {m['lane_id']} | {m['board']} | {m['candidate_id']} | {m['sha256']} | "
            f"{item['score']['metrics']['neighborhood_mmd']} | score_pending | awaiting_server_score |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "All six contract-valid candidates remain ready for manual upload; local public NFS is diagnostic and is not a leaderboard score.",
            "",
            "## Only next action",
            "等待用户人工上传六个 artifact 并回填 submission ID 和服务器分数。",
        ]
    )
    result_path = atom_root / "RESULT.md"
    result_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"atom_id": ATOM_ID, "status": "SCORE_PENDING", "local_score_count": 6, "result": str(result_path.resolve())}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=PROJECT_ROOT / "artifacts" / "atomic_batch1" / ATOM_ID)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--finalize", action="store_true", help="finalize six completed local scorer JSON files")
    parser.add_argument("--functional-check", action="store_true", help="run the fixed 512-cell scramble check")
    parser.add_argument("--no-materialize-submissions", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.functional_check:
        result = run_functional_check(
            output_dir=args.output_root / "exploration" / "attempt-001",
            project_root=args.project_root,
            seed=args.seed,
        )
    elif args.finalize:
        result = finalize_scores(args.output_root)
    else:
        result = run_batch1_a4(
            atom_root=args.output_root,
            project_root=args.project_root,
            seed=args.seed,
            materialize_submissions=not args.no_materialize_submissions,
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
