#!/usr/bin/env python3
"""Low-capacity, target-blind expression-only T2 stage-shift candidate."""

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
        PROJECT_ROOT,
        TASK_PANEL_FILES,
        _celltypes,
        _dense_prediction_buffer,
        _normalize_log1p_rows,
        load_t2_input,
    )
except ImportError:  # direct ``python scripts/t2_expression_model.py`` execution
    from t2_baseline import (
        DEFAULT_PANEL_DIR,
        PROJECT_ROOT,
        TASK_PANEL_FILES,
        _celltypes,
        _dense_prediction_buffer,
        _normalize_log1p_rows,
        load_t2_input,
    )


def _means_by_type(a: ad.AnnData, celltypes: np.ndarray) -> dict[str, np.ndarray]:
    result: dict[str, np.ndarray] = {}
    for celltype in np.unique(celltypes):
        rows = a.X[celltypes == celltype]
        if sparse.issparse(rows):
            mean = np.asarray(rows.mean(axis=0)).ravel()
        else:
            mean = np.asarray(rows, dtype=np.float32).mean(axis=0)
        result[celltype] = np.asarray(mean, dtype=np.float32)
    return result


def run_shrunk_stage_shift(
    *,
    task: str,
    shift_start_path: Path,
    shift_end_path: Path,
    base_path: Path,
    output_path: Path,
    panel_path: Path | None = None,
    celltype_key: str = "celltype",
    damp: float = 1.0,
    celltype_weight: float = 0.5,
    target_library_size: float | None = None,
    max_dense_mb: float = 512.0,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Apply a fixed shrinkage mixture of celltype and pooled stage shifts.

    The candidate is expression-only: ``base.obsm`` and all observation rows
    are carried through unchanged.  It uses only the two source stages and a
    pre-registered ``celltype_weight``; no target metadata is read.
    """

    task = task.lower()
    if task not in TASK_PANEL_FILES:
        raise ValueError(f"Unsupported T2 task {task!r}; choose embryo or heart")
    if not np.isfinite(damp):
        raise ValueError("damp must be finite")
    if not np.isfinite(celltype_weight) or not 0 <= celltype_weight <= 1:
        raise ValueError("celltype_weight must be in [0, 1]")
    if target_library_size is not None and (
        not np.isfinite(target_library_size) or target_library_size <= 0
    ):
        raise ValueError("target_library_size must be positive and finite")
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
    base_X = _dense_prediction_buffer(base.X, path=base_path, max_dense_mb=max_dense_mb)

    start_means = _means_by_type(shift_start, start_types)
    end_means = _means_by_type(shift_end, end_types)
    if sparse.issparse(shift_start.X):
        global_start = np.asarray(shift_start.X.mean(axis=0)).ravel()
    else:
        global_start = np.asarray(shift_start.X, dtype=np.float32).mean(axis=0)
    if sparse.issparse(shift_end.X):
        global_end = np.asarray(shift_end.X.mean(axis=0)).ravel()
    else:
        global_end = np.asarray(shift_end.X, dtype=np.float32).mean(axis=0)
    global_delta = np.asarray(global_end - global_start, dtype=np.float32)

    shifted_cells = 0
    max_abs_delta = 0.0
    fallback_celltypes: list[str] = []
    for celltype in np.unique(base_types):
        mask = base_types == celltype
        if celltype in start_means and celltype in end_means:
            celltype_delta = end_means[celltype] - start_means[celltype]
            delta = (
                float(celltype_weight) * celltype_delta
                + (1.0 - float(celltype_weight)) * global_delta
            )
        else:
            delta = global_delta
            fallback_celltypes.append(str(celltype))
        base_X[mask] += float(damp) * delta
        shifted_cells += int(mask.sum())
        if delta.size:
            max_abs_delta = max(max_abs_delta, float(np.max(np.abs(delta))))

    out = base.copy()
    base_X = np.clip(base_X, 0, None).astype(np.float32, copy=False)
    if target_library_size is not None:
        base_X = _normalize_log1p_rows(base_X, float(target_library_size))
    out.X = base_X
    metadata: dict[str, Any] = {
        "task": task,
        "method": "shrunk_pseudobulk_shift_expression_only",
        "shift_start_path": str(shift_start_path.resolve()),
        "shift_end_path": str(shift_end_path.resolve()),
        "base_path": str(base_path.resolve()),
        "panel_path": str(panel_path.resolve()),
        "celltype_key": celltype_key,
        "damp": float(damp),
        "celltype_weight": float(celltype_weight),
        "global_weight": float(1.0 - celltype_weight),
        "normalization": (
            "rowwise_log1p_library_size"
            if target_library_size is not None
            else "none"
        ),
        "target_library_size": (
            float(target_library_size) if target_library_size is not None else None
        ),
        "aggregation": "cell_weighted_pooled_no_sample_id",
        "fallback_celltypes": sorted(fallback_celltypes),
        "shifted_cells": int(shifted_cells),
        "max_abs_delta": float(max_abs_delta),
        "geometry_invariant": "base_obsm_unchanged",
    }
    out.uns["ve_expression_model"] = metadata
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
    parser.add_argument("--damp", type=float, required=True)
    parser.add_argument("--celltype-weight", type=float, default=0.5)
    parser.add_argument("--target-library-size", type=float)
    parser.add_argument("--max-dense-mb", type=float, default=512.0)
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = run_shrunk_stage_shift(
        task=args.task,
        shift_start_path=args.shift_start,
        shift_end_path=args.shift_end,
        base_path=args.base,
        output_path=args.output,
        panel_path=args.panel,
        celltype_key=args.celltype_key,
        damp=args.damp,
        celltype_weight=args.celltype_weight,
        target_library_size=args.target_library_size,
        max_dense_mb=args.max_dense_mb,
        overwrite=args.overwrite,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
