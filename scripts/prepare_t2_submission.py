#!/usr/bin/env python3
"""Prepare a board-valid T2 H5AD from a locally generated prediction.

This only performs deterministic cell-count sampling and contract validation;
it does not use a target or change expression/coordinates.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np

from scripts.t2_baseline import load_t2_input
from scripts.t2_pseudo_holdout import select_indices


BOARD_LIMITS = {
    ("embryo", "interp"): (583, 5000),
    ("heart", "interp"): (1000, 17616),
    ("heart", "extrap"): (1000, 25179),
}
PANEL_FILES = {
    ("embryo", "interp"): "T2__embryo__val_interp.genes.txt",
    ("heart", "interp"): "T2__heart__val_interp.genes.txt",
    ("heart", "extrap"): "T2__heart__val_extrap.genes.txt",
}


def prepare_submission(
    *,
    task: str,
    setting: str,
    input_path: Path,
    output_path: Path,
    n_cells: int,
    seed: int,
    strategy: str = "stratified",
    overwrite: bool = False,
) -> dict[str, Any]:
    task = task.lower()
    setting = setting.lower()
    key = (task, setting)
    if key not in BOARD_LIMITS:
        raise ValueError(f"Unsupported T2 board {task}/{setting}")
    lower, upper = BOARD_LIMITS[key]
    if not lower <= n_cells <= upper:
        raise ValueError(f"n_cells={n_cells} outside board limits [{lower}, {upper}]")
    if seed < 0:
        raise ValueError("seed must be non-negative")

    input_path = Path(input_path)
    output_path = Path(output_path)
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output_path}; pass overwrite=True to replace it")
    panel_path = Path(__file__).resolve().parents[1] / "data" / "gene_panel" / PANEL_FILES[key]
    source = load_t2_input(input_path, panel_path)
    if n_cells > source.n_obs:
        raise ValueError(f"n_cells={n_cells} exceeds input n_obs={source.n_obs}")
    if "celltype" not in source.obs:
        if strategy != "first":
            raise ValueError("stratified preparation requires source obs['celltype']")
        indices = np.arange(n_cells, dtype=np.int64)
    else:
        values = source.obs["celltype"]
        if values.isna().any():
            raise ValueError("source obs['celltype'] contains missing values")
        indices = select_indices(
            np.asarray(values.astype(str)),
            n_cells=n_cells,
            seed=seed,
            strategy=strategy,
        )

    out = source[indices].copy()
    metadata = {
        "board": f"T2:{task}:{'val_' + setting}",
        "task": "T2",
        "setting": setting,
        "source_path": str(input_path.resolve()),
        "panel_path": str(panel_path.resolve()),
        "n_cells": int(n_cells),
        "seed": int(seed),
        "sampling_strategy": strategy,
        "target_used": False,
        "submission_contract_validated": True,
    }
    out.uns["ve_submission_prep"] = metadata
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out.write_h5ad(output_path)
    checked = load_t2_input(output_path, panel_path)
    if not lower <= checked.n_obs <= upper:
        raise AssertionError("prepared output failed board cell-limit validation")
    metadata.update(
        {
            "output_path": str(output_path.resolve()),
            "n_obs": int(checked.n_obs),
            "n_vars": int(checked.n_vars),
            "spatial_3D_shape": list(np.asarray(checked.obsm["spatial_3D"]).shape),
        }
    )
    return metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=["embryo", "heart"], required=True)
    parser.add_argument("--setting", choices=["interp", "extrap"], required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--n-cells", type=int, required=True)
    parser.add_argument("--seed", type=int, default=20260821)
    parser.add_argument("--strategy", choices=["stratified", "first"], default="stratified")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = prepare_submission(
        task=args.task,
        setting=args.setting,
        input_path=args.input,
        output_path=args.output,
        n_cells=args.n_cells,
        seed=args.seed,
        strategy=args.strategy,
        overwrite=args.overwrite,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
