#!/usr/bin/env python3
"""Prepare board-valid T1/T3 floor baseline submission files.

The inputs are released reference stages only.  This script performs ordered
panel alignment, deterministic cell sampling, and task-specific output cleanup;
it never reads a held-out target.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np
from scipy import sparse

from scripts.t2_pseudo_holdout import select_indices


BOARD_CONFIG = {
    ("T1", "val"): {
        "min_cells": 1000,
        "max_cells": 5118,
        "panel": "T1__val.genes.txt",
        "needs_coords": False,
        "method": "copy_last",
    },
    ("T3", "gata4"): {
        "min_cells": 1000,
        "max_cells": 7449,
        "panel": "T3__gata4.genes.txt",
        "needs_coords": True,
        "method": "wt_identity",
    },
}


def _load_board_input(
    path: Path,
    panel_path: Path,
    *,
    needs_coords: bool,
    row_indices: np.ndarray | None = None,
) -> ad.AnnData:
    a = ad.read_h5ad(path, backed="r" if row_indices is not None else None)
    names = [str(g) for g in a.var_names]
    if len(set(names)) != len(names):
        raise ValueError(f"{path}: var_names contains duplicates")
    panel = [line.strip() for line in panel_path.read_text().splitlines() if line.strip()]
    missing = [g for g in panel if g not in set(names)]
    if missing:
        raise ValueError(f"{path}: missing panel genes, head={missing[:10]}")
    if row_indices is not None:
        view = a[row_indices, panel].to_memory()
        a.file.close()
        a = view
    else:
        a = a[:, panel].copy()
    if getattr(a.X, "ndim", None) != 2:
        raise ValueError(f"{path}: X must be a 2D matrix")
    if sparse.issparse(a.X):
        values = np.asarray(a.X.data)
    else:
        values = np.asarray(a.X)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError(f"{path}: X must be finite and non-negative")
    if needs_coords:
        if "spatial_3D" not in a.obsm:
            raise ValueError(f"{path}: missing obsm['spatial_3D']")
        coords = np.asarray(a.obsm["spatial_3D"])
        if coords.ndim != 2 or coords.shape[0] != a.n_obs or coords.shape[1] < 3:
            raise ValueError(f"{path}: spatial_3D has invalid shape {coords.shape}")
        if not np.isfinite(coords[:, :3]).all():
            raise ValueError(f"{path}: spatial_3D contains non-finite values")
    return a


def prepare_submission(
    *,
    task: str,
    board: str,
    input_path: Path,
    output_path: Path,
    n_cells: int,
    seed: int,
    overwrite: bool = False,
) -> dict[str, Any]:
    task = task.upper()
    key = (task, board.lower())
    if key not in BOARD_CONFIG:
        raise ValueError(f"Unsupported board {task}/{board}")
    config = BOARD_CONFIG[key]
    if not config["min_cells"] <= n_cells <= config["max_cells"]:
        raise ValueError(
            f"n_cells={n_cells} outside board limits "
            f"[{config['min_cells']}, {config['max_cells']}]"
        )
    if seed < 0:
        raise ValueError("seed must be non-negative")

    input_path = Path(input_path)
    output_path = Path(output_path)
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output_path}; pass overwrite=True to replace it")
    panel_path = Path(__file__).resolve().parents[1] / "data" / "gene_panel" / config["panel"]
    source_meta = ad.read_h5ad(input_path, backed="r")
    if n_cells > source_meta.n_obs:
        source_meta.file.close()
        raise ValueError(f"n_cells={n_cells} exceeds input n_obs={source_meta.n_obs}")
    if "celltype" not in source_meta.obs:
        source_meta.file.close()
        raise ValueError(f"{input_path}: celltype is required for deterministic stratified sampling")
    values = source_meta.obs["celltype"]
    if values.isna().any():
        source_meta.file.close()
        raise ValueError(f"{input_path}: celltype contains missing values")
    indices = select_indices(
        np.asarray(values.astype(str)), n_cells=n_cells, seed=seed, strategy="stratified"
    )
    source_meta.file.close()
    source = _load_board_input(
        input_path,
        panel_path,
        needs_coords=bool(config["needs_coords"]),
        row_indices=indices,
    )
    out = source.copy()
    if task == "T1":
        # T1 is dissociated RNA; do not carry over an input UMAP as submission coordinates.
        out.obsm.clear()
    else:
        coords = np.asarray(out.obsm["spatial_3D"], dtype=np.float32)[:, :3]
        out.obsm.clear()
        out.obsm["spatial_3D"] = coords

    metadata = {
        "board": f"{task}:{board.lower()}",
        "task": task,
        "method": config["method"],
        "source_path": str(input_path.resolve()),
        "panel_path": str(panel_path.resolve()),
        "n_cells": int(n_cells),
        "seed": int(seed),
        "sampling_strategy": "stratified",
        "target_used": False,
        "submission_contract_validated": True,
    }
    out.uns["ve_submission_prep"] = metadata
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out.write_h5ad(output_path)
    checked = _load_board_input(output_path, panel_path, needs_coords=bool(config["needs_coords"]))
    if not config["min_cells"] <= checked.n_obs <= config["max_cells"]:
        raise AssertionError("prepared output failed board cell-limit validation")
    if task == "T1" and checked.obsm:
        raise AssertionError("T1 output unexpectedly contains obsm entries")
    metadata.update(
        {
            "output_path": str(output_path.resolve()),
            "n_obs": int(checked.n_obs),
            "n_vars": int(checked.n_vars),
            "spatial_3D_shape": (
                list(np.asarray(checked.obsm["spatial_3D"]).shape)
                if "spatial_3D" in checked.obsm
                else None
            ),
        }
    )
    return metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=["T1", "T3"], required=True)
    parser.add_argument("--board", choices=["val", "gata4"], required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--n-cells", type=int, required=True)
    parser.add_argument("--seed", type=int, default=20260821)
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = prepare_submission(
        task=args.task,
        board=args.board,
        input_path=args.input,
        output_path=args.output,
        n_cells=args.n_cells,
        seed=args.seed,
        overwrite=args.overwrite,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
