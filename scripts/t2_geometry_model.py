#!/usr/bin/env python3
"""Low-capacity, source-only geometry interpolation for T2 diagnostics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np
from scipy import sparse

try:
    from .t2_baseline import (
        DEFAULT_PANEL_DIR,
        TASK_PANEL_FILES,
        _celltypes,
        load_t2_input,
    )
except ImportError:  # direct ``python scripts/t2_geometry_model.py`` execution
    from t2_baseline import DEFAULT_PANEL_DIR, TASK_PANEL_FILES, _celltypes, load_t2_input


def _coords(a: ad.AnnData, path: Path) -> np.ndarray:
    value = a.obsm["spatial_3D"]
    if sparse.issparse(value):
        value = value.toarray()
    coords = np.asarray(value, dtype=np.float64)
    if coords.ndim != 2 or coords.shape[1] < 3 or coords.shape[0] != a.n_obs:
        raise ValueError(f"{path}: spatial_3D must have shape (n_obs, >=3), got {coords.shape}")
    coords = coords[:, :3]
    if not np.isfinite(coords).all():
        raise ValueError(f"{path}: spatial_3D contains NaN or infinite values")
    return coords


def _rms_radius(coords: np.ndarray) -> float:
    centered = coords - coords.mean(axis=0, keepdims=True)
    return float(np.sqrt(np.mean(np.sum(centered * centered, axis=1))))


def _centroids(a: ad.AnnData, celltypes: np.ndarray, coords: np.ndarray) -> dict[str, np.ndarray]:
    return {
        str(celltype): coords[celltypes == celltype].mean(axis=0)
        for celltype in np.unique(celltypes)
    }


def run_source_geometry_shift(
    *,
    task: str,
    shift_start_path: Path,
    shift_end_path: Path,
    base_path: Path,
    output_path: Path,
    panel_path: Path | None = None,
    celltype_key: str = "celltype",
    damp: float = -0.6,
    centroid_weight: float = 0.5,
    max_dense_mb: float = 512.0,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Interpolate source-only global scale and celltype centroid displacement.

    The transformation is a conservative similarity special case: identity
    rotation, an isotropic scale interpolated from the source RMS radii, and a
    source-only per-celltype centroid correction.  Expression and observation
    rows are copied from ``base`` unchanged.
    """

    task = task.lower()
    if task not in TASK_PANEL_FILES:
        raise ValueError(f"Unsupported T2 task {task!r}; choose embryo or heart")
    if not np.isfinite(damp):
        raise ValueError("damp must be finite")
    if not np.isfinite(centroid_weight) or not 0 <= centroid_weight <= 1:
        raise ValueError("centroid_weight must be in [0, 1]")
    if max_dense_mb <= 0 or not np.isfinite(max_dense_mb):
        raise ValueError("max_dense_mb must be a positive finite number")

    panel_path = Path(panel_path) if panel_path else DEFAULT_PANEL_DIR / TASK_PANEL_FILES[task]
    shift_start_path = Path(shift_start_path)
    shift_end_path = Path(shift_end_path)
    base_path = Path(base_path)
    output_path = Path(output_path)
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output_path}; pass overwrite=True to replace it")

    shift_start = load_t2_input(shift_start_path, panel_path)
    shift_end = load_t2_input(shift_end_path, panel_path)
    base = load_t2_input(base_path, panel_path)
    start_types = _celltypes(shift_start, celltype_key, shift_start_path)
    end_types = _celltypes(shift_end, celltype_key, shift_end_path)
    base_types = _celltypes(base, celltype_key, base_path)
    start_coords = _coords(shift_start, shift_start_path)
    end_coords = _coords(shift_end, shift_end_path)
    base_coords = _coords(base, base_path)

    start_rms = _rms_radius(start_coords)
    end_rms = _rms_radius(end_coords)
    if start_rms <= 0 or end_rms <= 0:
        raise ValueError("source spatial_3D must have non-zero RMS radius")
    predicted_rms = end_rms + float(damp) * (end_rms - start_rms)
    if predicted_rms <= 0 or not np.isfinite(predicted_rms):
        raise ValueError("source-only interpolated RMS radius is non-positive or non-finite")
    scale_factor = predicted_rms / end_rms

    start_centroids = _centroids(shift_start, start_types, start_coords)
    end_centroids = _centroids(shift_end, end_types, end_coords)
    out_coords = base_coords * scale_factor
    fallback_celltypes: list[str] = []
    for celltype in np.unique(base_types):
        mask = base_types == celltype
        if celltype not in start_centroids or celltype not in end_centroids:
            fallback_celltypes.append(str(celltype))
            continue
        predicted_centroid = end_centroids[celltype] + float(damp) * (
            end_centroids[celltype] - start_centroids[celltype]
        )
        transformed_base_centroid = base_coords[mask].mean(axis=0) * scale_factor
        out_coords[mask] += float(centroid_weight) * (
            predicted_centroid - transformed_base_centroid
        )

    out = base.copy()
    out.obsm["spatial_3D"] = out_coords.astype(np.float32, copy=False)
    metadata: dict[str, Any] = {
        "task": task,
        "method": "source_only_similarity_centroid_geometry",
        "shift_start_path": str(shift_start_path.resolve()),
        "shift_end_path": str(shift_end_path.resolve()),
        "base_path": str(base_path.resolve()),
        "panel_path": str(panel_path.resolve()),
        "celltype_key": celltype_key,
        "damp": float(damp),
        "centroid_weight": float(centroid_weight),
        "transform": "identity_rotation_isotropic_scale_plus_celltype_centroid_displacement",
        "start_rms": start_rms,
        "end_rms": end_rms,
        "predicted_rms": predicted_rms,
        "scale_factor": scale_factor,
        "fallback_celltypes": sorted(fallback_celltypes),
        "expression_invariant": "base_X_unchanged",
    }
    out.uns["ve_geometry_model"] = metadata
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out.write_h5ad(output_path)
    metadata.update(
        {
            "output_path": str(output_path.resolve()),
            "n_obs": int(out.n_obs),
            "n_vars": int(out.n_vars),
            "spatial_3D_shape": list(np.asarray(out.obsm["spatial_3D"]).shape),
        }
    )
    return metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=sorted(TASK_PANEL_FILES), required=True)
    parser.add_argument("--shift-start", type=Path, required=True)
    parser.add_argument("--shift-end", type=Path, required=True)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--panel", type=Path)
    parser.add_argument("--celltype-key", default="celltype")
    parser.add_argument("--damp", type=float, default=-0.6)
    parser.add_argument("--centroid-weight", type=float, default=0.5)
    parser.add_argument("--max-dense-mb", type=float, default=512.0)
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = run_source_geometry_shift(
        task=args.task,
        shift_start_path=args.shift_start,
        shift_end_path=args.shift_end,
        base_path=args.base,
        output_path=args.output,
        panel_path=args.panel,
        celltype_key=args.celltype_key,
        damp=args.damp,
        centroid_weight=args.centroid_weight,
        max_dense_mb=args.max_dense_mb,
        overwrite=args.overwrite,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
