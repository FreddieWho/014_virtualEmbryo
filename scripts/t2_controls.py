#!/usr/bin/env python3
"""Build the official T2 adversarial reference-row controls.

These controls are scorer audits, not candidate predictors.  In particular,
``ctrl_random_cube`` uses the true target only to obtain its coordinate
bounding box; it must never be used as a model output or for model selection.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np

from scripts.t2_baseline import (
    DEFAULT_PANEL_DIR,
    TASK_PANEL_FILES,
    load_t2_input,
)


CONTROL_NAMES = ("ctrl_scale_ref", "ctrl_random_cube", "ctrl_squashed_ref")


def _replace_first_three_coords(a: ad.AnnData, coords: np.ndarray) -> None:
    """Replace the scored coordinates while retaining any extra columns."""

    original = np.asarray(a.obsm["spatial_3D"])
    if original.shape[1] == 3:
        a.obsm["spatial_3D"] = np.asarray(coords, dtype=np.float32)
        return
    updated = np.array(original, dtype=np.float32, copy=True)
    updated[:, :3] = np.asarray(coords, dtype=np.float32)
    a.obsm["spatial_3D"] = updated


def _control_metadata(
    *,
    task: str,
    control: str,
    reference_path: Path,
    target_path: Path | None,
    panel_path: Path,
    seed: int | None,
) -> dict[str, Any]:
    return {
        "task": task,
        "control": control,
        "audit_only": True,
        "reference_path": str(reference_path.resolve()),
        "target_path_for_bbox_only": (
            str(target_path.resolve()) if target_path is not None else None
        ),
        "panel_path": str(panel_path.resolve()),
        "seed": int(seed) if seed is not None else None,
    }


def run_control(
    *,
    task: str,
    control: str,
    reference_path: Path,
    output_path: Path,
    target_path: Path | None = None,
    panel_path: Path | None = None,
    seed: int = 0,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Write one official T2 control on the ordered board panel.

    ``target_path`` is mandatory only for ``ctrl_random_cube`` and is read
    solely for the minimum/maximum coordinate bounds.  The control's
    expression and cell rows always come from ``reference_path``.
    """

    task = task.lower()
    control = control.lower()
    if task not in TASK_PANEL_FILES:
        raise ValueError(f"Unsupported T2 task {task!r}; choose embryo or heart")
    if control not in CONTROL_NAMES:
        raise ValueError(f"Unsupported T2 control {control!r}; choose from {CONTROL_NAMES}")
    if seed < 0:
        raise ValueError("seed must be non-negative")
    if control != "ctrl_random_cube" and target_path is not None:
        raise ValueError(f"{control} does not read a target; omit target_path")

    panel_path = Path(panel_path) if panel_path else DEFAULT_PANEL_DIR / TASK_PANEL_FILES[task]
    reference_path = Path(reference_path)
    output_path = Path(output_path)
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output_path}; pass overwrite=True to replace it")

    reference = load_t2_input(reference_path, panel_path)
    target: ad.AnnData | None = None
    if control == "ctrl_random_cube":
        if target_path is None:
            raise ValueError("ctrl_random_cube requires target_path for its audit bounding box")
        target_path = Path(target_path)
        target = load_t2_input(target_path, panel_path)

    out = reference.copy()
    if control == "ctrl_scale_ref":
        out.X = reference.X * 2.0
    elif control == "ctrl_squashed_ref":
        coords = np.asarray(reference.obsm["spatial_3D"], dtype=np.float64)[:, :3]
        center = coords.mean(axis=0, keepdims=True)
        squashed = (coords - center) * np.array([4.0, 1.0, 0.25]) + center
        _replace_first_three_coords(out, squashed)
    else:
        assert target is not None
        target_coords = np.asarray(target.obsm["spatial_3D"], dtype=np.float64)[:, :3]
        lower = target_coords.min(axis=0)
        upper = target_coords.max(axis=0)
        rng = np.random.default_rng(seed)
        random_coords = rng.uniform(lower, upper, size=(reference.n_obs, 3))
        _replace_first_three_coords(out, random_coords)

    metadata = _control_metadata(
        task=task,
        control=control,
        reference_path=reference_path,
        target_path=target_path if control == "ctrl_random_cube" else None,
        panel_path=panel_path,
        seed=seed if control == "ctrl_random_cube" else None,
    )
    out.uns["ve_control"] = metadata
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
    parser.add_argument("--control", choices=CONTROL_NAMES, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--target", type=Path, help="Required only for ctrl_random_cube; bbox source only")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--panel", type=Path)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = run_control(
        task=args.task,
        control=args.control,
        reference_path=args.reference,
        target_path=args.target,
        output_path=args.output,
        panel_path=args.panel,
        seed=args.seed,
        overwrite=args.overwrite,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
