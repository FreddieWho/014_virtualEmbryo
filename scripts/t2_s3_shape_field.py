#!/usr/bin/env python3
"""T2-S3-SHAPE-FIELD: geometry-only shape-field atom on the locked T2 parents.

On each board's locked parent this atom changes only the occupied shape and the
internal distance structure of ``obsm["spatial_3D"][:, :3]`` (atoms G2/ODS and
G3/SDD).  G1/TSR scale, the expression matrix, the expression row order and any
active J1 pairing are protected and never touched.

Two lanes (``docs/batch3/prompts/T2_S3_SHAPE_FIELD.md``):

* ``L1_PYCPD``  -- subsampled landmarks, PCA-canonical + proper-flip init,
  rigid-CPD polish, Gaussian-regularized non-rigid CPD (pycpd); interpolation
  combines the forward and backward fields with analytic time weights;
  extrapolation applies the endpoint field with a pre-declared strong
  shrinkage; the field is propagated to the full parent point cloud with the
  same Gaussian motion model; RMS is re-locked afterwards.
* ``L2_SPATEO`` -- the same landmark pair is aligned with Spateo's
  morphometric alignment; only the landmark displacement/field is exported
  (Spateo never writes the final H5AD); the core applies the field, recentres
  and re-locks RMS exactly like L1.  If Spateo cannot be installed or its
  alignment API cannot be validated, the lane is marked ``BLOCKED_TOOLCHAIN``.

Environment split (toolchain rule: the external tool env must not write the
final H5AD): the ``fit-field`` worker runs under the isolated
``.venvs/ve-t2-geometry`` interpreter on plain npz intermediates; every other
subcommand runs under the ve-core interpreter.

Subcommands (atomic writes; interruption cannot create a false PASS):

* ``input-lock``      -- hash-lock every input (parents, stages, panels, locks)
* ``env-probe``       -- record ve-t2-geometry tool versions / spateo API probe
* ``fields``          -- canonical landmarks + all CPD/Spateo field fits
* ``fit-field``       -- worker: one (pair, direction, backend) registration
* ``pseudoholdout``   -- source-only leave-middle-out / next-stage holdouts
                         with the locked veckit shape metrics mirrored in-process
* ``generate``        -- one full candidate per (board, lane)
* ``contract``        -- locked-loader contract checks per candidate
* ``score-launch`` / ``score-collect`` -- locked scorer wrapper (pseudo-target)
* ``checks``          -- aggregated protected checks re-verified from disk
* ``finalize``        -- config_resolved.yaml, TOOL_VERSIONS.json, summary
* ``manifest`` / ``verify`` -- stable artifact manifest + self-verify

Pre-declared constants below are fixed before any run; no grid search, no
server feedback, seed 20260830 everywhere.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ATOM = "T2-S3-SHAPE-FIELD-20260903-v1"
OUTPUT_DEFAULT = ROOT / "artifacts" / "tool_integration" / ATOM
SEED = 20260830

VENV_PYTHON = ROOT / ".venvs" / "ve-t2-geometry" / "bin" / "python"
WORKER_THREADS = "8"

SCORER_LOCK_PATH = ROOT / "artifacts/tool_integration/P0-LOCK/locks/SCORER_LOCK.json"
SCORER_ENTRYPOINT = ROOT / "third_party/veckit/score_h5ad.py"
SHAPE_METRICS_PATH = ROOT / "third_party/veckit/common/shape_metrics.py"
PARENT_REGISTRY_PATH = ROOT / "artifacts/tool_integration/P0-LOCK/locks/PARENT_REGISTRY.yaml"
BOARD_REGISTRY_PATH = ROOT / "artifacts/tool_integration/P0-LOCK/locks/BOARD_REGISTRY.yaml"
TOOLCHAIN_LOCK_PATH = ROOT / "artifacts/tool_integration/P0-LOCK/locks/TOOLCHAIN_LOCK.json"
T2_LOADER_PATH = ROOT / "scripts/t2_baseline.py"
T2_BUILDER_PATH = ROOT / "scripts/prepare_t2_submission.py"

STAGE_FILES: dict[float, str] = {
    6.75: "data/E6.75.h5ad",
    7.25: "data/E7.25.h5ad",
    8.0: "data/E8.0.h5ad",
    8.25: "data/E8.25_late.h5ad",
    8.75: "data/E8.75.h5ad",
    9.5: "data/E9.5.h5ad",
}
PANEL_BY_STAGE = {
    6.75: "data/gene_panel/T2__embryo__val_interp.genes.txt",
    7.25: "data/gene_panel/T2__embryo__val_interp.genes.txt",
    8.0: "data/gene_panel/T2__heart__val_interp.genes.txt",
    8.25: "data/gene_panel/T2__heart__val_interp.genes.txt",
    8.75: "data/gene_panel/T2__heart__val_interp.genes.txt",
    9.5: "data/gene_panel/T2__heart__val_interp.genes.txt",
}

LANE_PYCPD = "L1_PYCPD"
LANE_SPATEO = "L2_SPATEO"
LANES = (LANE_PYCPD, LANE_SPATEO)
BACKEND_BY_LANE = {LANE_PYCPD: "pycpd", LANE_SPATEO: "spateo"}

# ---------------------------------------------------------------------------
# Pre-declared analysis constants (announced before any run; no grid search).
# ---------------------------------------------------------------------------
N_LANDMARKS = 1500            # stratified landmark subsample per stage
CPD_BETA = 1.0                # Gaussian motion-coherence kernel width (RMS units)
CPD_ALPHA = 2.0               # non-rigid regularisation strength
CPD_MAX_ITER = 150
CPD_TOL = 1e-6
RIGID_POLISH_MAX_ITER = 200
RIGID_POLISH_TOL = 1e-7
EXTRAP_RHO = 0.25             # pre-declared strong shrinkage for extrapolation
SPATEO_MAX_ITER = 200         # morpho_align SVI iterations (spateo default)
SPATEO_RIDGE_EPS = 1e-3       # ridge for re-fitting the Gaussian propagation field
N_HOLDOUT_BASE = 4000         # base-cloud subsample for pseudo-holdout arms
KNN_K = 15                    # protected kNN topology neighbourhood size
KNN_ABS_FLOOR = 0.80          # candidate mean kNN overlap must stay above this
KNN_REF_SLACK = 0.02          # and no more than this below the full-field reference
EXTREME_OUTLIER_MAD = 5.0     # |v| beyond median + 5*MAD counts as extreme outlier
RMS_RTOL = 2e-5               # P0-derived G1 re-lock tolerance (t2_g1_scale.py)
RMS_ATOL = 2e-6


@dataclass(frozen=True)
class BoardSpec:
    slug: str
    official_key: str
    task: str            # scorer --setting
    setting: str         # interp | extrap
    regime: str          # interpolation | extrapolation
    panel: str
    parent_path: str
    parent_sha256: str
    parent_candidate_id: str
    target_stage: float
    base_stage: float    # parent geometry provenance stage (uns-audited)
    left_stage: float    # field pair: left flank (interp) / pair-left (extrap)
    right_stage: float
    min_cells: int
    max_cells: int
    scorer_pseudo_target: str
    scorer_pseudo_reference: str
    scorer_truth_cells: int
    panel_genes: int


BOARD_SPECS: dict[str, BoardSpec] = {
    "T2_embryo_val_interp": BoardSpec(
        slug="T2_embryo_val_interp",
        official_key="T2:embryo:val_interp",
        task="embryo",
        setting="interp",
        regime="interpolation",
        panel="data/gene_panel/T2__embryo__val_interp.genes.txt",
        parent_path="submissions/candidates/T2_embryo_val_interp/v0002_g1_formal_log_rms/submission.h5ad",
        parent_sha256="392c470e4af35797ad27c100e773c1a7695c989baed95c911fceb0b5d7965fd4",
        parent_candidate_id="B1-A1-L1-T2_embryo_val_interp",
        target_stage=7.5,
        base_stage=7.25,
        left_stage=7.25,
        right_stage=8.0,
        min_cells=583,
        max_cells=5000,
        scorer_pseudo_target="data/E7.25.h5ad",
        scorer_pseudo_reference="data/E6.75.h5ad",
        scorer_truth_cells=13295,
        panel_genes=498,
    ),
    "T2_heart_val_interp": BoardSpec(
        slug="T2_heart_val_interp",
        official_key="T2:heart:val_interp",
        task="heart",
        setting="interp",
        regime="interpolation",
        panel="data/gene_panel/T2__heart__val_interp.genes.txt",
        parent_path="submissions/candidates/T2_heart_val_interp/v0003_g1_formal_log_rms/submission.h5ad",
        parent_sha256="f8a4da854bf9e01e25503b59fddb70bae242c0382b38cc0f3984bf80cd751424",
        parent_candidate_id="B1-A1-L1-T2_heart_val_interp",
        target_stage=8.5,
        base_stage=8.25,
        left_stage=8.25,
        right_stage=8.75,
        min_cells=1000,
        max_cells=17616,
        scorer_pseudo_target="data/E8.75.h5ad",
        scorer_pseudo_reference="data/E8.25_late.h5ad",
        scorer_truth_cells=24826,
        panel_genes=500,
    ),
    "T2_heart_val_extrap": BoardSpec(
        slug="T2_heart_val_extrap",
        official_key="T2:heart:val_extrap",
        task="heart",
        setting="extrap",
        regime="extrapolation",
        panel="data/gene_panel/T2__heart__val_extrap.genes.txt",
        parent_path="submissions/scored/baseline-001/T2_heart_val_extrap/submission.h5ad",
        parent_sha256="f30beba62da673bb4c980d92eec2bc9ea03696e5c2b65414307c2e0402bd7504",
        parent_candidate_id="baseline-001-T2_heart_val_extrap-v0001",
        target_stage=10.5,
        base_stage=9.5,
        left_stage=8.75,
        right_stage=9.5,
        min_cells=1000,
        max_cells=25179,
        scorer_pseudo_target="data/E9.5.h5ad",
        scorer_pseudo_reference="data/E8.75.h5ad",
        scorer_truth_cells=53742,
        panel_genes=500,
    ),
}
BOARD_ORDER = tuple(BOARD_SPECS)


@dataclass(frozen=True)
class HoldoutSpec:
    name: str
    regime: str          # interpolation | extrapolation
    regime_model: str    # which board regime this holdout rehearses
    left_stage: float
    right_stage: float
    truth_stage: float
    base_stage: float    # base cloud = this observed stage (copy_last flavour)
    description: str


HOLDOUT_SPECS: tuple[HoldoutSpec, ...] = (
    HoldoutSpec(
        name="H1_embryo_regime_leave_E7.25_out",
        regime="interpolation",
        regime_model="T2_embryo_val_interp",
        left_stage=6.75,
        right_stage=8.0,
        truth_stage=7.25,
        base_stage=6.75,
        description="leave-middle-out on the embryo gastrulation window",
    ),
    HoldoutSpec(
        name="H2_heart_regime_leave_E8.25_out",
        regime="interpolation",
        regime_model="T2_heart_val_interp",
        left_stage=8.0,
        right_stage=8.75,
        truth_stage=8.25,
        base_stage=8.0,
        description="leave-middle-out on the early heart window",
    ),
    HoldoutSpec(
        name="H3_heart_regime_leave_E8.75_out",
        regime="interpolation",
        regime_model="T2_heart_val_interp",
        left_stage=8.25,
        right_stage=9.5,
        truth_stage=8.75,
        base_stage=8.25,
        description="leave-middle-out on the wider heart window",
    ),
    HoldoutSpec(
        name="H4_extrap_leave_E9.5_out",
        regime="extrapolation",
        regime_model="T2_heart_val_extrap",
        left_stage=8.25,
        right_stage=8.75,
        truth_stage=9.5,
        base_stage=8.75,
        description="earlier consecutive pair predicts the next observed stage",
    ),
)

# Field pairs actually fitted: pair key -> (left, right, directions).
FIELD_PAIRS: dict[str, tuple[float, float, tuple[str, ...]]] = {
    "E6.75__E8.0": (6.75, 8.0, ("fwd", "bwd")),
    "E7.25__E8.0": (7.25, 8.0, ("fwd", "bwd")),
    "E8.0__E8.75": (8.0, 8.75, ("fwd", "bwd")),
    "E8.25__E8.75": (8.25, 8.75, ("fwd", "bwd")),
    "E8.25__E9.5": (8.25, 9.5, ("fwd", "bwd")),
    "E8.75__E9.5": (8.75, 9.5, ("fwd",)),
}

_PROPER_FLIPS = ((1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1))  # det = +1


# ---------------------------------------------------------------------------
# small utilities
# ---------------------------------------------------------------------------


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json_atomic(path: Path, value: Any) -> None:
    """Publish a checkpoint atomically so interruption cannot create a false PASS."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _write_bytes_atomic(path: Path, payload: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)


def _write_npz_atomic(path: Path, **arrays: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as handle:
        np.savez(handle, **arrays)
    temporary.replace(path)


def _write_npy_atomic(path: Path, array: np.ndarray) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as handle:
        np.save(handle, np.asarray(array))
    temporary.replace(path)


def _write_h5ad_atomic(adata: Any, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp.h5ad")
    adata.write_h5ad(temporary)
    temporary.replace(path)


def _derived_seed(*parts: Any) -> int:
    payload = "/".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:4], "big")


def _append_run_log(out_dir: Path, line: str) -> None:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "run.log").open("a", encoding="utf-8") as handle:
        handle.write(f"{datetime.now(timezone.utc).isoformat()} {line}\n")


def _git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _matrix_digest(value: Any) -> str:
    """Content digest identical to scripts/t2_g1_scale.py (lock-compatible)."""
    from scipy import sparse

    digest = hashlib.sha256()
    if sparse.issparse(value):
        matrix = value.tocsr(copy=True)
        matrix.sum_duplicates()
        matrix.sort_indices()
        digest.update(b"sparse_csr")
        digest.update(str(matrix.shape).encode("utf-8"))
        digest.update(matrix.dtype.str.encode("utf-8"))
        for part in (matrix.indptr, matrix.indices, matrix.data):
            contiguous = np.ascontiguousarray(part)
            digest.update(contiguous.tobytes(order="C"))
    else:
        array = np.ascontiguousarray(np.asarray(value))
        digest.update(b"dense")
        digest.update(str(array.shape).encode("utf-8"))
        digest.update(array.dtype.str.encode("utf-8"))
        digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def _names_digest(names: Iterable[Any]) -> str:
    canonical = chr(10).join(str(name) for name in names).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


# ---------------------------------------------------------------------------
# geometry primitives (shared by driver, worker and tests)
# ---------------------------------------------------------------------------


def stage_label(stage: float) -> str:
    """Stage label matching the on-disk file names: 8.0 -> E8.0, 8.25 -> E8.25."""
    text = f"{float(stage):.2f}".rstrip("0")
    if text.endswith("."):
        text += "0"
    return f"E{text}"


def pair_key(left: float, right: float) -> str:
    return f"{stage_label(left)}__{stage_label(right)}"


def rms_radius(coords: np.ndarray) -> float:
    values = np.asarray(coords, dtype=np.float64)
    if values.ndim != 2 or values.shape[1] < 3 or values.shape[0] == 0:
        raise ValueError(f"coords must have shape (n_obs>0, >=3), got {values.shape}")
    centered = values[:, :3] - values[:, :3].mean(axis=0, keepdims=True)
    rms = float(np.sqrt(np.mean(np.sum(centered * centered, axis=1))))
    if not np.isfinite(rms) or rms <= 0:
        raise ValueError("coords must have a positive finite RMS radius")
    return rms


def canonicalize(coords: np.ndarray) -> tuple[np.ndarray, np.ndarray, float, np.ndarray]:
    """Centre, PCA-rotate and RMS-normalise a point cloud (scorer convention).

    Returns ``(Z, center, rms, V)`` with ``Z = (coords - center) @ V / rms``;
    the inverse map is ``coords = center + rms * (Z @ V.T)``.  PCA axis signs
    stay ambiguous and are resolved explicitly with proper flips downstream.
    """
    values = np.asarray(coords, dtype=np.float64)[:, :3]
    center = values.mean(axis=0)
    centered = values - center
    rms = float(np.sqrt(np.mean(np.sum(centered * centered, axis=1))))
    if not np.isfinite(rms) or rms <= 0:
        raise ValueError("coords must have a positive finite RMS radius")
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    axes = vt.T
    return (centered @ axes) / rms, center, rms, axes


def best_proper_flip(
    moving: np.ndarray, reference: np.ndarray
) -> tuple[np.ndarray, dict[str, float]]:
    """Pick the det=+1 axis flip of ``moving`` minimising symmetric Chamfer distance."""
    from scipy.spatial import cKDTree

    moving = np.asarray(moving, dtype=np.float64)[:, :3]
    reference = np.asarray(reference, dtype=np.float64)[:, :3]
    ref_tree = cKDTree(reference)
    scores: dict[str, float] = {}
    best_flip: tuple[int, int, int] | None = None
    best_score = np.inf
    for flip in _PROPER_FLIPS:
        flipped = moving * np.asarray(flip, dtype=np.float64)
        forward = float(ref_tree.query(flipped)[0].mean())
        backward = float(cKDTree(flipped).query(reference)[0].mean())
        score = forward + backward
        scores["x".join(str(s) for s in flip)] = score
        if score < best_score:
            best_score = score
            best_flip = flip
    if best_flip is None:
        raise RuntimeError("proper-flip selection failed")
    return np.asarray(best_flip, dtype=np.float64), scores


def gaussian_field_eval(
    points: np.ndarray,
    anchors: np.ndarray,
    weights: np.ndarray,
    beta: float,
    *,
    chunk: int = 4096,
) -> np.ndarray:
    """Evaluate the CPD Gaussian motion model ``v(x) = G(x, anchors; beta) @ weights``."""
    points = np.asarray(points, dtype=np.float64)[:, :3]
    anchors = np.asarray(anchors, dtype=np.float64)[:, :3]
    weights = np.asarray(weights, dtype=np.float64)
    if anchors.shape[0] != weights.shape[0]:
        raise ValueError("anchors and weights row counts differ")
    if not np.isfinite(beta) or beta <= 0:
        raise ValueError("beta must be a positive finite number")
    out = np.empty((points.shape[0], 3), dtype=np.float64)
    scale = 2.0 * float(beta) ** 2
    for start in range(0, points.shape[0], chunk):
        part = points[start : start + chunk]
        diff = part[:, None, :] - anchors[None, :, :]
        gram = np.exp(-np.sum(diff * diff, axis=2) / scale)
        out[start : start + part.shape[0]] = gram @ weights
    return out


def interpolation_coefficient(
    *, target_stage: float, base_stage: float, left_stage: float, right_stage: float
) -> float:
    """Analytic time weight: fraction of the flank-to-flank motion from base to target."""
    if not left_stage < right_stage:
        raise ValueError("left_stage must precede right_stage")
    if not (left_stage <= base_stage <= right_stage):
        raise ValueError("base_stage must lie inside the flank interval")
    if not (left_stage <= target_stage <= right_stage):
        raise ValueError("target_stage must lie inside the flank interval")
    span = right_stage - left_stage
    return float((target_stage - base_stage) / span)


def extrapolation_coefficient(
    *,
    target_stage: float,
    base_stage: float,
    left_stage: float,
    right_stage: float,
    rho: float = EXTRAP_RHO,
) -> float:
    """Shrunk endpoint coefficient; never reuses any interpolation slope."""
    if not left_stage < right_stage <= base_stage < target_stage:
        raise ValueError("require left < right <= base < target for extrapolation")
    if not np.isfinite(rho) or not 0 < rho <= 1:
        raise ValueError("rho must be in (0, 1]")
    raw = (target_stage - base_stage) / (right_stage - left_stage)
    return float(rho * raw)


def combine_fields(
    points: np.ndarray,
    *,
    fwd: Mapping[str, Any],
    bwd: Mapping[str, Any] | None,
    regime: str,
    coefficient: float,
) -> np.ndarray:
    """Symmetric forward-time displacement at ``points`` (pair frame, RMS units).

    ``fwd`` maps the left flank onto the right flank; ``bwd`` maps right onto
    left, so ``-U_bwd`` is a second estimate of the forward-time field.  The
    interpolation combination is their time-weighted symmetric average; the
    extrapolation regime uses the endpoint forward field only, already shrunk
    in ``coefficient``.
    """
    if not np.isfinite(coefficient):
        raise ValueError("coefficient must be finite")
    u_fwd = gaussian_field_eval(points, fwd["anchors"], fwd["W"], float(fwd["beta"]))
    if regime == "extrapolation":
        return float(coefficient) * u_fwd
    if regime != "interpolation":
        raise ValueError(f"unknown regime {regime!r}")
    if bwd is None:
        raise ValueError("interpolation requires the backward field")
    u_bwd = gaussian_field_eval(points, bwd["anchors"], bwd["W"], float(bwd["beta"]))
    return float(coefficient) * 0.5 * (u_fwd - u_bwd)


def deform_recenter_relock(
    coords: np.ndarray, displacement: np.ndarray, *, locked_rms: float
) -> tuple[np.ndarray, dict[str, Any]]:
    """Apply a displacement, restore the original centre and re-lock the RMS radius."""
    values = np.asarray(coords, dtype=np.float64)[:, :3]
    displacement = np.asarray(displacement, dtype=np.float64)
    if values.shape != displacement.shape:
        raise ValueError("displacement must match coords shape")
    if not np.isfinite(locked_rms) or locked_rms <= 0:
        raise ValueError("locked_rms must be positive and finite")
    center = values.mean(axis=0)
    moved = values + displacement
    recentered = moved - moved.mean(axis=0) + center
    moved_rms = rms_radius(recentered)
    scale = float(locked_rms) / moved_rms
    out = center + scale * (recentered - center)
    actual = rms_radius(out)
    if not np.isclose(actual, locked_rms, rtol=RMS_RTOL, atol=RMS_ATOL):
        raise AssertionError(f"re-lock failed: rms {actual} != locked {locked_rms}")
    return out, {
        "center_restored_to_parent_centroid": True,
        "post_deform_rms": moved_rms,
        "relock_scale": scale,
        "locked_rms": float(locked_rms),
        "actual_rms": actual,
    }


def knn_overlap(before: np.ndarray, after: np.ndarray, k: int = KNN_K) -> dict[str, Any]:
    """Mean per-point Jaccard-style kNN set overlap between two aligned clouds."""
    from sklearn.neighbors import NearestNeighbors

    before = np.asarray(before, dtype=np.float64)[:, :3]
    after = np.asarray(after, dtype=np.float64)[:, :3]
    if before.shape != after.shape:
        raise ValueError("kNN overlap requires aligned clouds of equal shape")
    n = before.shape[0]
    count = min(int(k), n - 1)
    if count < 1:
        raise ValueError("need at least 2 points for kNN overlap")

    def _neighbours(cloud: np.ndarray) -> np.ndarray:
        model = NearestNeighbors(n_neighbors=count + 1).fit(cloud)
        indices = model.kneighbors(cloud, return_distance=False)
        selected = np.empty((n, count), dtype=np.int64)
        for row, neighbours in enumerate(indices):
            without_self = neighbours[neighbours != row]
            if len(without_self) != count:
                raise RuntimeError("nearest-neighbor query returned an incomplete row")
            selected[row] = without_self[:count]
        return selected

    nb_before = _neighbours(before)
    nb_after = _neighbours(after)
    overlaps = np.empty(n, dtype=np.float64)
    for row in range(n):
        overlaps[row] = len(np.intersect1d(nb_before[row], nb_after[row])) / float(count)
    return {
        "k": count,
        "mean_overlap": float(overlaps.mean()),
        "median_overlap": float(np.median(overlaps)),
        "frac_below_0.5": float(np.mean(overlaps < 0.5)),
    }


def topology_verdict(candidate_overlap: float, reference_overlap: float) -> str:
    """Pre-declared topology rule (04_DECISION_RULES.md section 6).

    The candidate deforms by a fraction of one full observed stage transition,
    so its kNN overlap must not drop below the full-field reference (minus a
    small slack) nor below an absolute catastrophic floor.
    """
    if candidate_overlap < KNN_ABS_FLOOR:
        return "CATASTROPHIC"
    if candidate_overlap < reference_overlap - KNN_REF_SLACK:
        return "DISRUPTIVE"
    return "PASS"


# ---------------------------------------------------------------------------
# field fitting worker (runs under .venvs/ve-t2-geometry; npz in, npz out)
# ---------------------------------------------------------------------------


def _fit_worker_pycpd(
    source_lm: np.ndarray, target_lm: np.ndarray
) -> dict[str, Any]:
    """Rigid polish + Gaussian-regularized non-rigid CPD (pycpd).

    pycpd convention: ``X`` is the fixed target, ``Y`` the moving source;
    ``register()`` returns the transformed source.  The deformable motion model
    is ``TY = Y + G(Y; beta) @ W`` with ``G`` built on the rigid-polished
    landmarks, so those polished landmarks are the field anchors.
    """
    from pycpd import DeformableRegistration, RigidRegistration

    started = time.monotonic()
    rigid = RigidRegistration(
        X=target_lm,
        Y=source_lm,
        max_iterations=RIGID_POLISH_MAX_ITER,
        tolerance=RIGID_POLISH_TOL,
    )
    polished, _ = rigid.register()
    deform = DeformableRegistration(
        X=target_lm,
        Y=polished,
        alpha=CPD_ALPHA,
        beta=CPD_BETA,
        max_iterations=CPD_MAX_ITER,
        tolerance=CPD_TOL,
    )
    predicted, _ = deform.register()
    weights = np.asarray(deform.W, dtype=np.float64)
    return {
        "anchors": np.asarray(polished, dtype=np.float64),
        "predicted_lm": np.asarray(predicted, dtype=np.float64),
        "W": weights,
        "beta": float(CPD_BETA),
        "meta": {
            "backend": "pycpd",
            "rigid_iterations": int(getattr(rigid, "iteration", -1)),
            "deform_iterations": int(getattr(deform, "iteration", -1)),
            "deform_objective": float(getattr(deform, "q", float("nan"))),
            "sigma2_final": float(getattr(deform, "sigma2", float("nan"))),
            "alpha": float(CPD_ALPHA),
            "beta": float(CPD_BETA),
            "max_iterations": int(CPD_MAX_ITER),
            "tolerance": float(CPD_TOL),
            "wall_seconds": round(time.monotonic() - started, 3),
        },
    }


def _fit_worker_spateo(
    source_lm: np.ndarray,
    target_lm: np.ndarray,
    source_X: np.ndarray,
    target_X: np.ndarray,
) -> dict[str, Any]:
    """Spateo morphometric alignment; only the landmark field is exported.

    ``spateo.alignment.morpho_align`` keeps the FIRST model fixed as the
    reference and aligns the second onto it (verified in the API smoke), so the
    source landmarks are passed as the second model.  The landmark expression
    rows of the two observed stages are Spateo's alignment features (its
    morphometric model is expression + spatial by design; a constant-feature
    variant crashes this Spateo version with an SVD non-convergence, recorded
    in run.log).  Only geometry is exported: the aligned source landmarks and
    their displacement, re-fit into the same Gaussian motion model used by L1
    (ridge-solved ``W`` with the pre-declared beta) so both lanes share one
    downstream application path.  Spateo never writes the final H5AD.
    """
    import anndata as ad  # available inside the tool venv
    import spateo as st

    started = time.monotonic()
    seed_everything = _derived_seed(SEED, "spateo-worker")
    np.random.seed(seed_everything % (2**31 - 1))
    try:
        import torch

        torch.manual_seed(seed_everything % (2**31 - 1))
        torch.set_num_threads(int(WORKER_THREADS))
    except ImportError:
        pass

    def _model(points: np.ndarray, matrix: np.ndarray) -> Any:
        model = ad.AnnData(X=np.asarray(matrix, dtype=np.float64))
        model.obsm["spatial"] = np.asarray(points, dtype=np.float64).copy()
        model.var_names = [f"f{i}" for i in range(matrix.shape[1])]
        return model

    reference = _model(target_lm, target_X)
    moving = _model(source_lm, source_X)
    models, _pis = st.align.morpho_align(
        models=[reference, moving],
        spatial_key="spatial",
        key_added="align_spatial",
        device="cpu",
        dtype="float64",
        verbose=False,
        max_iter=SPATEO_MAX_ITER,
    )
    aligned_source = np.asarray(models[1].obsm["align_spatial"], dtype=np.float64)
    if aligned_source.shape != source_lm.shape:
        raise RuntimeError(
            f"spateo alignment returned shape {aligned_source.shape}, expected {source_lm.shape}"
        )
    if not np.isfinite(aligned_source).all():
        raise RuntimeError("spateo alignment produced non-finite coordinates")
    displacement = aligned_source - np.asarray(source_lm, dtype=np.float64)
    scale = 2.0 * float(CPD_BETA) ** 2
    diff = source_lm[:, None, :] - source_lm[None, :, :]
    gram = np.exp(-np.sum(diff * diff, axis=2) / scale)
    ridge = gram + float(SPATEO_RIDGE_EPS) * np.eye(gram.shape[0])
    weights = np.linalg.solve(ridge, displacement)
    return {
        "anchors": np.asarray(source_lm, dtype=np.float64),
        "predicted_lm": aligned_source,
        "W": np.asarray(weights, dtype=np.float64),
        "beta": float(CPD_BETA),
        "meta": {
            "backend": "spateo",
            "alignment_api": "spateo.alignment.morpho_align (second model aligned onto fixed first)",
            "alignment_features": "observed landmark expression rows (pair-shared genes) + spatial",
            "max_iter": int(SPATEO_MAX_ITER),
            "propagation": "gaussian_rbf_ridge_refit",
            "ridge_eps": float(SPATEO_RIDGE_EPS),
            "beta": float(CPD_BETA),
            "seed": int(seed_everything),
            "wall_seconds": round(time.monotonic() - started, 3),
        },
    }


def command_fit_field(
    out_dir: Path, *, pair: str, direction: str, backend: str
) -> dict[str, Any]:
    """Worker entrypoint: fit one (pair, direction, backend) field from landmarks.npz."""
    if pair not in FIELD_PAIRS:
        raise ValueError(f"unknown pair {pair!r}; choose from {sorted(FIELD_PAIRS)}")
    if direction not in ("fwd", "bwd"):
        raise ValueError("direction must be fwd or bwd")
    if backend not in ("pycpd", "spateo"):
        raise ValueError("backend must be pycpd or spateo")
    pair_dir = Path(out_dir) / "intermediates" / "fields" / pair
    landmarks_path = pair_dir / "landmarks.npz"
    if not landmarks_path.is_file():
        raise FileNotFoundError(f"landmarks missing: {landmarks_path} (run fields first)")
    bundle = np.load(landmarks_path)
    left_lm = np.asarray(bundle["left_lm"], dtype=np.float64)
    right_lm = np.asarray(bundle["right_lm"], dtype=np.float64)
    if direction == "fwd":
        source_lm, target_lm = left_lm, right_lm
    else:
        source_lm, target_lm = right_lm, left_lm
    if backend == "pycpd":
        result = _fit_worker_pycpd(source_lm, target_lm)
    else:
        # Spateo's morphometric alignment needs expression features per landmark.
        if "left_X" not in bundle or "right_X" not in bundle:
            raise KeyError(
                f"{landmarks_path} lacks landmark expression (left_X/right_X); "
                "re-run fields with the current implementation"
            )
        if direction == "fwd":
            source_x = np.asarray(bundle["left_X"], dtype=np.float64)
            target_x = np.asarray(bundle["right_X"], dtype=np.float64)
        else:
            source_x = np.asarray(bundle["right_X"], dtype=np.float64)
            target_x = np.asarray(bundle["left_X"], dtype=np.float64)
        result = _fit_worker_spateo(source_lm, target_lm, source_x, target_x)
    displacement = result["predicted_lm"] - result["anchors"]
    out_path = pair_dir / f"field_{backend}_{direction}.npz"
    _write_npz_atomic(
        out_path,
        anchors=result["anchors"],
        predicted_lm=result["predicted_lm"],
        displacement=displacement,
        W=result["W"],
        beta=np.float64(result["beta"]),
    )
    meta = dict(result["meta"])
    meta.update(
        {
            "pair": pair,
            "direction": direction,
            "n_landmarks": int(source_lm.shape[0]),
            "field_npz": str(out_path),
            "field_npz_sha256": sha256_file(out_path),
        }
    )
    _write_json_atomic(pair_dir / f"field_{backend}_{direction}_meta.json", meta)
    return meta


# ---------------------------------------------------------------------------
# driver: landmark preparation and field orchestration (ve-core interpreter)
# ---------------------------------------------------------------------------


def _worker_env() -> dict[str, str]:
    """Worker subprocess env: pinned BLAS threads + a libstdc++ with GLIBCXX_3.4.29.

    The system /lib libstdc++ predates GLIBCXX_3.4.29 (the P0 scorer command
    carries the same workaround); the local/anaconda lib dirs provide a newer
    one.  Background launches do not inherit the interactive shell's value.
    """
    env = dict(os.environ)
    env["OPENBLAS_NUM_THREADS"] = WORKER_THREADS
    env["OMP_NUM_THREADS"] = WORKER_THREADS
    prefix = "/home/huyudi/.local/lib:/opt/anaconda3/lib"
    existing = env.get("LD_LIBRARY_PATH") or ""
    env["LD_LIBRARY_PATH"] = prefix + (":" + existing if existing else "")
    return env


def _core_load_t2_input() -> Any:
    try:
        from scripts.t2_baseline import load_t2_input
    except ImportError:  # direct ``python scripts/t2_s3_shape_field.py`` execution
        from t2_baseline import load_t2_input
    return load_t2_input


def _core_select_indices() -> Any:
    try:
        from scripts.t2_pseudo_holdout import select_indices
    except ImportError:  # direct ``python scripts/t2_s3_shape_field.py`` execution
        from t2_pseudo_holdout import select_indices
    return select_indices


def _load_stage_coords(
    stage: float, *, n_landmarks: int | None = None
) -> tuple[np.ndarray, dict[str, Any], np.ndarray | None, list[str]]:
    """Load one observed stage via the locked T2 loader; optionally subsample landmarks.

    Returns ``(coords, meta, landmark_X, var_names)``; ``landmark_X`` carries the
    landmark expression rows (needed as Spateo's alignment features) and is
    ``None`` when no subsampling is requested.
    """
    load_t2_input = _core_load_t2_input()
    select_indices = _core_select_indices()

    if stage not in STAGE_FILES:
        raise ValueError(f"stage {stage} has no configured file")
    path = ROOT / STAGE_FILES[stage]
    panel_path = ROOT / PANEL_BY_STAGE[stage]
    adata = load_t2_input(path, panel_path)
    coords = np.asarray(adata.obsm["spatial_3D"], dtype=np.float64)[:, :3]
    var_names = [str(g) for g in adata.var_names]
    meta: dict[str, Any] = {
        "stage": float(stage),
        "path": STAGE_FILES[stage],
        "sha256": sha256_file(path),
        "n_obs": int(adata.n_obs),
    }
    landmark_x: np.ndarray | None = None
    if n_landmarks is not None:
        celltypes = np.asarray(adata.obs["celltype"].astype(str))
        indices = select_indices(
            celltypes,
            n_cells=n_landmarks,
            seed=_derived_seed(SEED, "landmarks", stage_label(stage)),
            strategy="stratified",
        )
        coords = coords[indices]
        from scipy import sparse as _sparse

        rows = adata.X[indices]
        landmark_x = np.asarray(
            rows.toarray() if _sparse.issparse(rows) else rows, dtype=np.float32
        )
        meta["landmark_indices_sha256"] = _names_digest(indices.tolist())
        meta["n_landmarks"] = int(n_landmarks)
    return coords, meta, landmark_x, var_names


def command_env_probe(out_dir: Path) -> dict[str, Any]:
    """Record ve-t2-geometry tool versions and probe the Spateo alignment API."""
    out_dir = Path(out_dir)
    probe_code = (
        "import json, importlib.metadata as im\n"
        "payload = {'python': __import__('sys').version.split()[0]}\n"
        "for pkg in ('pycpd', 'numpy', 'scipy', 'spateo-release', 'anndata'):\n"
        "    try: payload[pkg] = im.version(pkg)\n"
        "    except Exception: payload[pkg] = None\n"
        "try:\n"
        "    import pycpd; payload['pycpd_import'] = 'ok'\n"
        "except Exception as exc: payload['pycpd_import'] = f'FAIL: {exc}'\n"
        "try:\n"
        "    import spateo as st\n"
        "    payload['spateo_import'] = 'ok'\n"
        "    payload['spateo_version'] = getattr(st, '__version__', 'unknown')\n"
        "    align = getattr(st, 'align', None)\n"
        "    payload['spateo_morpho_align'] = callable(getattr(align, 'morpho_align', None))\n"
        "except Exception as exc:\n"
        "    payload['spateo_import'] = f'FAIL: {type(exc).__name__}: {exc}'\n"
        "    payload['spateo_morpho_align'] = False\n"
        "print(json.dumps(payload))\n"
    )
    started = time.monotonic()
    proc = subprocess.run(
        [str(VENV_PYTHON), "-c", probe_code],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=600,
        env=_worker_env(),
    )
    probe: dict[str, Any]
    if proc.returncode == 0:
        probe = json.loads(proc.stdout.strip().splitlines()[-1])
    else:
        probe = {"probe_failed": True, "stderr_tail": proc.stderr[-2000:]}
    probe["wall_seconds"] = round(time.monotonic() - started, 3)
    probe["venv_python"] = str(VENV_PYTHON)
    payload = {
        "schema": "ve.t2.s3-env-probe.v1",
        "atom": ATOM,
        "probed_at": datetime.now(timezone.utc).isoformat(),
        "probe": probe,
        "l2_spateo_available": bool(
            probe.get("spateo_import") == "ok" and probe.get("spateo_morpho_align")
        ),
    }
    _write_json_atomic(out_dir / "metrics" / "t2_geometry_env_versions.json", payload)
    _append_run_log(
        out_dir,
        "env-probe: pycpd=%s spateo=%s morpho_align=%s"
        % (
            probe.get("pycpd"),
            probe.get("spateo_version") or probe.get("spateo_import"),
            probe.get("spateo_morpho_align"),
        ),
    )
    return payload


def command_fields(out_dir: Path, *, backends: tuple[str, ...] = ("pycpd",)) -> dict[str, Any]:
    """Prepare canonical landmarks for every field pair and run all registrations."""
    out_dir = Path(out_dir)
    results: list[dict[str, Any]] = []
    for key, (left, right, directions) in FIELD_PAIRS.items():
        pair_dir = out_dir / "intermediates" / "fields" / key
        landmarks_path = pair_dir / "landmarks.npz"
        if not landmarks_path.is_file():
            left_coords, left_meta, left_x, left_genes = _load_stage_coords(
                left, n_landmarks=N_LANDMARKS
            )
            right_coords, right_meta, right_x, right_genes = _load_stage_coords(
                right, n_landmarks=N_LANDMARKS
            )
            left_z, left_center, left_rms, left_axes = canonicalize(left_coords)
            right_z, right_center, right_rms, right_axes = canonicalize(right_coords)
            flip, flip_scores = best_proper_flip(right_z, left_z)
            right_aligned = right_z * flip
            # Spateo's morphometric alignment consumes expression features; the
            # early-embryo panel lacks two heart-panel genes, so restrict both
            # sides to the pair-shared genes in a fixed order.
            shared = [g for g in left_genes if g in set(right_genes)]
            left_take = np.array([left_genes.index(g) for g in shared], dtype=np.int64)
            right_take = np.array([right_genes.index(g) for g in shared], dtype=np.int64)
            assert left_x is not None and right_x is not None
            _write_npz_atomic(
                landmarks_path,
                left_lm=left_z,
                right_lm=right_aligned,
                left_raw=left_coords,
                right_raw=right_coords,
                left_X=left_x[:, left_take],
                right_X=right_x[:, right_take],
            )
            pair_meta = {
                "schema": "ve.t2.s3-field-pair.v1",
                "pair": key,
                "left": left_meta,
                "right": right_meta,
                "frame": "left-stage canonical (centre + PCA + RMS), scorer convention",
                "right_proper_flip": [int(v) for v in flip],
                "flip_chamfer_scores": flip_scores,
                "left_rms": left_rms,
                "right_rms": right_rms,
                "n_landmarks": N_LANDMARKS,
                "n_shared_genes": len(shared),
                "landmark_sampling": "stratified_by_celltype",
                "seed": SEED,
            }
            _write_json_atomic(pair_dir / "pair_meta.json", pair_meta)
            _append_run_log(out_dir, f"fields: landmarks prepared for {key}")
        for backend in backends:
            for direction in directions:
                done = pair_dir / f"field_{backend}_{direction}_meta.json"
                if done.is_file():
                    results.append(json.loads(done.read_text(encoding="utf-8")))
                    continue
                log_path = pair_dir / f"field_{backend}_{direction}.log"
                with log_path.open("w", encoding="utf-8") as log_handle:
                    proc = subprocess.run(
                        [
                            str(VENV_PYTHON),
                            str(Path(__file__).resolve()),
                            "fit-field",
                            "--out-dir", str(out_dir),
                            "--pair", key,
                            "--direction", direction,
                            "--backend", backend,
                        ],
                        cwd=ROOT,
                        stdout=log_handle,
                        stderr=subprocess.STDOUT,
                        env=_worker_env(),
                    )
                if proc.returncode != 0:
                    raise RuntimeError(
                        f"field fit failed: pair={key} direction={direction} backend={backend}; "
                        f"see {log_path}"
                    )
                record = json.loads(done.read_text(encoding="utf-8"))
                results.append(record)
                _append_run_log(
                    out_dir,
                    f"fields: fit {key}/{direction}/{backend} "
                    f"wall={record.get('wall_seconds')}s",
                )
    return {"step": "fields", "n_fits": len(results), "backends": list(backends)}


def _load_field(out_dir: Path, pair: str, backend: str, direction: str) -> dict[str, Any]:
    path = Path(out_dir) / "intermediates" / "fields" / pair / f"field_{backend}_{direction}.npz"
    if not path.is_file():
        raise FileNotFoundError(f"field missing: {path}")
    bundle = np.load(path)
    return {
        "anchors": np.asarray(bundle["anchors"], dtype=np.float64),
        "W": np.asarray(bundle["W"], dtype=np.float64),
        "beta": float(bundle["beta"]),
        "predicted_lm": np.asarray(bundle["predicted_lm"], dtype=np.float64),
        "displacement": np.asarray(bundle["displacement"], dtype=np.float64),
        "path": str(path),
    }


def command_input_lock(out_dir: Path) -> dict[str, Any]:
    """Hash-lock every input this atom reads (parents, stages, panels, locks)."""
    out_dir = Path(out_dir)
    inputs: dict[str, Any] = {}

    def _add(name: str, relative: str) -> None:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(f"required input missing: {path}")
        inputs[name] = {
            "path": relative,
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }

    for stage, relative in STAGE_FILES.items():
        _add(f"stage_{stage_label(stage)}", relative)
    for board in BOARD_SPECS.values():
        _add(f"parent_{board.slug}", board.parent_path)
        _add(f"panel_{board.task}_{board.setting}", board.panel)
    for name, path in (
        ("scorer_lock", SCORER_LOCK_PATH),
        ("board_registry", BOARD_REGISTRY_PATH),
        ("parent_registry", PARENT_REGISTRY_PATH),
        ("toolchain_lock", TOOLCHAIN_LOCK_PATH),
        ("scorer_entrypoint", SCORER_ENTRYPOINT),
        ("shape_metrics", SHAPE_METRICS_PATH),
        ("t2_loader", T2_LOADER_PATH),
        ("t2_builder", T2_BUILDER_PATH),
    ):
        if not path.is_file():
            raise FileNotFoundError(f"required input missing: {path}")
        inputs[name] = {
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }

    for board in BOARD_SPECS.values():
        actual = inputs[f"parent_{board.slug}"]["sha256"]
        if actual != board.parent_sha256:
            raise RuntimeError(
                f"parent hash drift on {board.slug}: registry {board.parent_sha256} vs {actual}"
            )
    lock = json.loads(SCORER_LOCK_PATH.read_text(encoding="utf-8"))
    expected_loader = lock["contract_snapshot"]["t2_loader"]["sha256"]
    if inputs["t2_loader"]["sha256"] != expected_loader:
        raise RuntimeError("t2_baseline.py drift vs SCORER_LOCK")
    expected_scorer = lock["entrypoint"]["sha256"]
    if inputs["scorer_entrypoint"]["sha256"] != expected_scorer:
        raise RuntimeError("score_h5ad.py drift vs SCORER_LOCK")

    payload = {
        "schema": "ve.t2.s3-input-lock.v1",
        "atom": ATOM,
        "locked_at": datetime.now(timezone.utc).isoformat(),
        "allow_network": True,
        "network_scope": "pip package installation only; no external data downloads",
        "inputs": inputs,
    }
    _write_json_atomic(out_dir / "inputs" / "input_lock.json", payload)
    _append_run_log(out_dir, f"input-lock: {len(inputs)} inputs hashed and verified")
    return {"step": "input-lock", "n_inputs": len(inputs)}


# ---------------------------------------------------------------------------
# field application (shared by pseudo-holdout arms and formal generation)
# ---------------------------------------------------------------------------


def apply_lane_field(
    coords: np.ndarray,
    *,
    fwd: Mapping[str, Any],
    bwd: Mapping[str, Any] | None,
    regime: str,
    coefficient: float,
    anchor_lm: np.ndarray,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Deform ``coords`` by the lane field in the pair frame, mapped back exactly.

    The cloud is canonicalised (centre/PCA/RMS, scorer convention), aligned to
    the pair frame with the best proper flip against ``anchor_lm``, displaced
    by ``combine_fields`` and mapped back through the inverse flip/rotation/scale.
    """
    values = np.asarray(coords, dtype=np.float64)[:, :3]
    z, center, rms, axes = canonicalize(values)
    flip, flip_scores = best_proper_flip(z, np.asarray(anchor_lm, dtype=np.float64))
    aligned = z * flip
    displacement = combine_fields(
        aligned, fwd=fwd, bwd=bwd, regime=regime, coefficient=coefficient
    )
    deformed = aligned + displacement
    restored = deformed * flip  # proper flips are involutions
    out = center + rms * (restored @ axes.T)
    return out, {
        "parent_to_pair_flip": [int(v) for v in flip],
        "parent_to_pair_flip_chamfer": flip_scores,
        "center": center,
        "rms": rms,
        "coefficient": float(coefficient),
        "regime": regime,
    }


def _flip_anchor_landmarks(out_dir: Path, pair: str, *, base_stage: float, left_stage: float) -> np.ndarray:
    bundle = np.load(Path(out_dir) / "intermediates" / "fields" / pair / "landmarks.npz")
    if base_stage == left_stage:
        return np.asarray(bundle["left_lm"], dtype=np.float64)
    return np.asarray(bundle["right_lm"], dtype=np.float64)


def _board_coefficient(spec: BoardSpec) -> float:
    if spec.regime == "interpolation":
        return interpolation_coefficient(
            target_stage=spec.target_stage,
            base_stage=spec.base_stage,
            left_stage=spec.left_stage,
            right_stage=spec.right_stage,
        )
    return extrapolation_coefficient(
        target_stage=spec.target_stage,
        base_stage=spec.base_stage,
        left_stage=spec.left_stage,
        right_stage=spec.right_stage,
    )


def _shape_metric_functions() -> tuple[Any, Any, Any]:
    """Load the locked veckit shape metrics in-process (official implementation)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("ve_shape_metrics", SHAPE_METRICS_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.d2_distance, module.sliced_wasserstein, module.occupancy_dice


def _shape_proxy_panel(pred_coords: np.ndarray, truth_coords: np.ndarray) -> dict[str, Any]:
    """G2/ODS + G3/SDD proxies with the locked scorer implementations and seed."""
    d2_distance, sliced_wasserstein_fn, occupancy_dice_fn = _shape_metric_functions()
    d2 = d2_distance(pred_coords, truth_coords, seed=SEED)
    sw, sw_spread = sliced_wasserstein_fn(pred_coords, truth_coords, seed=SEED)
    dice, vox_ratio = occupancy_dice_fn(pred_coords, truth_coords, seed=SEED)
    return {
        "d2_shape_G3_SDD": round(float(d2), 5),
        "sliced_wasserstein": round(float(sw), 5),
        "occupancy_dice_G2_ODS": round(float(dice), 4),
        "_sw_flip_spread": round(float(sw_spread), 5),
        "_dice_voxel_over_nn": round(float(vox_ratio), 1),
        "metric_seed": SEED,
        "implementation": "third_party/veckit/common/shape_metrics.py (locked bundle, in-process mirror)",
    }


# ---------------------------------------------------------------------------
# pseudo-holdout (source-only; fixes parameters once; never reads board truth)
# ---------------------------------------------------------------------------


def _holdout_arm_cloud(
    out_dir: Path,
    spec: HoldoutSpec,
    backend: str | None,
    base_coords: np.ndarray,
) -> np.ndarray:
    """One holdout arm: ``backend=None`` is the low-cost copy_geometry baseline."""
    if backend is None:
        return np.asarray(base_coords, dtype=np.float64)
    pair = pair_key(spec.left_stage, spec.right_stage)
    fwd = _load_field(out_dir, pair, backend, "fwd")
    bwd = (
        _load_field(out_dir, pair, backend, "bwd")
        if spec.regime == "interpolation"
        else None
    )
    if spec.regime == "interpolation":
        coefficient = interpolation_coefficient(
            target_stage=spec.truth_stage,
            base_stage=spec.base_stage,
            left_stage=spec.left_stage,
            right_stage=spec.right_stage,
        )
    else:
        coefficient = extrapolation_coefficient(
            target_stage=spec.truth_stage,
            base_stage=spec.base_stage,
            left_stage=spec.left_stage,
            right_stage=spec.right_stage,
        )
    anchor = _flip_anchor_landmarks(
        out_dir, pair, base_stage=spec.base_stage, left_stage=spec.left_stage
    )
    moved, _ = apply_lane_field(
        base_coords,
        fwd=fwd,
        bwd=bwd,
        regime=spec.regime,
        coefficient=coefficient,
        anchor_lm=anchor,
    )
    locked = rms_radius(base_coords)
    out, _ = deform_recenter_relock(base_coords, moved - base_coords, locked_rms=locked)
    return out


def command_pseudoholdout(
    out_dir: Path, *, backends: tuple[str, ...] = ("pycpd",)
) -> dict[str, Any]:
    """Source-only holdouts: base_copy vs each lane, locked shape proxies in-process."""
    load_t2_input = _core_load_t2_input()
    select_indices = _core_select_indices()

    out_dir = Path(out_dir)
    arms = ["base_copy"] + [BACKEND_BY_LANE[lane] for lane in LANES if BACKEND_BY_LANE[lane] in backends]
    report: dict[str, Any] = {
        "schema": "ve.t2.s3-pseudoholdout.v1",
        "atom": ATOM,
        "seed": SEED,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "arms": arms,
        "arm_notes": {
            "base_copy": (
                "low-cost/parent-analog geometry arm: the base stage cloud is copied "
                "unchanged; the G1 scale step is RMS-invariant for every proxy here, "
                "so a separately rescaled arm would be numerically identical"
            )
        },
        "pre_declared": {
            "n_holdout_base": N_HOLDOUT_BASE,
            "cpd_beta": CPD_BETA,
            "cpd_alpha": CPD_ALPHA,
            "extrap_rho": EXTRAP_RHO,
            "coefficients": "analytic from stage distances; extrapolation shrunk, no interpolation slope reuse",
        },
        "holdouts": {},
    }
    for spec in HOLDOUT_SPECS:
        base_path = ROOT / STAGE_FILES[spec.base_stage]
        truth_path = ROOT / STAGE_FILES[spec.truth_stage]
        base = load_t2_input(base_path, ROOT / PANEL_BY_STAGE[spec.base_stage])
        truth = load_t2_input(truth_path, ROOT / PANEL_BY_STAGE[spec.truth_stage])
        base_coords_full = np.asarray(base.obsm["spatial_3D"], dtype=np.float64)[:, :3]
        truth_coords = np.asarray(truth.obsm["spatial_3D"], dtype=np.float64)[:, :3]
        indices = select_indices(
            np.asarray(base.obs["celltype"].astype(str)),
            n_cells=N_HOLDOUT_BASE,
            seed=_derived_seed(SEED, "holdout-base", spec.name),
            strategy="stratified",
        )
        base_coords = base_coords_full[indices]
        entry: dict[str, Any] = {
            "regime": spec.regime,
            "regime_model": spec.regime_model,
            "description": spec.description,
            "left_stage": spec.left_stage,
            "right_stage": spec.right_stage,
            "truth_stage": spec.truth_stage,
            "truth_path": STAGE_FILES[spec.truth_stage],
            "truth_sha256": sha256_file(truth_path),
            "base_stage": spec.base_stage,
            "base_path": STAGE_FILES[spec.base_stage],
            "base_sha256": sha256_file(base_path),
            "n_base_cells": int(base_coords.shape[0]),
            "n_truth_cells": int(truth_coords.shape[0]),
            "coefficient": (
                interpolation_coefficient(
                    target_stage=spec.truth_stage,
                    base_stage=spec.base_stage,
                    left_stage=spec.left_stage,
                    right_stage=spec.right_stage,
                )
                if spec.regime == "interpolation"
                else extrapolation_coefficient(
                    target_stage=spec.truth_stage,
                    base_stage=spec.base_stage,
                    left_stage=spec.left_stage,
                    right_stage=spec.right_stage,
                )
            ),
            "arms": {},
        }
        reference_cloud: np.ndarray | None = None
        for arm in arms:
            backend = None if arm == "base_copy" else arm
            cloud = _holdout_arm_cloud(out_dir, spec, backend, base_coords)
            panel = _shape_proxy_panel(cloud, truth_coords)
            if arm == "base_copy":
                reference_cloud = cloud
                panel["knn15_overlap_vs_base"] = 1.0
            else:
                assert reference_cloud is not None
                overlap = knn_overlap(reference_cloud, cloud)
                panel["knn15_overlap_vs_base"] = overlap["mean_overlap"]
                panel["knn15_frac_below_0.5"] = overlap["frac_below_0.5"]
            entry["arms"][arm] = panel
            _append_run_log(out_dir, f"pseudoholdout: {spec.name} arm={arm} done")
        entry["improves_vs_base_copy"] = {
            arm: {
                "d2_shape_G3_SDD": bool(
                    entry["arms"][arm]["d2_shape_G3_SDD"]
                    < entry["arms"]["base_copy"]["d2_shape_G3_SDD"]
                ),
                "sliced_wasserstein": bool(
                    entry["arms"][arm]["sliced_wasserstein"]
                    < entry["arms"]["base_copy"]["sliced_wasserstein"]
                ),
                "occupancy_dice_G2_ODS": bool(
                    entry["arms"][arm]["occupancy_dice_G2_ODS"]
                    > entry["arms"]["base_copy"]["occupancy_dice_G2_ODS"]
                ),
            }
            for arm in arms
            if arm != "base_copy"
        }
        report["holdouts"][spec.name] = entry
        del base, truth
    report["note"] = (
        "holdout stages are observed training stages; these numbers fix the "
        "pre-declared parameters and audit topology only -- they are not "
        "leaderboard evidence and must not be tuned against"
    )
    _write_json_atomic(out_dir / "metrics" / "pseudoholdout_report.json", report)
    return {"step": "pseudoholdout", "n_holdouts": len(HOLDOUT_SPECS), "arms": arms}


# ---------------------------------------------------------------------------
# formal candidate generation
# ---------------------------------------------------------------------------


def _extreme_outlier_fraction(displacement: np.ndarray) -> dict[str, Any]:
    norms = np.linalg.norm(np.asarray(displacement, dtype=np.float64), axis=1)
    median = float(np.median(norms))
    mad = float(np.median(np.abs(norms - median)))
    threshold = median + EXTREME_OUTLIER_MAD * mad
    return {
        "median": median,
        "mad": mad,
        "threshold": threshold,
        "extreme_outlier_fraction": float(np.mean(norms > threshold)) if mad > 0 else 0.0,
        "max_norm": float(norms.max()),
    }


def _nn_collapse_proxy(before: np.ndarray, after: np.ndarray) -> dict[str, Any]:
    from sklearn.neighbors import NearestNeighbors

    def _nn1(cloud: np.ndarray) -> np.ndarray:
        model = NearestNeighbors(n_neighbors=2).fit(cloud)
        return model.kneighbors(cloud)[0][:, 1]

    nn_before = _nn1(np.asarray(before, dtype=np.float64)[:, :3])
    nn_after = _nn1(np.asarray(after, dtype=np.float64)[:, :3])
    ratio = nn_after / np.maximum(nn_before, 1e-12)
    return {
        "min_nn_distance_before": float(nn_before.min()),
        "min_nn_distance_after": float(nn_after.min()),
        "min_nn_distance_ratio": float(ratio.min()),
        "frac_nn_distance_collapsed_below_0.1x": float(np.mean(ratio < 0.1)),
    }


def _geometry_checks(
    *,
    parent_coords: np.ndarray,
    candidate_coords: np.ndarray,
    reference_coords: np.ndarray,
    locked_rms: float,
    coefficient: float,
    regime: str,
) -> dict[str, Any]:
    """Protected geometry checks for one candidate (all target-free)."""
    parent_coords = np.asarray(parent_coords, dtype=np.float64)[:, :3]
    candidate_coords = np.asarray(candidate_coords, dtype=np.float64)[:, :3]
    displacement = candidate_coords - parent_coords
    rms_parent = rms_radius(parent_coords)
    rms_candidate = rms_radius(candidate_coords)
    knn_candidate = knn_overlap(parent_coords, candidate_coords)
    knn_reference = knn_overlap(parent_coords, np.asarray(reference_coords, dtype=np.float64)[:, :3])
    verdict = topology_verdict(knn_candidate["mean_overlap"], knn_reference["mean_overlap"])
    norms = np.linalg.norm(displacement, axis=1)
    quantiles = np.quantile(norms, [0.5, 0.9, 0.99, 1.0])
    d2_distance, _, occupancy_dice_fn = _shape_metric_functions()
    checks = {
        "schema": "ve.t2.s3-geometry-checks.v1",
        "rms": {
            "parent": rms_parent,
            "candidate": rms_candidate,
            "locked_target": float(locked_rms),
            "abs_error": abs(rms_candidate - float(locked_rms)),
            "within_p0_tolerance": bool(
                np.isclose(rms_candidate, locked_rms, rtol=RMS_RTOL, atol=RMS_ATOL)
            ),
            "rtol": RMS_RTOL,
            "atol": RMS_ATOL,
        },
        "center": {
            "parent": [float(v) for v in parent_coords.mean(axis=0)],
            "candidate": [float(v) for v in candidate_coords.mean(axis=0)],
            "max_abs_shift": float(
                np.abs(candidate_coords.mean(axis=0) - parent_coords.mean(axis=0)).max()
            ),
        },
        "internal_distance_distribution": {
            "d2_parent_vs_candidate": round(
                float(d2_distance(parent_coords, candidate_coords, seed=SEED)), 5
            ),
            "note": "change magnitude against the parent cloud; no target involved",
        },
        "occupancy_voxel_proxy": {
            "dice_parent_vs_candidate": round(
                float(occupancy_dice_fn(parent_coords, candidate_coords, seed=SEED)[0]), 4
            ),
            "note": "change magnitude against the parent cloud; no target involved",
        },
        "knn_topology": {
            "k": KNN_K,
            "candidate": knn_candidate,
            "full_field_reference": {
                **knn_reference,
                "definition": (
                    "same lane field applied at coefficient 1.0 (one full observed "
                    "stage transition), the reasonable-range reference from real "
                    "adjacent-stage deformation"
                ),
            },
            "verdict": verdict,
            "thresholds": {
                "absolute_floor": KNN_ABS_FLOOR,
                "reference_slack": KNN_REF_SLACK,
                "catastrophic_rule": "HOLD or REJECT only; never auto-submit on proxy gains",
            },
        },
        "field_displacement": {
            "regime": regime,
            "coefficient": float(coefficient),
            "quantiles_original_units": {
                "p50": float(quantiles[0]),
                "p90": float(quantiles[1]),
                "p99": float(quantiles[2]),
                "max": float(quantiles[3]),
            },
            "quantiles_rms_units": {
                "p50": float(quantiles[0] / rms_parent),
                "p90": float(quantiles[1] / rms_parent),
                "p99": float(quantiles[2] / rms_parent),
                "max": float(quantiles[3] / rms_parent),
            },
            "extreme_outliers": _extreme_outlier_fraction(displacement),
        },
        "self_intersection": _nn_collapse_proxy(parent_coords, candidate_coords),
    }
    return checks


def command_generate(
    out_dir: Path, *, board: str, lane: str, overwrite: bool = False
) -> dict[str, Any]:
    """Generate one full candidate for (board, lane) from the locked parent."""
    load_t2_input = _core_load_t2_input()

    if board not in BOARD_SPECS:
        raise ValueError(f"unknown board {board!r}; choose from {BOARD_ORDER}")
    if lane not in LANES:
        raise ValueError(f"unknown lane {lane!r}; choose from {LANES}")
    out_dir = Path(out_dir)
    spec = BOARD_SPECS[board]
    backend = BACKEND_BY_LANE[lane]
    candidate_dir = out_dir / "candidates" / board / lane
    candidate_path = candidate_dir / "submission.h5ad"
    if candidate_path.exists() and not overwrite:
        raise FileExistsError(
            f"candidate already exists: {candidate_path}; pass overwrite=True to replace it"
        )
    if lane == LANE_SPATEO:
        probe_path = out_dir / "metrics" / "t2_geometry_env_versions.json"
        available = False
        if probe_path.is_file():
            probe = json.loads(probe_path.read_text(encoding="utf-8"))
            available = bool(probe.get("l2_spateo_available"))
        if not available:
            raise RuntimeError(
                "L2_SPATEO is BLOCKED_TOOLCHAIN (env probe says Spateo alignment is "
                "unavailable); refusing to fabricate the lane"
            )

    parent_path = ROOT / spec.parent_path
    if sha256_file(parent_path) != spec.parent_sha256:
        raise RuntimeError(f"parent hash drift: {parent_path}")
    parent = load_t2_input(parent_path, ROOT / spec.panel)
    parent_coords = np.asarray(parent.obsm["spatial_3D"], dtype=np.float64)[:, :3]
    locked_rms = rms_radius(parent_coords)
    g1_uns_audit: dict[str, Any] = {"locked_rms_from_parent_file": locked_rms}
    if "ve_g1_scale" in parent.uns:
        declared = json.loads(parent.uns["ve_g1_scale"])
        declared_rms = float(declared["fit"]["target_rms"])
        g1_uns_audit["parent_uns_target_rms"] = declared_rms
        g1_uns_audit["parent_uns_consistent"] = bool(
            np.isclose(locked_rms, declared_rms, rtol=RMS_RTOL, atol=1e-4)
        )
    else:
        g1_uns_audit["parent_uns_target_rms"] = None
        g1_uns_audit["note"] = (
            "baseline parent carries no ve_g1_scale; the locked RMS is the parent "
            "file's own RMS (board rule: reuse locked parent scale, never the "
            "interpolation slope)"
        )

    pair = pair_key(spec.left_stage, spec.right_stage)
    fwd = _load_field(out_dir, pair, backend, "fwd")
    bwd = (
        _load_field(out_dir, pair, backend, "bwd")
        if spec.regime == "interpolation"
        else None
    )
    coefficient = _board_coefficient(spec)
    anchor = _flip_anchor_landmarks(
        out_dir, pair, base_stage=spec.base_stage, left_stage=spec.left_stage
    )
    moved, apply_meta = apply_lane_field(
        parent_coords,
        fwd=fwd,
        bwd=bwd,
        regime=spec.regime,
        coefficient=coefficient,
        anchor_lm=anchor,
    )
    candidate_coords, relock_meta = deform_recenter_relock(
        parent_coords, moved - parent_coords, locked_rms=locked_rms
    )
    reference_coords, _ = deform_recenter_relock(
        parent_coords,
        apply_lane_field(
            parent_coords,
            fwd=fwd,
            bwd=bwd,
            regime=spec.regime,
            coefficient=1.0,
            anchor_lm=anchor,
        )[0]
        - parent_coords,
        locked_rms=locked_rms,
    )
    checks = _geometry_checks(
        parent_coords=parent_coords,
        candidate_coords=candidate_coords,
        reference_coords=reference_coords,
        locked_rms=locked_rms,
        coefficient=coefficient,
        regime=spec.regime,
    )

    output = parent.copy()
    full_coords = np.asarray(parent.obsm["spatial_3D"])
    out_dtype = np.result_type(full_coords.dtype, np.float32)
    out_coords = np.asarray(full_coords, dtype=out_dtype).copy()
    out_coords[:, :3] = candidate_coords.astype(out_dtype, copy=False)
    output.obsm["spatial_3D"] = out_coords
    model = {
        "atom_id": ATOM,
        "lane_id": lane,
        "backend": backend,
        "board": board,
        "official_board_key": spec.official_key,
        "regime": spec.regime,
        "parent_path": spec.parent_path,
        "parent_sha256": spec.parent_sha256,
        "parent_candidate_id": spec.parent_candidate_id,
        "target_stage": spec.target_stage,
        "base_stage": spec.base_stage,
        "field_pair": pair,
        "field_pair_stages": [spec.left_stage, spec.right_stage],
        "coefficient": coefficient,
        "coefficient_rule": (
            "analytic stage-distance interpolation weight"
            if spec.regime == "interpolation"
            else f"endpoint field x pre-declared shrinkage rho={EXTRAP_RHO}"
        ),
        "g1_lock": g1_uns_audit,
        "relock": relock_meta,
        "application": {
            "frame": "pair canonical frame (centre + PCA + RMS), proper-flip aligned",
            **{k: v for k, v in apply_meta.items() if k != "center"},
        },
        "n_obs_parent": int(parent.n_obs),
        "expression_invariant": "parent_X_unchanged",
        "obs_var_order_invariant": True,
        "j1_pairing": "untouched (parent row order preserved exactly)",
        "target_used": False,
        "source_only": True,
        "seed": SEED,
    }
    output.uns["ve_shape_field"] = json.dumps(
        model, ensure_ascii=False, sort_keys=True, default=str
    )
    _write_h5ad_atomic(output, candidate_path)

    # Re-verify from disk against the immutable parent.
    checked = load_t2_input(candidate_path, ROOT / spec.panel)
    candidate_disk = np.asarray(checked.obsm["spatial_3D"], dtype=np.float64)[:, :3]
    invariants = {
        "expression_checksum_parent": _matrix_digest(parent.X),
        "expression_checksum_candidate": _matrix_digest(checked.X),
        "expression_checksum_unchanged": _matrix_digest(parent.X) == _matrix_digest(checked.X),
        "obs_order_unchanged": [str(v) for v in parent.obs_names]
        == [str(v) for v in checked.obs_names],
        "var_order_unchanged": [str(v) for v in parent.var_names]
        == [str(v) for v in checked.var_names],
        "gene_order_hash": _names_digest(checked.var_names),
        "obs_names_hash": _names_digest(checked.obs_names),
        "spatial_shape_unchanged": list(parent_coords.shape) == list(candidate_disk.shape),
        "coordinate_hash_parent": _matrix_digest(parent_coords),
        "coordinate_hash_candidate": _matrix_digest(candidate_disk),
        "n_obs": int(checked.n_obs),
        "n_vars": int(checked.n_vars),
    }
    checks["invariants"] = invariants
    checks["board"] = board
    checks["lane"] = lane
    checks["backend"] = backend
    checks["candidate_path"] = str(candidate_path)
    checks["candidate_sha256"] = sha256_file(candidate_path)
    checks["parent_sha256"] = spec.parent_sha256
    checks["g1_lock"] = g1_uns_audit

    intermediate_dir = out_dir / "intermediates" / board / lane
    _write_npy_atomic(intermediate_dir / "source_landmarks.npy", fwd["anchors"])
    _write_npy_atomic(intermediate_dir / "predicted_landmarks.npy", fwd["predicted_lm"])
    _write_npy_atomic(intermediate_dir / "displacement.npy", fwd["displacement"])
    field_meta = {
        "schema": "ve.t2.s3-field-meta.v1",
        "board": board,
        "lane": lane,
        "backend": backend,
        "pair": pair,
        "pair_stages": [spec.left_stage, spec.right_stage],
        "direction_saved": "fwd",
        "regime": spec.regime,
        "coefficient": float(coefficient),
        "reference_coefficient_for_topology": 1.0,
        "n_landmarks": N_LANDMARKS,
        "cpd": {"beta": CPD_BETA, "alpha": CPD_ALPHA, "max_iterations": CPD_MAX_ITER},
        "extrap_rho": EXTRAP_RHO if spec.regime == "extrapolation" else None,
        "field_npz_fwd": fwd["path"],
        "field_npz_bwd": bwd["path"] if bwd else None,
        "application": model["application"],
        "seed": SEED,
    }
    _write_json_atomic(intermediate_dir / "field_meta.json", field_meta)
    _write_json_atomic(out_dir / "metrics" / board / lane / "geometry_checks.json", checks)
    diagnostics = {
        "schema": "ve.t2.s3-generation.v1",
        "board": board,
        "lane": lane,
        "candidate_path": str(candidate_path),
        "candidate_sha256": checks["candidate_sha256"],
        "model": model,
        "knn_verdict": checks["knn_topology"]["verdict"],
        "rms_within_p0_tolerance": checks["rms"]["within_p0_tolerance"],
        "expression_unchanged": invariants["expression_checksum_unchanged"],
    }
    _write_json_atomic(candidate_dir / "generation_diagnostics.json", diagnostics)
    _append_run_log(
        out_dir,
        f"generate: {board}/{lane} candidate sha256={checks['candidate_sha256'][:16]} "
        f"knn={checks['knn_topology']['verdict']}",
    )
    return diagnostics


# ---------------------------------------------------------------------------
# contract, locked scorer wrapper, aggregated protected checks
# ---------------------------------------------------------------------------


def command_contract(out_dir: Path, *, board: str, lane: str) -> dict[str, Any]:
    """Locked-loader contract check for one candidate (no resampling, no target)."""
    load_t2_input = _core_load_t2_input()

    if board not in BOARD_SPECS or lane not in LANES:
        raise ValueError("unknown board or lane")
    out_dir = Path(out_dir)
    spec = BOARD_SPECS[board]
    candidate_path = out_dir / "candidates" / board / lane / "submission.h5ad"
    if not candidate_path.is_file():
        raise FileNotFoundError(f"candidate missing: {candidate_path}")
    report: dict[str, Any] = {
        "schema": "ve.t2.s3-contract.v1",
        "board": board,
        "lane": lane,
        "candidate_path": str(candidate_path),
        "candidate_sha256": sha256_file(candidate_path),
        "builder_contract": {
            "path": "scripts/prepare_t2_submission.py",
            "sha256": sha256_file(T2_BUILDER_PATH),
        },
        "loader_contract": {
            "path": "scripts/t2_baseline.py",
            "sha256": sha256_file(T2_LOADER_PATH),
        },
        "target_used": False,
    }
    try:
        checked = load_t2_input(candidate_path, ROOT / spec.panel)
        report["n_obs"] = int(checked.n_obs)
        report["n_vars"] = int(checked.n_vars)
        report["panel_genes"] = spec.panel_genes
        report["board_cell_limits"] = [spec.min_cells, spec.max_cells]
        report["cell_limits_ok"] = bool(spec.min_cells <= checked.n_obs <= spec.max_cells)
        report["panel_order_ok"] = [str(g) for g in checked.var_names] == [
            line.strip()
            for line in (ROOT / spec.panel).read_text().splitlines()
            if line.strip()
        ]
        report["spatial_3D_shape"] = list(np.asarray(checked.obsm["spatial_3D"]).shape)
        report["status"] = (
            "PASS"
            if report["cell_limits_ok"] and report["panel_order_ok"]
            else "FAIL"
        )
    except Exception as exc:  # fail closed with the reason recorded
        report["status"] = "FAIL"
        report["error"] = f"{type(exc).__name__}: {exc}"
    _write_json_atomic(
        out_dir / "candidates" / board / lane / "contract_report.json", report
    )
    _append_run_log(out_dir, f"contract: {board}/{lane} status={report['status']}")
    return report


def _load_scorer_lock() -> dict[str, Any]:
    lock = json.loads(SCORER_LOCK_PATH.read_text(encoding="utf-8"))
    entry = lock["entrypoint"]
    actual = sha256_file(SCORER_ENTRYPOINT)
    if actual != entry["sha256"]:
        raise RuntimeError(
            f"scorer entrypoint hash drift: lock {entry['sha256']} vs actual {actual}"
        )
    return lock


def scorer_command(spec: BoardSpec, out_path: Path, input_path: Path) -> list[str]:
    """Locked scorer invocation adapted to the T2 interface (P0 command template)."""
    return [
        "env",
        "LD_LIBRARY_PATH=/opt/anaconda3/lib",
        "PYTHONPATH=third_party/veckit",
        "python",
        "third_party/veckit/score_h5ad.py",
        "--task",
        "T2",
        "--setting",
        spec.task,
        "--input",
        str(input_path),
        "--target",
        spec.scorer_pseudo_target,  # pseudo-target: never the hidden truth
        "--reference",
        spec.scorer_pseudo_reference,
        "--seed",
        str(SEED),
        "--out",
        str(out_path),
    ]


def _read_rss_bytes(pid: int) -> int | None:
    try:
        status = Path(f"/proc/{pid}/status").read_text(encoding="utf-8")
    except OSError:
        return None
    for line in status.splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1]) * 1024
    return None


def _process_tree_rss_bytes(pid: int) -> int | None:
    own = _read_rss_bytes(pid)
    if own is None:
        return None
    children: list[int] = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            stat = (entry / "stat").read_text(encoding="utf-8")
            ppid = int(stat.rsplit(")", 1)[1].split()[2])
        except (OSError, IndexError, ValueError):
            continue
        if ppid == pid:
            children.append(int(entry.name))
    total = own
    for child in children:
        child_rss = _read_rss_bytes(child)
        if child_rss is not None:
            total += child_rss
    return total


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    try:
        state = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").rsplit(")", 1)[1].split()[1]
        return state != "Z"
    except OSError:
        return True


def scorer_launch(out_dir: Path, *, board: str, lane: str) -> dict[str, Any]:
    """Launch the locked scorer as a detached child; record PID and log path."""
    out_dir = Path(out_dir)
    spec = BOARD_SPECS[board]
    name = f"{board}__{lane}"
    metrics_dir = out_dir / "metrics" / board / lane
    run_record_path = metrics_dir / f"scorer_{name}_run.json"
    if run_record_path.exists():
        record = json.loads(run_record_path.read_text(encoding="utf-8"))
        if record.get("status") == "RUNNING" and _pid_alive(int(record["pid"])):
            raise FileExistsError(
                f"scorer run {name!r} already running as pid {record['pid']}"
            )
        raise FileExistsError(
            f"run record exists at {run_record_path}; refusing to overwrite an immutable run"
        )
    _load_scorer_lock()  # fail closed on scorer bundle drift
    input_path = out_dir / "candidates" / board / lane / "submission.h5ad"
    if not input_path.is_file():
        raise FileNotFoundError(f"scorer input missing: {input_path}")
    out_tmp = metrics_dir / f"scorer_{name}_output.tmp.json"
    out_final = metrics_dir / f"scorer_{name}_output.json"
    log_path = metrics_dir / f"scorer_{name}.log"
    rc_tmp = metrics_dir / f"scorer_{name}.rc.tmp"
    rc_file = metrics_dir / f"scorer_{name}.rc"
    for stale in (out_tmp, out_final, rc_tmp, rc_file):
        if stale.exists():
            raise FileExistsError(f"refusing to overwrite existing scorer artifact: {stale}")
    command = scorer_command(spec, out_tmp, input_path)
    supervisor = (
        " ".join(command)
        + f"; rc=$?; printf '%s' \"$rc\" > '{rc_tmp}' && mv '{rc_tmp}' '{rc_file}'"
    )
    log_handle = log_path.open("w", encoding="utf-8")
    process = subprocess.Popen(
        ["bash", "-c", supervisor],
        cwd=ROOT,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    log_handle.close()
    record = {
        "schema": "ve.t2.s3-scorer-run.v1",
        "atom": ATOM,
        "name": name,
        "board": board,
        "lane": lane,
        "status": "RUNNING",
        "pid": process.pid,
        "command": " ".join(command),
        "pseudo_target": spec.scorer_pseudo_target,
        "pseudo_reference": spec.scorer_pseudo_reference,
        "pseudo_target_note": (
            "local --target is a pseudo-target (a training stage); it cannot "
            "establish leaderboard improvement or hidden-target validity. For the "
            "embryo-interp and heart-extrap boards the parent's geometry base "
            "stage IS the pseudo-target stage, which structurally favours the "
            "parent on shape metrics -- read shape terms accordingly."
        ),
        "scorer_lock_path": str(SCORER_LOCK_PATH),
        "scorer_lock_sha256": sha256_file(SCORER_LOCK_PATH),
        "input_path": str(input_path),
        "input_sha256": sha256_file(input_path),
        "log_path": str(log_path),
        "out_tmp": str(out_tmp),
        "out_final": str(out_final),
        "rc_file": str(rc_file),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "started_monotonic": time.monotonic(),
        "rss_samples": [],
        "peak_rss_bytes": None,
        "seed": SEED,
    }
    _write_json_atomic(run_record_path, record)
    _append_run_log(out_dir, f"score-launch: {name} pid={process.pid}")
    return record


def scorer_collect(out_dir: Path, *, board: str, lane: str) -> dict[str, Any]:
    """Low-frequency status check: RSS sample when running, result when done."""
    out_dir = Path(out_dir)
    spec = BOARD_SPECS[board]
    name = f"{board}__{lane}"
    metrics_dir = out_dir / "metrics" / board / lane
    run_record_path = metrics_dir / f"scorer_{name}_run.json"
    if not run_record_path.is_file():
        return {"status": "NOT_LAUNCHED", "name": name}
    record = json.loads(run_record_path.read_text(encoding="utf-8"))
    if record.get("status") != "RUNNING":
        return record
    pid = int(record["pid"])
    rss = _process_tree_rss_bytes(pid)
    if rss is not None:
        record["rss_samples"].append(
            {"at": datetime.now(timezone.utc).isoformat(), "rss_bytes": rss}
        )
        record["rss_samples"] = record["rss_samples"][-200:]
        record["peak_rss_bytes"] = max([record.get("peak_rss_bytes") or 0] + [rss])
    rc_file = Path(record["rc_file"])
    if rc_file.is_file():
        exit_code = int(rc_file.read_text(encoding="utf-8").strip())
        record["exit_code"] = exit_code
        record["finished_at"] = datetime.now(timezone.utc).isoformat()
        record["wall_seconds"] = time.monotonic() - float(record["started_monotonic"])
        out_tmp = Path(record["out_tmp"])
        if exit_code == 0 and out_tmp.is_file():
            out_final = Path(record["out_final"])
            out_tmp.replace(out_final)
            payload = json.loads(out_final.read_text(encoding="utf-8"))
            meta = payload.get("meta", {})
            parent_n_obs = None
            diag_path = out_dir / "candidates" / board / lane / "generation_diagnostics.json"
            if diag_path.is_file():
                diag = json.loads(diag_path.read_text(encoding="utf-8"))
                parent_n_obs = diag.get("model", {}).get("n_obs_parent")
            checks = {
                "genes_match": meta.get("genes") == spec.panel_genes,
                "truth_cells_match": meta.get("truth_cells") == spec.scorer_truth_cells,
                "prediction_cells": meta.get("prediction_cells"),
                "prediction_cells_match_parent": (
                    parent_n_obs is not None
                    and meta.get("prediction_cells") == parent_n_obs
                ),
            }
            record["status"] = "DONE"
            record["result_path"] = str(out_final)
            record["result_sha256"] = sha256_file(out_final)
            record["result_meta"] = meta
            record["result_metrics"] = payload.get("metrics", {})
            record["result_checks"] = checks
        else:
            record["status"] = "FAILED"
            record["failure_reason"] = (
                f"scorer exit_code={exit_code}; see {record['log_path']}"
            )
    elif not _pid_alive(pid):
        record["status"] = "FAILED"
        record["failure_reason"] = (
            f"scorer supervisor pid {pid} gone without an rc file; see {record['log_path']}"
        )
        record["finished_at"] = datetime.now(timezone.utc).isoformat()
        record["wall_seconds"] = time.monotonic() - float(record["started_monotonic"])
    _write_json_atomic(run_record_path, record)
    return record


def command_checks(out_dir: Path) -> dict[str, Any]:
    """Aggregate protected checks, re-verified from disk for every candidate."""
    load_t2_input = _core_load_t2_input()

    out_dir = Path(out_dir)
    per_candidate: dict[str, Any] = {}
    errors: list[str] = []
    for board in BOARD_ORDER:
        spec = BOARD_SPECS[board]
        parent = load_t2_input(ROOT / spec.parent_path, ROOT / spec.panel)
        parent_x = _matrix_digest(parent.X)
        parent_obs = [str(v) for v in parent.obs_names]
        parent_var = [str(v) for v in parent.var_names]
        parent_coords = np.asarray(parent.obsm["spatial_3D"], dtype=np.float64)[:, :3]
        for lane in LANES:
            key = f"{board}/{lane}"
            candidate_path = out_dir / "candidates" / board / lane / "submission.h5ad"
            checks_path = out_dir / "metrics" / board / lane / "geometry_checks.json"
            contract_path = out_dir / "candidates" / board / lane / "contract_report.json"
            if lane == LANE_SPATEO and not candidate_path.is_file():
                per_candidate[key] = {
                    "status": "BLOCKED_TOOLCHAIN",
                    "reason": "Spateo lane not generated; see t2_geometry_env_versions.json",
                }
                continue
            entry: dict[str, Any] = {}
            try:
                candidate = load_t2_input(candidate_path, ROOT / spec.panel)
                entry["expression_unchanged"] = _matrix_digest(candidate.X) == parent_x
                entry["obs_order_unchanged"] = [
                    str(v) for v in candidate.obs_names
                ] == parent_obs
                entry["var_order_unchanged"] = [
                    str(v) for v in candidate.var_names
                ] == parent_var
                entry["gene_order_hash_matches"] = (
                    _names_digest(candidate.var_names) == _names_digest(parent_var)
                )
                candidate_coords = np.asarray(candidate.obsm["spatial_3D"], dtype=np.float64)[:, :3]
                locked = rms_radius(parent_coords)
                entry["rms_parent"] = locked
                entry["rms_candidate"] = rms_radius(candidate_coords)
                entry["rms_within_p0_tolerance"] = bool(
                    np.isclose(
                        entry["rms_candidate"], locked, rtol=RMS_RTOL, atol=RMS_ATOL
                    )
                )
                entry["n_obs_matches_parent"] = candidate.n_obs == parent.n_obs
                stored = json.loads(checks_path.read_text(encoding="utf-8"))
                entry["knn_verdict"] = stored["knn_topology"]["verdict"]
                entry["stored_rms_check"] = stored["rms"]["within_p0_tolerance"]
                entry["stored_invariants_match"] = bool(
                    stored["invariants"]["expression_checksum_unchanged"]
                    and stored["invariants"]["obs_order_unchanged"]
                    and stored["invariants"]["var_order_unchanged"]
                )
                contract = json.loads(contract_path.read_text(encoding="utf-8"))
                entry["contract_status"] = contract["status"]
                ok = all(
                    bool(entry[name])
                    for name in (
                        "expression_unchanged",
                        "obs_order_unchanged",
                        "var_order_unchanged",
                        "gene_order_hash_matches",
                        "rms_within_p0_tolerance",
                        "n_obs_matches_parent",
                        "stored_rms_check",
                        "stored_invariants_match",
                    )
                ) and entry["contract_status"] == "PASS" and entry["knn_verdict"] == "PASS"
                entry["status"] = "PASS" if ok else "FAIL"
            except Exception as exc:
                entry["status"] = "FAIL"
                entry["error"] = f"{type(exc).__name__}: {exc}"
            if entry["status"] != "PASS" and entry.get("status") != "BLOCKED_TOOLCHAIN":
                errors.append(f"{key}: {entry.get('error') or entry}")
            per_candidate[key] = entry
        del parent
    overall = all(
        entry.get("status") in ("PASS", "BLOCKED_TOOLCHAIN")
        for entry in per_candidate.values()
    )
    payload = {
        "schema": "ve.t2.s3-protected-checks.v1",
        "atom": ATOM,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "candidates": per_candidate,
        "errors": errors,
        "status": "PASS" if overall and not errors else "FAIL",
    }
    _write_json_atomic(out_dir / "metrics" / "protected_checks.json", payload)
    _append_run_log(out_dir, f"checks: status={payload['status']}")
    return payload


# ---------------------------------------------------------------------------
# finalize, manifest, verify
# ---------------------------------------------------------------------------


def _safe_version(metadata_module: Any, package: str) -> str | None:
    try:
        return metadata_module.version(package)
    except Exception:
        return None


def _tool_versions(out_dir: Path) -> dict[str, Any]:
    import importlib.metadata

    payload: dict[str, Any] = {
        "schema": "ve.t2.s3-tool-versions.v1",
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
            "path": "scripts/t2_s3_shape_field.py",
            "sha256": sha256_file(Path(__file__).resolve()),
        },
        "scorer": {
            "entrypoint": "third_party/veckit/score_h5ad.py",
            "sha256": sha256_file(SCORER_ENTRYPOINT),
            "shape_metrics": "third_party/veckit/common/shape_metrics.py",
            "shape_metrics_sha256": sha256_file(SHAPE_METRICS_PATH),
            "lock": "artifacts/tool_integration/P0-LOCK/locks/SCORER_LOCK.json",
            "bundle_commit": "46d41e63f42a9aab815db20b742feeccd249cb17",
            "package_version": "0.1.1",
        },
    }
    env_path = out_dir / "metrics" / "t2_geometry_env_versions.json"
    if env_path.is_file():
        payload["ve_t2_geometry"] = json.loads(env_path.read_text(encoding="utf-8"))
    return payload


def command_finalize(out_dir: Path) -> dict[str, Any]:
    """Write config_resolved.yaml, TOOL_VERSIONS.json and the roll-up summary."""
    out_dir = Path(out_dir)
    summary: dict[str, Any] = {
        "schema": "ve.t2.s3-summary.v1",
        "atom": ATOM,
        "seed": SEED,
        "boards": {},
    }
    holdout_path = out_dir / "metrics" / "pseudoholdout_report.json"
    if holdout_path.is_file():
        summary["pseudoholdout"] = json.loads(holdout_path.read_text(encoding="utf-8"))
    for board in BOARD_ORDER:
        board_entry: dict[str, Any] = {"lanes": {}}
        for lane in LANES:
            lane_entry: dict[str, Any] = {}
            diag_path = out_dir / "candidates" / board / lane / "generation_diagnostics.json"
            if diag_path.is_file():
                diag = json.loads(diag_path.read_text(encoding="utf-8"))
                lane_entry["candidate_sha256"] = diag["candidate_sha256"]
                lane_entry["knn_verdict"] = diag["knn_verdict"]
                lane_entry["rms_within_p0_tolerance"] = diag["rms_within_p0_tolerance"]
                lane_entry["expression_unchanged"] = diag["expression_unchanged"]
            contract_path = out_dir / "candidates" / board / lane / "contract_report.json"
            if contract_path.is_file():
                lane_entry["contract_status"] = json.loads(
                    contract_path.read_text(encoding="utf-8")
                )["status"]
            checks_path = out_dir / "metrics" / board / lane / "geometry_checks.json"
            if checks_path.is_file():
                checks = json.loads(checks_path.read_text(encoding="utf-8"))
                lane_entry["knn15_overlap"] = checks["knn_topology"]["candidate"]["mean_overlap"]
                lane_entry["knn15_reference"] = checks["knn_topology"]["full_field_reference"]["mean_overlap"]
            scorer_path = out_dir / "metrics" / board / lane / f"scorer_{board}__{lane}_run.json"
            if scorer_path.is_file():
                run = json.loads(scorer_path.read_text(encoding="utf-8"))
                lane_entry["scorer"] = {
                    "status": run.get("status"),
                    "result_metrics": run.get("result_metrics"),
                    "result_meta": run.get("result_meta"),
                    "pseudo_target": run.get("pseudo_target"),
                }
            board_entry["lanes"][lane] = lane_entry
        summary["boards"][board] = board_entry
    _write_json_atomic(out_dir / "metrics" / "shape_field_summary.json", summary)

    config_lines = [
        f"atom: {ATOM}",
        "task: T2-S3-SHAPE-FIELD",
        f"seed: {SEED}",
        "allow_network: true  # pip package installation only; no external data downloads",
        "allow_server_submission: false",
        "candidate_generation: true",
        f"lanes: [{', '.join(LANES)}]",
        "lane_difference: field estimator only (pycpd deformable CPD vs spateo morpho_align)",
        "protected_atoms: [G1_TSR_scale, expression_matrix, expression_row_order, active_J1_pairing]",
        f"n_landmarks: {N_LANDMARKS}",
        "landmark_sampling: stratified_by_celltype",
        f"cpd_beta: {CPD_BETA}",
        f"cpd_alpha: {CPD_ALPHA}",
        f"cpd_max_iterations: {CPD_MAX_ITER}",
        f"cpd_tolerance: {CPD_TOL}",
        f"rigid_polish: pycpd RigidRegistration max_iterations={RIGID_POLISH_MAX_ITER} tol={RIGID_POLISH_TOL}",
        "frame: per-stage canonical (centre + PCA + RMS), proper-flip Chamfer alignment",
        f"extrap_rho: {EXTRAP_RHO}  # pre-declared strong shrinkage; no interpolation slope reuse",
        f"n_holdout_base: {N_HOLDOUT_BASE}",
        f"knn_k: {KNN_K}",
        f"knn_abs_floor: {KNN_ABS_FLOOR}",
        f"knn_ref_slack: {KNN_REF_SLACK}",
        f"rms_relock_tolerance: rtol={RMS_RTOL} atol={RMS_ATOL}  # P0-derived",
        "boards:",
    ]
    for board in BOARD_ORDER:
        spec = BOARD_SPECS[board]
        config_lines.extend(
            [
                f"  {board}:",
                f"    official_key: {spec.official_key}",
                f"    regime: {spec.regime}",
                f"    target_stage: {spec.target_stage}  # hidden truth; never read",
                f"    base_stage: {spec.base_stage}  # parent geometry provenance",
                f"    field_pair: [{spec.left_stage}, {spec.right_stage}]",
                f"    coefficient: {_board_coefficient(spec):.6f}",
                f"    parent: {spec.parent_path}",
                f"    parent_sha256: {spec.parent_sha256}",
                f"    scorer_pseudo_target: {spec.scorer_pseudo_target}  # training stage, not a leaderboard preview",
            ]
        )
    config_lines.append("deviations: []")
    config_lines.append("")
    _write_bytes_atomic(
        out_dir / "config_resolved.yaml", "\n".join(config_lines).encode("utf-8")
    )
    _write_json_atomic(out_dir / "TOOL_VERSIONS.json", _tool_versions(out_dir))
    _append_run_log(out_dir, "finalize: config_resolved.yaml + TOOL_VERSIONS.json + summary")
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
            "implementation": "scripts/t2_s3_shape_field.py",
            "implementation_sha256": sha256_file(Path(__file__).resolve()),
            "test_module": "tests/test_t2_s3_shape_field.py",
            "test_module_sha256": sha256_file(ROOT / "tests" / "test_t2_s3_shape_field.py")
            if (ROOT / "tests" / "test_t2_s3_shape_field.py").is_file()
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
            "input-lock", "env-probe", "fields", "fit-field", "pseudoholdout",
            "generate", "contract", "score-launch", "score-collect", "checks",
            "finalize", "manifest", "verify",
        ],
    )
    parser.add_argument("--out-dir", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--pair", type=str, default=None)
    parser.add_argument("--direction", choices=["fwd", "bwd"], default=None)
    parser.add_argument("--backend", choices=["pycpd", "spateo"], default=None)
    parser.add_argument("--backends", type=str, default="pycpd",
                        help="comma-separated backends for fields/pseudoholdout")
    parser.add_argument("--board", choices=list(BOARD_ORDER) + ["all"], default="all")
    parser.add_argument("--lane", choices=list(LANES) + ["all"], default="all")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir)
    if args.command == "input-lock":
        result = command_input_lock(out_dir)
    elif args.command == "env-probe":
        result = command_env_probe(out_dir)
    elif args.command == "fields":
        result = command_fields(out_dir, backends=tuple(args.backends.split(",")))
    elif args.command == "fit-field":
        if args.pair is None or args.direction is None or args.backend is None:
            raise ValueError("fit-field requires --pair, --direction and --backend")
        result = command_fit_field(
            out_dir, pair=args.pair, direction=args.direction, backend=args.backend
        )
    elif args.command == "pseudoholdout":
        result = command_pseudoholdout(out_dir, backends=tuple(args.backends.split(",")))
    elif args.command == "generate":
        boards = BOARD_ORDER if args.board == "all" else (args.board,)
        lanes = LANES if args.lane == "all" else (args.lane,)
        result = {
            "step": "generate",
            "candidates": [
                command_generate(out_dir, board=b, lane=l, overwrite=args.overwrite)
                for b in boards
                for l in lanes
            ],
        }
    elif args.command == "contract":
        boards = BOARD_ORDER if args.board == "all" else (args.board,)
        lanes = LANES if args.lane == "all" else (args.lane,)
        reports = []
        for b in boards:
            for l in lanes:
                candidate = out_dir / "candidates" / b / l / "submission.h5ad"
                if not candidate.is_file():
                    reports.append({"board": b, "lane": l, "status": "MISSING"})
                    continue
                reports.append(command_contract(out_dir, board=b, lane=l))
        result = {"step": "contract", "reports": reports}
    elif args.command == "score-launch":
        boards = BOARD_ORDER if args.board == "all" else (args.board,)
        lanes = LANES if args.lane == "all" else (args.lane,)
        result = {
            "step": "score-launch",
            "runs": [
                scorer_launch(out_dir, board=b, lane=l)
                for b in boards
                for l in lanes
                if (out_dir / "candidates" / b / l / "submission.h5ad").is_file()
            ],
        }
    elif args.command == "score-collect":
        boards = BOARD_ORDER if args.board == "all" else (args.board,)
        lanes = LANES if args.lane == "all" else (args.lane,)
        result = {
            "step": "score-collect",
            "runs": [
                scorer_collect(out_dir, board=b, lane=l)
                for b in boards
                for l in lanes
            ],
        }
    elif args.command == "checks":
        result = command_checks(out_dir)
    elif args.command == "finalize":
        result = command_finalize(out_dir)
    elif args.command == "manifest":
        result = {
            "step": "manifest",
            "n_files": len(write_manifest(out_dir, exclude=(
                "run.log",
            ))["files"]),
        }
    elif args.command == "verify":
        result = verify_manifest(out_dir)
    else:  # pragma: no cover
        raise ValueError(args.command)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
