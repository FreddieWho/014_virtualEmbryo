#!/usr/bin/env python3
"""B4-P0 exact-floor candidate builder.

Constructs official-semantics no-change floor candidates:

- T1 copy_last: last observed stage (E9.5_RNA) submitted unchanged;
- T3 wt_identity: matched WT (E8.75) submitted unchanged.

The official floor bundle's row-subset rule is not public (see
FLOOR_PARITY_ANALYSIS.md). Contract cell caps force a subset, so this script
applies one pre-declared deterministic rule and nothing else:

1. no use of obs.celltype (no stratification);
2. uniform random draw without replacement, numpy default_rng(seed);
3. selected rows keep their original relative order;
4. expression matrix copied unchanged (float32, no shift/clip/normalization);
5. T1: no obsm; T3: spatial_3D kept, cast to float32[:, :3] per contract doc;
6. source obs columns kept; uns carries only source palettes/log1p plus a
   provenance marker.

It never reads any held-out target. target_used=False by construction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import anndata as ad
import numpy as np
from scipy import sparse

REPO = Path(__file__).resolve().parents[2]

BOARD_CONFIG = {
    ("T1", "val"): {
        "source": "data/E9.5_RNA.h5ad",
        "panel": "T1__val.genes.txt",
        "max_cells": 5118,
        "needs_coords": False,
        "method": "copy_last",
    },
    ("T3", "gata4"): {
        "source": "data/E8.75.h5ad",
        "panel": "T3__gata4.genes.txt",
        "max_cells": 7449,
        "needs_coords": True,
        "method": "wt_identity",
    },
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def build(task: str, board: str, out_path: Path, seed: int, overwrite: bool, n_cells: int | None = None) -> dict:
    key = (task.upper(), board.lower())
    cfg = BOARD_CONFIG[key]
    src_path = REPO / cfg["source"]
    panel = [l.strip() for l in (REPO / "data" / "gene_panel" / cfg["panel"]).read_text().splitlines() if l.strip()]

    meta = ad.read_h5ad(src_path, backed="r")
    n_src = meta.n_obs
    src_obs_names = list(meta.obs_names)
    meta.file.close()

    rng = np.random.default_rng(seed)
    n_take = cfg["max_cells"] if n_cells is None else int(n_cells)
    assert 1000 <= n_take <= n_src, f"n_cells={n_take} outside [1000, source {n_src}]"
    chosen = np.sort(rng.choice(n_src, size=n_take, replace=False))
    # np.sort keeps original relative order (indices ascending == file order).

    a = ad.read_h5ad(src_path, backed="r")
    names = [str(g) for g in a.var_names]
    assert len(set(names)) == len(names), "duplicate var_names"
    missing = [g for g in panel if g not in set(names)]
    assert not missing, f"missing panel genes: {missing[:5]}"
    view = a[chosen, panel].to_memory()
    a.file.close()

    X = view.X
    vals = np.asarray(X.data if sparse.issparse(X) else X)
    assert np.isfinite(vals).all() and (vals >= 0).all(), "X must be finite and non-negative"

    out = view.copy()
    if cfg["needs_coords"]:
        coords = np.asarray(out.obsm["spatial_3D"], dtype=np.float32)[:, :3]
        assert coords.shape == (out.n_obs, 3) and np.isfinite(coords).all()
        out.obsm.clear()
        out.obsm["spatial_3D"] = coords
    else:
        out.obsm.clear()

    prov = {
        "task": task.upper(),
        "board": f"{task.upper()}:{board.lower()}",
        "method": cfg["method"],
        "rule": "uniform_random_no_replace_seed_sorted_original_order",
        "seed": int(seed),
        "source_path": str(src_path.resolve()),
        "source_n_obs": int(n_src),
        "n_obs": int(out.n_obs),
        "target_used": False,
    }
    if n_cells is not None:
        # Only present for override runs; keeps default output byte-identical to v1.
        prov["n_cells_requested"] = int(n_cells)
    out.uns["ve_b4p0_floor"] = prov

    if out_path.exists() and not overwrite:
        raise FileExistsError(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.write_h5ad(out_path)

    return {
        "output": str(out_path),
        "sha256": sha256(out_path),
        "n_obs": int(out.n_obs),
        "n_vars": int(out.n_vars),
        "selected_obs_names_head": [src_obs_names[i] for i in chosen[:5]],
        "chosen_indices_sha256": hashlib.sha256(chosen.tobytes()).hexdigest(),
        "seed": int(seed),
        "source": cfg["source"],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--task", choices=["T1", "T3"], required=True)
    ap.add_argument("--board", choices=["val", "gata4"], required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=20260904)
    ap.add_argument("--n-cells", type=int, default=None,
                    help="override row count (default: board max_cells); contract min is 1000")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    summary = build(args.task, args.board, args.out, args.seed, args.overwrite, args.n_cells)
    print(json.dumps(summary, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
