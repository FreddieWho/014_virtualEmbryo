#!/usr/bin/env python3
"""Memory-bounded T2 floor and pseudobulk-shift baselines.

The public notebook is a tutorial over 150-cell samples.  This module keeps its
scientific rule but makes the data boundary explicit:

* ``previous_path`` supplies the earlier observed stage used to estimate a
  cell-type-specific shift;
* ``base_path`` supplies the cells whose expression and coordinates are copied
  or shifted (normally the latest observed/reference cells);
* all inputs are aligned to the official T2 board panel before computation.

The T2 matrices are small enough for a guarded dense prediction buffer.  The
guard is intentional: it prevents this runner from being reused silently on a
large T1 matrix, where a sparse/chunked implementation is required instead.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np
from scipy import sparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PANEL_DIR = PROJECT_ROOT / "data" / "gene_panel"
TASK_PANEL_FILES = {
    "embryo": "T2__embryo__val_interp.genes.txt",
    "heart": "T2__heart__val_interp.genes.txt",
}


def read_panel(panel_path: Path) -> list[str]:
    """Read an ordered, unique gene panel."""

    genes = [line.strip() for line in Path(panel_path).read_text().splitlines() if line.strip()]
    if not genes:
        raise ValueError(f"Gene panel is empty: {panel_path}")
    if len(set(genes)) != len(genes):
        raise ValueError(f"Gene panel contains duplicate genes: {panel_path}")
    return genes


def _matrix_check(X: Any, path: Path) -> None:
    if getattr(X, "ndim", None) != 2:
        raise ValueError(f"{path}: X must be a 2D matrix, got ndim={getattr(X, 'ndim', None)}")
    if sparse.issparse(X):
        values = np.asarray(X.data)
        if not np.isfinite(values).all():
            raise ValueError(f"{path}: X contains NaN or infinite stored values")
        if (values < 0).any():
            raise ValueError(f"{path}: X contains negative stored values")
    else:
        values = np.asarray(X)
        if not np.isfinite(values).all():
            raise ValueError(f"{path}: X contains NaN or infinite values")
        if (values < 0).any():
            raise ValueError(f"{path}: X contains negative values")


def _spatial_check(a: ad.AnnData, path: Path) -> None:
    if "spatial_3D" not in a.obsm:
        raise ValueError(f"{path}: T2 input requires obsm['spatial_3D']")
    coords = np.asarray(a.obsm["spatial_3D"])
    if coords.ndim != 2 or coords.shape[0] != a.n_obs or coords.shape[1] < 3:
        raise ValueError(
            f"{path}: spatial_3D must have shape (n_obs, >=3), got {coords.shape}"
        )
    if not np.isfinite(coords).all():
        raise ValueError(f"{path}: spatial_3D contains NaN or infinite values")


def load_t2_input(path: Path, panel_path: Path) -> ad.AnnData:
    """Load one T2 input and align it to the official ordered panel.

    The early embryo release can contain the two genes absent from the official
    498-gene board.  They are dropped by ordered slicing; arbitrary missing
    panel genes or duplicate var names fail closed.
    """

    path = Path(path)
    panel = read_panel(panel_path)
    a = ad.read_h5ad(path)
    genes = [str(g) for g in a.var_names]
    if len(set(genes)) != len(genes):
        raise ValueError(f"{path}: var_names contains duplicates")
    if genes != panel:
        present = set(genes)
        missing = [g for g in panel if g not in present]
        if missing:
            raise ValueError(
                f"{path}: missing panel genes (head={missing[:10]}); "
                f"expected {len(panel)} board genes, got {len(genes)}"
            )
        a = a[:, panel].copy()
    if [str(g) for g in a.var_names] != panel:
        raise ValueError(f"{path}: failed to align var_names to panel order")
    _matrix_check(a.X, path)
    _spatial_check(a, path)
    return a


def _dense_prediction_buffer(X: Any, *, path: Path, max_dense_mb: float) -> np.ndarray:
    """Create a mutable float32 buffer with an explicit T2 memory guard."""

    n_obs, n_vars = X.shape
    one_buffer_mb = n_obs * n_vars * np.dtype(np.float32).itemsize / (1024**2)
    # The calculation holds the source conversion and the prediction buffer
    # briefly, so guard two float32 buffers rather than only one.
    estimated_mb = 2.0 * one_buffer_mb
    if estimated_mb > max_dense_mb:
        raise MemoryError(
            f"{path}: T2 prediction would need about {estimated_mb:.1f} MiB of dense buffers, "
            f"above max_dense_mb={max_dense_mb:.1f}; use a sparse/chunked runner"
        )
    if sparse.issparse(X):
        dense = X.toarray()
    else:
        dense = np.asarray(X)
    dense = np.array(dense, dtype=np.float32, copy=True)
    if not np.isfinite(dense).all() or (dense < 0).any():
        raise ValueError(f"{path}: dense prediction buffer is not finite and nonnegative")
    return dense


def _normalize_log1p_rows(X: np.ndarray, target_library_size: float) -> np.ndarray:
    """Renormalize log1p-normalized rows to an explicit implied library size."""

    if not np.isfinite(target_library_size) or target_library_size <= 0:
        raise ValueError("target_library_size must be a positive finite number")
    raw = np.expm1(np.clip(np.asarray(X, dtype=np.float64), 0, 50))
    totals = raw.sum(axis=1, keepdims=True)
    if not np.isfinite(raw).all() or (totals <= 0).any():
        raise ValueError("cannot normalize rows with non-finite values or zero implied library size")
    normalized = raw * (float(target_library_size) / totals)
    return np.log1p(normalized).astype(np.float32, copy=False)


def _celltypes(a: ad.AnnData, key: str, path: Path) -> np.ndarray:
    if key not in a.obs:
        raise ValueError(f"{path}: required celltype column {key!r} is absent")
    values = a.obs[key]
    if values.isna().any():
        raise ValueError(f"{path}: celltype column {key!r} contains missing values")
    return np.asarray(values.astype(str))


def _summary_metadata(
    *,
    task: str,
    method: str,
    previous_path: Path | None,
    base_path: Path,
    panel_path: Path,
    damp: float,
    shifted_cells: int,
    max_abs_delta: float,
) -> dict[str, Any]:
    return {
        "task": task,
        "method": method,
        "previous_path": str(previous_path.resolve()) if previous_path else None,
        "base_path": str(base_path.resolve()),
        "panel_path": str(panel_path.resolve()),
        "damp": float(damp),
        "shifted_cells": int(shifted_cells),
        "max_abs_delta": float(max_abs_delta),
    }


def run_stage_shift(
    *,
    task: str,
    shift_start_path: Path,
    shift_end_path: Path,
    base_path: Path,
    output_path: Path,
    panel_path: Path | None = None,
    celltype_key: str = "celltype",
    damp: float = 1.0,
    target_library_size: float | None = None,
    max_dense_mb: float = 512.0,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Apply a learned stage-to-stage shift to an explicit carrier stage.

    This is the primitive used by the configured pseudo-holdouts.  The shift
    is estimated as ``mean(shift_end) - mean(shift_start)`` per cell type and
    applied to ``base`` with ``damp``.  A negative damp moves the late carrier
    backward for interpolation; a damp greater than one performs forward
    extrapolation.  Geometry always comes from ``base``.
    """

    task = task.lower()
    if task not in TASK_PANEL_FILES:
        raise ValueError(f"Unsupported T2 task {task!r}; choose embryo or heart")
    if not np.isfinite(damp):
        raise ValueError("damp must be finite")
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

    def means_by_type(a: ad.AnnData, types: np.ndarray) -> dict[str, np.ndarray]:
        result: dict[str, np.ndarray] = {}
        for celltype in np.unique(types):
            rows = a.X[types == celltype]
            if sparse.issparse(rows):
                mean = np.asarray(rows.mean(axis=0)).ravel()
            else:
                mean = np.asarray(rows, dtype=np.float32).mean(axis=0)
            result[celltype] = np.asarray(mean, dtype=np.float32)
        return result

    start_means = means_by_type(shift_start, start_types)
    end_means = means_by_type(shift_end, end_types)
    shifted_cells = 0
    max_abs_delta = 0.0
    for celltype in np.unique(base_types):
        if celltype not in start_means or celltype not in end_means:
            continue
        mask = base_types == celltype
        delta = end_means[celltype] - start_means[celltype]
        base_X[mask] += float(damp) * delta
        shifted_cells += int(mask.sum())
        if delta.size:
            max_abs_delta = max(max_abs_delta, float(np.max(np.abs(delta))))

    out = base.copy()
    base_X = np.clip(base_X, 0, None).astype(np.float32, copy=False)
    if target_library_size is not None:
        base_X = _normalize_log1p_rows(base_X, float(target_library_size))
    out.X = base_X
    metadata = {
        "task": task,
        "method": "pseudobulk_shift_stage_proxy",
        "shift_start_path": str(shift_start_path.resolve()),
        "shift_end_path": str(shift_end_path.resolve()),
        "base_path": str(base_path.resolve()),
        "panel_path": str(panel_path.resolve()),
        "damp": float(damp),
        "normalization": (
            "rowwise_log1p_library_size" if target_library_size is not None else "none"
        ),
        "target_library_size": (
            float(target_library_size) if target_library_size is not None else None
        ),
        "shifted_cells": int(shifted_cells),
        "max_abs_delta": float(max_abs_delta),
    }
    out.uns["ve_baseline"] = metadata
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


def run_baseline(
    *,
    task: str,
    method: str,
    previous_path: Path | None,
    base_path: Path,
    output_path: Path,
    panel_path: Path | None = None,
    celltype_key: str = "celltype",
    damp: float = 1.0,
    max_dense_mb: float = 512.0,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Run one T2 baseline and write a board-aligned H5AD prediction."""

    task = task.lower()
    method = method.lower()
    if task not in TASK_PANEL_FILES:
        raise ValueError(f"Unsupported T2 task {task!r}; choose embryo or heart")
    if method not in {"copy_last", "pseudobulk_shift"}:
        raise ValueError(f"Unsupported T2 baseline {method!r}")
    if not np.isfinite(damp):
        raise ValueError("damp must be finite")
    if max_dense_mb <= 0 or not np.isfinite(max_dense_mb):
        raise ValueError("max_dense_mb must be a positive finite number")

    panel_path = Path(panel_path) if panel_path else DEFAULT_PANEL_DIR / TASK_PANEL_FILES[task]
    base_path = Path(base_path)
    output_path = Path(output_path)
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output_path}; pass overwrite=True to replace it")

    base = load_t2_input(base_path, panel_path)
    shifted_cells = 0
    max_abs_delta = 0.0

    if method == "copy_last":
        if previous_path is not None:
            # Validate an explicitly supplied previous file even though the
            # floor does not use it; this prevents accidental panel mixing.
            load_t2_input(Path(previous_path), panel_path)
        out = base.copy()
    else:
        if previous_path is None:
            raise ValueError("pseudobulk_shift requires previous_path")
        previous_path = Path(previous_path)
        previous = load_t2_input(previous_path, panel_path)
        previous_types = _celltypes(previous, celltype_key, previous_path)
        base_types = _celltypes(base, celltype_key, base_path)
        base_X = _dense_prediction_buffer(base.X, path=base_path, max_dense_mb=max_dense_mb)

        previous_means: dict[str, np.ndarray] = {}
        for celltype in np.unique(previous_types):
            mask = previous_types == celltype
            rows = previous.X[mask]
            if sparse.issparse(rows):
                mean = np.asarray(rows.mean(axis=0)).ravel()
            else:
                mean = np.asarray(rows, dtype=np.float32).mean(axis=0)
            previous_means[celltype] = np.asarray(mean, dtype=np.float32)

        for celltype in np.unique(base_types):
            mask = base_types == celltype
            if celltype not in previous_means:
                continue
            delta = base_X[mask].mean(axis=0) - previous_means[celltype]
            base_X[mask] += float(damp) * delta
            shifted_cells += int(mask.sum())
            if delta.size:
                max_abs_delta = max(max_abs_delta, float(np.max(np.abs(delta))))

        out = base.copy()
        out.X = np.clip(base_X, 0, None).astype(np.float32, copy=False)

    metadata = _summary_metadata(
        task=task,
        method=method,
        previous_path=Path(previous_path) if previous_path else None,
        base_path=base_path,
        panel_path=panel_path,
        damp=damp,
        shifted_cells=shifted_cells,
        max_abs_delta=max_abs_delta,
    )
    out.uns["ve_baseline"] = metadata
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
    parser.add_argument("--method", choices=["copy_last", "pseudobulk_shift"], default="pseudobulk_shift")
    parser.add_argument("--previous", type=Path, help="Earlier observed stage used for pseudobulk_shift")
    parser.add_argument("--base", type=Path, required=True, help="Cells to copy or shift")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--panel", type=Path, help="Override the official task panel file")
    parser.add_argument("--celltype-key", default="celltype")
    parser.add_argument("--damp", type=float, default=1.0)
    parser.add_argument("--max-dense-mb", type=float, default=512.0)
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = run_baseline(
        task=args.task,
        method=args.method,
        previous_path=args.previous,
        base_path=args.base,
        output_path=args.output,
        panel_path=args.panel,
        celltype_key=args.celltype_key,
        damp=args.damp,
        max_dense_mb=args.max_dense_mb,
        overwrite=args.overwrite,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
