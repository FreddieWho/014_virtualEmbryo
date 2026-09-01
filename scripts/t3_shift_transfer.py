#!/usr/bin/env python3
"""Build target-blind T3 shift-transfer candidates.

The runner transfers a public Mab21l2-KO response measured at E9.5 onto a
public matched-WT carrier for the Gata4 board.  It never accepts or reads a
held-out KO target.  Two named presets are intentionally kept explicit:

``official_norm``
    Full global response, damp=1, with log1p library-size restoration.
``conservative``
    Count-depth matched response, source-gene masking, top-50 tails,
    damp=0.5, and explicit target-gene zeroing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np
from scipy import sparse


BOARD = "T3:gata4"
PANEL_PATH = Path(__file__).resolve().parents[1] / "data" / "gene_panel" / "T3__gata4.genes.txt"
MIN_CELLS = 1_000
MAX_CELLS = 7_449
DEFAULT_LIBRARY_SIZE = 10_000.0
SCALE_RTOL = 1e-5
SCALE_ATOL = 1e-6
CHUNK_SIZE = 2_048


VARIANTS: dict[str, dict[str, Any]] = {
    "official_norm": {
        "damp": 1.0,
        "depth_match": False,
        "depth_bins": None,
        "depth_seed": 20260822,
        "top_up": None,
        "top_down": None,
        "source_gene": None,
        "target_gene": None,
    },
    "conservative": {
        "damp": 0.5,
        "depth_match": True,
        "depth_bins": 10,
        "depth_seed": 20260822,
        "top_up": 50,
        "top_down": 50,
        "source_gene": "Mab21l2",
        "target_gene": "Gata4",
    },
}


@dataclass
class Source:
    path: Path
    adata: ad.AnnData
    X: Any
    counts: Any
    panel: list[str]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _panel(path: Path) -> list[str]:
    genes = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    if len(genes) != 500 or len(set(genes)) != len(genes):
        raise ValueError(f"{path}: expected 500 unique panel genes")
    return genes


def _as_dense(value: Any) -> np.ndarray:
    if sparse.issparse(value):
        value = value.toarray()
    return np.asarray(value)


def _iter_chunks(matrix: Any, n_rows: int, chunk_size: int = CHUNK_SIZE):
    for start in range(0, n_rows, chunk_size):
        yield start, min(start + chunk_size, n_rows), _as_dense(matrix[start : min(start + chunk_size, n_rows)])


def _validate_values(matrix: Any, n_rows: int, label: str) -> None:
    for _, _, values in _iter_chunks(matrix, n_rows):
        if values.ndim != 2 or not np.isfinite(values).all() or (values < 0).any():
            raise ValueError(f"{label}: matrix must be finite, non-negative, and 2D")


def _row_sums(matrix: Any, n_rows: int, label: str) -> np.ndarray:
    totals = np.empty(n_rows, dtype=np.float64)
    for start, end, values in _iter_chunks(matrix, n_rows):
        if values.ndim != 2 or not np.isfinite(values).all() or (values < 0).any():
            raise ValueError(f"{label}: counts must be finite and non-negative")
        totals[start:end] = values.astype(np.float64, copy=False).sum(axis=1)
    if not np.isfinite(totals).all() or (totals <= 0).any():
        raise ValueError(f"{label}: counts contain a non-positive library size")
    return totals


def _column_mean(matrix: Any, n_rows: int, label: str) -> np.ndarray:
    total = None
    for _, _, values in _iter_chunks(matrix, n_rows):
        if values.ndim != 2 or not np.isfinite(values).all() or (values < 0).any():
            raise ValueError(f"{label}: expression must be finite and non-negative")
        piece = values.astype(np.float64, copy=False).sum(axis=0)
        total = piece if total is None else total + piece
    if total is None:
        raise ValueError(f"{label}: empty matrix")
    return total / float(n_rows)


def _mean_rows(matrix: Any, indices: np.ndarray, label: str) -> np.ndarray:
    if len(indices) == 0:
        raise ValueError(f"{label}: no rows selected")
    total = None
    # np.ndarray indexing is supported by both AnnData backed datasets and
    # scipy sparse matrices when indices are sorted (the caller guarantees it).
    for start in range(0, len(indices), CHUNK_SIZE):
        selected = np.asarray(indices[start : start + CHUNK_SIZE], dtype=np.int64)
        values = _as_dense(matrix[selected])
        if values.ndim != 2 or not np.isfinite(values).all() or (values < 0).any():
            raise ValueError(f"{label}: expression must be finite and non-negative")
        piece = values.astype(np.float64, copy=False).sum(axis=0)
        total = piece if total is None else total + piece
    return total / float(len(indices))


def _validate_log1p_scale(X: Any, counts: Any, n_rows: int, label: str) -> np.ndarray:
    """Validate X against counts normalized to the released 10k log1p scale."""

    depths = _row_sums(counts, n_rows, f"{label}.counts")
    for start, end, values in _iter_chunks(X, n_rows):
        count_values = _as_dense(counts[start:end]).astype(np.float64, copy=False)
        expected = np.log1p(count_values * (DEFAULT_LIBRARY_SIZE / depths[start:end, None]))
        if not np.allclose(values, expected, rtol=SCALE_RTOL, atol=SCALE_ATOL):
            max_error = float(np.max(np.abs(values.astype(np.float64) - expected)))
            raise ValueError(f"{label}.X is not counts-derived log1p(10k); max_error={max_error:.6g}")
    return depths


def _open_source(path: Path, panel: list[str], label: str) -> Source:
    if not path.exists():
        raise FileNotFoundError(path)
    source = ad.read_h5ad(path, backed="r")
    names = [str(gene) for gene in source.var_names]
    if len(names) != len(set(names)):
        source.file.close()
        raise ValueError(f"{path}: var_names contains duplicates")
    missing = [gene for gene in panel if gene not in set(names)]
    if missing:
        source.file.close()
        raise ValueError(f"{path}: missing panel genes, head={missing[:10]}")
    # The released T3 files already use panel order.  Materializing a view
    # handles a harmless released-order permutation without changing the data.
    aligned = source[:, panel]
    if "counts" not in aligned.layers:
        source.file.close()
        raise ValueError(f"{path}: layers['counts'] is required for scale/depth validation")
    _validate_values(aligned.X, aligned.n_obs, f"{label}.X")
    _validate_values(aligned.layers["counts"], aligned.n_obs, f"{label}.counts")
    _validate_log1p_scale(aligned.X, aligned.layers["counts"], aligned.n_obs, label)
    return Source(path=path, adata=source, X=aligned.X, counts=aligned.layers["counts"], panel=panel)


def _close_source(source: Source) -> None:
    if getattr(source.adata, "file", None) is not None:
        source.adata.file.close()


def _depth_match_indices(
    wt_depth: np.ndarray,
    ko_depth: np.ndarray,
    *,
    bins: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, list[dict[str, int]]]:
    if bins < 2:
        raise ValueError("depth bins must be at least 2")
    pooled = np.concatenate([wt_depth, ko_depth])
    edges = np.unique(np.quantile(pooled, np.linspace(0.0, 1.0, bins + 1)))
    if len(edges) < 2:
        raise ValueError("depth matching requires at least two distinct count depths")
    wt_bin = np.digitize(wt_depth, edges[1:-1], right=False)
    ko_bin = np.digitize(ko_depth, edges[1:-1], right=False)
    rng = np.random.default_rng(int(seed))
    wt_selected: list[np.ndarray] = []
    ko_selected: list[np.ndarray] = []
    summary: list[dict[str, int]] = []
    for bin_id in range(len(edges) - 1):
        wt_indices = np.flatnonzero(wt_bin == bin_id)
        ko_indices = np.flatnonzero(ko_bin == bin_id)
        take = min(len(wt_indices), len(ko_indices))
        if take:
            wt_selected.append(np.sort(rng.choice(wt_indices, size=take, replace=False)))
            ko_selected.append(np.sort(rng.choice(ko_indices, size=take, replace=False)))
        summary.append({"bin": int(bin_id), "wt_available": int(len(wt_indices)), "ko_available": int(len(ko_indices)), "selected_each": int(take)})
    if not wt_selected:
        raise ValueError("depth matching produced no paired cells")
    return np.sort(np.concatenate(wt_selected)), np.sort(np.concatenate(ko_selected)), summary


def _sparsify_delta(delta: np.ndarray, *, top_up: int | None, top_down: int | None) -> tuple[np.ndarray, list[int], list[int]]:
    if top_up is None and top_down is None:
        return delta, [], []
    keep = np.zeros(delta.shape, dtype=bool)
    up = np.flatnonzero(delta > 0)
    down = np.flatnonzero(delta < 0)
    up = up[np.argsort(delta[up])[::-1]][: int(top_up or 0)]
    down = down[np.argsort(delta[down])][: int(top_down or 0)]
    keep[up] = True
    keep[down] = True
    out = np.where(keep, delta, 0.0)
    return out, [int(i) for i in up], [int(i) for i in down]


def _normalize_log1p_rows(X: np.ndarray, target_library_size: float) -> np.ndarray:
    if not np.isfinite(target_library_size) or target_library_size <= 0:
        raise ValueError("target_library_size must be positive and finite")
    raw = np.expm1(np.clip(np.asarray(X, dtype=np.float64), 0.0, 50.0))
    totals = raw.sum(axis=1, keepdims=True)
    if not np.isfinite(raw).all() or (totals <= 0).any():
        raise ValueError("cannot normalize rows with non-finite values or zero implied library size")
    return np.log1p(raw * (float(target_library_size) / totals)).astype(np.float32, copy=False)


def _carrier(path: Path, panel: list[str]) -> ad.AnnData:
    if not path.exists():
        raise FileNotFoundError(path)
    carrier = ad.read_h5ad(path)
    names = [str(gene) for gene in carrier.var_names]
    if len(names) != len(set(names)):
        raise ValueError(f"{path}: carrier var_names contains duplicates")
    missing = [gene for gene in panel if gene not in set(names)]
    if missing:
        raise ValueError(f"{path}: carrier missing panel genes, head={missing[:10]}")
    carrier = carrier[:, panel].copy()
    if not MIN_CELLS <= carrier.n_obs <= MAX_CELLS:
        raise ValueError(f"carrier n_obs={carrier.n_obs} outside [{MIN_CELLS}, {MAX_CELLS}]")
    _validate_values(carrier.X, carrier.n_obs, "carrier.X")
    if "spatial_3D" not in carrier.obsm:
        raise ValueError("carrier: missing obsm['spatial_3D']")
    coords = np.asarray(carrier.obsm["spatial_3D"])
    if coords.ndim != 2 or coords.shape[0] != carrier.n_obs or coords.shape[1] < 3 or not np.isfinite(coords[:, :3]).all():
        raise ValueError("carrier: spatial_3D must have at least three finite columns")
    X = _as_dense(carrier.X).astype(np.float64, copy=False)
    implied = np.expm1(X).sum(axis=1)
    if not np.allclose(implied, DEFAULT_LIBRARY_SIZE, rtol=1e-5, atol=1e-2):
        raise ValueError("carrier.X is not on the released 10k log1p scale")
    carrier.obsm.clear()
    carrier.obsm["spatial_3D"] = coords[:, :3].astype(np.float32, copy=False)
    carrier.X = X
    return carrier


def run_shift_transfer(
    *,
    variant: str,
    train_wt_path: Path,
    train_ko_path: Path,
    carrier_path: Path,
    output_path: Path,
    summary_path: Path | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    if variant not in VARIANTS:
        raise ValueError(f"unsupported variant {variant!r}; choose from {sorted(VARIANTS)}")
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"output already exists: {output_path}; pass overwrite=True to replace it")
    config = dict(VARIANTS[variant])
    panel = _panel(PANEL_PATH)
    wt: Source | None = None
    ko: Source | None = None
    carrier = None
    try:
        wt = _open_source(Path(train_wt_path), panel, "train_wt")
        ko = _open_source(Path(train_ko_path), panel, "train_ko")
        carrier = _carrier(Path(carrier_path), panel)
        wt_depth = _row_sums(wt.counts, wt.adata.n_obs, "train_wt.counts")
        ko_depth = _row_sums(ko.counts, ko.adata.n_obs, "train_ko.counts")
        depth_summary: list[dict[str, int]] = []
        if config["depth_match"]:
            wt_idx, ko_idx, depth_summary = _depth_match_indices(
                wt_depth, ko_depth, bins=int(config["depth_bins"]), seed=int(config["depth_seed"])
            )
            wt_mean = _mean_rows(wt.X, wt_idx, "train_wt.depth_matched")
            ko_mean = _mean_rows(ko.X, ko_idx, "train_ko.depth_matched")
        else:
            wt_idx = np.arange(wt.adata.n_obs, dtype=np.int64)
            ko_idx = np.arange(ko.adata.n_obs, dtype=np.int64)
            wt_mean = _column_mean(wt.X, wt.adata.n_obs, "train_wt.X")
            ko_mean = _column_mean(ko.X, ko.adata.n_obs, "train_ko.X")
        delta_raw = ko_mean - wt_mean
        gene_to_index = {gene.lower(): i for i, gene in enumerate(panel)}
        source_gene_index = None
        target_gene_index = None
        if config["source_gene"] is not None:
            source_gene_index = gene_to_index.get(str(config["source_gene"]).lower())
            if source_gene_index is None:
                raise ValueError(f"source gene {config['source_gene']!r} is absent from the T3 panel")
            delta_raw[source_gene_index] = 0.0
        delta, selected_up, selected_down = _sparsify_delta(
            delta_raw,
            top_up=config["top_up"],
            top_down=config["top_down"],
        )
        if config["target_gene"] is not None:
            target_gene_index = gene_to_index.get(str(config["target_gene"]).lower())
            if target_gene_index is None:
                raise ValueError(f"target gene {config['target_gene']!r} is absent from the T3 panel")
        carrier_X = np.asarray(carrier.X, dtype=np.float64)
        preclip = carrier_X + float(config["damp"]) * delta[None, :]
        preclip_negative_fraction = float(np.mean(preclip < 0))
        prediction = np.clip(preclip, 0.0, None)
        if target_gene_index is not None:
            prediction[:, target_gene_index] = 0.0
        normalized = _normalize_log1p_rows(prediction, DEFAULT_LIBRARY_SIZE)
        carrier.X = normalized
        metadata = {
            "board": BOARD,
            "task": "T3",
            "variant": variant,
            "method": "shift_transfer",
            "parent_candidate": "baseline-001/T3_gata4/v0001",
            "train_wt_path": str(Path(train_wt_path).resolve()),
            "train_wt_sha256": _sha256(Path(train_wt_path)),
            "train_ko_path": str(Path(train_ko_path).resolve()),
            "train_ko_sha256": _sha256(Path(train_ko_path)),
            "carrier_path": str(Path(carrier_path).resolve()),
            "carrier_sha256": _sha256(Path(carrier_path)),
            "panel_path": str(PANEL_PATH.resolve()),
            "panel_genes": len(panel),
            "damp": float(config["damp"]),
            "depth_match": bool(config["depth_match"]),
            "depth_bins": config["depth_bins"],
            "depth_seed": int(config["depth_seed"]),
            "matched_wt_cells": int(len(wt_idx)),
            "matched_ko_cells": int(len(ko_idx)),
            # AnnData's uns writer cannot serialize list[dict] values; keep
            # the full machine-readable bin table as a stable JSON string.
            "depth_bins_summary": json.dumps(depth_summary, sort_keys=True),
            "source_gene_masked": config["source_gene"],
            "target_gene_zeroed": config["target_gene"],
            "top_up": config["top_up"],
            "top_down": config["top_down"],
            "selected_up_genes": [panel[i] for i in selected_up],
            "selected_down_genes": [panel[i] for i in selected_down],
            "delta_by_gene": {panel[i]: float(delta[i]) for i in range(len(panel))},
            "delta_abs_mean": float(np.abs(delta).mean()),
            "delta_nonzero_genes": int(np.count_nonzero(delta)),
            "preclip_negative_fraction": preclip_negative_fraction,
            "output_density": float(np.count_nonzero(normalized) / normalized.size),
            "output_library_size_q": [float(x) for x in np.quantile(np.expm1(normalized).sum(axis=1), [0.0, 0.5, 1.0])],
            "n_obs": int(carrier.n_obs),
            "n_vars": int(carrier.n_vars),
            "sampling_strategy": "immutable_v0001_scaffold",
            "target_used": False,
            "submission_contract_validated": True,
        }
        carrier.uns["ve_submission_prep"] = metadata
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        carrier.write_h5ad(output_path)
        if summary_path is not None:
            summary_path = Path(summary_path)
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            summary_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        return metadata
    finally:
        if wt is not None:
            _close_source(wt)
        if ko is not None:
            _close_source(ko)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=sorted(VARIANTS), required=True)
    parser.add_argument("--train-wt", type=Path, required=True)
    parser.add_argument("--train-ko", type=Path, required=True)
    parser.add_argument("--carrier", type=Path, required=True, help="released WT carrier or immutable v0001 scaffold")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = run_shift_transfer(
        variant=args.variant,
        train_wt_path=args.train_wt,
        train_ko_path=args.train_ko,
        carrier_path=args.carrier,
        output_path=args.output,
        summary_path=args.summary,
        overwrite=args.overwrite,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
