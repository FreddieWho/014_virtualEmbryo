#!/usr/bin/env python3
"""Create post-hoc T2 expression/geometry attribution variants.

Replacing prediction coordinates with target coordinates is an oracle
diagnostic.  It must be run after prediction and never used to claim a valid
submission or to tune a model without an explicit leakage boundary.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np


def replace_geometry(
    expression_path: Path,
    geometry_path: Path,
    output_path: Path,
    *,
    label: str,
    overwrite: bool = False,
) -> dict[str, Any]:
    expression_path = Path(expression_path)
    geometry_path = Path(geometry_path)
    output_path = Path(output_path)
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output_path}; pass overwrite=True")
    expression = ad.read_h5ad(expression_path)
    geometry = ad.read_h5ad(geometry_path)
    if expression.shape != geometry.shape:
        raise ValueError(
            f"Expression and geometry files must have the same shape; "
            f"got {expression.shape} vs {geometry.shape}"
        )
    if [str(g) for g in expression.var_names] != [str(g) for g in geometry.var_names]:
        raise ValueError("Expression and geometry var_names/order do not match")
    if "spatial_3D" not in geometry.obsm:
        raise ValueError(f"{geometry_path}: missing obsm['spatial_3D']")
    coords = np.asarray(geometry.obsm["spatial_3D"], dtype=np.float32)
    if coords.ndim != 2 or coords.shape[0] != expression.n_obs or coords.shape[1] < 3:
        raise ValueError(f"Invalid spatial_3D shape: {coords.shape}")
    if not np.isfinite(coords).all():
        raise ValueError("geometry spatial_3D contains non-finite values")

    out = expression.copy()
    out.obsm["spatial_3D"] = np.array(coords[:, :3], dtype=np.float32, copy=True)
    metadata = {
        "method": "geometry_attribution",
        "geometry_label": label,
        "expression_path": str(expression_path.resolve()),
        "geometry_path": str(geometry_path.resolve()),
        "oracle_geometry": label.lower().startswith("oracle"),
        "n_obs": int(out.n_obs),
        "n_vars": int(out.n_vars),
    }
    out.uns["ve_attribution"] = metadata
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out.write_h5ad(output_path)
    metadata["output_path"] = str(output_path.resolve())
    return metadata


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expression", type=Path, required=True)
    parser.add_argument("--geometry", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    print(
        json.dumps(
            replace_geometry(
                args.expression,
                args.geometry,
                args.output,
                label=args.label,
                overwrite=args.overwrite,
            ),
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
