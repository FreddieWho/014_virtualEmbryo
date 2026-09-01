#!/usr/bin/env python3
"""Run the starter-pack T2 pseudo-holdout proxies reproducibly.

These are model-selection checks, not official validation.  Each proxy hides
the configured target stage from the predictor and uses two other public
stages to estimate a per-cell-type temporal shift.  The late training stage is
the carrier for expression and local-frame geometry; a signed damp moves it
backward for interpolation or forward for extrapolation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np

try:
    from .t2_baseline import PROJECT_ROOT, load_t2_input, run_baseline, run_stage_shift
    from .t2_expression_model import run_shrunk_stage_shift
except ImportError:  # direct ``python scripts/t2_pseudo_holdout.py`` execution
    from t2_baseline import PROJECT_ROOT, load_t2_input, run_baseline, run_stage_shift
    from t2_expression_model import run_shrunk_stage_shift


BOARD_LIMITS = {
    ("embryo", "interp"): (583, 5000),
    ("heart", "interp"): (1000, 17616),
    ("heart", "extrap"): (1000, 25179),
}
DEFAULT_TARGET_LIBRARY_SIZE = 10_000.0
DEFAULT_CELLTYPE_WEIGHT = 0.5


PROXIES: dict[str, dict[str, Any]] = {
    "T2_heart_interp_proxy": {
        "task": "heart",
        "setting": "interp",
        "fidelity": "MEDIUM_HIGH",
        "shift_start": "E8.25_late.h5ad",
        "shift_end": "E9.5.h5ad",
        "base": "E9.5.h5ad",
        "target": "E8.75.h5ad",
        "reference": "E9.5.h5ad",
        "damp": -0.6,
        "limitation": "official interpolation target is E8.5; stage spacing differs",
    },
    "T2_heart_extrap_proxy": {
        "task": "heart",
        "setting": "extrap",
        "fidelity": "MEDIUM",
        "shift_start": "E8.25_late.h5ad",
        "shift_end": "E8.75.h5ad",
        "base": "E8.75.h5ad",
        "target": "E9.5.h5ad",
        "reference": "E8.75.h5ad",
        "damp": 1.5,
        "limitation": "does not validate long-range E10.5/E12.5 extrapolation",
    },
    "T2_embryo_interp_proxy": {
        "task": "embryo",
        "setting": "interp",
        "fidelity": "MEDIUM",
        "shift_start": "E6.75.h5ad",
        "shift_end": "E8.0.h5ad",
        "base": "E8.0.h5ad",
        "target": "E7.25.h5ad",
        "reference": "E8.0.h5ad",
        "damp": -0.6,
        "limitation": "official targets E7.5/E7.75 occupy a later gastrulation window",
    },
}


def _data_path(name: str) -> Path:
    return PROJECT_ROOT / "data" / name


def validate_board(path: Path, *, task: str, setting: str, enforce_cell_limits: bool) -> dict[str, Any]:
    """Validate one H5AD against the panel and, optionally, board cell limits."""

    panel_name = {
        "embryo": "T2__embryo__val_interp.genes.txt",
        "heart": "T2__heart__val_interp.genes.txt",
    }[task]
    panel_path = PROJECT_ROOT / "data" / "gene_panel" / panel_name
    a = load_t2_input(path, panel_path)
    limits = BOARD_LIMITS[(task, setting)]
    if enforce_cell_limits and not (limits[0] <= a.n_obs <= limits[1]):
        raise ValueError(
            f"{path}: n_obs={a.n_obs} outside {task}/{setting} board limits {limits}"
        )
    return {
        "path": str(path.resolve()),
        "task": task,
        "setting": setting,
        "n_obs": int(a.n_obs),
        "n_vars": int(a.n_vars),
        "spatial_3D_shape": list(a.obsm["spatial_3D"].shape),
        "cell_limits": list(limits),
        "cell_limits_checked": bool(enforce_cell_limits),
    }


def select_indices(
    celltypes: np.ndarray,
    *,
    n_cells: int,
    seed: int,
    strategy: str = "stratified",
) -> np.ndarray:
    """Select reproducible indices, proportionally stratified by cell type."""

    values = np.asarray(celltypes).astype(str)
    if values.ndim != 1:
        raise ValueError("celltypes must be one-dimensional")
    if n_cells < 1 or n_cells > len(values):
        raise ValueError(f"n_cells must be in [1, {len(values)}], got {n_cells}")
    if strategy == "first":
        return np.arange(n_cells, dtype=np.int64)
    if strategy != "stratified":
        raise ValueError("strategy must be first or stratified")
    if not np.isfinite(seed):
        raise ValueError("seed must be finite")

    groups = sorted(np.unique(values).tolist())
    group_indices = {group: np.flatnonzero(values == group) for group in groups}
    counts = np.asarray([len(group_indices[group]) for group in groups], dtype=float)
    exact = counts * float(n_cells) / float(len(values))
    take = np.floor(exact).astype(int)
    remainder = int(n_cells - int(take.sum()))
    fractions = exact - take
    # Stable lexical tie-breaking makes allocations reproducible even when
    # two groups have the same fractional remainder.
    order = sorted(range(len(groups)), key=lambda i: (-fractions[i], groups[i]))
    for i in order[:remainder]:
        take[i] += 1

    rng = np.random.default_rng(int(seed))
    selected = []
    for i, group in enumerate(groups):
        selected.append(rng.choice(group_indices[group], size=int(take[i]), replace=False))
    return np.sort(np.concatenate(selected).astype(np.int64))


def _write_slice(
    source: Path,
    destination: Path,
    *,
    panel_path: Path,
    n_cells: int,
    seed: int,
    strategy: str,
    stratify_key: str = "celltype",
) -> dict[str, Any]:
    a = load_t2_input(source, panel_path)
    if stratify_key not in a.obs:
        raise ValueError(f"{source}: cannot stratify because {stratify_key!r} is absent")
    values = a.obs[stratify_key]
    if values.isna().any():
        raise ValueError(f"{source}: {stratify_key!r} contains missing values")
    indices = select_indices(
        np.asarray(values.astype(str)), n_cells=n_cells, seed=seed, strategy=strategy
    )
    sliced = a[indices].copy()
    destination.parent.mkdir(parents=True, exist_ok=True)
    sliced.write_h5ad(destination)
    return {
        "path": str(destination.resolve()),
        "n_obs": int(sliced.n_obs),
        "n_vars": int(sliced.n_vars),
        "seed": int(seed),
        "sampling_strategy": strategy,
        "stratify_key": stratify_key,
        "celltype_counts": {
            str(key): int(value) for key, value in sliced.obs[stratify_key].astype(str).value_counts().sort_index().items()
        },
        "selected_index_head": indices[:10].tolist(),
    }


def run_proxy(
    name: str,
    *,
    method: str = "pseudobulk_shift",
    output_path: Path,
    score_dir: Path | None = None,
    score_cells: int = 1000,
    seed: int = 20260818,
    sampling_strategy: str = "stratified",
    stratify_key: str = "celltype",
    max_dense_mb: float = 512.0,
    overwrite: bool = False,
) -> dict[str, Any]:
    if name not in PROXIES:
        raise ValueError(f"Unknown proxy {name!r}; choose from {sorted(PROXIES)}")
    if method not in {
        "copy_last",
        "pseudobulk_shift",
        "pseudobulk_shift_row_norm",
        "shrunk_pseudobulk_shift",
    }:
        raise ValueError(
            "method must be copy_last, pseudobulk_shift, pseudobulk_shift_row_norm, "
            "or shrunk_pseudobulk_shift"
        )
    cfg = PROXIES[name]
    task = str(cfg["task"])
    setting = str(cfg["setting"])
    panel_name = {
        "embryo": "T2__embryo__val_interp.genes.txt",
        "heart": "T2__heart__val_interp.genes.txt",
    }[task]
    panel_path = PROJECT_ROOT / "data" / "gene_panel" / panel_name
    limits = BOARD_LIMITS[(task, setting)]
    if not (limits[0] <= score_cells <= limits[1]):
        raise ValueError(f"score_cells={score_cells} outside {task}/{setting} limits {limits}")

    output_path = Path(output_path)
    if method == "copy_last":
        result_meta = run_baseline(
            task=task,
            method="copy_last",
            previous_path=None,
            base_path=_data_path(str(cfg["base"])),
            output_path=output_path,
            panel_path=panel_path,
            max_dense_mb=max_dense_mb,
            overwrite=overwrite,
        )
    elif method in {"pseudobulk_shift", "pseudobulk_shift_row_norm"}:
        result_meta = run_stage_shift(
            task=task,
            shift_start_path=_data_path(str(cfg["shift_start"])),
            shift_end_path=_data_path(str(cfg["shift_end"])),
            base_path=_data_path(str(cfg["base"])),
            output_path=output_path,
            panel_path=panel_path,
            damp=float(cfg["damp"]),
            target_library_size=(
                DEFAULT_TARGET_LIBRARY_SIZE if method == "pseudobulk_shift_row_norm" else None
            ),
            max_dense_mb=max_dense_mb,
            overwrite=overwrite,
        )
    else:
        result_meta = run_shrunk_stage_shift(
            task=task,
            shift_start_path=_data_path(str(cfg["shift_start"])),
            shift_end_path=_data_path(str(cfg["shift_end"])),
            base_path=_data_path(str(cfg["base"])),
            output_path=output_path,
            panel_path=panel_path,
            damp=float(cfg["damp"]),
            celltype_weight=DEFAULT_CELLTYPE_WEIGHT,
            max_dense_mb=max_dense_mb,
            overwrite=overwrite,
        )
    result_meta["proxy_method"] = method
    full_validation = validate_board(
        output_path, task=task, setting=setting, enforce_cell_limits=False
    )

    summary: dict[str, Any] = {
        "proxy": name,
        "fidelity": cfg["fidelity"],
        "limitation": cfg["limitation"],
        "config": cfg,
        "prediction": result_meta,
        "prediction_validation": full_validation,
    }

    if score_dir is not None:
        score_dir = Path(score_dir)
        if score_dir.exists() and any(score_dir.iterdir()) and not overwrite:
            raise FileExistsError(f"Score directory is not empty: {score_dir}; pass --overwrite")
        score_dir.mkdir(parents=True, exist_ok=True)
        names = {
            "input": output_path,
            "target": _data_path(str(cfg["target"])),
            "reference": _data_path(str(cfg["reference"])),
        }
        score_files = {}
        for role, source in names.items():
            destination = score_dir / f"{role}.h5ad"
            score_files[role] = _write_slice(
                source,
                destination,
                panel_path=panel_path,
                n_cells=score_cells,
                seed=seed,
                strategy=sampling_strategy,
                stratify_key=stratify_key,
            )
            score_files[role]["validation"] = validate_board(
                destination, task=task, setting=setting, enforce_cell_limits=True
            )
        summary["score_slice"] = {
            "n_cells": score_cells,
            "seed": int(seed),
            "sampling_strategy": sampling_strategy,
            "stratify_key": stratify_key,
            "files": score_files,
            "scorer_command": (
                "env LD_LIBRARY_PATH=/opt/anaconda3/lib PYTHONPATH=third_party/veckit "
                f"python3 third_party/veckit/score_h5ad.py --task T2 --setting {task} "
                f"--input {score_dir / 'input.h5ad'} --target {score_dir / 'target.h5ad'} "
                f"--reference {score_dir / 'reference.h5ad'} "
                f"--out {score_dir / 'score.json'}"
            ),
        }
        (score_dir / "manifest.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proxy", choices=sorted(PROXIES), required=True)
    parser.add_argument(
        "--method",
        choices=[
            "copy_last",
            "pseudobulk_shift",
            "pseudobulk_shift_row_norm",
            "shrunk_pseudobulk_shift",
        ],
        default="pseudobulk_shift",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--score-dir", type=Path)
    parser.add_argument("--score-cells", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260818)
    parser.add_argument("--sampling-strategy", choices=["first", "stratified"], default="stratified")
    parser.add_argument("--stratify-key", default="celltype")
    parser.add_argument("--max-dense-mb", type=float, default=512.0)
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(
        json.dumps(
            run_proxy(
                args.proxy,
                method=args.method,
                output_path=args.output,
                score_dir=args.score_dir,
                score_cells=args.score_cells,
                seed=args.seed,
                sampling_strategy=args.sampling_strategy,
                stratify_key=args.stratify_key,
                max_dense_mb=args.max_dense_mb,
                overwrite=args.overwrite,
            ),
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
