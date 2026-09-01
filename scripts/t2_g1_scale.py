#!/usr/bin/env python3
"""Source-only T2 G1 scale calibration for the B1-A1 two-lane experiment.

The runner deliberately changes only the first three columns of
obsm["spatial_3D"]. It never reads a target coordinate file and never
changes expression, observation order, variable order, or row pairing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import anndata as ad
import numpy as np
from scipy import sparse

try:
    from .t2_baseline import load_t2_input, read_panel
except ImportError:  # direct python scripts/t2_g1_scale.py execution
    from t2_baseline import load_t2_input, read_panel


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ATOM_ID = "B1-A1"
SCORER_VERSION = "veckit@46d41e63f42a9aab815db20b742feeccd249cb17"
LANE_FORMAL = "L1_FORMAL_LOG_RMS"
LANE_TREND = "L2_ALL_STAGE_LOG_RMS_OLS"
LANES = (LANE_FORMAL, LANE_TREND)
BOARD_ORDER = (
    "T2_embryo_val_interp",
    "T2_heart_val_interp",
    "T2_heart_val_extrap",
)


@dataclass(frozen=True)
class BoardSpec:
    slug: str
    official_key: str
    task: str
    panel: str
    target_stage: float
    source_stages: tuple[tuple[float, str], ...]
    base_submission: str
    min_cells: int
    max_cells: int


BOARD_SPECS: dict[str, BoardSpec] = {
    "T2_embryo_val_interp": BoardSpec(
        slug="T2_embryo_val_interp",
        official_key="T2:embryo:val_interp",
        task="embryo",
        panel="data/gene_panel/T2__embryo__val_interp.genes.txt",
        target_stage=7.5,
        source_stages=(
            (6.75, "data/E6.75.h5ad"),
            (7.25, "data/E7.25.h5ad"),
            (8.0, "data/E8.0.h5ad"),
        ),
        base_submission=(
            "submissions/scored/baseline-001/"
            "T2_embryo_val_interp/submission.h5ad"
        ),
        min_cells=583,
        max_cells=5000,
    ),
    "T2_heart_val_interp": BoardSpec(
        slug="T2_heart_val_interp",
        official_key="T2:heart:val_interp",
        task="heart",
        panel="data/gene_panel/T2__heart__val_interp.genes.txt",
        target_stage=8.5,
        source_stages=(
            (8.25, "data/E8.25_late.h5ad"),
            (8.75, "data/E8.75.h5ad"),
            (9.5, "data/E9.5.h5ad"),
        ),
        base_submission=(
            "submissions/scored/submission-002/"
            "T2_heart_val_interp/submission.h5ad"
        ),
        min_cells=1000,
        max_cells=17616,
    ),
    "T2_heart_val_extrap": BoardSpec(
        slug="T2_heart_val_extrap",
        official_key="T2:heart:val_extrap",
        task="heart",
        panel="data/gene_panel/T2__heart__val_extrap.genes.txt",
        target_stage=10.5,
        source_stages=(
            (8.25, "data/E8.25_late.h5ad"),
            (8.75, "data/E8.75.h5ad"),
            (9.5, "data/E9.5.h5ad"),
        ),
        base_submission=(
            "submissions/scored/baseline-001/"
            "T2_heart_val_extrap/submission.h5ad"
        ),
        min_cells=1000,
        max_cells=25179,
    ),
}


def _resolve(project_root: Path, relative_path: str | Path) -> Path:
    path = Path(relative_path)
    return path if path.is_absolute() else Path(project_root) / path


def _coords(a: ad.AnnData, path: Path) -> np.ndarray:
    if "spatial_3D" not in a.obsm:
        raise ValueError(f"{path}: missing obsm['spatial_3D']")
    value = a.obsm["spatial_3D"]
    if sparse.issparse(value):
        value = value.toarray()
    coords = np.asarray(value)
    if coords.ndim != 2 or coords.shape[0] != a.n_obs or coords.shape[1] < 3:
        raise ValueError(
            f"{path}: spatial_3D must have shape (n_obs, >=3), got {coords.shape}"
        )
    coords = np.asarray(coords[:, :3], dtype=np.float64)
    if not np.isfinite(coords).all():
        raise ValueError(f"{path}: spatial_3D contains NaN or infinite values")
    return coords


def _full_coords(a: ad.AnnData, path: Path) -> np.ndarray:
    value = a.obsm["spatial_3D"]
    if sparse.issparse(value):
        value = value.toarray()
    coords = np.asarray(value)
    if coords.ndim != 2 or coords.shape[0] != a.n_obs or coords.shape[1] < 3:
        raise ValueError(
            f"{path}: spatial_3D must have shape (n_obs, >=3), got {coords.shape}"
        )
    if not np.isfinite(coords).all():
        raise ValueError(f"{path}: spatial_3D contains NaN or infinite values")
    return coords


def _rms_radius(coords: np.ndarray) -> float:
    values = np.asarray(coords, dtype=np.float64)
    if values.ndim != 2 or values.shape[1] < 3 or values.shape[0] == 0:
        raise ValueError(f"coords must have shape (n_obs>0, >=3), got {values.shape}")
    values = values[:, :3]
    centered = values - values.mean(axis=0, keepdims=True)
    rms = float(np.sqrt(np.mean(np.sum(centered * centered, axis=1))))
    if not np.isfinite(rms) or rms <= 0:
        raise ValueError("spatial_3D must have a positive finite RMS radius")
    return rms


def _fit_target_log_rms(
    lane: str,
    stages: Iterable[float],
    rms_values: Iterable[float],
    target_stage: float,
) -> dict[str, Any]:
    lane = str(lane)
    if lane not in LANES:
        raise ValueError(f"unknown lane {lane!r}; choose from {LANES}")
    times = np.asarray(tuple(stages), dtype=np.float64)
    rms = np.asarray(tuple(rms_values), dtype=np.float64)
    if times.ndim != 1 or rms.ndim != 1 or len(times) != len(rms):
        raise ValueError("stages and rms_values must be one-dimensional and equal length")
    if len(times) < 2:
        raise ValueError("at least two observed stages are required")
    if not np.isfinite(times).all() or not np.isfinite(rms).all() or (rms <= 0).any():
        raise ValueError("stages and RMS values must be finite; RMS values must be positive")
    if np.any(np.diff(times) <= 0):
        raise ValueError("stages must be strictly increasing")
    target_stage = float(target_stage)
    if not np.isfinite(target_stage):
        raise ValueError("target_stage must be finite")

    log_rms = np.log(rms)
    if lane == LANE_TREND:
        design = np.column_stack((np.ones(len(times), dtype=np.float64), times))
        coefficients, _, rank, _ = np.linalg.lstsq(design, log_rms, rcond=None)
        if int(rank) < 2:
            raise ValueError("all-stage log-RMS trend is rank deficient")
        target_log = float(np.array([1.0, target_stage]) @ coefficients)
        fit = {
            "fit": "ordinary_least_squares",
            "coefficients": [float(value) for value in coefficients],
            "rank": int(rank),
        }
    else:
        if target_stage < times[0]:
            raise ValueError("L1 does not define a pre-first-stage extrapolation")
        if target_stage > times[-1]:
            slopes = np.diff(log_rms) / np.diff(times)
            last_slope = float(slopes[-1])
            clipped_slope = float(np.clip(last_slope, slopes.min(), slopes.max()))
            target_log = float(log_rms[-1] + clipped_slope * (target_stage - times[-1]))
            fit = {
                "fit": "last_adjacent_log_slope_extrapolation",
                "slopes": [float(value) for value in slopes],
                "slope_min": float(slopes.min()),
                "slope_max": float(slopes.max()),
                "raw_last_slope": last_slope,
                "clipped_last_slope": clipped_slope,
            }
        else:
            exact = np.flatnonzero(np.isclose(times, target_stage, rtol=0.0, atol=1e-12))
            if len(exact):
                target_log = float(log_rms[int(exact[0])])
                fit = {"fit": "observed_stage", "stage_index": int(exact[0])}
            else:
                right = int(np.searchsorted(times, target_stage, side="right"))
                left = right - 1
                if left < 0 or right >= len(times):
                    raise ValueError("L1 target is outside the configured stage range")
                fraction = float((target_stage - times[left]) / (times[right] - times[left]))
                target_log = float(
                    log_rms[left] + fraction * (log_rms[right] - log_rms[left])
                )
                fit = {
                    "fit": "strict_linear_interpolation",
                    "left_stage": float(times[left]),
                    "right_stage": float(times[right]),
                    "fraction": fraction,
                }

    target_rms = float(np.exp(target_log))
    if not np.isfinite(target_rms) or target_rms <= 0:
        raise ValueError("predicted target RMS is non-positive or non-finite")
    return {
        "lane": lane,
        "stages": [float(value) for value in times],
        "rms": [float(value) for value in rms],
        "log_rms": [float(value) for value in log_rms],
        "target_stage": target_stage,
        "target_log_rms": target_log,
        "target_rms": target_rms,
        **fit,
    }


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
            contiguous = np.ascontiguousarray(part)
            digest.update(contiguous.tobytes(order="C"))
    else:
        array = np.ascontiguousarray(np.asarray(value))
        digest.update(b"dense")
        digest.update(str(array.shape).encode("utf-8"))
        digest.update(array.dtype.str.encode("utf-8"))
        digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def _names_digest(names: Iterable[Any]) -> str:
    canonical = chr(10).join(str(name) for name in names).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _knn_fingerprint(coords: np.ndarray, n_neighbors: int = 15) -> str | None:
    values = np.asarray(coords, dtype=np.float64)[:, :3]
    if len(values) < 2:
        return None
    from sklearn.neighbors import NearestNeighbors

    count = min(int(n_neighbors), len(values) - 1)
    model = NearestNeighbors(n_neighbors=count + 1, algorithm="auto")
    model.fit(values)
    _, indices = model.kneighbors(values, return_distance=True)
    selected = np.empty((len(values), count), dtype=np.int64)
    for row, neighbours in enumerate(indices):
        without_self = neighbours[neighbours != row]
        if len(without_self) != count:
            raise RuntimeError("nearest-neighbor query did not return a complete self-excluded row")
        selected[row] = without_self[:count]
    return hashlib.sha256(np.ascontiguousarray(selected).tobytes()).hexdigest()


def _invariant_checks(
    base: ad.AnnData,
    candidate: ad.AnnData,
    base_path: Path,
    candidate_path: Path,
) -> dict[str, Any]:
    base_coords = _coords(base, base_path)
    candidate_coords = _coords(candidate, candidate_path)
    base_knn = _knn_fingerprint(base_coords)
    candidate_knn = _knn_fingerprint(candidate_coords)
    base_x_hash = _matrix_digest(base.X)
    candidate_x_hash = _matrix_digest(candidate.X)
    return {
        "expression_checksum_unchanged": base_x_hash == candidate_x_hash,
        "expression_checksum_base": base_x_hash,
        "expression_checksum_candidate": candidate_x_hash,
        "obs_order_unchanged": [str(value) for value in base.obs_names]
        == [str(value) for value in candidate.obs_names],
        "var_order_unchanged": [str(value) for value in base.var_names]
        == [str(value) for value in candidate.var_names],
        "spatial_shape_unchanged": list(base_coords.shape) == list(candidate_coords.shape),
        "coordinate_hash_base": _matrix_digest(base_coords),
        "coordinate_hash_candidate": _matrix_digest(candidate_coords),
        "knn15_fingerprint_base": base_knn,
        "knn15_fingerprint_candidate": candidate_knn,
        "knn15_exact": base_knn == candidate_knn,
        "target_used": False,
    }


def _relative_path(project_root: Path, path: Path) -> str:
    return path.resolve().relative_to(Path(project_root).resolve()).as_posix()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + chr(10),
        encoding="utf-8",
    )


def run_g1_scale(
    *,
    lane: str,
    board: str,
    output_path: Path,
    project_root: Path = PROJECT_ROOT,
    seed: int = 20260827,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Generate one board-specific final candidate for one fixed lane."""

    if lane not in LANES:
        raise ValueError(f"unknown lane {lane!r}; choose from {LANES}")
    if board not in BOARD_SPECS:
        raise ValueError(f"unknown board {board!r}; choose from {BOARD_ORDER}")
    output_path = Path(output_path)
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"output already exists: {output_path}; pass overwrite=True to replace it")

    project_root = Path(project_root).resolve()
    spec = BOARD_SPECS[board]
    panel_path = _resolve(project_root, spec.panel)
    base_path = _resolve(project_root, spec.base_submission)
    if not panel_path.exists():
        raise FileNotFoundError(panel_path)
    if not base_path.exists():
        raise FileNotFoundError(base_path)

    panel = read_panel(panel_path)
    source_stats: list[dict[str, Any]] = []
    for stage, relative_path in spec.source_stages:
        source_path = _resolve(project_root, relative_path)
        if not source_path.exists():
            raise FileNotFoundError(source_path)
        source = load_t2_input(source_path, panel_path)
        source_coords = _coords(source, source_path)
        source_stats.append(
            {
                "stage": float(stage),
                "path": _relative_path(project_root, source_path),
                "n_obs": int(source.n_obs),
                "rms": _rms_radius(source_coords),
            }
        )
        del source

    fit = _fit_target_log_rms(
        lane,
        (item["stage"] for item in source_stats),
        (item["rms"] for item in source_stats),
        spec.target_stage,
    )
    base = load_t2_input(base_path, panel_path)
    if not spec.min_cells <= base.n_obs <= spec.max_cells:
        raise ValueError(
            f"{base_path}: n_obs={base.n_obs} outside board limits "
            f"[{spec.min_cells}, {spec.max_cells}]"
        )
    base_coords = _coords(base, base_path)
    base_rms = _rms_radius(base_coords)
    scale_factor = float(fit["target_rms"] / base_rms)
    if not np.isfinite(scale_factor) or scale_factor <= 0:
        raise ValueError("scale factor must be positive and finite")

    base_centroid = base_coords.mean(axis=0)
    transformed = base_centroid + scale_factor * (base_coords - base_centroid)
    full_coords = _full_coords(base, base_path)
    output_dtype = np.result_type(full_coords.dtype, np.float32)
    output_coords = np.asarray(full_coords, dtype=output_dtype).copy()
    output_coords[:, :3] = transformed.astype(output_dtype, copy=False)

    model: dict[str, Any] = {
        "atom_id": ATOM_ID,
        "lane_id": lane,
        "board": board,
        "official_board_key": spec.official_key,
        "task": spec.task,
        "panel": _relative_path(project_root, panel_path),
        "panel_gene_count": len(panel),
        "base_submission": _relative_path(project_root, base_path),
        "target_stage": float(spec.target_stage),
        "source_only": True,
        "target_used": False,
        "source_stats": source_stats,
        "fit": fit,
        "base_rms": base_rms,
        "scale_factor": scale_factor,
        "transform": "base_centroid_plus_uniform_positive_scale",
        "expression_invariant": "base_X_unchanged",
        "seed": int(seed),
    }
    output = base.copy()
    output.obsm["spatial_3D"] = output_coords
    output.uns["ve_g1_scale"] = json.dumps(
        model, ensure_ascii=False, sort_keys=True, default=str
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output.write_h5ad(output_path)

    checked = load_t2_input(output_path, panel_path)
    checks = _invariant_checks(base, checked, base_path, output_path)
    if not all(
        checks[key]
        for key in (
            "expression_checksum_unchanged",
            "obs_order_unchanged",
            "var_order_unchanged",
            "spatial_shape_unchanged",
            "knn15_exact",
        )
    ):
        raise AssertionError(f"{output_path}: G1 invariant check failed: {checks}")
    actual_rms = _rms_radius(_coords(checked, output_path))
    expected_rms = float(base_rms * scale_factor)
    if not np.isclose(actual_rms, expected_rms, rtol=2e-5, atol=2e-6):
        raise AssertionError(
            f"{output_path}: transformed RMS {actual_rms} != expected {expected_rms}"
        )
    model["actual_output_rms"] = actual_rms
    model["protected_checks"] = checks
    model["output_file"] = _relative_path(project_root, output_path)
    model["output_sha256"] = _sha256_file(output_path)
    model["n_obs"] = int(checked.n_obs)
    model["n_vars"] = int(checked.n_vars)
    model["gene_order_hash"] = _names_digest(checked.var_names)
    return {
        "model": model,
        "protected_checks": checks,
        "output_path": str(output_path.resolve()),
        "output_sha256": model["output_sha256"],
        "n_obs": model["n_obs"],
        "n_vars": model["n_vars"],
        "gene_order_hash": model["gene_order_hash"],
    }


def _candidate_id(lane: str, board: str) -> str:
    lane_number = "L1" if lane == LANE_FORMAL else "L2"
    return f"{ATOM_ID}-{lane_number}-{board}"


def _candidate_manifest(
    *,
    lane: str,
    board: str,
    result: dict[str, Any],
    project_root: Path,
    atom_root: Path,
    seed: int,
) -> dict[str, Any]:
    spec = BOARD_SPECS[board]
    output_path = Path(result["output_path"])
    candidate_id = _candidate_id(lane, board)
    return {
        "atom_id": ATOM_ID,
        "lane_id": lane,
        "candidate_id": candidate_id,
        "final_candidate": True,
        "score_required": True,
        "attempt_id": None,
        "task": "T2",
        "board": board,
        "official_board_key": spec.official_key,
        "base_submission": _relative_path(
            project_root, _resolve(project_root, spec.base_submission)
        ),
        "output_file": _relative_path(project_root, output_path),
        "sha256": result["output_sha256"],
        "n_obs": int(result["n_obs"]),
        "n_vars": int(result["n_vars"]),
        "gene_order_hash": result["gene_order_hash"],
        "expression_multiset_hash": result["protected_checks"]["expression_checksum_candidate"],
        "coordinate_hash": result["protected_checks"]["coordinate_hash_candidate"],
        "official_index_hash": _sha256_file(project_root / "data" / "gene_panel" / "index.json"),
        "scorer_version": SCORER_VERSION,
        "seed": int(seed),
        "primary_metrics": {
            "scale_log_ratio": {"status": "NOT_RUN"},
            "TSR": {"status": "NOT_RUN"},
        },
        "protected_checks": result["protected_checks"],
        "recommend_submit": True,
        "score_status": "score_pending",
        "target_used": False,
        "model_file": _relative_path(
            project_root, atom_root / "final" / lane / board / "scale_model.json"
        ),
        "notes": (
            "Final B1-A1 lane. Local public pseudo-holdout and server score are "
            "recorded separately; no hidden target was used for generation."
        ),
    }


def run_lane(
    *,
    lane: str,
    final_root: Path,
    project_root: Path = PROJECT_ROOT,
    seed: int = 20260827,
    boards: Iterable[str] | None = None,
    overwrite: bool = False,
) -> list[dict[str, Any]]:
    """Run one complete lane across the three configured boards."""

    if lane not in LANES:
        raise ValueError(f"unknown lane {lane!r}; choose from {LANES}")
    project_root = Path(project_root).resolve()
    final_root = Path(final_root)
    atom_root = final_root.parent
    records: list[dict[str, Any]] = []
    board_names = BOARD_ORDER if boards is None else tuple(boards)
    for board in board_names:
        board_dir = final_root / lane / board
        output_path = board_dir / "prediction.h5ad"
        result = run_g1_scale(
            lane=lane,
            board=board,
            output_path=output_path,
            project_root=project_root,
            seed=seed,
            overwrite=overwrite,
        )
        _write_json(board_dir / "scale_model.json", result["model"])
        metrics_dir = atom_root / "metrics" / lane / board
        _write_json(metrics_dir / "protected_checks.json", result["protected_checks"])
        _write_json(
            metrics_dir / "local_or_official.json",
            {
                "status": "NOT_RUN",
                "score_type": "public_pseudo_holdout",
                "target_used_for_generation": False,
                "raw_metrics": {},
                "candidate_id": _candidate_id(lane, board),
                "notes": "Populate only after the fixed public score command is run.",
            },
        )
        manifest = _candidate_manifest(
            lane=lane,
            board=board,
            result=result,
            project_root=project_root,
            atom_root=atom_root,
            seed=seed,
        )
        _write_json(board_dir / "MANIFEST.json", manifest)
        records.append(manifest)
    return records


def run_batch1_a1(
    *,
    atom_root: Path = PROJECT_ROOT / "artifacts" / "atomic_batch1" / ATOM_ID,
    project_root: Path = PROJECT_ROOT,
    seed: int = 20260827,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Generate both final lanes and the six-candidate freeze manifest."""

    project_root = Path(project_root).resolve()
    atom_root = Path(atom_root)
    final_root = atom_root / "final"
    candidates: list[dict[str, Any]] = []
    for lane in LANES:
        candidates.extend(
            run_lane(
                lane=lane,
                final_root=final_root,
                project_root=project_root,
                seed=seed,
                overwrite=overwrite,
            )
        )
    if len(candidates) != 6:
        raise AssertionError(f"B1-A1 requires exactly 6 final candidates, got {len(candidates)}")

    set_manifest = {
        "atom_id": ATOM_ID,
        "final_lanes": list(LANES),
        "boards": list(BOARD_ORDER),
        "expected_final_artifacts": 6,
        "exploration_attempt_budget": 4,
        "exploration_attempts": [],
        "candidates": [
            {
                "candidate_id": item["candidate_id"],
                "lane_id": item["lane_id"],
                "board": item["board"],
                "manifest": item["output_file"].replace(
                    "/prediction.h5ad", "/MANIFEST.json"
                ),
                "output_file": item["output_file"],
                "sha256": item["sha256"],
            }
            for item in candidates
        ],
        "submission_mode": "manual_user_upload",
        "all_scores_required": True,
        "score_status": "score_pending",
    }
    _write_json(atom_root / "FINAL_SET_MANIFEST.json", set_manifest)
    _write_json(
        atom_root / "config_resolved.yaml",
        {
            "atom_id": ATOM_ID,
            "seed": int(seed),
            "final_lanes": list(LANES),
            "boards": list(BOARD_ORDER),
            "final_artifact_count": 6,
            "exploration_attempt_budget": 4,
            "submission_mode": "manual_user_upload",
            "auto_submit": False,
            "scorer_version": SCORER_VERSION,
        },
    )
    return {
        "atom_id": ATOM_ID,
        "final_set_manifest": set_manifest,
        "candidates": candidates,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lane",
        choices=["both", LANE_FORMAL, LANE_TREND],
        default="both",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=PROJECT_ROOT / "artifacts" / "atomic_batch1" / ATOM_ID,
    )
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--seed", type=int, default=20260827)
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.lane == "both":
        result = run_batch1_a1(
            atom_root=args.output_root,
            project_root=args.project_root,
            seed=args.seed,
            overwrite=args.overwrite,
        )
    else:
        result = {
            "atom_id": ATOM_ID,
            "lane": args.lane,
            "candidates": run_lane(
                lane=args.lane,
                final_root=Path(args.output_root) / "final",
                project_root=args.project_root,
                seed=args.seed,
                overwrite=args.overwrite,
            ),
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
