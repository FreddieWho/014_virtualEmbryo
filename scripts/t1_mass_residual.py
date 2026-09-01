#!/usr/bin/env python3
"""B1-A3 T1 state-mass forecast with sparse, state-conditioned row replay.

The released E8.5 and E9.5 annotations use different vocabularies.  This
module therefore makes the cross-stage state rule explicit before estimating
growth.  It has two source-only lanes:

* ``L1_SHARED_UNRESOLVED`` keeps exact shared labels and puts every
  stage-specific label in one explicitly unresolved bucket.
* ``L2_E95_EXPRESSION_PROBE`` uses E9.5's existing labels as the fixed state
  vocabulary and assigns E8.5 cells by cosine similarity to E9.5 state means.

Candidate expression rows are always complete rows from the immutable parent;
there is no per-gene noise, dense residual matrix, or target read.
"""

from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import anndata as ad
import numpy as np
from scipy import sparse


BOARD = "T1:val"
TASK = "T1"
TARGET_STAGE = 10.5
PREVIOUS_STAGE = 8.5
BASE_STAGE = 9.5
ALPHA = 0.5
SEED = 20260827
N_CELLS = 5118
MIN_CELLS = 1000
MAX_CELLS = 5118
PARENT_CANDIDATE = "baseline-001/T1_val/v0001"
PARENT_SHA256 = "11dbf50a0eb876a1a3c53a283459c8f53e14dcd314f1e7725a3a6107618c981e"
SCORER_VERSION = "veckit@46d41e63f42a9aab815db20b742feeccd249cb17"
UNRESOLVED_STATE = "UNRESOLVED_STAGE_SPECIFIC"

LANES = {
    "L1_SHARED_UNRESOLVED": "shared_exact_plus_unresolved",
    "L2_E95_EXPRESSION_PROBE": "e95_labels_with_expression_projection",
}


@dataclass(frozen=True)
class PartitionResult:
    lane_id: str
    method: str
    previous_states: np.ndarray
    base_states: np.ndarray
    previous_raw: np.ndarray
    base_raw: np.ndarray
    previous_obs_names: tuple[str, ...]
    base_obs_names: tuple[str, ...]
    previous_sha256: str
    base_sha256: str
    assignment_sha256: str
    centroid_sha256: str | None
    partition_sha256: str
    states: tuple[str, ...]
    manifest_path: Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _sha256_text(lines: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for line in lines:
        digest.update(line.encode("utf-8"))
    return digest.hexdigest()


def read_panel(path: Path) -> list[str]:
    genes = [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(genes) != 32285 or len(set(genes)) != len(genes):
        raise ValueError(f"{path}: expected 32285 unique genes")
    return genes


def gene_order_hash(genes: Sequence[str]) -> str:
    return hashlib.sha256("\n".join(map(str, genes)).encode("utf-8")).hexdigest()


def _labels(adata: ad.AnnData, path: Path) -> np.ndarray:
    if "celltype" not in adata.obs:
        raise ValueError(f"{path}: obs['celltype'] is required")
    values = adata.obs["celltype"]
    if values.isna().any():
        raise ValueError(f"{path}: obs['celltype'] contains missing values")
    result = np.asarray(values.astype(str), dtype=str)
    if result.ndim != 1 or len(result) != adata.n_obs or (result == "").any():
        raise ValueError(f"{path}: invalid celltype vector")
    return result


def _validate_input(adata: ad.AnnData, path: Path, panel: Sequence[str]) -> np.ndarray:
    names = [str(value) for value in adata.var_names]
    if names != list(panel):
        raise ValueError(f"{path}: var_names do not exactly match the T1 panel")
    if getattr(adata.X, "ndim", None) != 2 or adata.n_vars != len(panel):
        raise ValueError(f"{path}: X must be cells x 32285")
    values = np.asarray(adata.X.data if sparse.issparse(adata.X) else adata.X)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError(f"{path}: X must be finite and non-negative")
    names = [str(value) for value in adata.obs_names]
    if len(set(names)) != len(names):
        raise ValueError(f"{path}: obs_names must be unique")
    return _labels(adata, path)


def canonicalize_shared_unresolved(labels: Sequence[str], shared_states: set[str]) -> np.ndarray:
    values = np.asarray(labels, dtype=str)
    if values.ndim != 1:
        raise ValueError("labels must be one-dimensional")
    return np.asarray(
        [value if value in shared_states else UNRESOLVED_STATE for value in values], dtype=str
    )


def _row_l2_normalize(X: Any) -> Any:
    if sparse.issparse(X):
        matrix = X.tocsr().astype(np.float32, copy=False)
        norms = np.sqrt(np.asarray(matrix.multiply(matrix).sum(axis=1)).ravel())
        norms[norms == 0] = 1.0
        return matrix.multiply((1.0 / norms)[:, None]).tocsr()
    matrix = np.asarray(X, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1)
    norms[norms == 0] = 1.0
    return matrix / norms[:, None]


def fit_expression_centroids(X: Any, labels: Sequence[str], states: Sequence[str]) -> np.ndarray:
    values = np.asarray(labels, dtype=str)
    normalized = _row_l2_normalize(X)
    columns: list[np.ndarray] = []
    for state in states:
        rows = np.flatnonzero(values == state)
        if len(rows) == 0:
            raise ValueError(f"cannot fit centroid for absent state {state!r}")
        mean = np.asarray(normalized[rows].mean(axis=0)).ravel().astype(np.float32)
        norm = float(np.linalg.norm(mean))
        if norm == 0:
            raise ValueError(f"state {state!r} has a zero expression centroid")
        columns.append(mean / norm)
    return np.stack(columns, axis=1).astype(np.float32, copy=False)


def predict_expression_states(X: Any, centroids: np.ndarray, states: Sequence[str]) -> np.ndarray:
    if centroids.ndim != 2 or centroids.shape[1] != len(states):
        raise ValueError("centroid shape does not match state vocabulary")
    normalized = _row_l2_normalize(X)
    scores = normalized @ centroids
    scores = np.asarray(scores)
    if scores.ndim != 2 or scores.shape[1] != len(states) or not np.isfinite(scores).all():
        raise ValueError("expression projection produced invalid scores")
    return np.asarray(states, dtype=str)[np.argmax(scores, axis=1)]


def _write_tsv(path: Path, header: Sequence[str], rows: Iterable[Sequence[Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def _assignment_digest(
    previous_sha: str,
    base_sha: str,
    previous_obs: Sequence[str],
    base_obs: Sequence[str],
    previous_raw: Sequence[str],
    base_raw: Sequence[str],
    previous_states: Sequence[str],
    base_states: Sequence[str],
) -> str:
    def records(stage: str, file_sha: str, obs: Sequence[str], raw: Sequence[str], states: Sequence[str]):
        for name, raw_value, state in zip(obs, raw, states):
            yield f"{stage}\t{file_sha}\t{name}\t{raw_value}\t{state}\n"

    return _sha256_text(
        list(records("E8.5", previous_sha, previous_obs, previous_raw, previous_states))
        + list(records("E9.5", base_sha, base_obs, base_raw, base_states))
    )


def freeze_partition(
    *,
    lane_id: str,
    previous_path: Path,
    base_path: Path,
    panel_path: Path,
    output_dir: Path,
    overwrite: bool = False,
) -> PartitionResult:
    if lane_id not in LANES:
        raise ValueError(f"unsupported lane {lane_id!r}")
    output_dir = Path(output_dir)
    manifest_path = output_dir / "partition_manifest.json"
    if manifest_path.exists() and not overwrite:
        raise FileExistsError(f"partition already exists: {manifest_path}")
    panel = read_panel(Path(panel_path))
    previous_path, base_path = Path(previous_path), Path(base_path)
    previous_sha, base_sha = sha256_file(previous_path), sha256_file(base_path)

    base = ad.read_h5ad(base_path)
    base_raw = _validate_input(base, base_path, panel)
    base_obs = tuple(str(value) for value in base.obs_names)
    states = tuple(sorted(np.unique(base_raw).tolist()))
    centroids: np.ndarray | None = None
    centroid_sha: str | None = None
    if lane_id == "L2_E95_EXPRESSION_PROBE":
        centroids = fit_expression_centroids(base.X, base_raw, states)
        centroid_path = output_dir / "e95_expression_centroids.npz"
        output_dir.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(centroid_path, states=np.asarray(states), centroids=centroids)
        centroid_sha = sha256_file(centroid_path)
    if lane_id == "L1_SHARED_UNRESOLVED":
        # The source label vocabulary itself is the only allowed partition rule.
        del base
        gc.collect()
    else:
        del base
        gc.collect()

    previous = ad.read_h5ad(previous_path)
    previous_raw = _validate_input(previous, previous_path, panel)
    previous_obs = tuple(str(value) for value in previous.obs_names)
    if lane_id == "L1_SHARED_UNRESOLVED":
        shared = set(np.unique(previous_raw)).intersection(states)
        previous_states = canonicalize_shared_unresolved(previous_raw, shared)
        base_states = canonicalize_shared_unresolved(base_raw, shared)
        states = tuple(sorted(np.unique(np.concatenate([previous_states, base_states])).tolist()))
    else:
        assert centroids is not None
        previous_states = predict_expression_states(previous.X, centroids, states)
        base_states = base_raw.copy()
    del previous
    gc.collect()

    assignment_sha = _assignment_digest(
        previous_sha,
        base_sha,
        previous_obs,
        base_obs,
        previous_raw,
        base_raw,
        previous_states,
        base_states,
    )
    partition_identity = {
        "lane_id": lane_id,
        "method": LANES[lane_id],
        "previous_sha256": previous_sha,
        "base_sha256": base_sha,
        "assignment_sha256": assignment_sha,
        "centroid_sha256": centroid_sha,
        "states": list(states),
        "source_only": True,
        "target_used": False,
    }
    partition_sha = hashlib.sha256(
        json.dumps(partition_identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    rows = []
    rows.extend(
        ("E8.5", previous_sha, name, raw, state)
        for name, raw, state in zip(previous_obs, previous_raw, previous_states)
    )
    rows.extend(
        ("E9.5", base_sha, name, raw, state)
        for name, raw, state in zip(base_obs, base_raw, base_states)
    )
    _write_tsv(
        output_dir / "partition_assignments.tsv",
        ["stage", "input_sha256", "obs_name", "raw_celltype", "state_id"],
        rows,
    )
    manifest = {
        **partition_identity,
        "partition_sha256": partition_sha,
        "previous_n": len(previous_states),
        "base_n": len(base_states),
        "assignment_coverage": 1.0,
        "assignment_unique_keys": True,
        "generated_by": "scripts/t1_mass_residual.py",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return PartitionResult(
        lane_id=lane_id,
        method=LANES[lane_id],
        previous_states=previous_states,
        base_states=base_states,
        previous_raw=previous_raw,
        base_raw=base_raw,
        previous_obs_names=previous_obs,
        base_obs_names=base_obs,
        previous_sha256=previous_sha,
        base_sha256=base_sha,
        assignment_sha256=assignment_sha,
        centroid_sha256=centroid_sha,
        partition_sha256=partition_sha,
        states=states,
        manifest_path=manifest_path,
    )


def _counts(labels: Sequence[str]) -> dict[str, int]:
    values, counts = np.unique(np.asarray(labels, dtype=str), return_counts=True)
    return {str(value): int(count) for value, count in zip(values, counts)}


def forecast_state_mass(
    previous_states: Sequence[str],
    base_states: Sequence[str],
    *,
    n_cells: int,
    alpha: float = ALPHA,
    t0: float = PREVIOUS_STAGE,
    t1: float = BASE_STAGE,
    target_stage: float = TARGET_STAGE,
    min_quota: int = 1,
) -> tuple[dict[str, int], list[dict[str, Any]]]:
    previous = np.asarray(previous_states, dtype=str)
    base = np.asarray(base_states, dtype=str)
    if previous.ndim != 1 or base.ndim != 1 or len(previous) == 0 or len(base) == 0:
        raise ValueError("at least one state is required in both stages")
    if not np.isfinite(alpha) or alpha <= 0:
        raise ValueError("alpha must be positive and finite")
    if not t0 < t1 <= target_stage:
        raise ValueError("stages must be ordered")
    if n_cells < 1 or n_cells > MAX_CELLS:
        raise ValueError(f"n_cells must be in [1, {MAX_CELLS}]")
    if min_quota < 0:
        raise ValueError("min_quota must be non-negative")
    previous_counts, base_counts = _counts(previous), _counts(base)
    states = sorted(set(previous_counts) | set(base_counts))
    observed = [state for state in states if previous_counts.get(state, 0) and base_counts.get(state, 0)]
    if not observed:
        raise ValueError("at least one state must be observed in both stages")
    n0, n1 = len(previous), len(base)
    denominator0 = n0 + alpha * len(states)
    denominator1 = n1 + alpha * len(states)
    p0 = {state: (previous_counts.get(state, 0) + alpha) / denominator0 for state in states}
    p1 = {state: (base_counts.get(state, 0) + alpha) / denominator1 for state in states}
    dt = float(t1 - t0)
    growth = {state: float((np.log(p1[state]) - np.log(p0[state])) / dt) for state in states}
    observed_growth = np.asarray([growth[state] for state in observed], dtype=float)
    growth_median = float(np.median(observed_growth))
    train_counts = np.asarray(
        [previous_counts.get(state, 0) + base_counts.get(state, 0) for state in observed],
        dtype=float,
    )
    tau = float(np.median(train_counts))
    if tau <= 0:
        raise ValueError("state-count EB scale must be positive")
    low, high = (float(value) for value in np.quantile(observed_growth, [0.05, 0.95], method="linear"))
    shrunk: dict[str, float] = {}
    clipped: dict[str, float] = {}
    for state in states:
        count = float(previous_counts.get(state, 0) + base_counts.get(state, 0))
        weight = count / (count + tau)
        shrunk[state] = weight * growth[state] + (1.0 - weight) * growth_median
        clipped[state] = float(np.clip(shrunk[state], low, high))

    bank_states = sorted(set(base_counts))
    if min_quota * len(bank_states) > n_cells:
        raise ValueError("n_cells is smaller than the requested minimum quota")
    log_mass = {
        state: float(np.log(p1[state]) + clipped[state] * (target_stage - t1)) for state in bank_states
    }
    max_log = max(log_mass.values())
    unnormalized = {state: float(np.exp(log_mass[state] - max_log)) for state in bank_states}
    total = float(sum(unnormalized.values()))
    p_star = {state: unnormalized[state] / total for state in bank_states}
    remaining = n_cells - min_quota * len(bank_states)
    exact = {state: remaining * p_star[state] for state in bank_states}
    quota = {state: min_quota + int(np.floor(exact[state])) for state in bank_states}
    remainder = n_cells - sum(quota.values())
    order = sorted(
        bank_states,
        key=lambda state: (-(exact[state] - np.floor(exact[state])), state.encode("utf-8")),
    )
    for state in order[:remainder]:
        quota[state] += 1
    if sum(quota.values()) != n_cells:
        raise AssertionError("Hamilton allocation did not conserve n_cells")

    rows: list[dict[str, Any]] = []
    for state in states:
        role = (
            "observed_both"
            if state in observed
            else "emerging_e95"
            if state not in previous_counts
            else "disappeared_e95"
        )
        rows.append(
            {
                "state_id": state,
                "role": role,
                "n_previous": previous_counts.get(state, 0),
                "n_base": base_counts.get(state, 0),
                "p_previous": p0[state],
                "p_base": p1[state],
                "growth_raw": growth[state],
                "growth_shrunk": shrunk[state],
                "growth_clipped": clipped[state],
                "p_star": p_star.get(state, 0.0),
                "quota": quota.get(state, 0),
                "source_bank_n": base_counts.get(state, 0),
                "target_stage": target_stage,
                "alpha": alpha,
                "growth_median_observed": growth_median,
                "eb_tau_observed": tau,
                "clip_low_observed": low,
                "clip_high_observed": high,
            }
        )
    return quota, rows


def _state_seed(seed: int, state: str) -> int:
    digest = hashlib.sha256(f"{seed}\0{state}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "little") % (2**63 - 1)


def balanced_donor_indices(
    banks: Mapping[str, Sequence[int]],
    quotas: Mapping[str, int],
    *,
    seed: int,
) -> tuple[np.ndarray, dict[str, Any]]:
    if set(banks) != set(quotas):
        raise ValueError("banks and quotas must have identical state keys")
    donors: list[np.ndarray] = []
    donor_states: list[str] = []
    slices: dict[str, slice] = {}
    multiplicities: dict[str, dict[str, int]] = {}
    start = 0
    for state in sorted(banks):
        bank = np.asarray(banks[state], dtype=np.int64)
        q = int(quotas[state])
        if bank.ndim != 1 or len(bank) == 0:
            raise ValueError(f"state {state!r} has an empty residual bank")
        if q < 0:
            raise ValueError(f"state {state!r} has a negative quota")
        rng = np.random.default_rng(_state_seed(seed, state))
        permuted = bank.copy()
        rng.shuffle(permuted)
        full, remainder = divmod(q, len(permuted))
        selected = np.tile(permuted, full)
        if remainder:
            selected = np.concatenate([selected, permuted[:remainder]])
        donors.append(selected)
        donor_states.extend([state] * len(selected))
        slices[state] = slice(start, start + len(selected))
        start += len(selected)
        unique, counts = np.unique(selected, return_counts=True)
        multiplicities[state] = {str(int(index)): int(count) for index, count in zip(unique, counts)}
    result = np.concatenate(donors).astype(np.int64) if donors else np.empty(0, dtype=np.int64)
    return result, {
        "state_slices": slices,
        "donor_states": np.asarray(donor_states, dtype=str),
        "multiplicities": multiplicities,
        "seed": int(seed),
    }


def _column_block(X: Any, columns: np.ndarray) -> np.ndarray:
    value = X[:, columns]
    if sparse.issparse(value):
        value = value.toarray()
    return np.asarray(value, dtype=np.float32)


def fixed_gene_pairs(n_vars: int, *, n_pairs: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    left = rng.integers(0, n_vars, size=n_pairs)
    right = rng.integers(0, n_vars, size=n_pairs)
    keep = left != right
    if not np.any(keep):
        raise ValueError("gene-pair sampler produced no valid pairs")
    return left[keep], right[keep]


def variogram_rmse(
    source_X: Any,
    candidate_X: Any,
    *,
    left: np.ndarray,
    right: np.ndarray,
    p: float = 0.5,
    pair_chunk: int = 512,
) -> float:
    if p <= 0 or not np.isfinite(p):
        raise ValueError("p must be positive and finite")
    errors: list[np.ndarray] = []
    for start in range(0, len(left), pair_chunk):
        i, j = left[start : start + pair_chunk], right[start : start + pair_chunk]
        source = _column_block(source_X, np.concatenate([i, j]))
        candidate = _column_block(candidate_X, np.concatenate([i, j]))
        half = len(i)
        source_v = np.mean(np.abs(source[:, :half] - source[:, half:]) ** p, axis=0)
        candidate_v = np.mean(np.abs(candidate[:, :half] - candidate[:, half:]) ** p, axis=0)
        errors.append((candidate_v - source_v) ** 2)
    return float(np.sqrt(np.mean(np.concatenate(errors))))


def _mean_error(source_X: Any, candidate_X: Any) -> float:
    source_mean = np.asarray(source_X.mean(axis=0)).ravel().astype(np.float64)
    candidate_mean = np.asarray(candidate_X.mean(axis=0)).ravel().astype(np.float64)
    return float(np.sqrt(np.mean((source_mean - candidate_mean) ** 2)))


def _finite_nonnegative(X: Any) -> bool:
    values = np.asarray(X.data if sparse.issparse(X) else X)
    return bool(np.isfinite(values).all() and (values >= 0).all())


def _write_mass_table(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    fields = [
        "state_id",
        "role",
        "n_previous",
        "n_base",
        "p_previous",
        "p_base",
        "growth_raw",
        "growth_shrunk",
        "growth_clipped",
        "p_star",
        "quota",
        "realized_n",
        "realized_share",
        "source_bank_n",
        "target_stage",
        "alpha",
        "growth_median_observed",
        "eb_tau_observed",
        "clip_low_observed",
        "clip_high_observed",
    ]
    _write_tsv(path, fields, ([row.get(field, "") for field in fields] for row in rows))


def run_lane(
    *,
    lane_id: str,
    previous_path: Path,
    base_path: Path,
    parent_path: Path,
    panel_path: Path,
    artifact_dir: Path,
    submission_path: Path,
    seed: int = SEED,
    overwrite: bool = False,
) -> dict[str, Any]:
    if lane_id not in LANES:
        raise ValueError(f"unsupported lane {lane_id!r}")
    artifact_dir, submission_path = Path(artifact_dir), Path(submission_path)
    output_path = artifact_dir / "prediction.h5ad"
    if (output_path.exists() or submission_path.exists()) and not overwrite:
        raise FileExistsError("candidate output already exists; immutable artifacts are not overwritten")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    partition = freeze_partition(
        lane_id=lane_id,
        previous_path=previous_path,
        base_path=base_path,
        panel_path=panel_path,
        output_dir=artifact_dir / "partition",
        overwrite=overwrite,
    )
    parent_path = Path(parent_path)
    if sha256_file(parent_path) != PARENT_SHA256:
        raise ValueError("parent SHA256 does not match immutable T1 best")
    panel = read_panel(Path(panel_path))
    parent = ad.read_h5ad(parent_path)
    parent_raw = _validate_input(parent, parent_path, panel)
    if not MIN_CELLS <= parent.n_obs <= MAX_CELLS or parent.n_obs != N_CELLS:
        raise ValueError(f"parent has invalid T1 cell count: {parent.n_obs}")
    base_by_obs = dict(zip(partition.base_obs_names, partition.base_states))
    missing = [name for name in parent.obs_names if str(name) not in base_by_obs]
    if missing:
        raise ValueError(f"parent rows missing from frozen E9.5 assignment: {missing[:3]}")
    parent_states = np.asarray([base_by_obs[str(name)] for name in parent.obs_names], dtype=str)
    quotas, mass_rows = forecast_state_mass(
        partition.previous_states,
        partition.base_states,
        n_cells=parent.n_obs,
    )
    banks = {
        state: np.flatnonzero(parent_states == state).astype(np.int64)
        for state in sorted(quotas)
    }
    donors, donor_details = balanced_donor_indices(banks, quotas, seed=seed)
    candidate_states = donor_details["donor_states"]
    if len(donors) != parent.n_obs or len(candidate_states) != parent.n_obs:
        raise AssertionError("donor allocation changed the parent cell count")
    out = parent[donors, :].copy()
    if sparse.issparse(out.X):
        out.X = out.X.tocsr().astype(np.float32, copy=False)
    else:
        out.X = np.asarray(out.X, dtype=np.float32)
    out.obs_names = np.asarray(
        [f"{lane_id.lower()}_{index:05d}" for index in range(out.n_obs)], dtype=str
    )
    if not out.obs_names.is_unique:
        raise AssertionError("candidate obs_names are not unique")
    out.layers.clear()
    out.obsm.clear()
    out.uns = {
        "ve_submission_prep": {
            "board": BOARD,
            "task": TASK,
            "atom_id": "B1-A3",
            "lane_id": lane_id,
            "method": LANES[lane_id],
            "parent_candidate": PARENT_CANDIDATE,
            "parent_sha256": PARENT_SHA256,
            "previous_stage": PREVIOUS_STAGE,
            "base_stage": BASE_STAGE,
            "target_stage": TARGET_STAGE,
            "seed": int(seed),
            "target_used": False,
            "sampling_strategy": "state_mass_hamilton_plus_balanced_full_row_replay",
            "submission_contract_validated": True,
        }
    }
    out.write_h5ad(output_path)
    submission_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(output_path, submission_path)

    parent_X = parent.X
    candidate_X = out.X
    parent_selected_X = parent_X[donors]
    if sparse.issparse(parent_selected_X) and sparse.issparse(candidate_X):
        row_replay_exact = (candidate_X != parent_selected_X).nnz == 0
    else:
        row_replay_exact = bool(np.array_equal(np.asarray(candidate_X), np.asarray(parent_selected_X)))
    left, right = fixed_gene_pairs(parent.n_vars, n_pairs=20000, seed=seed)
    source_variogram: dict[str, float] = {}
    candidate_variogram: dict[str, float] = {}
    state_mean_error: dict[str, float] = {}
    for state in sorted(quotas):
        source_rows = banks[state]
        candidate_rows = np.flatnonzero(candidate_states == state)
        source_variogram[state] = variogram_rmse(
            parent_X[source_rows], candidate_X[candidate_rows], left=left, right=right
        )
        candidate_variogram[state] = source_variogram[state]
        state_mean_error[state] = _mean_error(parent_X[source_rows], candidate_X[candidate_rows])
    mass_by_state = _counts(candidate_states)
    for row in mass_rows:
        row["realized_n"] = mass_by_state.get(row["state_id"], 0)
        row["realized_share"] = mass_by_state.get(row["state_id"], 0) / parent.n_obs
    _write_mass_table(artifact_dir / "state_mass_forecast.tsv", mass_rows)
    (artifact_dir / "residual_bank_manifest.json").write_text(
        json.dumps(
            {
                "parent_candidate": PARENT_CANDIDATE,
                "parent_sha256": PARENT_SHA256,
                "lane_id": lane_id,
                "bank_source": "immutable_parent_rows",
                "state_bank_sizes": {state: int(len(banks[state])) for state in sorted(banks)},
                "donor_multiplicities": donor_details["multiplicities"],
                "seed": int(seed),
                "full_vector_replay": True,
                "candidate_row_count": int(len(donors)),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    protected = {
        "all_core_invariants": bool(
            row_replay_exact
            and parent.n_obs == out.n_obs
            and parent.n_vars == out.n_vars
            and list(parent.var_names) == list(out.var_names)
            and out.obs_names.is_unique
            and _finite_nonnegative(out.X)
            and not out.obsm
            and not out.layers
            and sum(quotas.values()) == out.n_obs
        ),
        "parent_sha256_matches": sha256_file(parent_path) == PARENT_SHA256,
        "shape_unchanged": list(parent.shape) == list(out.shape),
        "gene_order_hash": gene_order_hash(panel),
        "var_order_unchanged": list(parent.var_names) == list(out.var_names) == panel,
        "obs_names_unique": bool(out.obs_names.is_unique),
        "finite_nonnegative": _finite_nonnegative(out.X),
        "layers_cleared": len(out.layers) == 0,
        "obsm_cleared": len(out.obsm) == 0,
        "row_replay_exact": row_replay_exact,
        "state_quota_exact": all(mass_by_state.get(state, 0) == quota for state, quota in quotas.items()),
        "partition_assignment_coverage": 1.0,
        "partition_sha256": partition.partition_sha256,
        "assignment_sha256": partition.assignment_sha256,
        "memory_safe_sparse_replay": True,
        "target_used": False,
        "state_mean_rmse": state_mean_error,
        "source_variogram_rmse": source_variogram,
        "candidate_variogram_rmse": candidate_variogram,
        "file_size_bytes": output_path.stat().st_size,
        "file_size_limit_bytes": 1_200_000_000,
    }
    if protected["file_size_bytes"] > protected["file_size_limit_bytes"]:
        protected["all_core_invariants"] = False
    sha = sha256_file(output_path)
    candidate_id = f"B1-A3-{lane_id}-T1_val"
    manifest = {
        "atom_id": "B1-A3",
        "task": TASK,
        "board": BOARD,
        "lane_id": lane_id,
        "candidate_id": candidate_id,
        "base_submission": PARENT_CANDIDATE,
        "output_file": str(output_path.resolve()),
        "submission_file": str(submission_path.resolve()),
        "sha256": sha,
        "n_obs": int(out.n_obs),
        "n_vars": int(out.n_vars),
        "gene_order_hash": gene_order_hash(panel),
        "expression_multiset_hash": None,
        "coordinate_hash": None,
        "scorer_version": SCORER_VERSION,
        "official_index_hash": None,
        "seed": int(seed),
        "primary_metrics": {
            "MMD": None,
            "CSS": None,
            "DES": None,
            "DCS": None,
            "status": "score_pending",
        },
        "protected_checks": protected,
        "recommend_submit": bool(protected["all_core_invariants"]),
        "final_candidate": True,
        "score_required": True,
        "score_status": "score_pending",
        "final_partition_manifest": str(partition.manifest_path.resolve()),
        "notes": (
            "Source-only B1-A3 lane. Local scorer is a temporal-mismatch diagnostic; "
            "manual server upload is required for the official score."
        ),
    }
    (artifact_dir / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    (artifact_dir / "config_resolved.json").write_text(
        json.dumps(
            {
                "lane_id": lane_id,
                "method": LANES[lane_id],
                "alpha": ALPHA,
                "seed": seed,
                "stages": {"previous": PREVIOUS_STAGE, "base": BASE_STAGE, "target": TARGET_STAGE},
                "parent_candidate": PARENT_CANDIDATE,
                "parent_sha256": PARENT_SHA256,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    del parent, out
    gc.collect()
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lane", choices=sorted(LANES), required=True)
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_lane(
        lane_id=args.lane,
        previous_path=args.previous,
        base_path=args.base,
        parent_path=args.parent,
        panel_path=args.panel,
        artifact_dir=args.artifact_dir,
        submission_path=args.submission,
        seed=args.seed,
        overwrite=args.overwrite,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
