#!/usr/bin/env python3
"""T2-J1-PROXY: source-only NFS-correlated FGW objective gate (no candidates).

Validates, in a leave-one-stage-out setting over the observed MERFISH stages,
whether one fixed expression-neighbourhood objective -- entropic fused
Gromov-Wasserstein (FGW) soft assignment with an expression state cost plus a
graph/internal-distance cost -- produces expression-to-coordinate assignments
whose official NFS-like neighbourhood consistency (``neighborhood_mmd`` mirror)
is stably better than random permutation in at least two independent holdouts,
and whether the improvement comes from expression neighbourhood structure
rather than from geometry or cell-type labels alone.

This atom generates no formal candidate and never touches the hidden target
boards; the target-space support is always the real observed point cloud of the
held-out source stage.  The Batch-1 greedy local-swap pairing (B1-A4) is not
re-run or repeated; its published local NFS values are cited as historical
reference only.

Environment split (toolchain rule: the external tool env must not write core
artifacts): the ``solve`` worker runs under the isolated ``.venvs/ve-t1-ot``
interpreter (POT) on plain npz problems and writes only coupling npz
intermediates; every other subcommand runs under the ve-core interpreter.

Subcommands (atomic writes; interruption cannot create a false PASS):

* ``input-lock``  -- hash-lock every input (stages, panels, veckit mirrors)
* ``env-probe``   -- record ve-t1-ot tool versions
* ``spec``        -- freeze ``intermediates/objective_spec.yaml`` (before runs)
* ``holdout``     -- build one holdout, dispatch FGW solves, evaluate all arms
* ``solve``       -- worker: one (holdout, arm) POT entropic-FGW solve
* ``gate``        -- aggregate holdout metrics into the proxy gate report
* ``finalize``    -- config_resolved.yaml + TOOL_VERSIONS.json
* ``manifest`` / ``verify`` -- stable artifact manifest + self-verify

Pre-declared constants below are fixed before any full run; no grid search, no
server feedback, seed 20260830 everywhere.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

try:
    from scripts.t2_j1_pairing import (
        _balanced_indices,
        _coords,
        _dense_float32,
        _labels,
        _nfs_like,
        _spatial_knn,
    )
    from scripts.t2_baseline import load_t2_input
    from scripts.t2_s3_shape_field import (
        _append_run_log,
        _derived_seed,
        _git_commit,
        _write_json_atomic,
        _write_npz_atomic,
        best_proper_flip,
        canonicalize,
        sha256_file,
        stage_label,
    )
except ImportError:  # direct ``python scripts/t2_j1_proxy.py`` execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts.t2_j1_pairing import (
        _balanced_indices,
        _coords,
        _dense_float32,
        _labels,
        _nfs_like,
        _spatial_knn,
    )
    from scripts.t2_baseline import load_t2_input
    from scripts.t2_s3_shape_field import (
        _append_run_log,
        _derived_seed,
        _git_commit,
        _write_json_atomic,
        _write_npz_atomic,
        best_proper_flip,
        canonicalize,
        sha256_file,
        stage_label,
    )

ROOT = Path(__file__).resolve().parents[1]
ATOM = "T2-J1-PROXY-20260903-v1"
OUTPUT_DEFAULT = ROOT / "artifacts" / "tool_integration" / ATOM
SEED = 20260830

VENV_PYTHON = ROOT / ".venvs" / "ve-t1-ot" / "bin" / "python"
WORKER_THREADS = "8"
WORKER_LD_LIBRARY_PATH = "/opt/anaconda3/lib:/home/huyudi/.local/lib"

VECKIT_ROOT = ROOT / "third_party" / "veckit"
T2_METRICS_PATH = VECKIT_ROOT / "T2" / "metrics.py"
CORE_METRICS_PATH = VECKIT_ROOT / "common" / "core_metrics.py"
SCORER_LOCK_PATH = ROOT / "artifacts" / "tool_integration" / "P0-LOCK" / "locks" / "SCORER_LOCK.json"
TOOLCHAIN_LOCK_PATH = ROOT / "artifacts" / "tool_integration" / "P0-LOCK" / "locks" / "TOOLCHAIN_LOCK.json"

# ---------------------------------------------------------------------------
# Pre-declared objective constants (frozen in intermediates/objective_spec.yaml
# before any full run; synthetic-only smoke/benchmark informed solver settings,
# never holdout outcomes).
# ---------------------------------------------------------------------------
N_SUB = 2000                  # stratified holdout subsample (cloud + expression)
N_REF = 8000                  # stratified reference subsample per bracketing stage
REG_K = 32                    # kNN regression neighbours for the position reference
PCA_COMPONENTS = 30           # expression latent for C1 and M (B1-A4 convention)
FGW_ALPHA = 0.5               # weight of the graph/internal-distance (GW) term
FGW_EPSILON = 0.005           # entropic regularisation on max-normalised costs
FGW_MAX_ITER = 500
FGW_TOL = 1e-7
FGW_LOSS = "square_loss"
FGW_SOLVER = "PGD"
KNN_K = 15                    # official NFS neighbourhood size (self-inclusive)
MMD_N = 2000                  # official neighborhood_mmd subsample cap
MMD_SEED = 0                  # official neighborhood_mmd seed
N_RANDOM = 64                 # random permutation draws per holdout
N_RANDOM_OBJ = 8              # random couplings for the objective-value check

ARM_FULL = "fgw_full"
ARM_LABEL = "fgw_label_only"
ARM_SHUFFLED = "fgw_shuffled_expression"
ARM_SCRAMBLED = "fgw_scrambled_reference"
ARM_GW_ONLY = "fgw_gw_only"
FGW_ARMS = (ARM_FULL, ARM_LABEL, ARM_SHUFFLED, ARM_SCRAMBLED, ARM_GW_ONLY)
ARM_IDENTITY = "identity_current_pairing"
ARM_B1A4 = "b1_a4_greedy_reference"

# Per-arm solver overrides: the candidate objective is alpha=0.5; the GW-only
# arm is a diagnostic ablation of the same problem with the state cost removed.
ARM_ALPHA = {ARM_GW_ONLY: 1.0}

# Pre-declared gate thresholds (04_DECISION_RULES.md §7).
GATE_RANDOM_Q = 0.05          # full arm must beat this random quantile (lower NFS)
GATE_MIN_HOLDOUTS = 2

# Historical B1-A4 local NFS values (cited, never recomputed here; source:
# artifacts/atomic_batch1/B1-A4/RESULT.md, server outcome in T2_TRACKING.md).
B1A4_LOCAL_NFS = {
    "T2_embryo_val_interp": {"L1_LATENT_KNN10": 0.15017, "L2_STATE_HASH10": 0.15104},
    "T2_heart_val_interp": {"L1_LATENT_KNN10": 0.19003, "L2_STATE_HASH10": 0.19050},
    "T2_heart_val_extrap": {"L1_LATENT_KNN10": 0.10775, "L2_STATE_HASH10": 0.11151},
}
B1A4_SOURCE = "artifacts/atomic_batch1/B1-A4/RESULT.md"

STAGE_FILES: dict[float, str] = {
    6.75: "data/E6.75.h5ad",
    7.25: "data/E7.25.h5ad",
    8.0: "data/E8.0.h5ad",
    8.25: "data/E8.25_late.h5ad",
    8.75: "data/E8.75.h5ad",
    9.5: "data/E9.5.h5ad",
}
PANEL_EMBRYO = "data/gene_panel/T2__embryo__val_interp.genes.txt"
PANEL_HEART = "data/gene_panel/T2__heart__val_interp.genes.txt"


@dataclass(frozen=True)
class HoldoutSpec:
    name: str
    tissue: str
    holdout_stage: float
    left_stage: float
    right_stage: float
    panel: str

    @property
    def time_weight(self) -> float:
        """lambda: position of the holdout stage between the bracketing stages."""
        span = self.right_stage - self.left_stage
        if span <= 0:
            raise ValueError(f"{self.name}: bracketing stages must be ordered")
        if not (self.left_stage < self.holdout_stage < self.right_stage):
            raise ValueError(f"{self.name}: holdout stage must be interior")
        return (self.holdout_stage - self.left_stage) / span


HOLDOUT_SPECS: tuple[HoldoutSpec, ...] = (
    HoldoutSpec(
        name="H1_embryo_leave_E7.25_out",
        tissue="embryo",
        holdout_stage=7.25,
        left_stage=6.75,
        right_stage=8.0,
        panel=PANEL_EMBRYO,
    ),
    HoldoutSpec(
        name="H2_heart_leave_E8.75_out",
        tissue="heart",
        holdout_stage=8.75,
        left_stage=8.25,
        right_stage=9.5,
        panel=PANEL_HEART,
    ),
)
HOLDOUT_BY_NAME = {spec.name: spec for spec in HOLDOUT_SPECS}


# ---------------------------------------------------------------------------
# small shared helpers
# ---------------------------------------------------------------------------


def _relative(path: Path) -> str:
    return Path(path).resolve().relative_to(ROOT).as_posix()


def _worker_env() -> dict[str, str]:
    env = dict(os.environ)
    env["LD_LIBRARY_PATH"] = WORKER_LD_LIBRARY_PATH
    env["OPENBLAS_NUM_THREADS"] = WORKER_THREADS
    env["OMP_NUM_THREADS"] = WORKER_THREADS
    env["MKL_NUM_THREADS"] = WORKER_THREADS
    env["NUMEXPR_NUM_THREADS"] = WORKER_THREADS
    return env


def max_normalise(matrix: np.ndarray) -> np.ndarray:
    """Divide by the max entry (fixed cost-normalisation rule)."""
    values = np.asarray(matrix, dtype=np.float64)
    peak = float(values.max())
    if not np.isfinite(peak) or peak <= 0:
        raise ValueError("cost matrix must have a positive finite max")
    return values / peak


def pairwise_euclidean(features: np.ndarray) -> np.ndarray:
    values = np.asarray(features, dtype=np.float64)
    sq = np.sum((values[:, None, :] - values[None, :, :]) ** 2, axis=2)
    return np.sqrt(np.maximum(sq, 0.0))


def expression_latent(
    X: np.ndarray, n_components: int = PCA_COMPONENTS
) -> tuple[np.ndarray, Any]:
    """PCA latent fit on the given expression matrix (deterministic svd)."""
    from sklearn.decomposition import PCA

    values = np.asarray(X, dtype=np.float64)
    n_pc = min(n_components, values.shape[0], values.shape[1])
    pca = PCA(n_components=n_pc, random_state=0).fit(values)
    return np.asarray(pca.transform(values), dtype=np.float64), pca


def one_hot(labels: np.ndarray, vocabulary: Sequence[str]) -> np.ndarray:
    index = {label: i for i, label in enumerate(vocabulary)}
    missing = sorted(set(map(str, labels)) - set(vocabulary))
    if missing:
        raise ValueError(f"labels missing from vocabulary: {missing[:5]}")
    out = np.zeros((len(labels), len(vocabulary)), dtype=np.float64)
    for row, label in enumerate(map(str, labels)):
        out[row, index[label]] = 1.0
    return out


def shuffle_within_label(labels: np.ndarray, seed: int) -> np.ndarray:
    """Permutation that shuffles rows inside each cell-type label only."""
    rng = np.random.default_rng(seed)
    order = np.arange(len(labels), dtype=np.int64)
    for label in sorted(np.unique(labels).tolist()):
        group = np.flatnonzero(labels == label)
        shuffled = group.copy()
        rng.shuffle(shuffled)
        order[group] = shuffled
    return order


def barycentric_expression(T: np.ndarray, X: np.ndarray) -> np.ndarray:
    """Soft-assignment readout: expression placed at position j = sum_i T_ij x_i / sum_i T_ij."""
    coupling = np.asarray(T, dtype=np.float64)
    values = np.asarray(X, dtype=np.float64)
    if coupling.ndim != 2 or coupling.shape[0] != values.shape[0]:
        raise ValueError("coupling and expression shapes disagree")
    if (coupling < -1e-12).any():
        raise ValueError("coupling contains negative mass")
    colsum = coupling.sum(axis=0)
    if (colsum <= 0).any():
        raise ValueError("coupling has an empty target column")
    return (coupling.T @ values) / colsum[:, None]


def fgw_loss(
    M: np.ndarray, C1: np.ndarray, C2: np.ndarray, T: np.ndarray, alpha: float
) -> dict[str, float]:
    """Pure (non-entropic) FGW square-loss decomposition for an arbitrary coupling.

    Convention: rows of ``T`` are expression profiles, columns are target
    positions; ``T[i, j]`` is the mass of row ``i`` placed at position ``j``.
    GW square loss = <C1^2 p, p> + <C2^2 q, q> - 2 <C1 T C2, T> with the
    row/column marginals p = T 1, q = T^T 1 (C1/C2 symmetric).
    """
    M = np.asarray(M, dtype=np.float64)
    C1 = np.asarray(C1, dtype=np.float64)
    C2 = np.asarray(C2, dtype=np.float64)
    T = np.asarray(T, dtype=np.float64)
    p = T.sum(axis=1)
    q = T.sum(axis=0)
    linear = float((M * T).sum())
    const = float((((C1**2) @ p) * p).sum() + (((C2**2) @ q) * q).sum())
    cross = float((((C1 @ T) @ C2) * T).sum())
    gw = const - 2.0 * cross
    total = (1.0 - alpha) * linear + alpha * gw
    return {"linear": linear, "gw": gw, "total": total}


def fgw_loss_permutation(
    M: np.ndarray, C1: np.ndarray, C2: np.ndarray, placement: np.ndarray, alpha: float
) -> dict[str, float]:
    """O(n^2) FGW square loss of the hard placement ``X_pred = X[placement]``.

    ``placement[j]`` is the expression row placed at target position ``j``; the
    coupling is ``T[placement[j], j] = 1/n``, matching ``barycentric_expression``.
    """
    M = np.asarray(M, dtype=np.float64)
    C1 = np.asarray(C1, dtype=np.float64)
    C2 = np.asarray(C2, dtype=np.float64)
    placement = np.asarray(placement, dtype=np.int64)
    n = len(placement)
    if sorted(placement.tolist()) != list(range(n)):
        raise ValueError("not a permutation")
    linear = float(M[placement, np.arange(n)].mean())
    gw = float(np.mean((C1[np.ix_(placement, placement)] - C2) ** 2))
    total = (1.0 - alpha) * linear + alpha * gw
    return {"linear": linear, "gw": gw, "total": total}


# ---------------------------------------------------------------------------
# official NFS-like mirror (evaluation side; definition source is veckit)
# ---------------------------------------------------------------------------


def knn_neighbourhood_pseudobulk(
    X: np.ndarray, coords: np.ndarray, k: int = KNN_K
) -> np.ndarray:
    """Mirror of veckit ``T2.metrics._knn_neighborhood_pb``: self-inclusive kNN."""
    graph = _spatial_knn(np.asarray(coords, dtype=np.float64), k=k)
    return np.asarray(X, dtype=np.float64)[graph].mean(axis=1)


def nfs_like(pred_X: np.ndarray, true_X: np.ndarray, coords: np.ndarray) -> float:
    """Local mirror of official ``neighborhood_mmd`` (B1-A4 ``_nfs_like`` path)."""
    return _nfs_like(pred_X, coords, true_X, coords)


def neighbourhood_pearson(pred_X: np.ndarray, true_X: np.ndarray, coords: np.ndarray) -> float:
    """Pearson between predicted and true neighbourhood pseudobulks (same kNN),
    gene-wise centred on the truth means; oversmoothing-proof companion metric."""
    pred_pb = knn_neighbourhood_pseudobulk(pred_X, coords)
    true_pb = knn_neighbourhood_pseudobulk(true_X, coords)
    centre = true_pb.mean(axis=0, keepdims=True)
    a = (pred_pb - centre).ravel()
    b = (true_pb - centre).ravel()
    denom = float(np.sqrt((a**2).sum() * (b**2).sum()))
    if denom <= 0:
        raise ValueError("degenerate neighbourhood pseudobulk")
    return float((a * b).sum() / denom)


# ---------------------------------------------------------------------------
# holdout data preparation (core env)
# ---------------------------------------------------------------------------


def _load_stage_panel(stage: float, panel: str) -> Any:
    path = ROOT / STAGE_FILES[stage]
    return load_t2_input(path, ROOT / panel)


def _stratified_subsample(labels: np.ndarray, n: int, seed: int) -> np.ndarray:
    if len(labels) <= n:
        return np.arange(len(labels), dtype=np.int64)
    return _balanced_indices(labels, n, seed)


def prepare_holdout(spec: HoldoutSpec) -> dict[str, Any]:
    """Load the holdout stage, break the pairing, build the position reference.

    The reference expression at each holdout position is a time-weighted kNN
    regression over the two bracketing stages in a shared canonical frame
    (centre + PCA + RMS, proper-flip Chamfer alignment); only observed source
    stages are used.  Returns float64-ready arrays plus provenance metadata.
    """
    seed = _derived_seed(SEED, spec.name, "prepare")
    holdout = _load_stage_panel(spec.holdout_stage, spec.panel)
    labels_all = _labels(holdout, ROOT / STAGE_FILES[spec.holdout_stage])
    sub = _stratified_subsample(labels_all, N_SUB, _derived_seed(seed, "subsample"))
    X_true = _dense_float32(holdout.X)[sub].astype(np.float64)
    coords = _coords(holdout, ROOT / STAGE_FILES[spec.holdout_stage])[sub]
    labels = labels_all[sub]

    rng = np.random.default_rng(_derived_seed(seed, "break-pairing"))
    sigma = rng.permutation(len(sub))
    X_broken = X_true[sigma]

    # canonical frame of the held-out cloud; bracketing clouds flipped into it
    z_hold, center, rms, _axes = canonicalize(coords)
    reference: dict[str, dict[str, Any]] = {}
    for side, stage in (("left", spec.left_stage), ("right", spec.right_stage)):
        ref = _load_stage_panel(stage, spec.panel)
        ref_labels_all = _labels(ref, ROOT / STAGE_FILES[stage])
        ref_sub = _stratified_subsample(
            ref_labels_all, N_REF, _derived_seed(seed, "ref", side)
        )
        ref_X = _dense_float32(ref.X)[ref_sub].astype(np.float64)
        ref_coords = _coords(ref, ROOT / STAGE_FILES[stage])[ref_sub]
        z_ref, _c, _r, _a = canonicalize(ref_coords)
        flip, flip_scores = best_proper_flip(z_ref, z_hold)
        reference[side] = {
            "stage": stage,
            "X": ref_X,
            "z": z_ref * flip,
            "labels": ref_labels_all[ref_sub],
            "n_cells": int(len(ref_sub)),
            "flip": [int(v) for v in flip],
            "flip_chamfer": {k: float(v) for k, v in flip_scores.items()},
        }

    from sklearn.neighbors import NearestNeighbors

    lam = spec.time_weight
    g_hat = np.zeros_like(X_true)
    g_hat_labels: dict[str, np.ndarray] = {}
    for side in ("left", "right"):
        weight = (1.0 - lam) if side == "left" else lam
        knn = NearestNeighbors(n_neighbors=REG_K).fit(reference[side]["z"])
        idx = knn.kneighbors(z_hold, return_distance=False)
        g_hat += weight * reference[side]["X"][idx].mean(axis=1)
        g_hat_labels[side] = np.asarray(sorted(set(reference[side]["labels"].tolist())))

    vocabulary = sorted(
        set(map(str, labels)).union(*[set(v) for v in g_hat_labels.values()])
    )
    label_ref = np.zeros((len(sub), len(vocabulary)), dtype=np.float64)
    for side in ("left", "right"):
        weight = (1.0 - lam) if side == "left" else lam
        ref_onehot = one_hot(reference[side]["labels"], vocabulary)
        knn = NearestNeighbors(n_neighbors=REG_K).fit(reference[side]["z"])
        idx = knn.kneighbors(z_hold, return_distance=False)
        label_ref += weight * ref_onehot[idx].mean(axis=1)

    return {
        "spec": spec,
        "seed": seed,
        "n_cells": int(len(sub)),
        "subsample_indices": sub,
        "sigma": sigma,
        "X_true": X_true,
        "X_broken": X_broken,
        "coords": coords,
        "labels": labels,
        "g_hat": g_hat,
        "label_vocabulary": vocabulary,
        "label_ref": label_ref,
        "reference_meta": {
            side: {k: v for k, v in reference[side].items() if k not in {"X", "z", "labels"}}
            for side in ("left", "right")
        },
        "time_weight": lam,
        "frame": {"center": center, "rms": rms},
    }


def build_arm_problem(prepared: Mapping[str, Any], arm: str) -> dict[str, Any]:
    """Frozen cost construction for one arm (max-normalised M, C1, C2)."""
    if arm not in FGW_ARMS:
        raise ValueError(f"unknown arm {arm!r}")
    X_broken = np.asarray(prepared["X_broken"], dtype=np.float64)
    coords = np.asarray(prepared["coords"], dtype=np.float64)
    labels = np.asarray(prepared["labels"], dtype=str)
    spec: HoldoutSpec = prepared["spec"]
    C2 = max_normalise(pairwise_euclidean(coords))

    if arm == ARM_LABEL:
        feat_expr = one_hot(labels, prepared["label_vocabulary"])
        feat_ref = np.asarray(prepared["label_ref"], dtype=np.float64)
        feature_note = f"one-hot celltype, union vocabulary n={feat_expr.shape[1]}"
        X_readout = X_broken
    else:
        if arm in (ARM_FULL, ARM_GW_ONLY, ARM_SCRAMBLED):
            X_objective = X_broken
        else:  # ARM_SHUFFLED: row-order invariance control (exact symmetry)
            rho = shuffle_within_label(
                labels, _derived_seed(prepared["seed"], "shuffle-within-label")
            )
            X_objective = X_broken[rho]
        latent, pca = expression_latent(X_objective)
        feat_expr = latent
        feat_ref = np.asarray(pca.transform(np.asarray(prepared["g_hat"])), dtype=np.float64)
        feature_note = f"PCA{n_components_used(pca)} latent of panel expression"
        X_readout = X_objective
        if arm == ARM_SCRAMBLED:
            # position-information null: the reference keeps its expression
            # values but loses its true position correspondence
            rng = np.random.default_rng(_derived_seed(prepared["seed"], "scramble-reference"))
            feat_ref = feat_ref[rng.permutation(len(feat_ref))]
            feature_note += "; position reference scrambled across positions"

    C1 = max_normalise(pairwise_euclidean(feat_expr))
    M = max_normalise(
        np.sum((feat_expr[:, None, :] - feat_ref[None, :, :]) ** 2, axis=2)
    )
    n = len(X_broken)
    p = np.full(n, 1.0 / n)
    q = np.full(n, 1.0 / n)
    return {
        "arm": arm,
        "holdout": spec.name,
        "M": M,
        "C1": C1,
        "C2": C2,
        "p": p,
        "q": q,
        "X_readout": X_readout,
        "feature_note": feature_note,
    }


def n_components_used(pca: Any) -> int:
    return int(getattr(pca, "n_components_", PCA_COMPONENTS))


# ---------------------------------------------------------------------------
# FGW solve (worker: runs under .venvs/ve-t1-ot with POT)
# ---------------------------------------------------------------------------


def solve_fgw(
    M: np.ndarray,
    C1: np.ndarray,
    C2: np.ndarray,
    p: np.ndarray,
    q: np.ndarray,
    *,
    alpha: float = FGW_ALPHA,
    epsilon: float = FGW_EPSILON,
    max_iter: int = FGW_MAX_ITER,
    tol: float = FGW_TOL,
) -> tuple[np.ndarray, dict[str, Any]]:
    """POT entropic fused Gromov-Wasserstein; deterministic given fixed inputs."""
    import ot  # POT: only available inside the ve-t1-ot env

    started = time.time()
    T, log = ot.gromov.entropic_fused_gromov_wasserstein(
        np.asarray(M, dtype=np.float64),
        np.asarray(C1, dtype=np.float64),
        np.asarray(C2, dtype=np.float64),
        np.asarray(p, dtype=np.float64),
        np.asarray(q, dtype=np.float64),
        loss_fun=FGW_LOSS,
        epsilon=epsilon,
        alpha=alpha,
        G0=None,
        max_iter=max_iter,
        tol=tol,
        solver=FGW_SOLVER,
        log=True,
    )
    wall = time.time() - started
    T = np.asarray(T, dtype=np.float64)
    if not np.isfinite(T).all():
        raise RuntimeError("FGW coupling is not finite")
    meta = {
        "backend": "POT",
        "pot_version": str(ot.__version__),
        "function": "ot.gromov.entropic_fused_gromov_wasserstein",
        "loss_fun": FGW_LOSS,
        "solver": FGW_SOLVER,
        "alpha": float(alpha),
        "epsilon": float(epsilon),
        "max_iter": int(max_iter),
        "tol": float(tol),
        "n_iter": int(len(log.get("err", []))),
        "fgw_dist": float(log.get("fgw_dist", float("nan"))),
        "wall_seconds": wall,
    }
    return T, meta


def command_solve(
    out_dir: Path,
    *,
    holdout: str,
    arm: str,
    problem_arm: str | None = None,
    alpha: float | None = None,
) -> dict[str, Any]:
    """Worker entry: load the frozen problem npz, solve, write the coupling npz."""
    out_dir = Path(out_dir)
    problem_arm = problem_arm or arm
    alpha = FGW_ALPHA if alpha is None else float(alpha)
    problem_path = out_dir / "intermediates" / holdout / f"problem_{problem_arm}.npz"
    bundle = np.load(problem_path)
    T, meta = solve_fgw(
        bundle["M"], bundle["C1"], bundle["C2"], bundle["p"], bundle["q"], alpha=alpha
    )
    meta["holdout"] = holdout
    meta["arm"] = arm
    meta["problem_arm"] = problem_arm
    meta["problem_sha256"] = sha256_file(problem_path)
    coupling_path = out_dir / "intermediates" / holdout / f"coupling_{arm}.npz"
    _write_npz_atomic(coupling_path, T=T)
    _write_json_atomic(
        out_dir / "intermediates" / holdout / f"solve_meta_{arm}.json", meta
    )
    return {"step": "solve", "holdout": holdout, "arm": arm, "wall_seconds": meta["wall_seconds"]}


# ---------------------------------------------------------------------------
# holdout orchestration (core env)
# ---------------------------------------------------------------------------


def _evaluate_readout(
    pred_X: np.ndarray, prepared: Mapping[str, Any]
) -> dict[str, float]:
    true_X = np.asarray(prepared["X_true"], dtype=np.float64)
    coords = np.asarray(prepared["coords"], dtype=np.float64)
    return {
        "nfs_like": nfs_like(pred_X, true_X, coords),
        "nbhd_pearson": neighbourhood_pearson(pred_X, true_X, coords),
    }


def _random_baseline(prepared: Mapping[str, Any]) -> list[dict[str, Any]]:
    """N_RANDOM independent permutation draws through the official-mirror metric."""
    spec: HoldoutSpec = prepared["spec"]
    X_broken = np.asarray(prepared["X_broken"], dtype=np.float64)
    n = len(X_broken)
    draws: list[dict[str, Any]] = []
    for draw in range(N_RANDOM):
        rng = np.random.default_rng(_derived_seed(prepared["seed"], "random", draw))
        perm = rng.permutation(n)
        metrics = _evaluate_readout(X_broken[perm], prepared)
        draws.append(
            {
                "holdout": spec.name,
                "draw": draw,
                "seed": int(_derived_seed(prepared["seed"], "random", draw)),
                "nfs_like": metrics["nfs_like"],
                "nbhd_pearson": metrics["nbhd_pearson"],
                "permutation": perm,
            }
        )
    return draws


def _load_prepared(out_dir: Path, spec: HoldoutSpec) -> dict[str, Any]:
    """Reload a previously prepared holdout (resume path; no recomputation)."""
    hold_dir = Path(out_dir) / "intermediates" / spec.name
    bundle = np.load(hold_dir / "prepared.npz", allow_pickle=False)
    meta = json.loads((hold_dir / "prepared_meta.json").read_text(encoding="utf-8"))
    prepared = {
        "spec": spec,
        "seed": int(meta["seed"]),
        "n_cells": int(meta["n_cells"]),
        "subsample_indices": bundle["subsample_indices"],
        "sigma": bundle["sigma"],
        "X_true": bundle["X_true"],
        "X_broken": bundle["X_broken"],
        "coords": bundle["coords"],
        "labels": bundle["labels"],
        "g_hat": bundle["g_hat"],
        "label_vocabulary": [str(v) for v in bundle["label_vocabulary"]],
        "label_ref": bundle["label_ref"],
        "reference_meta": meta["reference"],
        "time_weight": float(meta["time_weight"]),
        "frame": {
            "center": np.asarray(meta["frame"]["center"], dtype=np.float64),
            "rms": float(meta["frame"]["rms"]),
        },
    }
    return prepared


def _effective_sources(T: np.ndarray) -> float:
    """Mean over positions of the inverse participation ratio of T's columns."""
    T = np.asarray(T, dtype=np.float64)
    colsum = T.sum(axis=0)
    share = T / colsum[None, :]
    return float(np.mean(1.0 / np.maximum((share**2).sum(axis=0), 1e-300)))


def run_holdout(
    out_dir: Path, spec: HoldoutSpec, *, dispatch: bool = True
) -> dict[str, Any]:
    """Prepare one holdout, solve all FGW arms, evaluate every arm.

    Resume-safe: an existing prepared.npz / random-baseline JSON is reloaded
    instead of recomputed; existing couplings whose recorded problem hash still
    matches are not re-solved.
    """
    out_dir = Path(out_dir)
    hold_dir = out_dir / "intermediates" / spec.name
    hold_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    if (hold_dir / "prepared.npz").is_file() and (hold_dir / "prepared_meta.json").is_file():
        prepared = _load_prepared(out_dir, spec)
        _append_run_log(out_dir, f"holdout {spec.name}: resumed from prepared.npz")
    else:
        prepared = prepare_holdout(spec)
        _write_npz_atomic(
            hold_dir / "prepared.npz",
            subsample_indices=prepared["subsample_indices"],
            sigma=prepared["sigma"],
            X_true=prepared["X_true"],
            X_broken=prepared["X_broken"],
            coords=prepared["coords"],
            labels=prepared["labels"],
            g_hat=prepared["g_hat"],
            label_vocabulary=np.asarray(prepared["label_vocabulary"]),
            label_ref=prepared["label_ref"],
        )
        prep_meta = {
            "schema": "ve.t2.j1-proxy-holdout-prep.v1",
            "atom": ATOM,
            "holdout": spec.name,
            "seed": prepared["seed"],
            "n_cells": prepared["n_cells"],
            "time_weight": prepared["time_weight"],
            "reference": prepared["reference_meta"],
            "frame": {
                "center": [float(v) for v in prepared["frame"]["center"]],
                "rms": float(prepared["frame"]["rms"]),
            },
            "stage_files": {
                stage: STAGE_FILES[stage]
                for stage in (spec.holdout_stage, spec.left_stage, spec.right_stage)
            },
            "panel": spec.panel,
            "target_used": False,
        }
        _write_json_atomic(hold_dir / "prepared_meta.json", prep_meta)
        _append_run_log(
            out_dir,
            f"holdout {spec.name}: prepared n={prepared['n_cells']} "
            f"lambda={prepared['time_weight']:.4f}",
        )

    problems: dict[str, dict[str, Any]] = {}
    for arm in FGW_ARMS:
        problem = build_arm_problem(prepared, arm)
        problems[arm] = problem
        if arm == ARM_GW_ONLY:
            continue  # diagnostic arm: solves the full arm's frozen problem
        problem_path = hold_dir / f"problem_{arm}.npz"
        payload = {
            "M": problem["M"],
            "C1": problem["C1"],
            "C2": problem["C2"],
            "p": problem["p"],
            "q": problem["q"],
        }
        if problem_path.is_file():
            existing = np.load(problem_path)
            if not all(np.array_equal(existing[k], payload[k]) for k in payload):
                raise RuntimeError(
                    f"problem drift for {spec.name}/{arm}: frozen problem npz differs; "
                    "refusing silent overwrite"
                )
        else:
            _write_npz_atomic(problem_path, **payload)
    _append_run_log(out_dir, f"holdout {spec.name}: problems verified for {len(FGW_ARMS)} arms")

    if dispatch:
        if not VENV_PYTHON.is_file():
            raise RuntimeError(f"missing tool interpreter: {VENV_PYTHON}")
        for arm in FGW_ARMS:
            coupling_path = hold_dir / f"coupling_{arm}.npz"
            meta_path = hold_dir / f"solve_meta_{arm}.json"
            problem_arm = ARM_FULL if arm == ARM_GW_ONLY else arm
            problem_path = hold_dir / f"problem_{problem_arm}.npz"
            if coupling_path.is_file() and meta_path.is_file():
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                expected_alpha = ARM_ALPHA.get(arm, FGW_ALPHA)
                if (
                    meta.get("problem_sha256") == sha256_file(problem_path)
                    and float(meta.get("alpha", -1.0)) == float(expected_alpha)
                ):
                    continue  # up-to-date coupling
            t0 = time.time()
            command = [
                str(VENV_PYTHON),
                "-m",
                "scripts.t2_j1_proxy",
                "solve",
                "--out-dir",
                str(out_dir),
                "--holdout",
                spec.name,
                "--arm",
                arm,
                "--problem-arm",
                problem_arm,
                "--alpha",
                f"{ARM_ALPHA.get(arm, FGW_ALPHA)}",
            ]
            proc = subprocess.run(
                command,
                cwd=ROOT,
                capture_output=True,
                text=True,
                env=_worker_env(),
                timeout=7200,
            )
            if proc.returncode != 0:
                raise RuntimeError(
                    f"FGW solve failed for {spec.name}/{arm}: {proc.stderr[-2000:]}"
                )
            _append_run_log(
                out_dir,
                f"holdout {spec.name}: solve {arm} wall={time.time() - t0:.1f}s",
            )

    rows: list[dict[str, Any]] = []
    n = prepared["n_cells"]

    # identity / current pairing: the broken pairing exactly as given
    identity_metrics = _evaluate_readout(np.asarray(prepared["X_broken"]), prepared)
    rows.append(
        {
            "holdout": spec.name,
            "method": ARM_IDENTITY,
            "n_cells": n,
            **identity_metrics,
            "fgw_objective_total": "",
            "fgw_objective_linear": "",
            "fgw_objective_gw": "",
            "solver_iter": "",
            "effective_sources": "",
            "wall_seconds": "",
        }
    )

    # FGW arms
    for arm in FGW_ARMS:
        coupling_path = hold_dir / f"coupling_{arm}.npz"
        if not coupling_path.is_file():
            raise RuntimeError(f"missing coupling for {spec.name}/{arm}; run solve first")
        meta = json.loads((hold_dir / f"solve_meta_{arm}.json").read_text(encoding="utf-8"))
        problem_arm = ARM_FULL if arm == ARM_GW_ONLY else arm
        problem_path = hold_dir / f"problem_{problem_arm}.npz"
        if meta.get("problem_sha256") != sha256_file(problem_path):
            raise RuntimeError(
                f"stale coupling for {spec.name}/{arm}: problem npz changed since solve"
            )
        alpha = ARM_ALPHA.get(arm, FGW_ALPHA)
        if float(meta.get("alpha", -1.0)) != float(alpha):
            raise RuntimeError(f"stale coupling for {spec.name}/{arm}: alpha changed")
        T = np.load(coupling_path)["T"]
        problem = problems[arm]
        pred_X = barycentric_expression(T, problem["X_readout"])
        metrics = _evaluate_readout(pred_X, prepared)
        loss = fgw_loss(problem["M"], problem["C1"], problem["C2"], T, alpha)
        rows.append(
            {
                "holdout": spec.name,
                "method": arm,
                "n_cells": n,
                **metrics,
                "fgw_objective_total": loss["total"],
                "fgw_objective_linear": loss["linear"],
                "fgw_objective_gw": loss["gw"],
                "solver_iter": meta["n_iter"],
                "effective_sources": round(_effective_sources(T), 3),
                "wall_seconds": round(float(meta["wall_seconds"]), 3),
            }
        )

    # objective-value check: random permutation couplings on the full problem
    full = problems[ARM_FULL]
    rng_obj: list[dict[str, float]] = []
    for draw in range(N_RANDOM_OBJ):
        rng = np.random.default_rng(_derived_seed(prepared["seed"], "objective-random", draw))
        perm = rng.permutation(n)
        rng_obj.append(fgw_loss_permutation(full["M"], full["C1"], full["C2"], perm, FGW_ALPHA))
    identity_perm_loss = fgw_loss_permutation(
        full["M"], full["C1"], full["C2"], np.arange(n, dtype=np.int64), FGW_ALPHA
    )

    # row-order invariance control: the shuffled-row arm must reproduce the
    # full arm exactly (row permutation is an exact symmetry of the objective)
    rows_by_method = {row["method"]: row for row in rows}
    invariance_abs_diff = abs(
        rows_by_method[ARM_SHUFFLED]["nfs_like"] - rows_by_method[ARM_FULL]["nfs_like"]
    )

    # random permutation baseline through the NFS mirror (resume if present)
    baseline_json = out_dir / "metrics" / f"random_baseline_{spec.name}.json"
    if baseline_json.is_file():
        draws = json.loads(baseline_json.read_text(encoding="utf-8"))["draws"]
        _append_run_log(out_dir, f"holdout {spec.name}: reused {len(draws)} random draws")
    else:
        draws = _random_baseline(prepared)
        for draw in draws:
            draw.pop("permutation", None)
        _write_json_atomic(baseline_json, {
            "schema": "ve.t2.j1-proxy-random-baseline.v1",
            "atom": ATOM,
            "holdout": spec.name,
            "n_random": N_RANDOM,
            "draws": draws,
        })

    result = {
        "schema": "ve.t2.j1-proxy-holdout.v1",
        "atom": ATOM,
        "holdout": spec.name,
        "tissue": spec.tissue,
        "stages": {
            "holdout": spec.holdout_stage,
            "left": spec.left_stage,
            "right": spec.right_stage,
        },
        "seed": prepared["seed"],
        "n_cells": n,
        "time_weight": prepared["time_weight"],
        "rows": rows,
        "objective_check": {
            "problem_arm": ARM_FULL,
            "identity": identity_perm_loss,
            "random_couplings": rng_obj,
        },
        "row_order_invariance": {
            "description": "fgw_shuffled_expression must reproduce fgw_full exactly: "
            "input row permutation is an exact symmetry of the assignment objective",
            "abs_nfs_diff": float(invariance_abs_diff),
            "pass": bool(invariance_abs_diff < 1e-9),
        },
        "wall_seconds": time.time() - started,
        "target_used": False,
    }
    _write_json_atomic(out_dir / "metrics" / f"holdout_{spec.name}.json", result)
    _append_run_log(
        out_dir,
        f"holdout {spec.name}: evaluated {len(rows)} method rows + "
        f"{len(draws)} random draws, wall={result['wall_seconds']:.1f}s",
    )
    return result


# ---------------------------------------------------------------------------
# gate aggregation
# ---------------------------------------------------------------------------


def _quantile(values: Sequence[float], q: float) -> float:
    return float(np.quantile(np.asarray(values, dtype=np.float64), q))


def evaluate_gate(holdout_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Apply the pre-declared §7 criteria to the per-holdout measurements.

    ``information_dependence`` is the functional form of the prompt's
    expression-null control: destroying the position correspondence of the
    reference (fgw_scrambled_reference) must degrade the full arm's NFS,
    otherwise the improvement does not come from expression-position
    information.  (The originally specified within-label row shuffle is an
    exact symmetry of the assignment objective and is kept as the
    row-order-invariance control instead; see RESULT.md.)
    """
    report: dict[str, Any] = {"holdouts": {}, "criteria": {}}
    beats_random: dict[str, bool] = {}
    improvement: dict[str, float] = {}
    beats_labels: dict[str, bool] = {}
    information_dependence: dict[str, bool] = {}
    objective_ok: dict[str, bool] = {}
    invariance_ok: dict[str, bool] = {}
    for result in holdout_results:
        name = result["holdout"]
        rows = {row["method"]: row for row in result["rows"]}
        draws = result.get("random_baseline_draws") or []
        nfs_random = np.asarray([d["nfs_like"] for d in draws], dtype=np.float64)
        if nfs_random.size == 0:
            raise ValueError(f"{name}: empty random baseline")
        q05 = _quantile(nfs_random, GATE_RANDOM_Q)
        median = float(np.median(nfs_random))
        full = rows[ARM_FULL]["nfs_like"]
        label = rows[ARM_LABEL]["nfs_like"]
        scrambled = rows[ARM_SCRAMBLED]["nfs_like"]
        full_obj = rows[ARM_FULL]["fgw_objective_total"]
        random_obj = [c["total"] for c in result["objective_check"]["random_couplings"]]
        n_random_better = int((nfs_random <= full).sum())
        beats_random[name] = bool(full < q05)
        improvement[name] = float(median - full)
        beats_labels[name] = bool(full < label)
        information_dependence[name] = bool(full < scrambled)
        objective_ok[name] = bool(full_obj < min(random_obj))
        invariance_ok[name] = bool(result["row_order_invariance"]["pass"])
        report["holdouts"][name] = {
            "tissue": result["tissue"],
            "n_cells": result["n_cells"],
            "nfs": {
                "identity": rows[ARM_IDENTITY]["nfs_like"],
                "fgw_full": full,
                "fgw_label_only": label,
                "fgw_scrambled_reference": scrambled,
                "fgw_gw_only": rows[ARM_GW_ONLY]["nfs_like"],
                "fgw_shuffled_expression": rows[ARM_SHUFFLED]["nfs_like"],
                "random_q05": q05,
                "random_median": median,
                "random_min": float(nfs_random.min()),
                "random_mean": float(nfs_random.mean()),
                "random_std": float(nfs_random.std()),
                "random_draws_beating_full": n_random_better,
            },
            "nbhd_pearson": {
                "identity": rows[ARM_IDENTITY]["nbhd_pearson"],
                "fgw_full": rows[ARM_FULL]["nbhd_pearson"],
                "fgw_label_only": rows[ARM_LABEL]["nbhd_pearson"],
                "fgw_scrambled_reference": rows[ARM_SCRAMBLED]["nbhd_pearson"],
                "fgw_gw_only": rows[ARM_GW_ONLY]["nbhd_pearson"],
                "random_median": float(np.median([d["nbhd_pearson"] for d in draws])),
            },
            "effective_sources": {
                arm: rows[arm]["effective_sources"] for arm in FGW_ARMS
            },
            "fgw_objective": {
                "full_total": full_obj,
                "identity_total": result["objective_check"]["identity"]["total"],
                "random_total_min": float(min(random_obj)),
                "random_total_mean": float(np.mean(random_obj)),
            },
            "row_order_invariance": result["row_order_invariance"],
            "beats_random_q05": beats_random[name],
            "improvement_over_random_median": improvement[name],
            "beats_label_only": beats_labels[name],
            "information_dependence": information_dependence[name],
            "objective_below_all_random_couplings": objective_ok[name],
        }
    names = [result["holdout"] for result in holdout_results]
    criteria = {
        "min_two_independent_holdouts": len(names) >= GATE_MIN_HOLDOUTS,
        "beats_random_everywhere": all(beats_random.values()) and bool(beats_random),
        "same_direction": all(v > 0 for v in improvement.values()) and bool(improvement),
        "beyond_labels": all(beats_labels.values()) and bool(beats_labels),
        "information_dependence": all(information_dependence.values())
        and bool(information_dependence),
        "objective_optimised": all(objective_ok.values()) and bool(objective_ok),
        "row_order_invariance": all(invariance_ok.values()) and bool(invariance_ok),
    }
    if all(criteria.values()):
        verdict = "J1_PROXY_PASS"
    else:
        verdict = "REJECT"
    report["criteria"] = criteria
    report["verdict"] = verdict
    return report


def command_gate(out_dir: Path) -> dict[str, Any]:
    """Aggregate per-holdout metrics into holdout_results.tsv + proxy_gate_report.json."""
    out_dir = Path(out_dir)
    results: list[dict[str, Any]] = []
    for spec in HOLDOUT_SPECS:
        path = out_dir / "metrics" / f"holdout_{spec.name}.json"
        if not path.is_file():
            raise RuntimeError(f"missing holdout metrics: {path}")
        result = json.loads(path.read_text(encoding="utf-8"))
        baseline = json.loads(
            (out_dir / "metrics" / f"random_baseline_{spec.name}.json").read_text(
                encoding="utf-8"
            )
        )
        result["random_baseline_draws"] = baseline["draws"]
        results.append(result)

    # holdout_results.tsv: one row per holdout x method
    header = (
        "holdout\ttissue\tmethod\tn_cells\tnfs_like\tnbhd_pearson\t"
        "fgw_objective_total\tfgw_objective_linear\tfgw_objective_gw\t"
        "solver_iter\teffective_sources\twall_seconds"
    )
    lines = [header]
    for result in results:
        for row in result["rows"]:
            def _fmt(value: Any) -> str:
                if value == "" or value is None:
                    return ""
                if isinstance(value, float):
                    return f"{value:.8f}"
                return str(value)

            lines.append(
                "\t".join(
                    [
                        result["holdout"],
                        result["tissue"],
                        row["method"],
                        str(row["n_cells"]),
                        _fmt(row["nfs_like"]),
                        _fmt(row["nbhd_pearson"]),
                        _fmt(row["fgw_objective_total"]),
                        _fmt(row["fgw_objective_linear"]),
                        _fmt(row["fgw_objective_gw"]),
                        _fmt(row["solver_iter"]),
                        _fmt(row["effective_sources"]),
                        _fmt(row["wall_seconds"]),
                    ]
                )
            )
    tsv_path = out_dir / "metrics" / "holdout_results.tsv"
    temporary = tsv_path.with_name(tsv_path.name + ".tmp")
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    temporary.replace(tsv_path)

    # combined random_baseline.tsv across holdouts
    baseline_lines = ["holdout\tdraw\tseed\tnfs_like\tnbhd_pearson"]
    for result in results:
        for draw in result["random_baseline_draws"]:
            baseline_lines.append(
                f"{result['holdout']}\t{draw['draw']}\t{draw['seed']}"
                f"\t{draw['nfs_like']:.8f}\t{draw['nbhd_pearson']:.8f}"
            )
    rb_path = out_dir / "metrics" / "random_baseline.tsv"
    temporary = rb_path.with_name(rb_path.name + ".tmp")
    temporary.write_text("\n".join(baseline_lines) + "\n", encoding="utf-8")
    temporary.replace(rb_path)

    gate = evaluate_gate(results)
    report = {
        "schema": "ve.t2.j1-proxy-gate-report.v1",
        "atom": ATOM,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        "objective_spec": "intermediates/objective_spec.yaml",
        "objective_spec_sha256": sha256_file(out_dir / "intermediates" / "objective_spec.yaml"),
        "neighbor_definition": {
            "source": "third_party/veckit/T2/metrics.py::_knn_neighborhood_pb "
            "(k=15 self-inclusive sklearn NearestNeighbors, Euclidean) + "
            "common/core_metrics.py::mmd_unbiased (n=2000, seed=0)",
            "t2_metrics_sha256": sha256_file(T2_METRICS_PATH),
            "core_metrics_sha256": sha256_file(CORE_METRICS_PATH),
            "matches_official": True,
            "documented_differences": [
                "evaluation clouds are the stratified holdout subsample "
                f"(n={N_SUB}) instead of the full stage cloud",
                "the FGW objective itself uses full pairwise internal-distance "
                "costs, not the kNN graph; the kNN definition is used for "
                "evaluation only",
            ],
        },
        "gate_thresholds": {
            "random_quantile": GATE_RANDOM_Q,
            "min_holdouts": GATE_MIN_HOLDOUTS,
            "n_random": N_RANDOM,
        },
        "b1_a4_reference": {
            "source": B1A4_SOURCE,
            "local_nfs": B1A4_LOCAL_NFS,
            "note": "Batch-1 greedy local-swap pairing; cited as historical "
            "reference only, not recomputed and not repeated by this atom; "
            "server outcome: no board improvement (docs/coordination/T2_TRACKING.md)",
        },
        **gate,
        "target_used": False,
        "candidate_generated": False,
        "server_submission": False,
    }
    _write_json_atomic(out_dir / "metrics" / "proxy_gate_report.json", report)
    _append_run_log(out_dir, f"gate: verdict={report['verdict']}")
    return {"step": "gate", "verdict": report["verdict"]}


# ---------------------------------------------------------------------------
# input lock, env probe, spec, finalize, manifest
# ---------------------------------------------------------------------------


def command_input_lock(out_dir: Path) -> dict[str, Any]:
    """Hash-lock every input this atom reads."""
    out_dir = Path(out_dir)
    inputs: dict[str, Any] = {}

    def _add(name: str, path: Path) -> None:
        if not path.is_file():
            raise FileNotFoundError(f"required input missing: {path}")
        inputs[name] = {
            "path": _relative(path),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }

    for stage, relative in STAGE_FILES.items():
        _add(f"stage_{stage_label(stage)}", ROOT / relative)
    _add("panel_embryo_interp", ROOT / PANEL_EMBRYO)
    _add("panel_heart_interp", ROOT / PANEL_HEART)
    for name, path in (
        ("t2_metrics", T2_METRICS_PATH),
        ("core_metrics", CORE_METRICS_PATH),
        ("scorer_lock", SCORER_LOCK_PATH),
        ("toolchain_lock", TOOLCHAIN_LOCK_PATH),
        ("t2_loader", ROOT / "scripts" / "t2_baseline.py"),
        ("t2_j1_pairing", ROOT / "scripts" / "t2_j1_pairing.py"),
        ("t2_s3_shape_field", ROOT / "scripts" / "t2_s3_shape_field.py"),
    ):
        _add(name, path)

    lock = json.loads(SCORER_LOCK_PATH.read_text(encoding="utf-8"))
    expected_loader = lock["contract_snapshot"]["t2_loader"]["sha256"]
    if inputs["t2_loader"]["sha256"] != expected_loader:
        raise RuntimeError("t2_baseline.py drift vs SCORER_LOCK")

    payload = {
        "schema": "ve.t2.j1-proxy-input-lock.v1",
        "atom": ATOM,
        "locked_at": datetime.now(timezone.utc).isoformat(),
        "allow_network": False,
        "inputs": inputs,
    }
    _write_json_atomic(out_dir / "inputs" / "input_lock.json", payload)
    _append_run_log(out_dir, f"input-lock: {len(inputs)} inputs hashed and verified")
    return {"step": "input-lock", "n_inputs": len(inputs)}


def command_env_probe(out_dir: Path) -> dict[str, Any]:
    """Record the ve-t1-ot tool versions actually used by the solve worker."""
    out_dir = Path(out_dir)
    if not VENV_PYTHON.is_file():
        raise RuntimeError(f"missing tool interpreter: {VENV_PYTHON}")
    probe = (
        "import importlib.metadata as m, json, platform, sys;"
        "pkgs=['moscot','ott-jax','jax','jaxlib','POT','anndata','numpy','scipy','scikit-learn'];"
        "print(json.dumps({'interpreter':sys.executable,'python':platform.python_version(),"
        "'platform':platform.platform(),"
        "'packages':{p:m.version(p) for p in pkgs}}))"
    )
    started = time.time()
    proc = subprocess.run(
        [str(VENV_PYTHON), "-c", probe],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=_worker_env(),
        timeout=300,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"env probe failed: {proc.stderr[-1000:]}")
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    payload.update(
        {
            "schema": "ve.t2.j1-proxy-env-probe.v1",
            "atom": ATOM,
            "probed_at": datetime.now(timezone.utc).isoformat(),
            "wall_seconds": time.time() - started,
            "ld_library_path": WORKER_LD_LIBRARY_PATH,
            "worker_threads": WORKER_THREADS,
        }
    )
    _write_json_atomic(out_dir / "metrics" / "t2_j1_proxy_env_versions.json", payload)
    _append_run_log(
        out_dir,
        "env-probe: POT={pot} moscot={mos} ott={ott}".format(
            pot=payload["packages"].get("POT"),
            mos=payload["packages"].get("moscot"),
            ott=payload["packages"].get("ott-jax"),
        ),
    )
    return {"step": "env-probe"}


OBJECTIVE_SPEC = """\
# T2-J1-PROXY fixed objective specification (frozen before any full run).
# Any change to this file after the first holdout run is a new atom version.
schema: ve.t2.j1-proxy-objective-spec.v1
atom: T2-J1-PROXY-20260903-v1
seed: 20260830
objective:
  name: entropic_fused_gromov_wasserstein
  implementation: POT ot.gromov.entropic_fused_gromov_wasserstein
  solver: PGD
  loss_fun: square_loss
  alpha: 0.5            # weight of the graph/internal-distance (GW) term
  epsilon: 0.005        # entropic regularisation, max-normalised costs
  max_iter: 500
  tol: 1.0e-7
  init: uniform (G0=null)
  marginals: uniform p, uniform q (n expression rows == n target positions)
  costs:
    M: squared euclidean between expression features of row i and the
       time-weighted kNN-regressed position reference at target position j
    C1: pairwise euclidean distances between expression features (rows)
    C2: pairwise euclidean distances between target positions (3D)
    normalisation: each cost matrix divided by its own max entry
  expression_features: PCA(n_components=30, random_state=0) on the panel
    expression matrix of the holdout subsample (row-permutation invariant)
  position_reference:
    source: bracketing observed stages only (never the holdout expression)
    frame: per-stage canonical (centre + PCA + RMS, t2_s3_shape_field.canonicalize),
      det=+1 flip chosen by symmetric Chamfer against the holdout cloud
    regression: kNN (k=32) mean of bracketing-stage expression at each holdout
      position, time-weighted by lambda=(t_holdout-t_left)/(t_right-t_left)
    n_ref_per_stage: 8000 (stratified by celltype, fixed seed)
  target_support: real observed point cloud of the held-out source stage,
    stratified subsample n=2000; hidden future support is NOT claimed known
arms:
  fgw_full: full expression features (C1, M) as above; the candidate objective
  fgw_label_only: features replaced by one-hot celltype over the union label
    vocabulary (C1 and the position reference regress one-hot labels); the
    resulting coupling still maps real expression at readout
  fgw_shuffled_expression: expression rows shuffled within celltype before the
    objective is built; KEPT ONLY as the row-order-invariance control (input
    row permutation is an exact symmetry of this assignment objective, so this
    arm must reproduce fgw_full exactly)
  fgw_scrambled_reference: the position reference keeps its expression values
    but its row order across positions is permuted (fixed seed), destroying
    expression-position information while preserving geometry and labels
  fgw_gw_only: diagnostic ablation solving the frozen fgw_full problem with
    alpha=1.0 (state cost removed; graph/internal-distance term only)
evaluation:
  primary: NFS-like = veckit neighborhood_mmd mirror
    (T2/metrics.py::_knn_neighborhood_pb k=15 self-inclusive kNN pseudobulk +
    common/core_metrics.py::mmd_unbiased n=2000 seed=0), lower is better
  secondary: neighbourhood_pearson (gene-centred on truth means, same kNN)
  neighbor_definition_source: third_party/veckit (hash-locked in input_lock)
  documented_difference: evaluation uses the stratified subsample (n=2000), not
    the full stage cloud; the objective optimises full pairwise internal
    distances while the official metric reads k=15 neighbourhoods
baselines:
  identity_current_pairing: the pairing-broken input order, no repair
  random_permutation: 64 fixed-seed draws through the same NFS mirror
  b1_a4_greedy: cited from artifacts/atomic_batch1/B1-A4/RESULT.md, not re-run
gate_thresholds:  # 04_DECISION_RULES.md section 7, pre-declared
  random_quantile: 0.05   # fgw_full NFS must be below the random q05
  min_holdouts: 2          # in at least two independent holdouts
  same_direction: improvement over the random median must be positive in all
  beyond_labels: fgw_full NFS must beat fgw_label_only in all holdouts
  information_dependence: fgw_full NFS must beat fgw_scrambled_reference in all
    holdouts (the state cost must carry real expression-position information)
  objective_optimised: FGW objective of the solved coupling must be below every
    one of 8 fixed-seed random permutation couplings
  row_order_invariance: fgw_shuffled_expression must match fgw_full (abs diff
    < 1e-9) in all holdouts
holdouts:
  H1_embryo_leave_E7.25_out: {tissue: embryo, holdout: 7.25, bracket: [6.75, 8.0]}
  H2_heart_leave_E8.75_out: {tissue: heart, holdout: 8.75, bracket: [8.25, 9.5]}
amendments:
  - date: 2026-09-03
    note: >
      v1 spec listed fgw_shuffled_expression as the expression-null control.
      The first holdout run demonstrated that within-label row shuffling is an
      exact symmetry of the FGW assignment problem (expression rows are
      anonymous: shuffled and full arms produced bit-identical couplings and
      NFS), so that arm cannot falsify anything. It is repurposed as the
      row-order-invariance control, and the functional expression-information
      null is fgw_scrambled_reference. fgw_gw_only was added as a diagnostic
      ablation. The candidate objective (alpha=0.5 FGW) and all gate
      thresholds are unchanged; no holdout outcome was used to tune any
      hyperparameter.
"""


def command_spec(out_dir: Path, *, overwrite: bool = False) -> dict[str, Any]:
    """Freeze the objective spec; refuses to overwrite a locked spec."""
    out_dir = Path(out_dir)
    path = out_dir / "intermediates" / "objective_spec.yaml"
    if path.is_file() and not overwrite:
        existing = path.read_bytes()
        if existing != OBJECTIVE_SPEC.encode("utf-8"):
            raise RuntimeError(
                "objective_spec.yaml already exists with different content; "
                "freezing violation — bump the atom version instead"
            )
        return {"step": "spec", "status": "already_frozen"}
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(OBJECTIVE_SPEC, encoding="utf-8")
    temporary.replace(path)
    _append_run_log(out_dir, f"spec: objective frozen sha256={sha256_file(path)[:16]}")
    return {"step": "spec", "sha256": sha256_file(path)}


def _tool_versions(out_dir: Path) -> dict[str, Any]:
    import importlib.metadata

    payload: dict[str, Any] = {
        "schema": "ve.t2.j1-proxy-tool-versions.v1",
        "atom": ATOM,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "ve_core": {
            "interpreter": sys.executable,
            "anndata": _safe_version(importlib.metadata, "anndata"),
            "numpy": np.__version__,
            "scipy": _safe_version(importlib.metadata, "scipy"),
            "pandas": _safe_version(importlib.metadata, "pandas"),
            "scikit_learn": _safe_version(importlib.metadata, "scikit-learn"),
        },
        "implementation": {
            "path": "scripts/t2_j1_proxy.py",
            "sha256": sha256_file(Path(__file__).resolve()),
        },
        "nfs_mirror_sources": {
            "t2_metrics": "third_party/veckit/T2/metrics.py",
            "t2_metrics_sha256": sha256_file(T2_METRICS_PATH),
            "core_metrics": "third_party/veckit/common/core_metrics.py",
            "core_metrics_sha256": sha256_file(CORE_METRICS_PATH),
            "scorer_lock": "artifacts/tool_integration/P0-LOCK/locks/SCORER_LOCK.json",
        },
    }
    env_path = Path(out_dir) / "metrics" / "t2_j1_proxy_env_versions.json"
    if env_path.is_file():
        payload["ve_t1_ot"] = json.loads(env_path.read_text(encoding="utf-8"))
    return payload


def _safe_version(metadata_module: Any, package: str) -> str | None:
    try:
        return metadata_module.version(package)
    except Exception:
        return None


def command_finalize(out_dir: Path) -> dict[str, Any]:
    """Write config_resolved.yaml and TOOL_VERSIONS.json."""
    out_dir = Path(out_dir)
    config_lines = [
        f"atom: {ATOM}",
        "task: T2-J1-PROXY",
        f"seed: {SEED}",
        "allow_network: false",
        "allow_server_submission: false",
        "candidate_generation: false",
        "objective: entropic FGW (POT), state cost + internal-distance cost",
        f"fgw: alpha={FGW_ALPHA} epsilon={FGW_EPSILON} max_iter={FGW_MAX_ITER} tol={FGW_TOL} loss={FGW_LOSS} solver={FGW_SOLVER}",
        f"n_sub: {N_SUB}",
        f"n_ref_per_stage: {N_REF}",
        f"reg_k: {REG_K}",
        f"pca_components: {PCA_COMPONENTS}",
        f"knn_k_eval: {KNN_K}  # official self-inclusive neighbourhood",
        f"mmd: n={MMD_N} seed={MMD_SEED}  # official neighborhood_mmd defaults",
        f"n_random: {N_RANDOM}",
        f"n_random_obj: {N_RANDOM_OBJ}",
        f"gate_random_quantile: {GATE_RANDOM_Q}",
        "holdouts:",
    ]
    for spec in HOLDOUT_SPECS:
        config_lines.extend(
            [
                f"  {spec.name}:",
                f"    tissue: {spec.tissue}",
                f"    holdout_stage: {spec.holdout_stage}",
                f"    bracket: [{spec.left_stage}, {spec.right_stage}]",
                f"    time_weight: {spec.time_weight:.6f}",
                f"    panel: {spec.panel}",
            ]
        )
    config_lines.append(
        "deviations: "
        "[\"objective_spec amended 2026-09-03 after the first holdout run: the "
        "within-label row shuffle arm is an exact symmetry of the assignment "
        "objective (recorded finding) and was repurposed as the row-order "
        "invariance control; fgw_scrambled_reference is the functional "
        "expression-information null; fgw_gw_only added as diagnostic "
        "ablation; candidate objective and gate thresholds unchanged\"]"
    )
    config_lines.append("")
    path = out_dir / "config_resolved.yaml"
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text("\n".join(config_lines), encoding="utf-8")
    temporary.replace(path)
    _write_json_atomic(out_dir / "TOOL_VERSIONS.json", _tool_versions(out_dir))
    _append_run_log(out_dir, "finalize: config_resolved.yaml + TOOL_VERSIONS.json")
    return {"step": "finalize"}


def write_manifest(out_dir: Path, *, exclude: tuple[str, ...] = ()) -> dict[str, Any]:
    """Stable manifest: every stable artifact with bytes + SHA256, self-verified."""
    out_dir = Path(out_dir)
    manifest_path = out_dir / "metrics" / "artifact_manifest.stable.json"
    files: list[dict[str, Any]] = []
    for path in sorted(out_dir.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(out_dir).as_posix()
        if relative in exclude or path.name.endswith(".tmp"):
            continue
        if relative == "metrics/artifact_manifest.stable.json":
            continue
        files.append(
            {
                "path": relative,
                "bytes": path.stat().st_size,
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
                "role": relative.split("/", 1)[0],
            }
        )
    manifest = {
        "schema": "ve.tool-integration-artifact-manifest.v1",
        "task_id": ATOM,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "repo_commit": _git_commit(),
        "seed": SEED,
        "files": files,
        "excluded_live_paths": sorted(exclude),
        "provenance": {
            "implementation": "scripts/t2_j1_proxy.py",
            "implementation_sha256": sha256_file(Path(__file__).resolve()),
            "test_module": "tests/test_t2_j1_proxy.py",
            "test_module_sha256": sha256_file(ROOT / "tests" / "test_t2_j1_proxy.py")
            if (ROOT / "tests" / "test_t2_j1_proxy.py").is_file()
            else None,
        },
    }
    _write_json_atomic(manifest_path, manifest)
    verification = verify_manifest(out_dir)
    manifest["self_verify"] = verification
    _write_json_atomic(manifest_path, manifest)
    return manifest


def verify_manifest(out_dir: Path) -> dict[str, Any]:
    out_dir = Path(out_dir)
    manifest_path = out_dir / "metrics" / "artifact_manifest.stable.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    mismatches: list[str] = []
    missing: list[str] = []
    for entry in manifest.get("files", []):
        path = out_dir / entry["path"]
        if not path.is_file():
            missing.append(entry["path"])
            continue
        if path.stat().st_size != entry["bytes"] or sha256_file(path) != entry["sha256"]:
            mismatches.append(entry["path"])
    return {
        "ok": not mismatches and not missing,
        "n_files": len(manifest.get("files", [])),
        "missing": missing,
        "mismatches": mismatches,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=[
            "input-lock",
            "env-probe",
            "spec",
            "holdout",
            "solve",
            "gate",
            "finalize",
            "manifest",
            "verify",
        ],
    )
    parser.add_argument("--out-dir", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--holdout", type=str, default="all")
    parser.add_argument("--arm", choices=list(FGW_ARMS), default=None)
    parser.add_argument("--problem-arm", type=str, default=None)
    parser.add_argument("--alpha", type=float, default=None)
    parser.add_argument("--no-dispatch", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir)
    if args.command == "input-lock":
        result = command_input_lock(out_dir)
    elif args.command == "env-probe":
        result = command_env_probe(out_dir)
    elif args.command == "spec":
        result = command_spec(out_dir, overwrite=args.overwrite)
    elif args.command == "holdout":
        if args.holdout == "all":
            specs = HOLDOUT_SPECS
        else:
            if args.holdout not in HOLDOUT_BY_NAME:
                raise ValueError(f"unknown holdout {args.holdout!r}")
            specs = (HOLDOUT_BY_NAME[args.holdout],)
        result = {
            "step": "holdout",
            "holdouts": [
                run_holdout(out_dir, spec, dispatch=not args.no_dispatch)["holdout"]
                for spec in specs
            ],
        }
    elif args.command == "solve":
        if args.holdout in (None, "all") or args.arm is None:
            raise ValueError("solve requires --holdout and --arm")
        result = command_solve(
            out_dir,
            holdout=args.holdout,
            arm=args.arm,
            problem_arm=args.problem_arm,
            alpha=args.alpha,
        )
    elif args.command == "gate":
        result = command_gate(out_dir)
    elif args.command == "finalize":
        result = command_finalize(out_dir)
    elif args.command == "manifest":
        result = {
            "step": "manifest",
            "n_files": len(write_manifest(out_dir, exclude=("run.log",))["files"]),
        }
    elif args.command == "verify":
        result = verify_manifest(out_dir)
    else:  # pragma: no cover
        raise ValueError(args.command)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
