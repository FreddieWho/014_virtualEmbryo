#!/usr/bin/env python3
"""Build the B1-A2 target-blind signed sparse T3 response candidates.

The two final lanes differ only in the WT-only correlation used to rank genes:
cell-level Spearman and equal-state pseudobulk Spearman.  The public Mab21l2
KO/WT pair supplies an unsigned response budget (DE count and absolute effect
sizes); its gene-wise response signs are deliberately discarded.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np
from scipy import sparse
from scipy.stats import rankdata


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VECKIT_ROOT = PROJECT_ROOT / "third_party" / "veckit"
if str(VECKIT_ROOT) not in sys.path:
    sys.path.insert(0, str(VECKIT_ROOT))

from common.core_metrics import de_genes  # noqa: E402
from scripts.t2_pseudo_holdout import select_indices  # noqa: E402
from scripts.t3_shift_transfer import (  # noqa: E402
    MAX_CELLS,
    MIN_CELLS,
    PANEL_PATH,
    _as_dense,
    _carrier,
    _close_source,
    _open_source,
    _panel,
    _sha256,
)


ATOM_ID = "B1-A2"
BOARD = "T3:gata4"
SEED = 20260827
N_SELF_CELLS = 7_449
SCORER_VERSION = "veckit@46d41e63f42a9aab815db20b742feeccd249cb17"
EXPECTED_PARENT_SHA256 = (
    "8ed2373e16a037291f5ebb6e2308072639093e250ea10bc17b690ea183caeacd"
)
FINAL_LANES = (
    "L1_CELL_LEVEL_SPEARMAN",
    "L2_STATE_PSEUDOBULK_SPEARMAN",
)
LANE_METHODS = {
    "L1_CELL_LEVEL_SPEARMAN": "cell_level_spearman",
    "L2_STATE_PSEUDOBULK_SPEARMAN": "state_pseudobulk_spearman",
}


@dataclass(frozen=True)
class EffectBudget:
    """The only quantities allowed to cross from the KO training pair."""

    n_de: int
    abs_effects: np.ndarray
    median_abs_effect: float
    q90_abs_effect: float


@dataclass(frozen=True)
class SignedPrior:
    lane_id: str
    method: str
    target_gene: str
    rho: np.ndarray
    confidence: np.ndarray
    threshold: float
    eligible_indices: np.ndarray
    support_indices: np.ndarray


def _matrix_digest(value: Any) -> str:
    digest = hashlib.sha256()
    if sparse.issparse(value):
        matrix = value.tocsr(copy=True)
        matrix.sum_duplicates()
        matrix.sort_indices()
        digest.update(b"sparse_csr")
        digest.update(str(matrix.shape).encode("utf-8"))
        digest.update(matrix.dtype.str.encode("utf-8"))
        parts = (matrix.indptr, matrix.indices, matrix.data)
    else:
        array = np.ascontiguousarray(np.asarray(value))
        digest.update(b"dense")
        digest.update(str(array.shape).encode("utf-8"))
        digest.update(array.dtype.str.encode("utf-8"))
        parts = (array,)
    for part in parts:
        digest.update(np.ascontiguousarray(part).tobytes(order="C"))
    return digest.hexdigest()


def _names_digest(names: Any) -> str:
    canonical = "\n".join(str(name) for name in names).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def _artifact_relative_path(path: Path, project_root: Path) -> Path:
    relative = path.resolve().relative_to(project_root.resolve())
    parts = [part[:-len(".partial")] if part.endswith(".partial") else part for part in relative.parts]
    return Path(*parts)


def _decode_json_metadata(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return decoded if isinstance(decoded, dict) else {}
    return {}


def _enrich_manifest(
    manifest: dict[str, Any],
    candidate: ad.AnnData,
    *,
    output_path: Path,
    project_root: Path,
    prior: SignedPrior | None = None,
    budget: EffectBudget | None = None,
    prior_wt_path: Path | None = None,
) -> dict[str, Any]:
    response = candidate.uns.get("ve_signed_response", {})
    diagnostics = _decode_json_metadata(response.get("diagnostics"))
    gate_metadata = _decode_json_metadata(response.get("gate_metadata"))
    support_count = (
        int(len(prior.support_indices))
        if prior is not None
        else int(diagnostics.get("support_count", len(json.loads(response.get("selected_genes", "[]")))))
    )
    n_de = int(budget.n_de) if budget is not None else int(response.get("n_de_train", support_count + 1))
    selected_up = int(
        np.count_nonzero(-prior.rho[prior.support_indices] > 0)
        if prior is not None
        else diagnostics.get("selected_up_count", 0)
    )
    selected_down = int(
        np.count_nonzero(-prior.rho[prior.support_indices] < 0)
        if prior is not None
        else diagnostics.get("selected_down_count", 0)
    )
    output_rel = _artifact_relative_path(output_path, project_root)
    manifest.update(
        {
            "method": response.get("method", prior.method if prior is not None else manifest.get("method")),
            "prior_strength": response.get("prior_strength", "weak"),
            "prior_source": response.get("prior_source", "WT_only_Spearman"),
            "prior_wt_path": (
                str(prior_wt_path.resolve())
                if prior_wt_path is not None
                else manifest.get("prior_wt_path")
            ),
            "target_gene": response.get("target_gene", prior.target_gene if prior is not None else None),
            "target_used_for_generation": bool(response.get("target_used_for_generation", False)),
            "target_used_for_evaluation": bool(response.get("target_truth_used_for_evaluation", False)),
            "n_de_train": n_de,
            "prior_threshold": response.get("prior_threshold"),
            "eligible_count": int(response.get("eligible_count", 0)),
            "selected_support_count": support_count,
            "selected_up_count": selected_up,
            "selected_down_count": selected_down,
            "residual_sparsity": {
                "selected_gene_count": support_count,
                "nonzero_fraction_of_panel": float(support_count / candidate.n_vars),
                "support_rule": "K_train_minus_target_gene",
            },
            "state_gate_source": "WT_celltype_target_activity",
            "state_gates": gate_metadata.get("gates", {}),
            "state_gate_file": (output_rel.parent / "state_gates.tsv").as_posix(),
            "prior_file": (output_rel.parent / "signed_prior.tsv").as_posix(),
            "generation_diagnostics": diagnostics,
        }
    )
    return manifest


def _dense_float64(value: Any) -> np.ndarray:
    if sparse.issparse(value):
        array = value.toarray()
    else:
        try:
            array = np.asarray(value)
            if array.ndim != 2:
                raise ValueError("backed matrix needs explicit materialization")
        except (TypeError, ValueError):
            if not hasattr(value, "__getitem__"):
                raise
            array = value[:]
            if sparse.issparse(array):
                array = array.toarray()
    array = np.asarray(array, dtype=np.float64)
    if array.ndim != 2 or not np.isfinite(array).all() or (array < 0).any():
        raise ValueError("expression matrix must be finite, non-negative, and 2D")
    return array


def _celltypes(adata: ad.AnnData, path: Path) -> np.ndarray:
    if "celltype" not in adata.obs:
        raise ValueError(f"{path}: obs['celltype'] is required")
    values = adata.obs["celltype"]
    if values.isna().any():
        raise ValueError(f"{path}: obs['celltype'] contains missing values")
    return np.asarray(values.astype(str))


def _state_means(X: np.ndarray, labels: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    states, inverse = np.unique(np.asarray(labels).astype(str), return_inverse=True)
    counts = np.bincount(inverse, minlength=len(states)).astype(np.int64)
    if (counts <= 0).any():
        raise ValueError("state partition contains an empty state")
    means = np.zeros((len(states), X.shape[1]), dtype=np.float64)
    np.add.at(means, inverse, X)
    means /= counts[:, None]
    return states, inverse, means


def _target_correlations(X: np.ndarray, target_index: int) -> np.ndarray:
    ranks = rankdata(X, axis=0)
    target = ranks[:, target_index]
    centered_target = target - target.mean()
    target_norm = float(np.sqrt(np.dot(centered_target, centered_target)))
    if target_norm <= 0 or not np.isfinite(target_norm):
        raise ValueError("target gene has no rank variation in WT")
    centered = ranks - ranks.mean(axis=0, keepdims=True)
    norms = np.sqrt(np.sum(centered * centered, axis=0))
    rho = centered.T @ centered_target
    rho /= np.maximum(norms * target_norm, 1e-15)
    rho = np.asarray(np.clip(rho, -1.0, 1.0), dtype=np.float64)
    rho[norms <= 0] = 0.0
    rho[target_index] = 0.0
    if not np.isfinite(rho).all():
        raise ValueError("WT signed prior contains non-finite correlations")
    return rho


def build_signed_prior(
    wt_adata: ad.AnnData,
    *,
    lane_id: str,
    target_gene: str,
) -> SignedPrior:
    """Construct a target-blind weak prior from WT expression only."""

    if lane_id not in FINAL_LANES:
        raise ValueError(f"unsupported lane {lane_id!r}")
    genes = [str(gene) for gene in wt_adata.var_names]
    if target_gene not in genes:
        raise ValueError(f"target gene {target_gene!r} is absent from WT panel")
    target_index = genes.index(target_gene)
    X = _dense_float64(wt_adata.X)
    if lane_id == "L1_CELL_LEVEL_SPEARMAN":
        method = LANE_METHODS[lane_id]
        rho = _target_correlations(X, target_index)
    else:
        labels = _celltypes(wt_adata, Path("WT"))
        _, _, means = _state_means(X, labels)
        method = LANE_METHODS[lane_id]
        rho = _target_correlations(means, target_index)

    confidence = np.abs(rho)
    candidate = np.arange(len(genes), dtype=np.int64)
    candidate = candidate[candidate != target_index]
    nonzero = confidence[candidate][confidence[candidate] > 0]
    if len(nonzero) == 0:
        raise ValueError("signed prior has no non-zero confidence")
    threshold = float(np.median(nonzero))
    eligible = candidate[confidence[candidate] > threshold]
    return SignedPrior(
        lane_id=lane_id,
        method=method,
        target_gene=target_gene,
        rho=rho,
        confidence=confidence,
        threshold=threshold,
        eligible_indices=eligible,
        support_indices=np.empty(0, dtype=np.int64),
    )


def derive_effect_budget(ko_X: Any, wt_X: Any) -> EffectBudget:
    """Extract K and absolute effect sizes; discard response directions."""

    up, down, lfc = de_genes(ko_X, wt_X)
    indices = np.sort(np.concatenate([np.asarray(up, dtype=np.int64), np.asarray(down, dtype=np.int64)]))
    if len(indices) < 3:
        raise ValueError("training KO has fewer than three DE genes")
    abs_effects = np.sort(np.abs(np.asarray(lfc, dtype=np.float64)[indices]))
    if not np.isfinite(abs_effects).all() or (abs_effects <= 0).any():
        raise ValueError("training DE absolute effects must be finite and positive")
    return EffectBudget(
        n_de=int(len(abs_effects)),
        abs_effects=abs_effects,
        median_abs_effect=float(np.median(abs_effects)),
        q90_abs_effect=float(np.quantile(abs_effects, 0.90)),
    )


def _budget_from_signed_effects(effects: np.ndarray, de_indices: np.ndarray) -> EffectBudget:
    """Small pure helper used by tests to assert sign-invariance."""

    values = np.sort(np.abs(np.asarray(effects, dtype=np.float64)[np.asarray(de_indices, dtype=np.int64)]))
    if len(values) < 3 or not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError("invalid effect budget")
    return EffectBudget(
        n_de=int(len(values)),
        abs_effects=values,
        median_abs_effect=float(np.median(values)),
        q90_abs_effect=float(np.quantile(values, 0.90)),
    )


def select_support(prior: SignedPrior, budget: EffectBudget) -> SignedPrior:
    """Select exactly K-1 learned genes, retaining both response signs."""

    k_support = budget.n_de - 1
    eligible = np.asarray(prior.eligible_indices, dtype=np.int64)
    if len(eligible) < k_support:
        raise ValueError(f"eligible prior genes {len(eligible)} < required support {k_support}")
    order = sorted(eligible.tolist(), key=lambda index: (-float(prior.confidence[index]), int(index)))
    support = np.asarray(order[:k_support], dtype=np.int64)
    signed = -prior.rho[support]
    if not np.any(signed > 0) or not np.any(signed < 0):
        raise ValueError("signed support must contain both up and down directions")
    return SignedPrior(
        lane_id=prior.lane_id,
        method=prior.method,
        target_gene=prior.target_gene,
        rho=prior.rho,
        confidence=prior.confidence,
        threshold=prior.threshold,
        eligible_indices=eligible,
        support_indices=support,
    )


def build_state_gates(wt_adata: ad.AnnData, *, target_gene: str) -> tuple[dict[str, float], dict[str, Any]]:
    genes = [str(gene) for gene in wt_adata.var_names]
    if target_gene not in genes:
        raise ValueError(f"target gene {target_gene!r} is absent from WT panel")
    labels = _celltypes(wt_adata, Path("WT"))
    X = _dense_float64(wt_adata.X)
    states, _, means = _state_means(X, labels)
    activity = means[:, genes.index(target_gene)]
    maximum = float(np.max(activity))
    if not np.isfinite(maximum) or maximum <= 0:
        raise ValueError("target activity has no positive state")
    gates = {str(state): float(np.clip(value / maximum, 0.0, 1.0)) for state, value in zip(states, activity)}
    metadata = {
        "celltype_column": "celltype",
        "target_gene": target_gene,
        "states": [str(state) for state in states],
        "state_counts": {str(state): int((labels == state).sum()) for state in states},
        "activity": {str(state): float(value) for state, value in zip(states, activity)},
        "gates": gates,
    }
    return gates, metadata


def residual_vector(prior: SignedPrior, budget: EffectBudget) -> np.ndarray:
    if len(prior.support_indices) != budget.n_de - 1:
        raise ValueError("support size does not equal K_train - 1")
    residual = np.zeros_like(prior.rho, dtype=np.float64)
    for index in prior.support_indices:
        residual[index] = float(
            np.sign(-prior.rho[index])
            * min(budget.median_abs_effect * prior.confidence[index], budget.q90_abs_effect)
        )
    if not np.isfinite(residual).all() or not np.any(residual != 0):
        raise ValueError("residual is empty or non-finite")
    return residual


def apply_signed_residual(
    carrier_adata: ad.AnnData,
    *,
    prior: SignedPrior,
    gates: dict[str, float],
    budget: EffectBudget,
) -> tuple[np.ndarray, dict[str, Any]]:
    genes = [str(gene) for gene in carrier_adata.var_names]
    target_index = genes.index(prior.target_gene) if prior.target_gene in genes else -1
    if target_index < 0:
        raise ValueError(f"carrier is missing target gene {prior.target_gene!r}")
    labels = _celltypes(carrier_adata, Path("carrier"))
    unknown = sorted(set(labels) - set(gates))
    if unknown:
        raise ValueError(f"carrier contains states absent from gate table: {unknown}")
    row_gates = np.asarray([gates[str(label)] for label in labels], dtype=np.float64)
    residual = residual_vector(prior, budget)
    X = _dense_float64(carrier_adata.X)
    prediction = X.copy()
    clipped = 0
    for index in prior.support_indices:
        before = prediction[:, index] + row_gates * residual[index]
        clipped += int(np.count_nonzero(before < 0))
        prediction[:, index] = np.maximum(before, 0.0)
    prediction[:, target_index] = 0.0
    diagnostics = {
        "support_count": int(len(prior.support_indices)),
        "selected_up_count": int(np.count_nonzero(-prior.rho[prior.support_indices] > 0)),
        "selected_down_count": int(np.count_nonzero(-prior.rho[prior.support_indices] < 0)),
        "clipped_entries": int(clipped),
        "clipped_fraction_support_entries": float(clipped / (len(prior.support_indices) * carrier_adata.n_obs)),
        "target_zeroed": True,
        "target_mean_before": float(np.mean(X[:, target_index])),
        "target_mean_after": 0.0,
        "row_gate_min": float(np.min(row_gates)),
        "row_gate_max": float(np.max(row_gates)),
        "residual_nonzero_genes": int(np.count_nonzero(residual)),
        "normalization": "none_after_sparse_log1p_residual",
    }
    return prediction.astype(np.float32, copy=False), diagnostics


def write_table(path: Path, header: list[str], rows: list[list[Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def write_prior_table(path: Path, prior: SignedPrior, budget: EffectBudget, panel: list[str]) -> None:
    support = set(int(index) for index in prior.support_indices)
    rows = []
    residual = residual_vector(prior, budget)
    for index, gene in enumerate(panel):
        rows.append(
            [
                gene,
                index,
                f"{float(prior.rho[index]):.10g}",
                f"{float(-prior.rho[index]):.10g}",
                f"{float(prior.confidence[index]):.10g}",
                int(prior.confidence[index] > prior.threshold and gene != prior.target_gene),
                int(index in support),
                f"{float(residual[index]):.10g}",
            ]
        )
    write_table(
        path,
        ["gene", "panel_index", "rho_wt", "ko_sign_score", "confidence", "eligible", "selected", "residual"],
        rows,
    )


def write_gate_table(path: Path, metadata: dict[str, Any], carrier_labels: np.ndarray) -> None:
    counts = {str(state): int(np.count_nonzero(carrier_labels == state)) for state in metadata["states"]}
    rows = []
    for state in metadata["states"]:
        rows.append(
            [
                state,
                metadata["state_counts"][state],
                counts.get(state, 0),
                f"{metadata['activity'][state]:.10g}",
                f"{metadata['gates'][state]:.10g}",
            ]
        )
    write_table(path, ["celltype", "wt_n", "carrier_n", "target_activity", "gate"], rows)


def _prepare_output(
    carrier: ad.AnnData,
    prediction: np.ndarray,
    *,
    prior: SignedPrior,
    budget: EffectBudget,
    gate_metadata: dict[str, Any],
    diagnostics: dict[str, Any],
    output_path: Path,
    source_wt_path: Path,
    source_ko_path: Path,
    carrier_path: Path,
) -> ad.AnnData:
    out = carrier.copy()
    out.X = np.asarray(prediction, dtype=np.float32)
    out.layers.clear()
    coords = np.asarray(carrier.obsm["spatial_3D"], dtype=np.float32)[:, :3].copy()
    out.obsm.clear()
    out.obsm["spatial_3D"] = coords
    response_meta = {
        "atom_id": ATOM_ID,
        "board": BOARD,
        "lane_id": prior.lane_id,
        "method": prior.method,
        "prior_strength": "weak",
        "prior_source": "WT_only_Spearman",
        "target_gene": prior.target_gene,
        "train_wt_path": str(source_wt_path.resolve()),
        "train_ko_path": str(source_ko_path.resolve()),
        "carrier_path": str(carrier_path.resolve()),
        "train_ko_direction_used": False,
        "train_ko_abs_budget_used": True,
        "target_used_for_generation": False,
        "target_truth_used_for_evaluation": False,
        "n_de_train": budget.n_de,
        "median_abs_effect": budget.median_abs_effect,
        "q90_abs_effect": budget.q90_abs_effect,
        "prior_threshold": prior.threshold,
        "eligible_count": int(len(prior.eligible_indices)),
        "selected_genes": json.dumps([str(out.var_names[index]) for index in prior.support_indices]),
        "gate_metadata": json.dumps(gate_metadata, sort_keys=True),
        "diagnostics": json.dumps(diagnostics, sort_keys=True),
        "normalization": "no_rowwise_renormalization",
        "layers_cleared": True,
        "submission_contract_validated": True,
    }
    out.uns["ve_signed_response"] = response_meta
    out.uns["ve_submission_prep"] = {
        "board": BOARD,
        "task": "T3",
        "method": prior.method,
        "n_cells": int(out.n_obs),
        "seed": SEED,
        "sampling_strategy": "immutable_carrier_scaffold",
        "target_used": False,
        "submission_contract_validated": True,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out.write_h5ad(output_path)
    return out


def semantic_checks(
    base: ad.AnnData,
    candidate: ad.AnnData,
    *,
    prior: SignedPrior,
    carrier_path: Path,
    require_parent_sha: bool = True,
) -> dict[str, Any]:
    panel = [str(gene) for gene in base.var_names]
    target_index = panel.index(prior.target_gene)
    support = set(int(index) for index in prior.support_indices)
    non_response = [index for index in range(len(panel)) if index not in support and index != target_index]
    base_X = _dense_float64(base.X)
    candidate_X = _dense_float64(candidate.X)
    base_coords = np.asarray(base.obsm["spatial_3D"])
    candidate_coords = np.asarray(candidate.obsm["spatial_3D"])
    delta = candidate_X.mean(axis=0) - base_X.mean(axis=0)
    response_mask = np.zeros(len(panel), dtype=bool)
    response_mask[list(support)] = True
    non_target = np.ones(len(panel), dtype=bool)
    non_target[target_index] = False
    wt_pb = base_X.mean(axis=0)
    if np.std(delta[non_target]) > 0 and np.std(wt_pb[non_target]) > 0:
        rank_corr = float(
            np.corrcoef(rankdata(delta[non_target]), rankdata(wt_pb[non_target]))[0, 1]
        )
    else:
        rank_corr = 0.0
    base_library = np.expm1(np.clip(base_X, 0, 50)).sum(axis=1)
    candidate_library = np.expm1(np.clip(candidate_X, 0, 50)).sum(axis=1)
    checks = {
        "parent_sha256_matches": (
            (_sha256(carrier_path) == EXPECTED_PARENT_SHA256) if carrier_path.exists() else False
        )
        if require_parent_sha
        else True,
        "shape_unchanged": list(base.shape) == list(candidate.shape),
        "finite_nonnegative": bool(np.isfinite(candidate_X).all() and (candidate_X >= 0).all()),
        "obs_order_unchanged": [str(value) for value in base.obs_names]
        == [str(value) for value in candidate.obs_names],
        "var_order_unchanged": panel == [str(value) for value in candidate.var_names],
        "spatial_shape_unchanged": list(base_coords.shape) == list(candidate_coords.shape),
        "spatial_exact": bool(np.array_equal(base_coords, candidate_coords)),
        "target_exact_zero": bool(np.array_equal(candidate_X[:, target_index], np.zeros(candidate.n_obs))),
        "non_response_bitwise_unchanged": bool(np.array_equal(base_X[:, non_response], candidate_X[:, non_response])),
        "layers_cleared": len(candidate.layers) == 0,
        "support_count_exact": int(np.count_nonzero(np.any(candidate_X != base_X, axis=0))) == len(support) + 1,
        "signed_rank_nonzero": bool(np.count_nonzero(delta[response_mask]) > 0),
        "signed_rank_not_wt_collinear": bool(abs(rank_corr) < 1.0 - 1e-6),
        "n_obs_board_valid": MIN_CELLS <= candidate.n_obs <= MAX_CELLS,
    }
    checks.update(
        {
            "all_core_invariants": bool(all(checks.values())),
            "non_response_delta_max_abs": float(np.max(np.abs(delta[non_response]))) if non_response else 0.0,
            "residual_rank_corr_with_wt_expression": rank_corr,
            "library_ratio_median": float(np.median(candidate_library / base_library)),
            "library_ratio_q05": float(np.quantile(candidate_library / base_library, 0.05)),
            "library_ratio_q95": float(np.quantile(candidate_library / base_library, 0.95)),
            "candidate_expression_digest": _matrix_digest(candidate.X),
            "base_expression_digest": _matrix_digest(base.X),
            "coordinate_digest": _matrix_digest(candidate_coords),
        }
    )
    return checks


def _make_self_carrier(source: Any, path: Path, *, seed: int) -> ad.AnnData:
    labels = _celltypes(source.adata, source.path)
    if source.adata.n_obs < N_SELF_CELLS:
        raise ValueError("self-check WT has fewer cells than the T3 carrier requirement")
    indices = select_indices(labels, n_cells=N_SELF_CELLS, seed=seed, strategy="stratified")
    sampled = source.adata[indices, source.panel].to_memory()
    coords = np.asarray(sampled.obsm["spatial_3D"], dtype=np.float32)[:, :3]
    sampled.obsm.clear()
    sampled.obsm["spatial_3D"] = coords
    sampled.layers.clear()
    sampled.uns["ve_submission_prep"] = {
        "board": BOARD,
        "task": "T3",
        "method": "wt_identity_self_check_carrier",
        "n_cells": N_SELF_CELLS,
        "seed": int(seed),
        "sampling_strategy": "stratified",
        "target_used": False,
        "submission_contract_validated": True,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    sampled.write_h5ad(path)
    return sampled


def _run_scorer(*, input_path: Path, target_path: Path, wt_path: Path, output_path: Path) -> str:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(VECKIT_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    env["LD_LIBRARY_PATH"] = "/opt/anaconda3/lib" + os.pathsep + env.get("LD_LIBRARY_PATH", "")
    command = [
        sys.executable,
        str(VECKIT_ROOT / "score_h5ad.py"),
        "--task",
        "T3",
        "--input",
        str(input_path),
        "--target",
        str(target_path),
        "--wt",
        str(wt_path),
        "--seed",
        str(SEED),
        "--out",
        str(output_path),
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True, env=env)
    return result.stdout


def _manifest(
    *,
    lane_id: str,
    candidate_id: str,
    output_path: Path,
    base_submission: str,
    checks: dict[str, Any],
    prior: SignedPrior,
    budget: EffectBudget,
    self_score_path: Path,
    project_root: Path,
    prior_wt_path: Path | None = None,
) -> dict[str, Any]:
    candidate = ad.read_h5ad(output_path)
    self_metrics: dict[str, Any] = {}
    if self_score_path.exists():
        try:
            self_metrics = json.loads(self_score_path.read_text(encoding="utf-8")).get("metrics", {})
        except json.JSONDecodeError:
            self_metrics = {"status": "unparsed"}
    manifest = {
        "atom_id": ATOM_ID,
        "lane_id": lane_id,
        "candidate_id": candidate_id,
        "task": "T3",
        "board": "T3_gata4",
        "base_submission": base_submission,
        "output_file": _artifact_relative_path(output_path, project_root).as_posix(),
        "sha256": _sha256(output_path),
        "n_obs": int(candidate.n_obs),
        "n_vars": int(candidate.n_vars),
        "gene_order_hash": _names_digest(candidate.var_names),
        "expression_multiset_hash": _matrix_digest(candidate.X),
        "coordinate_hash": _matrix_digest(candidate.obsm["spatial_3D"]),
        "scorer_version": SCORER_VERSION,
        "official_index_hash": _sha256(PANEL_PATH),
        "seed": SEED,
        "primary_metrics": {
            "DES": self_metrics.get("de_score"),
            "DCS": self_metrics.get("de_direction"),
            "PSS": self_metrics.get("severity_slope"),
            "self_check_only": True,
            "server_score": None,
            "status": "score_pending",
        },
        "protected_checks": checks,
        "recommend_submit": True,
        "final_candidate": True,
        "score_required": True,
        "attempt_id": None,
        "score_status": "score_pending",
        "target_used": False,
        "notes": (
            f"B1-A2 {lane_id}; WT-only weak prior. Both final lanes are mandatory manual-score candidates; "
            f"K_train={budget.n_de}, learned_support={budget.n_de - 1}."
        ),
    }
    return _enrich_manifest(
        manifest,
        candidate,
        output_path=output_path,
        project_root=project_root,
        prior=prior,
        budget=budget,
        prior_wt_path=prior_wt_path,
    )


def _write_result(path: Path, manifests: list[dict[str, Any]], *, self_scores: dict[str, Any]) -> None:
    lines = [
        "# B1-A2 RESULT",
        "",
        "- status: SCORE_PENDING",
        "- overall decision: BOTH_LANES_REQUIRED_FOR_MANUAL_UPLOAD",
        "- task: T3:gata4",
        "- parent: baseline-001/T3_gata4/v0001",
        "- final candidates: 2",
        "- prior strength: weak (WT-only Spearman; no registered GRN/embedding available)",
        "- target used for generation: false",
        "- server scores: 0/2",
        "",
        "| Lane | Candidate | SHA256 | Contract | Self-check | Server status |",
        "|---|---|---|---|---|---|",
    ]
    for manifest in manifests:
        score = self_scores.get(manifest["lane_id"], {})
        lines.append(
            f"| {manifest['lane_id']} | {manifest['candidate_id']} | {manifest['sha256']} | "
            f"{'PASS' if manifest['protected_checks']['all_core_invariants'] else 'FAIL'} | "
            f"DES={score.get('de_score')}, DCS={score.get('de_direction')} | score_pending |"
        )
    lines.extend(
        [
            "",
            "本轮两条 lane 均通过硬性 contract/invariant 才进入人工评分；Mab21l2 self-check 仅作风险诊断，不取消任一条合规候选。",
            "分数回填只登记用户提供的服务器分数，不新增截图、链接或 JSON 证据要求。",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def refresh_self_score_manifests(
    artifact_root: Path, *, project_root: Path = PROJECT_ROOT
) -> dict[str, Any]:
    """Attach independently generated self-check scores to an existing run."""

    artifact_root = Path(artifact_root)
    final_set_path = artifact_root / "FINAL_SET_MANIFEST.json"
    if not final_set_path.exists():
        raise FileNotFoundError(f"missing final-set manifest: {final_set_path}")
    final_set = json.loads(final_set_path.read_text(encoding="utf-8"))
    manifests: list[dict[str, Any]] = []
    self_scores: dict[str, Any] = {}
    for item in final_set.get("candidates", []):
        manifest_path = artifact_root / item["manifest"]
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        lane_id = str(manifest["lane_id"])
        output_path = manifest_path.parent / "prediction.h5ad"
        candidate = ad.read_h5ad(output_path)
        score_path = artifact_root / "metrics" / "mab21l2_self_prediction" / lane_id / "candidate.json"
        if not score_path.exists():
            raise FileNotFoundError(f"missing self-check score for {lane_id}: {score_path}")
        score_payload = json.loads(score_path.read_text(encoding="utf-8"))
        metrics = score_payload.get("metrics", {})
        self_scores[lane_id] = metrics
        config_path = artifact_root / "config_resolved.yaml"
        config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
        manifest = _enrich_manifest(
            manifest,
            candidate,
            output_path=output_path,
            project_root=project_root,
            prior_wt_path=Path(config["target_wt"]) if config.get("target_wt") else None,
        )
        primary = manifest.setdefault("primary_metrics", {})
        primary.update(
            {
                "DES": metrics.get("de_score"),
                "DCS": metrics.get("de_direction"),
                "PSS": metrics.get("severity_slope"),
                "self_check_only": True,
                "server_score": None,
                "status": "score_pending",
            }
        )
        _json_write(manifest_path, manifest)
        manifests.append(manifest)
    final_set["self_check"] = self_scores
    final_set["score_status"] = "score_pending"
    _json_write(final_set_path, final_set)
    _write_result(artifact_root / "RESULT.md", manifests, self_scores=self_scores)
    run_log = artifact_root / "run.log"
    if run_log.exists():
        with run_log.open("a", encoding="utf-8") as handle:
            handle.write("attached independent Mab21l2 self-check scores\n")
    return {"artifact_root": str(artifact_root.resolve()), "candidates": manifests, "self_check": self_scores}


def run_batch1_a2(
    *,
    target_wt_path: Path,
    train_wt_path: Path,
    train_ko_path: Path,
    carrier_path: Path,
    artifact_root: Path,
    seed: int = SEED,
    run_self_scorer: bool = True,
) -> dict[str, Any]:
    if seed != SEED:
        raise ValueError(f"B1-A2 uses fixed seed {SEED}")
    target_wt_path = Path(target_wt_path)
    train_wt_path = Path(train_wt_path)
    train_ko_path = Path(train_ko_path)
    carrier_path = Path(carrier_path)
    artifact_root = Path(artifact_root)
    if artifact_root.exists():
        raise FileExistsError(f"artifact root already exists: {artifact_root}")
    candidate_paths = {
        "L1_CELL_LEVEL_SPEARMAN": PROJECT_ROOT / "submissions/candidates/T3_gata4/v0004_b1_a2_cell_spearman/submission.h5ad",
        "L2_STATE_PSEUDOBULK_SPEARMAN": PROJECT_ROOT / "submissions/candidates/T3_gata4/v0005_b1_a2_state_pb_spearman/submission.h5ad",
    }
    for path in candidate_paths.values():
        if path.exists():
            raise FileExistsError(f"candidate output already exists: {path}")
    if not carrier_path.exists() or _sha256(carrier_path) != EXPECTED_PARENT_SHA256:
        raise ValueError("carrier is not the immutable baseline-001 T3:gata4 scaffold")

    partial_root = artifact_root.parent / f"{artifact_root.name}.partial"
    if partial_root.exists():
        raise FileExistsError(f"partial artifact root already exists: {partial_root}")
    partial_root.mkdir(parents=True, exist_ok=False)
    events: list[str] = []
    manifests: list[dict[str, Any]] = []
    self_scores: dict[str, Any] = {}
    wt_target = wt_train = ko = None
    try:
        panel = _panel(PANEL_PATH)
        wt_target = _open_source(target_wt_path, panel, "target_stage_wt")
        wt_train = _open_source(train_wt_path, panel, "train_wt")
        ko = _open_source(train_ko_path, panel, "train_ko")
        carrier = _carrier(carrier_path, panel)
        events.append("locked panel, WT/KO training pair, and immutable carrier")
        budget = derive_effect_budget(ko.X, wt_train.X)
        events.append(f"effect budget: K_train={budget.n_de}, median_abs={budget.median_abs_effect:.10g}")

        for lane_id in FINAL_LANES:
            prior = select_support(
                build_signed_prior(wt_target.adata, lane_id=lane_id, target_gene="Gata4"), budget
            )
            gates, gate_metadata = build_state_gates(wt_target.adata, target_gene="Gata4")
            prediction, diagnostics = apply_signed_residual(
                carrier, prior=prior, gates=gates, budget=budget
            )
            final_dir = partial_root / "final" / lane_id / "T3_gata4"
            output_path = final_dir / "prediction.h5ad"
            candidate = _prepare_output(
                carrier,
                prediction,
                prior=prior,
                budget=budget,
                gate_metadata=gate_metadata,
                diagnostics=diagnostics,
                output_path=output_path,
                source_wt_path=train_wt_path,
                source_ko_path=train_ko_path,
                carrier_path=carrier_path,
            )
            checks = semantic_checks(carrier, candidate, prior=prior, carrier_path=carrier_path)
            if not checks["all_core_invariants"]:
                raise AssertionError(f"{lane_id}: core invariant failure: {checks}")
            write_prior_table(final_dir / "signed_prior.tsv", prior, budget, panel)
            write_gate_table(final_dir / "state_gates.tsv", gate_metadata, _celltypes(carrier, carrier_path))
            _json_write(final_dir / "protected_checks.json", checks)
            events.append(f"built {lane_id}: support={len(prior.support_indices)}")

        self_root = partial_root / "metrics" / "mab21l2_self_prediction"
        self_carrier_path = self_root / "wt_carrier.h5ad"
        self_carrier = _make_self_carrier(wt_train, self_carrier_path, seed=seed)
        for lane_id in FINAL_LANES:
            prior = select_support(
                build_signed_prior(wt_train.adata, lane_id=lane_id, target_gene="Mab21l2"), budget
            )
            gates, gate_metadata = build_state_gates(wt_train.adata, target_gene="Mab21l2")
            prediction, diagnostics = apply_signed_residual(
                self_carrier, prior=prior, gates=gates, budget=budget
            )
            lane_root = self_root / lane_id
            self_prediction_path = lane_root / "prediction.h5ad"
            self_candidate = _prepare_output(
                self_carrier,
                prediction,
                prior=prior,
                budget=budget,
                gate_metadata=gate_metadata,
                diagnostics=diagnostics,
                output_path=self_prediction_path,
                source_wt_path=train_wt_path,
                source_ko_path=train_ko_path,
                carrier_path=self_carrier_path,
            )
            self_checks = semantic_checks(
                self_carrier,
                self_candidate,
                prior=prior,
                carrier_path=self_carrier_path,
                require_parent_sha=False,
            )
            if not self_checks["all_core_invariants"]:
                raise AssertionError(f"{lane_id} self-check invariant failure: {self_checks}")
            write_prior_table(lane_root / "signed_prior.tsv", prior, budget, [str(gene) for gene in self_carrier.var_names])
            write_gate_table(lane_root / "state_gates.tsv", gate_metadata, _celltypes(self_carrier, self_carrier_path))
            _json_write(lane_root / "protected_checks.json", self_checks)
            if run_self_scorer:
                floor_path = lane_root / "floor.json"
                candidate_score_path = lane_root / "candidate.json"
                _run_scorer(
                    input_path=self_carrier_path,
                    target_path=train_ko_path,
                    wt_path=self_carrier_path,
                    output_path=floor_path,
                )
                _run_scorer(
                    input_path=self_prediction_path,
                    target_path=train_ko_path,
                    wt_path=self_carrier_path,
                    output_path=candidate_score_path,
                )
                self_scores[lane_id] = json.loads(candidate_score_path.read_text(encoding="utf-8")).get("metrics", {})
            events.append(f"completed Mab21l2 self-check for {lane_id}")

        for lane_id in FINAL_LANES:
            candidate_id = (
                "B1-A2-L1-T3_gata4" if lane_id == "L1_CELL_LEVEL_SPEARMAN" else "B1-A2-L2-T3_gata4"
            )
            final_dir = partial_root / "final" / lane_id / "T3_gata4"
            output_path = final_dir / "prediction.h5ad"
            self_score_path = partial_root / "metrics" / "mab21l2_self_prediction" / lane_id / "candidate.json"
            manifest = _manifest(
                lane_id=lane_id,
                candidate_id=candidate_id,
                output_path=output_path,
                base_submission="baseline-001/T3_gata4/v0001",
                checks=json.loads((final_dir / "protected_checks.json").read_text(encoding="utf-8")),
                prior=select_support(
                    build_signed_prior(wt_target.adata, lane_id=lane_id, target_gene="Gata4"), budget
                ),
                budget=budget,
                self_score_path=self_score_path,
                project_root=PROJECT_ROOT,
                prior_wt_path=target_wt_path,
            )
            _json_write(final_dir / "MANIFEST.json", manifest)
            manifests.append(manifest)

        _json_write(
            partial_root / "FINAL_SET_MANIFEST.json",
            {
                "atom_id": ATOM_ID,
                "final_lanes": list(FINAL_LANES),
                "boards": ["T3_gata4"],
                "expected_final_artifacts": 2,
                "exploration_attempt_budget": 4,
                "exploration_attempts": [],
                "candidates": [
                    {
                        "lane_id": manifest["lane_id"],
                        "candidate_id": manifest["candidate_id"],
                        "manifest": f"final/{manifest['lane_id']}/T3_gata4/MANIFEST.json",
                        "output_file": manifest["output_file"],
                        "sha256": manifest["sha256"],
                    }
                    for manifest in manifests
                ],
                "submission_mode": "manual_user_upload",
                "all_scores_required": True,
                "score_status": "score_pending",
                "self_check": self_scores,
            },
        )
        _json_write(
            partial_root / "config_resolved.yaml",
            {
                "atom_id": ATOM_ID,
                "seed": seed,
                "lanes": list(FINAL_LANES),
                "lane_methods": LANE_METHODS,
                "target_wt": str(target_wt_path.resolve()),
                "train_wt": str(train_wt_path.resolve()),
                "train_ko": str(train_ko_path.resolve()),
                "carrier": str(carrier_path.resolve()),
                "carrier_sha256": _sha256(carrier_path),
                "panel_sha256": _sha256(PANEL_PATH),
                "scorer_version": SCORER_VERSION,
                "normalization": "no_rowwise_renormalization",
                "target_used_for_generation": False,
                "train_ko_direction_used": False,
            },
        )
        _write_result(partial_root / "RESULT.md", manifests, self_scores=self_scores)
        partial_root.joinpath("run.log").write_text("\n".join(events) + "\n", encoding="utf-8")
        partial_root.rename(artifact_root)
        for lane_id in FINAL_LANES:
            source = artifact_root / "final" / lane_id / "T3_gata4" / "prediction.h5ad"
            destination = candidate_paths[lane_id]
            destination.parent.mkdir(parents=True, exist_ok=False)
            shutil.copy2(source, destination)
        return {
            "artifact_root": str(artifact_root.resolve()),
            "candidates": manifests,
            "self_check": self_scores,
            "events": events,
        }
    except Exception as exc:
        events.append(f"FAILED: {type(exc).__name__}: {exc}")
        partial_root.joinpath("run.log").write_text("\n".join(events) + "\n", encoding="utf-8")
        raise
    finally:
        for source in (wt_target, wt_train, ko):
            if source is not None:
                _close_source(source)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-wt", type=Path, default=PROJECT_ROOT / "data/E8.75.h5ad")
    parser.add_argument("--train-wt", type=Path, default=PROJECT_ROOT / "data/E9.5.h5ad")
    parser.add_argument("--train-ko", type=Path, default=PROJECT_ROOT / "data/E9.5_mab21l2_ko.h5ad")
    parser.add_argument(
        "--carrier",
        type=Path,
        default=PROJECT_ROOT / "submissions/scored/baseline-001/T3_gata4/submission.h5ad",
    )
    parser.add_argument("--artifact-root", type=Path, default=PROJECT_ROOT / "artifacts/atomic_batch1/B1-A2")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument(
        "--skip-self-scorer",
        action="store_true",
        help="仅拆分生成阶段；完成两个官方 self-check scorer 后再运行 --refresh-self-scores",
    )
    parser.add_argument(
        "--refresh-self-scores",
        action="store_true",
        help="将已生成的 candidate.json 写入现有 B1-A2 manifest",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.refresh_self_scores and args.skip_self_scorer:
        raise SystemExit("--refresh-self-scores and --skip-self-scorer are mutually exclusive")
    if args.refresh_self_scores:
        result = refresh_self_score_manifests(args.artifact_root)
    else:
        result = run_batch1_a2(
            target_wt_path=args.target_wt,
            train_wt_path=args.train_wt,
            train_ko_path=args.train_ko,
            carrier_path=args.carrier,
            artifact_root=args.artifact_root,
            seed=args.seed,
            run_self_scorer=not args.skip_self_scorer,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
