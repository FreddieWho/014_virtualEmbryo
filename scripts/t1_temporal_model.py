#!/usr/bin/env python3
"""T1 temporal candidate: shrunk per-celltype pseudobulk shift on real last-stage cells.

Same route as the official ``pseudobulk_shift`` reference
(``baseline/pseudobulk_shift_tutorial.ipynb``): measure per-celltype pseudobulk
movement between the two observed stages and add it to the last stage's real
cells, clipped at zero.  This script changes no underlying principle; it only
optimizes reusable preprocessing/parameter details:

* ``--unmapped-delta global``: cell types with no same-name counterpart in the
  earlier stage (the celltype vocabulary is NOT harmonised across stages, see
  ``data/reference/t1_composition.json``) receive the global all-cell delta
  instead of the official zero shift;
* ``--celltype-weight``: per-type deltas are shrunk toward the global delta,
  ``delta = w * delta_k + (1 - w) * delta_global`` -- the mixture pattern
  server-validated for T2 in ``scripts/t2_expression_model.py`` (A-0002);
* ``--composition-extrap linear``: the deterministic down-sampling targets the
  shared-type composition linearly extrapolated one day forward
  (``2 * p_last - p_prev``, floored and renormalised; types absent from the
  earlier stage keep their last-stage share) instead of the last-stage
  composition.

Setting ``--celltype-weight 1.0 --unmapped-delta zero --composition-extrap none``
reproduces the strict official reference baseline.

The held-out target (E10.5/E12.5) and any external measured stage are never
read; inputs are the released E8.5/E9.5 stages only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np
from scipy import sparse

try:
    from scripts.prepare_t1_t3_submission import BOARD_CONFIG, _load_board_input
except ImportError:  # direct ``python scripts/t1_temporal_model.py`` execution
    from prepare_t1_t3_submission import BOARD_CONFIG, _load_board_input


METHOD = "shrunk_pseudobulk_shift"
PARENT_CANDIDATE = "baseline-001/T1_val/v0001"


def _type_counts(celltypes: np.ndarray) -> dict[str, int]:
    values, counts = np.unique(celltypes, return_counts=True)
    return {str(v): int(c) for v, c in zip(values, counts)}


def _shares(counts: dict[str, int]) -> dict[str, float]:
    total = float(sum(counts.values()))
    return {k: v / total for k, v in counts.items()}


def extrapolate_shares(
    p_prev: dict[str, float],
    p_last: dict[str, float],
    *,
    floor: float = 0.001,
) -> dict[str, float]:
    """One-day linear composition extrapolation over the shared-type vocabulary.

    Types present only in the last stage keep their last-stage share (no
    observed trend under a non-harmonised vocabulary).  Shares are floored and
    renormalised to sum to one.
    """

    if floor < 0 or not np.isfinite(floor):
        raise ValueError("floor must be non-negative and finite")
    shares: dict[str, float] = {}
    for celltype, pl in p_last.items():
        if celltype in p_prev:
            shares[celltype] = max(floor, 2.0 * pl - p_prev[celltype])
        else:
            shares[celltype] = float(pl)
    total = float(sum(shares.values()))
    if total <= 0:
        raise ValueError("composition shares sum to zero")
    return {k: v / total for k, v in shares.items()}


def select_indices_by_shares(
    celltypes: np.ndarray,
    shares: dict[str, float],
    *,
    n_cells: int,
    seed: int,
) -> np.ndarray:
    """Deterministic per-type sampling without replacement toward target shares.

    Allocation is largest-remainder with stable lexical tie-breaking; requests
    are clipped to per-type availability and any deficit is redistributed to
    types with spare capacity in the same order.  This mirrors
    ``t2_pseudo_holdout.select_indices`` (which only supports proportional
    allocation) without changing its behaviour.
    """

    values = np.asarray(celltypes).astype(str)
    if values.ndim != 1:
        raise ValueError("celltypes must be one-dimensional")
    if n_cells < 1 or n_cells > len(values):
        raise ValueError(f"n_cells must be in [1, {len(values)}], got {n_cells}")
    if not np.isfinite(seed):
        raise ValueError("seed must be finite")

    groups = sorted(np.unique(values).tolist())
    group_indices = {group: np.flatnonzero(values == group) for group in groups}
    exact = np.asarray([float(shares.get(group, 0.0)) * n_cells for group in groups])
    take = np.minimum(
        np.floor(exact).astype(int),
        np.asarray([len(group_indices[group]) for group in groups]),
    )
    fractions = exact - np.floor(exact)
    order = sorted(range(len(groups)), key=lambda i: (-fractions[i], groups[i]))
    remainder = int(n_cells - int(take.sum()))
    for i in order:
        if remainder <= 0:
            break
        spare = len(group_indices[groups[i]]) - int(take[i])
        added = min(spare, remainder)
        take[i] += added
        remainder -= added
    if remainder > 0:
        raise ValueError("could not allocate n_cells within availability constraints")

    rng = np.random.default_rng(int(seed))
    selected = []
    for i, group in enumerate(groups):
        if take[i] > 0:
            selected.append(rng.choice(group_indices[group], size=int(take[i]), replace=False))
    return np.sort(np.concatenate(selected).astype(np.int64))


def _masked_means(X, celltypes: np.ndarray) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Per-type and global column means; sparse-safe, never fully densified."""

    per_type: dict[str, np.ndarray] = {}
    for celltype in np.unique(celltypes):
        rows = X[celltypes == celltype]
        mean = rows.mean(axis=0)
        per_type[str(celltype)] = np.asarray(mean).ravel().astype(np.float32)
    global_mean = np.asarray(X.mean(axis=0)).ravel().astype(np.float32)
    return per_type, global_mean


def run_t1_shift(
    *,
    board: str,
    previous_path: Path,
    base_path: Path,
    output_path: Path,
    n_cells: int,
    seed: int,
    damp: float = 1.0,
    celltype_weight: float = 0.5,
    unmapped_delta: str = "global",
    composition_extrap: str = "linear",
    composition_floor: float = 0.001,
    panel_path: Path | None = None,
    diagnostics_out: Path | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    board = board.lower()
    config = BOARD_CONFIG[("T1", board)]
    if not config["min_cells"] <= n_cells <= config["max_cells"]:
        raise ValueError(
            f"n_cells={n_cells} outside board limits "
            f"[{config['min_cells']}, {config['max_cells']}]"
        )
    if not np.isfinite(damp):
        raise ValueError("damp must be finite")
    if not np.isfinite(celltype_weight) or not 0 <= celltype_weight <= 1:
        raise ValueError("celltype_weight must be in [0, 1]")
    if unmapped_delta not in ("global", "zero"):
        raise ValueError("unmapped_delta must be 'global' or 'zero'")
    if composition_extrap not in ("linear", "none"):
        raise ValueError("composition_extrap must be 'linear' or 'none'")

    previous_path = Path(previous_path)
    base_path = Path(base_path)
    output_path = Path(output_path)
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output_path}; pass overwrite=True to replace it")
    panel_path = (
        Path(panel_path)
        if panel_path is not None
        else Path(__file__).resolve().parents[1] / "data" / "gene_panel" / config["panel"]
    )

    previous = _load_board_input(previous_path, panel_path, needs_coords=False)
    base = _load_board_input(base_path, panel_path, needs_coords=False)
    prev_types = np.asarray(previous.obs["celltype"].astype(str))
    base_types = np.asarray(base.obs["celltype"].astype(str))

    prev_means, global_prev = _masked_means(previous.X, prev_types)
    base_means, global_base = _masked_means(base.X, base_types)
    global_delta = global_base - global_prev

    deltas: dict[str, np.ndarray] = {}
    fallback_celltypes: list[str] = []
    for celltype in np.unique(base_types):
        if celltype in prev_means:
            type_delta = base_means[celltype] - prev_means[celltype]
            deltas[str(celltype)] = (
                float(celltype_weight) * type_delta
                + (1.0 - float(celltype_weight)) * global_delta
            ).astype(np.float32)
        else:
            fallback_celltypes.append(str(celltype))
            if unmapped_delta == "global":
                deltas[str(celltype)] = global_delta.astype(np.float32)
            else:
                deltas[str(celltype)] = np.zeros_like(global_delta, dtype=np.float32)

    last_counts = _type_counts(base_types)
    p_last = _shares(last_counts)
    if composition_extrap == "linear":
        p_prev = _shares(_type_counts(prev_types))
        target_shares = extrapolate_shares(p_prev, p_last, floor=composition_floor)
    else:
        target_shares = dict(p_last)
    indices = select_indices_by_shares(base_types, target_shares, n_cells=n_cells, seed=seed)

    sampled = base[indices].copy()
    sampled_types = base_types[indices]
    X = sampled.X
    pred = X.toarray() if sparse.issparse(X) else np.asarray(X, dtype=np.float32)
    pred = pred.astype(np.float32, copy=False)
    shifted_cells = 0
    for celltype in np.unique(sampled_types):
        mask = sampled_types == celltype
        pred[mask] += float(damp) * deltas[str(celltype)]
        shifted_cells += int(mask.sum())
    np.clip(pred, 0, None, out=pred)

    out = sampled.copy()
    out.X = pred
    # T1 is dissociated RNA; do not carry over an input UMAP as submission coordinates.
    out.obsm.clear()

    base_dense = X.toarray() if sparse.issparse(X) else np.asarray(X, dtype=np.float32)
    pb_base = base_dense.mean(axis=0)
    pb_pred = pred.mean(axis=0)
    moved = np.abs(pb_pred - pb_base)
    base_std = base_dense.std(axis=0)
    pred_std = pred.std(axis=0)
    if pb_base.std() > 0 and pb_pred.std() > 0:
        pearson = float(np.corrcoef(pb_pred, pb_base)[0, 1])
    else:  # constant toy-scale vectors leave the diagnostic undefined, never NaN
        pearson = None
    diagnostics: dict[str, Any] = {
        "pseudobulk_mean_abs_delta": float(moved.mean()),
        "pseudobulk_max_abs_delta": float(moved.max()),
        "n_genes_moved_gt_0.1": int((moved > 0.1).sum()),
        "pseudobulk_pearson_vs_base": pearson,
        "per_gene_std_base_mean": float(base_std.mean()),
        "per_gene_std_pred_mean": float(pred_std.mean()),
        "library_size_ratio_vs_base": float(
            pred.sum(axis=1).mean() / max(base_dense.sum(axis=1).mean(), 1e-9)
        ),
        "shifted_cells": shifted_cells,
        "output_composition": _type_counts(sampled_types),
        "target_shares": {k: round(v, 6) for k, v in sorted(target_shares.items())},
        "base_shares": {k: round(v, 6) for k, v in sorted(p_last.items())},
    }

    metadata: dict[str, Any] = {
        "board": f"T1:{board}",
        "task": "T1",
        "method": METHOD,
        "parent_candidate": PARENT_CANDIDATE,
        "previous_path": str(previous_path.resolve()),
        "base_path": str(base_path.resolve()),
        "panel_path": str(panel_path.resolve()),
        "n_cells": int(n_cells),
        "seed": int(seed),
        "damp": float(damp),
        "celltype_weight": float(celltype_weight),
        "unmapped_delta": unmapped_delta,
        "composition_extrap": composition_extrap,
        "composition_floor": float(composition_floor),
        "fallback_celltypes": sorted(fallback_celltypes),
        "sampling_strategy": "stratified_by_target_shares",
        "target_used": False,
        "submission_contract_validated": True,
    }
    out.uns["ve_submission_prep"] = metadata
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out.write_h5ad(output_path)

    checked = _load_board_input(output_path, panel_path, needs_coords=False)
    if not config["min_cells"] <= checked.n_obs <= config["max_cells"]:
        raise AssertionError("prepared output failed board cell-limit validation")
    if checked.obsm:
        raise AssertionError("T1 output unexpectedly contains obsm entries")
    metadata.update(
        {
            "output_path": str(output_path.resolve()),
            "n_obs": int(checked.n_obs),
            "n_vars": int(checked.n_vars),
        }
    )
    if diagnostics_out is not None:
        diagnostics_out = Path(diagnostics_out)
        diagnostics_out.parent.mkdir(parents=True, exist_ok=True)
        payload = {"metadata": metadata, "diagnostics": diagnostics}
        diagnostics_out.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return {"metadata": metadata, "diagnostics": diagnostics}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--board", choices=["val"], required=True)
    parser.add_argument("--previous", type=Path, required=True, help="earlier observed stage (E8.5)")
    parser.add_argument("--base", type=Path, required=True, help="last observed stage (E9.5)")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--n-cells", type=int, required=True)
    parser.add_argument("--seed", type=int, default=20260822)
    parser.add_argument("--damp", type=float, default=1.0)
    parser.add_argument("--celltype-weight", type=float, default=0.5)
    parser.add_argument("--unmapped-delta", choices=["global", "zero"], default="global")
    parser.add_argument("--composition-extrap", choices=["linear", "none"], default="linear")
    parser.add_argument("--composition-floor", type=float, default=0.001)
    parser.add_argument("--panel", type=Path)
    parser.add_argument("--diagnostics-out", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = run_t1_shift(
        board=args.board,
        previous_path=args.previous,
        base_path=args.base,
        output_path=args.output,
        n_cells=args.n_cells,
        seed=args.seed,
        damp=args.damp,
        celltype_weight=args.celltype_weight,
        unmapped_delta=args.unmapped_delta,
        composition_extrap=args.composition_extrap,
        composition_floor=args.composition_floor,
        panel_path=args.panel,
        diagnostics_out=args.diagnostics_out,
        overwrite=args.overwrite,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
