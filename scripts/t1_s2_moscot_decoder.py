#!/usr/bin/env python3
"""T1-S2-MOSCOT-DECODER: temporal coupling, state-mass forecast, state mean
program and a two-lane decoder on the locked T1 parent.

Replaces the parent's global constant-velocity shift with

    future population
    = locked parent cells
    + temporal coupling / state-mass forecast
    + state-specific mean program
    + residual/covariance replay

following ``docs/batch3/prompts/T1_S2_MOSCOT_DECODER.md``.  The atom never reads
the hidden E10.5 truth and never submits to the server.

Environment split (toolchain rule: the external tool env must not write the
final H5AD):

* ``couple`` runs under the isolated ``.venvs/ve-t1-ot`` interpreter and only
  writes standard intermediates (sparse coupling npz + transition TSV).  moscot
  ``TemporalProblem`` on state centroids (state/program latent) is the primary
  tool; POT's unbalanced Sinkhorn is the pre-declared fallback registered in
  ``P0-LOCK/locks/TOOLCHAIN_LOCK.json`` (``POT_manual_if_installed``).
* every other subcommand runs under the ve-core interpreter and reads only the
  frozen intermediates.

Subcommands (atomic writes; interruption cannot create a false PASS):

* ``couple``        -- state-level temporal coupling E8.5->E9.5 (cost = program
                       distance + lineage mismatch penalty), sparse coupling npz,
                       state_transition.tsv, coupling summary
* ``forecast``      -- state_mass.tsv (transport growth -> shrunk E10.5 state
                       probabilities) and state_gene_delta.npz (decoupled mean
                       program, extrapolation-shrunk for the E10.5 board)
* ``pseudoholdout`` -- one source-only E8.5->E9.5 pseudo-holdout: parent-method
                       arm, L1 arm, analytic alpha resolution (then frozen)
* ``generate``      -- one full T1:val (E10.5) candidate per lane
* ``contract``      -- locked prepare-builder contract checks per candidate
* ``score-launch`` / ``score-collect`` -- locked full-panel scorer wrapper
                       (pseudo-target E9.5; never a leaderboard preview)
* ``checks``        -- protected checks over candidates and intermediates
* ``finalize``      -- config_resolved.yaml, TOOL_VERSIONS.json,
                       metrics/component_ablation.json
* ``manifest`` / ``verify`` -- stable artifact manifest + self-verify

Pre-declared constants below are fixed before any run; no grid search, no
server feedback, seed 20260830 everywhere.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse

try:
    from scripts.t1_temporal_model import select_indices_by_shares
except ImportError:  # direct ``python scripts/t1_s2_moscot_decoder.py`` execution
    from t1_temporal_model import select_indices_by_shares

ROOT = Path(__file__).resolve().parents[1]
ATOM = "T1-S2-MOSCOT-DECODER-20260902-v1"
OUTPUT_DEFAULT = ROOT / "artifacts" / "tool_integration" / ATOM
SEED = 20260830

SOURCE_STAGE = "E8.5"
TARGET_STAGE = "E9.5"
BOARD = "T1:val"
BOARD_TARGET_STAGE = "E10.5"  # hidden truth; never read

SOURCE_PATH = ROOT / "data" / "E8.5_RNA.h5ad"
TARGET_PATH = ROOT / "data" / "E9.5_RNA.h5ad"
PARENT_PATH = ROOT / "submissions/candidates/T1_val/v0004_strict_pseudobulk_shift/submission.h5ad"
PARENT_SHA256 = "1bc069d9aecd4b9b15f3ff91c328ef27a9773bfd0d3c890f36f5f1b6fb4f49bd"
PANEL_PATH = ROOT / "data/gene_panel" / "T1__val.genes.txt"
SCORER_LOCK_PATH = ROOT / "artifacts/tool_integration/P0-LOCK/locks/SCORER_LOCK.json"
SCORER_ENTRYPOINT = ROOT / "third_party/veckit/score_h5ad.py"
PRE_DIR = ROOT / "artifacts" / "tool_integration" / "T1-PRE-HARMONIZE-20260902-v1"
PRE_CENTROIDS = PRE_DIR / "intermediates" / "state_centroids.npz"
PRE_VOCABULARY = PRE_DIR / "intermediates" / "state_vocabulary.tsv"
PRE_CROSSWALK = PRE_DIR / "intermediates" / "state_crosswalk.tsv"
PRE_PROGRAMS = PRE_DIR / "intermediates" / "program_definition.tsv"

EXPECTED_GENES = 32285
EXPECTED_TRUTH_CELLS = 17057
BOARD_MIN_CELLS = 1000
BOARD_MAX_CELLS = 5118
N_CELLS = 5118  # board max, identical to the locked parent
NORMALIZATION = "log1p_normalized"
UNRESOLVED = "UNRESOLVED"

LANES = ("L1_EMPIRICAL_RESIDUAL", "L2_MODULE_SCDESIGN3")

# ---------------------------------------------------------------------------
# Pre-declared analysis constants (announced before any run; no grid search).
# ---------------------------------------------------------------------------
# Coupling cost: squared euclidean distance between per-marker z-scored state
# centroids (74-marker program space from T1-PRE), normalised by the median of
# the raw program-distance matrix so the declared cost is scale-free with
# median 1.0 (raw z-space distances are O(10-100); without this normalisation
# epsilon=0.1 would collapse the entropic kernel numerically), plus
# LINEAGE_PENALTY for lineage-mismatched pairs.  Unbalanced Sinkhorn with
# equal relaxation on both marginals so source depletion/growth is visible in
# the transport mass.
LINEAGE_PENALTY = 8.0
OT_COST_NORMALISATION = "median_program_distance"
OT_EPSILON = 0.1
OT_TAU_A = 0.95
OT_TAU_B = 0.95
OT_BACKEND_PRIMARY = "moscot_temporal_problem"
OT_BACKEND_FALLBACK = "pot_unbalanced_sinkhorn"  # P0-registered fallback

# State-mass forecast (E10.5 extrapolation regime): geometric shrinkage of the
# transport-derived growth towards 1, clipped; small states shrink harder and
# are capped in share.  The same slope is never extended unshrunk.
GROWTH_RHO = 0.5
GROWTH_CLIP_LO = 1.0 / 3.0
GROWTH_CLIP_HI = 3.0
SMALL_STATE_MIN_CELLS = 50  # same floor as T1-PRE
SMALL_STATE_RHO = 0.25
SMALL_STATE_SHARE_CAP_MULT = 2.0

# Mean program: measured E8.5->E9.5 per-state pseudobulk deltas, shrunk by
# RHO_EXTRAP for the one-interval E9.5->E10.5 extrapolation (independent time
# regime for the extrapolation board).
RHO_EXTRAP = 0.5

# Calibration: one analytic source-only pseudo-holdout alpha, then frozen.
ALPHA_CLIP_LO = 0.0
ALPHA_CLIP_HI = 1.5

TRANSITION_TSV_FIELDS = [
    "source_state", "target_state", "transported_mass",
    "source_share_e85", "target_pred_share_e95", "target_actual_share_e95",
    "same_lineage", "crosswalk_match",
]
STATE_MASS_TSV_FIELDS = [
    "board", "target_stage", "state", "lineage", "parent_probability",
    "raw_forecast", "shrunk_probability", "uncertainty", "evidence",
]
SAMPLING_PLAN_TSV_FIELDS = [
    "board", "state", "forecast_count", "parent_supply", "n_unique",
    "n_duplicated", "parent_share", "forecast_share", "growth_raw",
    "growth_shrunk", "growth_rule",
]

LINEAGE_BY_STATE = {
    "OFT/RV-CM": "cardiac_mesoderm", "IFT-CM": "cardiac_mesoderm",
    "AVC-CM": "cardiac_mesoderm", "RV-CM": "cardiac_mesoderm",
    "LV-CM": "cardiac_mesoderm", "SV-CM": "cardiac_mesoderm",
    "V-CM": "cardiac_mesoderm", "pSHF": "cardiac_mesoderm",
    "aSHF": "cardiac_mesoderm", "JCF": "cardiac_mesoderm",
    "pPHM": "cardiac_mesoderm", "aPHM": "cardiac_mesoderm",
    "Endothelium": "vascular_endothelial", "Endocardium": "vascular_endothelial",
    "BEC": "vascular_endothelial", "Pericardium": "pericardial_mesoderm",
    "Proepicardium": "pericardial_mesoderm", "ST": "pericardial_mesoderm",
    "Foregut": "endoderm", "Hepatocyte": "endoderm", "Epithelium": "endoderm",
    "Surface Ectoderm": "ectoderm", "Neural Tube": "neuroectoderm",
    "NCC": "neural_crest", "NCC-derived": "neural_crest",
    "Paraxial Mesoderm": "paraxial_mesoderm",
    "EXEM": "extraembryonic_mesoderm", "Blood": "hematopoietic",
}


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
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _write_tsv_atomic(
    path: Path, rows: Iterable[Mapping[str, Any]], fields: list[str]
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    temporary.replace(path)


def _write_bytes_atomic(path: Path, payload: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)


def _read_tsv(path: Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _derived_seed(*parts: Any) -> int:
    """Deterministic child seed from the atom seed (stable across processes)."""
    key = json.dumps([SEED, *[str(p) for p in parts]]).encode("utf-8")
    return int.from_bytes(hashlib.sha256(key).digest()[:4], "little")


def state_counts(labels: np.ndarray) -> dict[str, int]:
    values, counts = np.unique(np.asarray(labels).astype(str), return_counts=True)
    return {str(v): int(c) for v, c in zip(values, counts)}


# ---------------------------------------------------------------------------
# Locked inputs / T1-PRE intermediates
# ---------------------------------------------------------------------------


def load_pre_intermediates() -> dict[str, Any]:
    """Read the frozen T1-PRE vocabulary/crosswalk/centroids (hash-audited)."""
    for path in (PRE_CENTROIDS, PRE_VOCABULARY, PRE_CROSSWALK, PRE_PROGRAMS):
        if not path.is_file():
            raise FileNotFoundError(f"T1-PRE intermediate missing: {path}")
    npz = np.load(PRE_CENTROIDS, allow_pickle=False)
    states_e85 = [str(s) for s in npz["states_e85"].tolist()]
    states_e95 = [str(s) for s in npz["states_e95"].tolist()]
    vocabulary = _read_tsv(PRE_VOCABULARY)
    crosswalk = _read_tsv(PRE_CROSSWALK)
    for row in vocabulary:
        state = row["fine_state"]
        if state not in LINEAGE_BY_STATE:
            raise ValueError(f"vocabulary state missing lineage hierarchy entry: {state!r}")
    return {
        "var_names": [str(g) for g in npz["var_names"].tolist()],
        "marker_genes": [str(g) for g in npz["marker_genes"].tolist()],
        "states_e85": states_e85,
        "states_e95": states_e95,
        "centroids_e85_full": npz["centroids_e85_full"],
        "centroids_e95_full": npz["centroids_e95_full"],
        "centroids_e85_marker": npz["centroids_e85_marker"],
        "centroids_e95_marker": npz["centroids_e95_marker"],
        "vocabulary": vocabulary,
        "crosswalk": crosswalk,
        "input_hashes": {
            "state_centroids_npz": sha256_file(PRE_CENTROIDS),
            "state_vocabulary_tsv": sha256_file(PRE_VOCABULARY),
            "state_crosswalk_tsv": sha256_file(PRE_CROSSWALK),
            "program_definition_tsv": sha256_file(PRE_PROGRAMS),
        },
    }


def forward_matches(crosswalk: list[dict[str, str]]) -> dict[str, str]:
    """Resolved E8.5->E9.5 matches; UNRESOLVED omitted (never force-paired)."""
    return {
        row["fine_state"]: row["matched_state"]
        for row in crosswalk
        if row["direction"] == "e85_to_e95" and row["matched_state"] != UNRESOLVED
    }


def reverse_matches(crosswalk: list[dict[str, str]]) -> dict[str, str]:
    """Resolved E9.5->E8.5 matches (explicit reverse rows, then inverted forward).

    The T1-PRE crosswalk only emits ``e95_to_e85`` rows where the reverse
    direction carries independent evidence (10 rows); SHARED_EXACT states and
    forward MUTUAL_NEAREST targets have no explicit reverse row but are
    resolved by the forward row, so the resolved forward rows are inverted to
    complete the map.  Explicit reverse rows take precedence on conflict.
    """
    rev = {
        row["fine_state"]: row["matched_state"]
        for row in crosswalk
        if row["direction"] == "e95_to_e85" and row["matched_state"] != UNRESOLVED
    }
    for row in crosswalk:
        if row["direction"] == "e85_to_e95" and row["matched_state"] != UNRESOLVED:
            rev.setdefault(row["matched_state"], row["fine_state"])
    return rev


# ---------------------------------------------------------------------------
# Coupling (runs under .venvs/ve-t1-ot)
# ---------------------------------------------------------------------------


def coupling_cost_matrix(
    centroids_a_marker: np.ndarray,
    centroids_b_marker: np.ndarray,
    states_a: list[str],
    states_b: list[str],
    *,
    lineage_penalty: float = LINEAGE_PENALTY,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Program distance + lineage/state mismatch penalty.

    Program distance = squared euclidean between per-marker z-scored centroids
    (marker programs frozen by T1-PRE), normalised by the median of the raw
    program-distance matrix (pre-declared ``OT_COST_NORMALISATION``); the
    declared cost is therefore scale-free with median program distance 1.0 and
    the lineage penalty keeps its declared weight relative to epsilon.  The
    penalty adds exactly ``lineage_penalty`` for lineage-mismatched pairs.
    z-scoring uses the union of both stages' centroids per marker, so the cost
    is deterministic; a zero-variance marker contributes zeros.
    """
    cent_a = np.asarray(centroids_a_marker, dtype=np.float64)
    cent_b = np.asarray(centroids_b_marker, dtype=np.float64)
    if cent_a.shape[0] != len(states_a) or cent_b.shape[0] != len(states_b):
        raise ValueError("centroid/state count mismatch")
    if cent_a.shape[1] != cent_b.shape[1]:
        raise ValueError("marker dimension mismatch between stages")
    za, zb = _zscore_union(cent_a, cent_b)
    program = ((za[:, None, :] - zb[None, :, :]) ** 2).sum(axis=2)
    median = float(np.median(program))
    if median <= 0:
        raise ValueError("degenerate program distance: median is zero")
    program = program / median
    penalty = np.zeros_like(program)
    for i, sa in enumerate(states_a):
        for j, sb in enumerate(states_b):
            if LINEAGE_BY_STATE[sa] != LINEAGE_BY_STATE[sb]:
                penalty[i, j] = float(lineage_penalty)
    cost = program + penalty
    diagnostics = {
        "n_markers": int(cent_a.shape[1]),
        "program_distance_mean_raw": float(program.mean() * median),
        "program_distance_median_raw": median,
        "cost_normalisation": OT_COST_NORMALISATION,
        "lineage_penalty": float(lineage_penalty),
        "mismatched_pairs": int((penalty > 0).sum()),
        "total_pairs": int(penalty.size),
        "zscore": "per-marker mean/std over the union of the 39 state centroids",
    }
    return cost.astype(np.float64), diagnostics


def _zscore_union(
    cent_a: np.ndarray, cent_b: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Per-marker z-score over the union of both stages' centroids."""
    both = np.vstack([cent_a, cent_b])
    mean = both.mean(axis=0)
    std = both.std(axis=0)
    std[std == 0] = 1.0
    return (cent_a - mean) / std, (cent_b - mean) / std


def _program_scale(cent_a: np.ndarray, cent_b: np.ndarray) -> float:
    """sqrt of the median raw program distance; the declared normaliser."""
    za, zb = _zscore_union(cent_a, cent_b)
    program = ((za[:, None, :] - zb[None, :, :]) ** 2).sum(axis=2)
    median = float(np.median(program))
    if median <= 0:
        raise ValueError("degenerate program distance: median is zero")
    return float(np.sqrt(median))


def augmented_program_coordinates(
    centroids_marker: np.ndarray,
    states: list[str],
    lineages: list[str],
    *,
    n_source: int,
    lineage_penalty: float = LINEAGE_PENALTY,
    reference_mean: np.ndarray | None = None,
    reference_std: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """z-scored marker centroids + sqrt(penalty/2) * one-hot(lineage).

    Rows ``0..n_source-1`` are the source stage, the rest the target stage;
    the program block is scaled by 1/sqrt(median raw program distance) so
    squared euclidean distance on the augmented coordinates equals exactly the
    declared cost ``program/median + lineage_penalty * 1[lineage mismatch]``,
    letting a standard moscot sq-euclidean problem realise the declared cost.
    Returns (augmented, mean, std); caller passes the union-fitted reference to
    keep both stages in one frame.
    """
    cent = np.asarray(centroids_marker, dtype=np.float64)
    if reference_mean is None or reference_std is None:
        reference_mean = cent.mean(axis=0)
        reference_std = cent.std(axis=0)
        reference_std[reference_std == 0] = 1.0
    z = (cent - reference_mean) / reference_std
    scale = _program_scale(cent[:n_source], cent[n_source:])
    z = z / scale
    lineage_index = {lineage: k for k, lineage in enumerate(sorted(set(lineages)))}
    onehot = np.zeros((len(states), len(lineage_index)), dtype=np.float64)
    for row, state in enumerate(states):
        onehot[row, lineage_index[lineages[row]]] = np.sqrt(lineage_penalty / 2.0)
    return np.hstack([z, onehot]), reference_mean, reference_std


def solve_coupling(
    cost: np.ndarray,
    a: np.ndarray,
    b: np.ndarray,
    *,
    augmented: np.ndarray | None = None,
    n_source: int | None = None,
    epsilon: float = OT_EPSILON,
    tau_a: float = OT_TAU_A,
    tau_b: float = OT_TAU_B,
    backend: str = "auto",
) -> tuple[np.ndarray, dict[str, Any]]:
    """Unbalanced temporal coupling for fixed marginals.

    Primary backend: moscot ``TemporalProblem`` on the state point sets with
    lineage-penalty-augmented program coordinates (sq-euclidean cost equals the
    declared cost exactly; verified against the explicit matrix).  The
    P0-registered fallback is POT's ``ot.unbalanced.sinkhorn_unbalanced`` on the
    explicit cost matrix.
    """
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    if a.sum() <= 0 or b.sum() <= 0:
        raise ValueError("marginals must have positive mass")
    a = a / a.sum()
    b = b / b.sum()
    if cost.shape != (a.shape[0], b.shape[0]):
        raise ValueError("cost shape disagrees with marginals")
    if backend == "auto":
        backend = OT_BACKEND_PRIMARY
    errors: dict[str, str] = {}
    if backend == OT_BACKEND_PRIMARY:
        try:
            if augmented is None or n_source is None:
                raise ValueError("moscot path needs augmented coordinates and n_source")
            transport, meta = _solve_coupling_moscot(
                augmented, n_source, a, b, cost_check=cost,
                epsilon=epsilon, tau_a=tau_a, tau_b=tau_b,
            )
            return transport, meta
        except Exception as exc:  # recorded, then the registered fallback runs
            errors[OT_BACKEND_PRIMARY] = f"{type(exc).__name__}: {exc}"
    try:
        transport, meta = _solve_coupling_pot(
            cost, a, b, epsilon=epsilon, tau_a=tau_a, tau_b=tau_b
        )
        meta["primary_error"] = errors.get(OT_BACKEND_PRIMARY)
        return transport, meta
    except Exception as exc:
        errors[OT_BACKEND_FALLBACK] = f"{type(exc).__name__}: {exc}"
    raise RuntimeError(f"no coupling backend succeeded: {errors}")


def _solve_coupling_moscot(
    augmented: np.ndarray,
    n_source: int,
    a: np.ndarray,
    b: np.ndarray,
    *,
    cost_check: np.ndarray,
    epsilon: float,
    tau_a: float,
    tau_b: float,
) -> tuple[np.ndarray, dict[str, Any]]:
    """moscot ``TemporalProblem`` on the penalty-augmented state coordinates."""
    import pandas as pd  # local import: only required inside the ve-t1-ot env
    import moscot
    from moscot.problems.time import TemporalProblem

    coords = np.asarray(augmented, dtype=np.float32)
    n_target = coords.shape[0] - n_source
    frame = ad.AnnData(
        X=coords,
        obs=pd.DataFrame(
            {
                "time": [8.5] * n_source + [9.5] * n_target,
                "mass": np.concatenate([a, b]),
            }
        ),
    )
    # audit: sq-euclidean on the augmented coordinates must equal the declared
    # cost (float32 round-trip for the AnnData frame, hence float32 tolerance;
    # the exact float64 identity is covered by the unit test)
    xa = coords[:n_source].astype(np.float64)
    xb = coords[n_source:].astype(np.float64)
    realised = ((xa[:, None, :] - xb[None, :, :]) ** 2).sum(axis=2)
    if not np.allclose(realised, cost_check, rtol=1e-4, atol=1e-4):
        raise RuntimeError("augmented-coordinate cost disagrees with the declared cost")

    problem = TemporalProblem(frame)
    problem = problem.prepare(
        time_key="time",
        joint_attr={"attr": "X"},  # str form would be read as an obsm key
        cost="sq_euclidean",
        a="mass",
        b="mass",
    )
    problem = problem.solve(
        epsilon=epsilon, tau_a=tau_a, tau_b=tau_b, scale_cost=1.0, jit=True
    )
    solution = problem[8.5, 9.5].solution
    transport = np.asarray(solution.transport_matrix, dtype=np.float64)
    meta = {
        "backend": OT_BACKEND_PRIMARY,
        "moscot_version": moscot.__version__,
        "solver": "moscot.problems.time.TemporalProblem (ott-jax sinkhorn backend)",
        "cost": "sq_euclidean on penalty-augmented program coordinates (exactly the declared cost)",
        "epsilon": float(epsilon),
        "tau_a": float(tau_a),
        "tau_b": float(tau_b),
        "scale_cost": 1.0,
        "mass_mode": "unbalanced",
        "converged": bool(solution.converged),
        "regularized_cost": float(solution.cost),
    }
    return transport, meta


def _solve_coupling_pot(
    cost: np.ndarray,
    a: np.ndarray,
    b: np.ndarray,
    *,
    epsilon: float,
    tau_a: float,
    tau_b: float,
) -> tuple[np.ndarray, dict[str, Any]]:
    """POT unbalanced Sinkhorn (P0-registered fallback ``POT_manual_if_installed``)."""
    import sys as _sys

    _sys.modules.setdefault("tensorflow", None)  # optional backend; numpy-2 ABI guard
    import ot

    # ot.unbalanced.sinkhorn_unbalanced reg_m is the marginal KL relaxation;
    # map moscot-style tau to the KL relaxation mass scale rho = reg_m * eps-form:
    # tau = rho / (rho + epsilon)  =>  rho = epsilon * tau / (1 - tau).
    reg_m = epsilon * tau_a / (1.0 - tau_a)
    transport = ot.unbalanced.sinkhorn_unbalanced(
        a, b, np.asarray(cost, dtype=np.float64), reg=epsilon, reg_m=reg_m,
        method="sinkhorn", numItermax=100000, stopThr=1e-9,
    )
    meta = {
        "backend": OT_BACKEND_FALLBACK,
        "pot_version": ot.__version__,
        "solver": "ot.unbalanced.sinkhorn_unbalanced",
        "cost": "explicit state-level cost matrix (program distance + lineage penalty)",
        "epsilon": float(epsilon),
        "tau_a": float(tau_a),
        "tau_b": float(tau_b),
        "reg_m": float(reg_m),
        "mass_mode": "unbalanced",
        "converged": None,
        "regularized_cost": float((transport * cost).sum()),
    }
    return np.asarray(transport, dtype=np.float64), meta


def _numpy_toy_sinkhorn(
    cost: np.ndarray,
    a: np.ndarray,
    b: np.ndarray,
    *,
    epsilon: float = OT_EPSILON,
    tau_a: float = OT_TAU_A,
    tau_b: float = OT_TAU_B,
    max_iter: int = 5000,
    tol: float = 1e-10,
) -> np.ndarray:
    """Pure-numpy unbalanced Sinkhorn for unit tests on toy problems only.

    Test scaffolding, not a production backend: the production coupling runs
    under ve-t1-ot with moscot/POT and records the backend in coupling_meta.
    """
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    a = a / a.sum()
    b = b / b.sum()
    kernel = np.exp(-np.asarray(cost, dtype=np.float64) / epsilon)
    fi_a = tau_a / (tau_a + epsilon / (1.0 - tau_a))  # unused; kept for clarity
    power_a = tau_a / 1.0  # KL-relaxed scaling exponent approximation
    u = np.ones_like(a)
    v = np.ones_like(b)
    frac_a = tau_a
    frac_b = tau_b
    for _ in range(max_iter):
        u_prev = u
        kv = kernel @ v
        kv[kv == 0] = 1e-300
        u = (a / kv) ** frac_a
        ktu = kernel.T @ u
        ktu[ktu == 0] = 1e-300
        v = (b / ktu) ** frac_b
        if np.max(np.abs(u - u_prev)) < tol:
            break
    _ = fi_a, power_a
    return (u[:, None] * kernel) * v[None, :]


def command_couple(out_dir: Path) -> dict[str, Any]:
    """State-level temporal coupling E8.5 -> E9.5 (state/program latent)."""
    out_dir = Path(out_dir)
    pre = load_pre_intermediates()
    states_a = pre["states_e85"]
    states_b = pre["states_e95"]
    counts_a = {row["fine_state"]: int(row["n_cells_e85"]) for row in pre["vocabulary"]}
    counts_b = {row["fine_state"]: int(row["n_cells_e95"]) for row in pre["vocabulary"]}
    a = np.asarray([counts_a[s] for s in states_a], dtype=np.float64)
    b = np.asarray([counts_b[s] for s in states_b], dtype=np.float64)
    shares_a = a / a.sum()
    shares_b = b / b.sum()

    cost, cost_diag = coupling_cost_matrix(
        pre["centroids_e85_marker"], pre["centroids_e95_marker"], states_a, states_b
    )
    union_states = states_a + states_b
    union_lineages = [LINEAGE_BY_STATE[s] for s in union_states]
    union_centroids = np.vstack(
        [pre["centroids_e85_marker"], pre["centroids_e95_marker"]]
    )
    augmented, _, _ = augmented_program_coordinates(
        union_centroids, union_states, union_lineages, n_source=len(states_a)
    )
    backend = os.environ.get("VE_T1_OT_BACKEND", "auto")
    transport, solve_meta = solve_coupling(
        cost, shares_a, shares_b,
        augmented=augmented, n_source=len(states_a),
        epsilon=OT_EPSILON, tau_a=OT_TAU_A, tau_b=OT_TAU_B,
        backend=backend,
    )
    if (transport < -1e-12).any():
        raise RuntimeError("coupling contains negative mass")
    transport = np.clip(transport, 0.0, None)
    pred_b = transport.sum(axis=0)
    pred_b_share = pred_b / pred_b.sum()
    fwd = forward_matches(pre["crosswalk"])

    csr = sparse.csr_matrix(transport)
    npz_tmp = out_dir / "intermediates" / "coupling.tmp.npz"
    npz_tmp.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        npz_tmp,
        format=np.asarray("csr"),
        data=csr.data,
        indices=csr.indices,
        indptr=csr.indptr,
        shape=np.asarray(csr.shape),
        source_states=np.asarray(states_a),
        target_states=np.asarray(states_b),
        source_marginal=shares_a,
        target_marginal=shares_b,
        target_pred_share=pred_b_share,
        cost=cost,
    )
    npz_tmp.replace(out_dir / "intermediates" / "coupling.npz")

    rows: list[dict[str, Any]] = []
    for i, sa in enumerate(states_a):
        for j, sb in enumerate(states_b):
            mass = float(transport[i, j])
            if mass <= 0:
                continue
            rows.append(
                {
                    "source_state": sa,
                    "target_state": sb,
                    "transported_mass": f"{mass:.8e}",
                    "source_share_e85": f"{shares_a[i]:.6f}",
                    "target_pred_share_e95": f"{pred_b_share[j]:.6f}",
                    "target_actual_share_e95": f"{shares_b[j]:.6f}",
                    "same_lineage": str(LINEAGE_BY_STATE[sa] == LINEAGE_BY_STATE[sb]),
                    "crosswalk_match": str(fwd.get(sa) == sb),
                }
            )
    rows.sort(key=lambda r: (r["source_state"], -float(r["transported_mass"])))
    _write_tsv_atomic(
        out_dir / "intermediates" / "state_transition.tsv", rows, TRANSITION_TSV_FIELDS
    )

    total = float(transport.sum())
    row_mass = transport.sum(axis=1)
    col_mass = transport.sum(axis=0)
    summary = {
        "schema": "ve.t1.s2-coupling-summary.v1",
        "atom": ATOM,
        "seed": SEED,
        "predeclared": {
            "lineage_penalty": LINEAGE_PENALTY,
            "cost_normalisation": OT_COST_NORMALISATION,
            "epsilon": OT_EPSILON,
            "tau_a": OT_TAU_A,
            "tau_b": OT_TAU_B,
            "latent": "T1-PRE 74-marker program space, per-marker z-scored over the union centroids",
        },
        "solver": solve_meta,
        "cost_diagnostics": cost_diag,
        "mass": {
            "total_transported": total,
            "source_marginal_mass": 1.0,
            "target_marginal_mass": 1.0,
            "row_mass_min": float(row_mass.min()),
            "row_mass_max": float(row_mass.max()),
            "col_mass_min": float(col_mass.min()),
            "col_mass_max": float(col_mass.max()),
            "note": (
                "unbalanced Sinkhorn (tau<1): row/col sums need not equal the "
                "marginals; the deficit is the depletion/growth signal"
            ),
        },
        "n_source_states": len(states_a),
        "n_target_states": len(states_b),
        "n_nonzero_transitions": len(rows),
        "crosswalk_consistency": {
            "resolved_pairs": len(fwd),
            "mass_on_crosswalk_pairs": float(
                sum(
                    transport[i, states_b.index(fwd[sa])]
                    for i, sa in enumerate(states_a)
                    if sa in fwd
                )
            ),
        },
        "inputs": pre["input_hashes"],
        "tool_env": os.environ.get("VE_T1_OT_ENV", "ve-t1-ot"),
    }
    _write_json_atomic(out_dir / "metrics" / "coupling_summary.json", summary)
    import importlib.metadata as _imd

    ot_env_versions = {
        "schema": "ve.t1.s2-ot-env-versions.v1",
        "atom": ATOM,
        "interpreter": sys.executable,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": {
            pkg: _safe_version(_imd, pkg)
            for pkg in ("moscot", "ott-jax", "jax", "jaxlib", "POT", "anndata", "numpy", "scipy")
        },
    }
    _write_json_atomic(out_dir / "metrics" / "ot_env_versions.json", ot_env_versions)
    meta = {
        "tool": solve_meta["backend"],
        "tool_version": solve_meta.get("moscot_version") or solve_meta.get("pot_version"),
        "epsilon": OT_EPSILON,
        "tau_a": OT_TAU_A,
        "tau_b": OT_TAU_B,
        "mass_mode": "unbalanced",
        "cost": (
            "median-normalised program distance (74-marker z-space) "
            "+ lineage mismatch penalty 8.0"
        ),
        "cost_normalisation": OT_COST_NORMALISATION,
        "inputs": pre["input_hashes"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _write_json_atomic(out_dir / "intermediates" / "coupling_meta.json", meta)
    return {
        "step": "couple",
        "backend": solve_meta["backend"],
        "converged": solve_meta.get("converged"),
        "total_transported": total,
        "n_nonzero_transitions": len(rows),
        "mass_on_crosswalk_pairs": summary["crosswalk_consistency"]["mass_on_crosswalk_pairs"],
    }


# ---------------------------------------------------------------------------
# Mass forecast + mean program (ve-core)
# ---------------------------------------------------------------------------


def _load_coupling(out_dir: Path) -> dict[str, Any]:
    path = Path(out_dir) / "intermediates" / "coupling.npz"
    if not path.is_file():
        raise FileNotFoundError(f"coupling missing: {path}; run `couple` first")
    npz = np.load(path, allow_pickle=False)
    csr = sparse.csr_matrix(
        (npz["data"], npz["indices"], npz["indptr"]), shape=tuple(npz["shape"])
    )
    return {
        "transport": np.asarray(csr.todense(), dtype=np.float64),
        "source_states": [str(s) for s in npz["source_states"].tolist()],
        "target_states": [str(s) for s in npz["target_states"].tolist()],
        "source_marginal": npz["source_marginal"],
        "target_marginal": npz["target_marginal"],
        "target_pred_share": npz["target_pred_share"],
        "sha256": sha256_file(path),
    }


def shrink_growth(
    growth_raw: float,
    *,
    rho: float = GROWTH_RHO,
    clip_lo: float = GROWTH_CLIP_LO,
    clip_hi: float = GROWTH_CLIP_HI,
) -> float:
    """Geometric shrinkage of a growth factor towards 1 after clipping."""
    if not np.isfinite(growth_raw) or growth_raw <= 0:
        raise ValueError(f"growth_raw must be positive and finite, got {growth_raw}")
    clipped = min(max(growth_raw, clip_lo), clip_hi)
    return float(np.exp(rho * np.log(clipped)))


def compute_state_mass(
    pre: Mapping[str, Any], coupling: Mapping[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Transport-derived growth -> pre-declared shrinkage -> E10.5 probabilities.

    Only probability mass is forecast, never absolute embryo cell counts.  The
    pseudo-holdout board reuses the measured regime (no extrapolation
    shrinkage): the transport-predicted E9.5 shares restricted to resolved
    targets, renormalised.
    """
    vocab = {row["fine_state"]: row for row in pre["vocabulary"]}
    rev = reverse_matches(pre["crosswalk"])
    states_e95 = coupling["target_states"]
    pred_share = coupling["target_pred_share"]
    share_e85 = {
        row["fine_state"]: int(row["n_cells_e85"]) / sum(
            int(r["n_cells_e85"]) for r in pre["vocabulary"]
        )
        for row in pre["vocabulary"]
    }
    share_e95 = {
        row["fine_state"]: int(row["n_cells_e95"]) / sum(
            int(r["n_cells_e95"]) for r in pre["vocabulary"]
        )
        for row in pre["vocabulary"]
    }
    pred = {state: float(pred_share[j]) for j, state in enumerate(states_e95)}

    growth: dict[str, dict[str, Any]] = {}
    for state in states_e95:
        lineage = LINEAGE_BY_STATE[state]
        if state in rev:
            source = rev[state]
            denominator = share_e85[source]
            growth[state] = {
                "growth_raw": pred[state] / max(denominator, 1e-12),
                "rule": "transport_over_matched_source",
                "matched_source": source,
            }
        else:
            resolved_in_lineage = [
                s for s in states_e95 if s in rev and LINEAGE_BY_STATE[s] == lineage
            ]
            if resolved_in_lineage:
                numerator = sum(pred[s] for s in resolved_in_lineage)
                denominator = sum(share_e85[rev[s]] for s in resolved_in_lineage)
                growth[state] = {
                    "growth_raw": numerator / max(denominator, 1e-12),
                    "rule": "lineage_mean_transport",
                    "matched_source": None,
                }
            else:
                growth[state] = {
                    "growth_raw": 1.0,
                    "rule": "no_lineage_evidence_flat",
                    "matched_source": None,
                }

    n_cells_e95 = {row["fine_state"]: int(row["n_cells_e95"]) for row in pre["vocabulary"]}
    rows: list[dict[str, Any]] = []
    raw_forecast: dict[str, float] = {}
    for state in sorted(states_e95):
        small = n_cells_e95[state] < SMALL_STATE_MIN_CELLS
        rho = SMALL_STATE_RHO if small else GROWTH_RHO
        g_shrunk = shrink_growth(growth[state]["growth_raw"], rho=rho)
        raw = share_e95[state] * g_shrunk
        if small:
            raw = min(raw, SMALL_STATE_SHARE_CAP_MULT * share_e95[state])
        raw_forecast[state] = raw
        growth[state]["growth_shrunk"] = g_shrunk
        growth[state]["small_state"] = small
    total = sum(raw_forecast.values())
    if total <= 0:
        raise RuntimeError("forecast mass sums to zero")
    for state in sorted(states_e95):
        shrunk = raw_forecast[state] / total
        rows.append(
            {
                "board": BOARD,
                "target_stage": BOARD_TARGET_STAGE,
                "state": state,
                "lineage": LINEAGE_BY_STATE[state],
                "parent_probability": f"{share_e95[state]:.6f}",
                "raw_forecast": f"{raw_forecast[state]:.6f}",
                "shrunk_probability": f"{shrunk:.6f}",
                "uncertainty": (
                    "small_state" if growth[state]["small_state"]
                    else "resolved" if growth[state]["rule"] == "transport_over_matched_source"
                    else "lineage_fallback"
                ),
                "evidence": growth[state]["rule"],
            }
        )

    holdout_rows: list[dict[str, Any]] = []
    resolved_targets = [s for s in states_e95 if s in rev]
    holdout_total = sum(pred[s] for s in resolved_targets)
    for state in sorted(resolved_targets):
        rows.append(
            {
                "board": "T1:pseudo_holdout",
                "target_stage": TARGET_STAGE,
                "state": state,
                "lineage": LINEAGE_BY_STATE[state],
                "parent_probability": f"{share_e85[rev[state]]:.6f}",
                "raw_forecast": f"{pred[state]:.6f}",
                "shrunk_probability": f"{pred[state] / holdout_total:.6f}",
                "uncertainty": "resolved" if state in vocab else "resolved",
                "evidence": "transport_pred_share_resolved_only_renormalised",
            }
        )
        holdout_rows.append(state)
    summary = {
        "growth": growth,
        "holdout_states": holdout_rows,
        "holdout_mass_total_before_renorm": holdout_total,
        "n_small_states": sum(1 for g in growth.values() if g["small_state"]),
        "small_states": sorted(s for s, g in growth.items() if g["small_state"]),
        "mass_sum_check": sum(raw_forecast.values()) / total,
    }
    return rows, summary


def compute_state_gene_delta(pre: Mapping[str, Any]) -> dict[str, Any]:
    """State-specific pseudobulk mean program, saved decoupled from coupling.

    Measured E8.5->E9.5 deltas for crosswalk-resolved states; UNRESOLVED states
    shrink to the lineage mean of resolved deltas (E8.5-cell-count weighted),
    then to the global delta.  The E10.5 board applies the pre-declared
    extrapolation shrinkage RHO_EXTRAP (independent time regime: the measured
    slope is never extended unshrunk).  No new states are created.
    """
    states_e85 = pre["states_e85"]
    states_e95 = pre["states_e95"]
    cent_e85 = {s: pre["centroids_e85_full"][i] for i, s in enumerate(states_e85)}
    cent_e95 = {s: pre["centroids_e95_full"][i] for i, s in enumerate(states_e95)}
    counts_e85 = {row["fine_state"]: int(row["n_cells_e85"]) for row in pre["vocabulary"]}
    counts_e95 = {row["fine_state"]: int(row["n_cells_e95"]) for row in pre["vocabulary"]}
    fwd = forward_matches(pre["crosswalk"])
    rev = reverse_matches(pre["crosswalk"])

    global_delta = (
        np.average(
            np.vstack([cent_e95[s] for s in states_e95]),
            axis=0,
            weights=np.asarray([counts_e95[s] for s in states_e95], dtype=np.float64),
        )
        - np.average(
            np.vstack([cent_e85[s] for s in states_e85]),
            axis=0,
            weights=np.asarray([counts_e85[s] for s in states_e85], dtype=np.float64),
        )
    ).astype(np.float32)

    def lineage_mean_delta(
        state: str, deltas: Mapping[str, np.ndarray], match: Mapping[str, str]
    ) -> np.ndarray | None:
        lineage = LINEAGE_BY_STATE[state]
        members = [
            s for s in deltas if LINEAGE_BY_STATE[s] == lineage and s in match
        ]
        if not members:
            return None
        weights = np.asarray([counts_e85[match[s]] for s in members], dtype=np.float64)
        stacked = np.vstack([deltas[s] for s in members])
        return np.average(stacked, axis=0, weights=weights).astype(np.float32)

    delta_e95: dict[str, np.ndarray] = {}
    rule_e95: dict[str, str] = {}
    for state in states_e95:
        if state in rev:
            delta_e95[state] = (cent_e95[state] - cent_e85[rev[state]]).astype(np.float32)
            rule_e95[state] = "crosswalk_measured"
    for state in states_e95:
        if state in delta_e95:
            continue
        fallback = lineage_mean_delta(state, delta_e95, rev)
        if fallback is not None:
            delta_e95[state] = fallback
            rule_e95[state] = "lineage_mean_shrinkage"
        else:
            delta_e95[state] = global_delta.copy()
            rule_e95[state] = "global_fallback"

    delta_holdout: dict[str, np.ndarray] = {}
    rule_holdout: dict[str, str] = {}
    for state in states_e85:
        if state in fwd:
            delta_holdout[state] = (cent_e95[fwd[state]] - cent_e85[state]).astype(np.float32)
            rule_holdout[state] = "crosswalk_measured"
    for state in states_e85:
        if state in delta_holdout:
            continue
        fallback = lineage_mean_delta(state, delta_holdout, fwd)
        if fallback is not None:
            delta_holdout[state] = fallback
            rule_holdout[state] = "lineage_mean_shrinkage"
        else:
            delta_holdout[state] = global_delta.copy()
            rule_holdout[state] = "global_fallback"

    return {
        "states_e95": states_e95,
        "delta_measured_e95": np.vstack([delta_e95[s] for s in states_e95]),
        "delta_e105": np.vstack([delta_e95[s] for s in states_e95]) * np.float32(RHO_EXTRAP),
        "rule_e95": [rule_e95[s] for s in states_e95],
        "states_e85": states_e85,
        "delta_holdout_e85": np.vstack([delta_holdout[s] for s in states_e85]),
        "rule_e85": [rule_holdout[s] for s in states_e85],
        "global_delta": global_delta,
        "rho_extrap": RHO_EXTRAP,
        "rule_counts_e95": {r: sum(1 for x in rule_e95.values() if x == r) for r in set(rule_e95.values())},
        "rule_counts_e85": {r: sum(1 for x in rule_holdout.values() if x == r) for r in set(rule_holdout.values())},
    }


def command_forecast(out_dir: Path) -> dict[str, Any]:
    out_dir = Path(out_dir)
    pre = load_pre_intermediates()
    coupling = _load_coupling(out_dir)
    rows, mass_summary = compute_state_mass(pre, coupling)
    _write_tsv_atomic(out_dir / "intermediates" / "state_mass.tsv", rows, STATE_MASS_TSV_FIELDS)

    deltas = compute_state_gene_delta(pre)
    npz_tmp = out_dir / "intermediates" / "state_gene_delta.tmp.npz"
    np.savez(
        npz_tmp,
        var_names=np.asarray(pre["var_names"]),
        states_e95=np.asarray(deltas["states_e95"]),
        delta_measured_e95=deltas["delta_measured_e95"],
        delta_e105=deltas["delta_e105"],
        rule_e95=np.asarray(deltas["rule_e95"]),
        states_e85=np.asarray(deltas["states_e85"]),
        delta_holdout_e85=deltas["delta_holdout_e85"],
        rule_e85=np.asarray(deltas["rule_e85"]),
        global_delta=deltas["global_delta"],
        rho_extrap=np.asarray(deltas["rho_extrap"], dtype=np.float64),
    )
    npz_tmp.replace(out_dir / "intermediates" / "state_gene_delta.npz")

    summary = {
        "schema": "ve.t1.s2-mass-forecast.v1",
        "atom": ATOM,
        "seed": SEED,
        "predeclared": {
            "growth_rho": GROWTH_RHO,
            "growth_clip": [GROWTH_CLIP_LO, GROWTH_CLIP_HI],
            "small_state_min_cells": SMALL_STATE_MIN_CELLS,
            "small_state_rho": SMALL_STATE_RHO,
            "small_state_share_cap_mult": SMALL_STATE_SHARE_CAP_MULT,
            "rho_extrap": RHO_EXTRAP,
        },
        "mass": {
            "board": BOARD,
            "target_stage": BOARD_TARGET_STAGE,
            "n_states": len(deltas["states_e95"]),
            "small_states": mass_summary["small_states"],
            "shrunk_probability_sum": mass_summary["mass_sum_check"],
            "top_states_by_shrunk_probability": sorted(
                (
                    (row["state"], float(row["shrunk_probability"]))
                    for row in rows
                    if row["board"] == BOARD
                ),
                key=lambda kv: -kv[1],
            )[:5],
            "growth_raw_range": [
                min(g["growth_raw"] for g in mass_summary["growth"].values()),
                max(g["growth_raw"] for g in mass_summary["growth"].values()),
            ],
            "growth_detail": {
                state: {
                    "growth_raw": g["growth_raw"],
                    "growth_shrunk": g["growth_shrunk"],
                    "rule": g["rule"],
                    "small_state": g["small_state"],
                }
                for state, g in sorted(mass_summary["growth"].items())
            },
        },
        "mean_program": {
            "rule_counts_e95": deltas["rule_counts_e95"],
            "rule_counts_e85": deltas["rule_counts_e85"],
            "rho_extrap": RHO_EXTRAP,
            "decoupled_from_coupling": True,
            "no_new_states": True,
        },
        "inputs": {**pre["input_hashes"], "coupling_npz": coupling["sha256"]},
    }
    _write_json_atomic(out_dir / "metrics" / "mass_forecast.json", summary)
    return {
        "step": "forecast",
        "small_states": mass_summary["small_states"],
        "top_states": summary["mass"]["top_states_by_shrunk_probability"],
        "rule_counts_e95": deltas["rule_counts_e95"],
    }


# ---------------------------------------------------------------------------
# Source-only pseudo-holdout (ve-core): parent-method arm, L1 arm, alpha
# ---------------------------------------------------------------------------


def _load_stage_dense(path: Path) -> ad.AnnData:
    adata = ad.read_h5ad(path)
    if sparse.issparse(adata.X):
        adata.X = adata.X.toarray()
    adata.X = np.asarray(adata.X, dtype=np.float32)
    return adata


def pseudo_parent_indices(labels: np.ndarray, n_cells: int = N_CELLS) -> np.ndarray:
    """The single shared E8.5 pseudo-parent sample (all holdout arms reuse it)."""
    counts = state_counts(labels)
    shares = {state: n / float(sum(counts.values())) for state, n in counts.items()}
    return select_indices_by_shares(
        labels, shares, n_cells=n_cells, seed=_derived_seed("pseudoholdout", "base")
    )


def holdout_counts_from_mass(
    mass_rows: list[dict[str, str]], n_cells: int = N_CELLS
) -> dict[str, int]:
    """Largest-remainder integer counts for the holdout forecast composition."""
    probs = {
        row["state"]: float(row["shrunk_probability"])
        for row in mass_rows
        if row["board"] == "T1:pseudo_holdout"
    }
    return _largest_remainder_counts(probs, n_cells)


def _largest_remainder_counts(probs: Mapping[str, float], n_cells: int) -> dict[str, int]:
    """Deterministic largest-remainder rounding, lexical tie-break; sums exactly."""
    total = sum(probs.values())
    if total <= 0:
        raise ValueError("probabilities sum to zero")
    states = sorted(probs)
    exact = {s: probs[s] / total * n_cells for s in states}
    counts = {s: int(np.floor(exact[s])) for s in states}
    remainder = n_cells - sum(counts.values())
    order = sorted(states, key=lambda s: (-(exact[s] - counts[s]), s))
    for s in order:
        if remainder <= 0:
            break
        counts[s] += 1
        remainder -= 1
    if sum(counts.values()) != n_cells:
        raise AssertionError("largest-remainder allocation failed")
    return counts


def draw_cells_from_pools(
    pools: Mapping[str, np.ndarray],
    demand: Mapping[str, int],
    *,
    seed_parts: Iterable[Any],
) -> dict[str, np.ndarray]:
    """Draw source rows per target state: without replacement first, then with
    replacement for the overflow (small-state growth).  Deterministic seeds."""
    draws: dict[str, np.ndarray] = {}
    for state in sorted(demand):
        n = int(demand[state])
        if n <= 0:
            continue
        pool = np.asarray(pools.get(state, np.asarray([], dtype=np.int64)))
        if pool.size == 0:
            raise ValueError(f"no source cells available for demanded state {state!r}")
        rng = np.random.default_rng(_derived_seed("sample", *seed_parts, state))
        if n <= pool.size:
            draws[state] = np.sort(rng.choice(pool, size=n, replace=False))
        else:
            extra = np.sort(rng.choice(pool, size=n - pool.size, replace=True))
            draws[state] = np.concatenate([np.sort(pool), extra])
    return draws


def resolve_alpha(
    base_rows: np.ndarray, delta_rows: np.ndarray, target_pseudobulk: np.ndarray
) -> dict[str, Any]:
    """One analytic source-only alpha: prediction = parent + alpha * structured_delta.

    Closed-form least squares on the full-panel pseudobulk, clipped to the
    pre-declared range; the frozen value is then used for every board and lane.
    """
    base_pb = np.asarray(base_rows, dtype=np.float64).mean(axis=0)
    delta_pb = np.asarray(delta_rows, dtype=np.float64).mean(axis=0)
    target_pb = np.asarray(target_pseudobulk, dtype=np.float64)
    denom = float(delta_pb @ delta_pb)
    if denom <= 0:
        raise ValueError("structured delta pseudobulk is zero; alpha undefined")
    raw = float(((target_pb - base_pb) @ delta_pb) / denom)
    frozen = min(max(raw, ALPHA_CLIP_LO), ALPHA_CLIP_HI)
    return {
        "alpha_raw": raw,
        "alpha_frozen": frozen,
        "clipped": raw != frozen,
        "clip_range": [ALPHA_CLIP_LO, ALPHA_CLIP_HI],
        "objective": "argmin_alpha ||pb_target - (pb_base + alpha * pb_delta)||^2 (closed form)",
        "n_cells": int(base_rows.shape[0]),
        "delta_pb_l2": float(np.sqrt(denom)),
    }


def _official_t1_metrics():
    """Load the locked veckit T1 metric functions exactly like score_h5ad.py."""
    sys.path.insert(0, str(ROOT / "third_party" / "veckit"))
    import score_h5ad

    return score_h5ad._load_task_metrics("T1")


def holdout_metric_panel(
    pred_X: np.ndarray,
    pred_ct: np.ndarray,
    true_X: np.ndarray,
    true_ct: np.ndarray,
    ref_X: np.ndarray,
    *,
    probe: Any,
) -> dict[str, Any]:
    """Locked scorer metric panel computed in-process (same code, same seed).

    DES = de_score, DCS = de_direction, MMD = mmd_u, CSS = composition_JSD; the
    remaining constraint metrics are reported for context.  Source-only
    pseudo-holdout evidence -- never a leaderboard preview.
    """
    _metrics, metrics_v2 = _official_t1_metrics()
    return metrics_v2.score_task1_v2(
        np.asarray(pred_X, dtype=np.float32),
        np.asarray(pred_ct).astype(str),
        np.asarray(true_X, dtype=np.float32),
        np.asarray(true_ct).astype(str),
        np.asarray(ref_X, dtype=np.float32),
        probe=probe,
        seed=SEED,
    )


def command_pseudoholdout(out_dir: Path) -> dict[str, Any]:
    """One E8.5->E9.5 source-only pseudo-holdout: parent / L1 arms + alpha.

    The E9.5 training stage is the holdout *target*: the check validates the
    machinery and freezes alpha; per batch3 rules it is not a generalization
    estimate and never feeds parameter search.
    """
    out_dir = Path(out_dir)
    holdout_dir = out_dir / "intermediates" / "pseudoholdout"
    pre = load_pre_intermediates()
    mass_rows = _read_tsv(out_dir / "intermediates" / "state_mass.tsv")
    delta_npz = np.load(out_dir / "intermediates" / "state_gene_delta.npz", allow_pickle=False)
    states_e85 = [str(s) for s in delta_npz["states_e85"].tolist()]
    states_e95 = [str(s) for s in delta_npz["states_e95"].tolist()]
    delta_holdout = {
        s: delta_npz["delta_holdout_e85"][i] for i, s in enumerate(states_e85)
    }

    source = _load_stage_dense(SOURCE_PATH)
    labels_e85 = source.obs["celltype"].astype(str).to_numpy()
    base_idx = pseudo_parent_indices(labels_e85)
    base = source[base_idx].copy()
    base_labels = labels_e85[base_idx]
    base_X = np.asarray(base.X, dtype=np.float32)

    fwd = forward_matches(pre["crosswalk"])
    shared_exact = {
        row["fine_state"]
        for row in pre["crosswalk"]
        if row["direction"] == "e85_to_e95" and row["match_rule"] == "SHARED_EXACT"
    }

    # ---- parent-method arm: strict v0004 recipe (name-matched per-type delta,
    # unmapped -> zero shift, source composition unchanged)
    parent_arm = base.copy()
    pred_parent = base_X.copy()
    for state in sorted(np.unique(base_labels).tolist()):
        mask = base_labels == state
        if state in shared_exact:
            i85 = states_e85.index(state)
            j95 = states_e95.index(state)
            delta = (
                pre["centroids_e95_full"][j95] - pre["centroids_e85_full"][i85]
            ).astype(np.float32)
            pred_parent[mask] += delta
    np.clip(pred_parent, 0, None, out=pred_parent)
    parent_arm.X = pred_parent
    parent_arm.obsm.clear()
    parent_arm_path = holdout_dir / "parent_method.h5ad"
    _write_h5ad_atomic(parent_arm, parent_arm_path)

    # ---- L1 arm: coupling forecast composition + crosswalk mean program +
    # empirical residual replay of the same pseudo-parent rows
    rev = reverse_matches(pre["crosswalk"])
    donor_by_target = {target: src for target, src in rev.items()}
    holdout_counts = holdout_counts_from_mass(mass_rows)
    pools: dict[str, np.ndarray] = {}
    for target, src in donor_by_target.items():
        pools[target] = np.flatnonzero(base_labels == src)
    draws = draw_cells_from_pools(pools, holdout_counts, seed_parts=("holdout", "L1"))

    src_rows: list[int] = []
    assigned: list[str] = []
    for target in sorted(draws):
        for row in draws[target]:
            src_rows.append(int(row))
            assigned.append(target)
    src_rows_arr = np.asarray(src_rows, dtype=np.int64)
    assigned_arr = np.asarray(assigned)
    donor_labels = base_labels[src_rows_arr]

    l1_base = base_X[src_rows_arr].copy()
    delta_rows = np.vstack([delta_holdout[d] for d in donor_labels]).astype(np.float32)

    target_truth = _load_stage_dense(TARGET_PATH)
    true_X = np.asarray(target_truth.X, dtype=np.float32)
    true_ct = target_truth.obs["celltype"].astype(str).to_numpy()
    truth_pb = true_X.mean(axis=0)

    alpha_record = resolve_alpha(l1_base, delta_rows, truth_pb)
    alpha = alpha_record["alpha_frozen"]

    pred_l1 = l1_base + np.float32(alpha) * delta_rows
    np.clip(pred_l1, 0, None, out=pred_l1)
    l1_arm = base.copy()
    l1_arm.X = pred_l1
    l1_arm.obsm.clear()
    l1_arm.obs["celltype"] = assigned_arr
    l1_arm.obs["assigned_state"] = assigned_arr
    l1_arm.obs["residual_source_index"] = src_rows_arr
    l1_arm.obs["residual_source_state"] = donor_labels
    l1_arm.obs_names = [f"holdout_l1_{k}" for k in range(l1_arm.n_obs)]
    l1_arm_path = holdout_dir / "L1_EMPIRICAL_RESIDUAL.h5ad"
    _write_h5ad_atomic(l1_arm, l1_arm_path)

    # ---- local metric mirror of the locked scorer panel (DES/DCS/MMD/CSS)
    metrics, _ = _official_t1_metrics()
    probe = metrics.train_frozen_probe(true_X, true_ct)
    ref_X = np.asarray(source.X, dtype=np.float32)
    panels = {
        "parent": holdout_metric_panel(
            pred_parent, base_labels, true_X, true_ct, ref_X, probe=probe
        ),
        "L1_EMPIRICAL_RESIDUAL": holdout_metric_panel(
            pred_l1, assigned_arr, true_X, true_ct, ref_X, probe=probe
        ),
    }
    panels["L1_EMPIRICAL_RESIDUAL"]["_alpha_applied"] = alpha

    # ---- L2 arm (only when the scDesign3 decoder parameters exist): identical
    # coupling/mass/mean/alpha as L1; only the module-gene decoder differs
    l2_path = None
    params_path = out_dir / "intermediates" / "l2_decoder_params.json"
    if params_path.is_file():
        decoder_params = json.loads(params_path.read_text(encoding="utf-8"))
        modules = _module_gene_index(
            out_dir, [str(g) for g in source.var_names]
        )
        pred_l2, l2_note = apply_l2_module_decoder(
            pred_l1, assigned_arr, decoder_params, modules,
            stage="e85", seed_parts=("holdout", "L2"),
        )
        l2_arm = l1_arm.copy()
        l2_arm.X = pred_l2
        l2_arm.obs_names = [f"holdout_l2_{k}" for k in range(l2_arm.n_obs)]
        l2_path = holdout_dir / "L2_MODULE_SCDESIGN3.h5ad"
        _write_h5ad_atomic(l2_arm, l2_path)
        panels["L2_MODULE_SCDESIGN3"] = holdout_metric_panel(
            pred_l2, assigned_arr, true_X, true_ct, ref_X, probe=probe
        )
        panels["L2_MODULE_SCDESIGN3"]["_alpha_applied"] = alpha
        panels["L2_MODULE_SCDESIGN3"]["_decoder_note"] = l2_note

    record = {
        "schema": "ve.t1.s2-pseudoholdout.v1",
        "atom": ATOM,
        "seed": SEED,
        "alpha": alpha_record,
        "alpha_note": (
            "single analytic source-only resolution on the pseudobulk of the L1 "
            "holdout construction; frozen afterwards for every board and lane"
        ),
        "holdout_construction": {
            "base_rows": "E8.5 pseudo-parent (5118 cells, observed E8.5 composition, shared across arms)",
            "parent_arm": "strict v0004 recipe analog: name-matched per-type delta, unmapped zero shift",
            "l1_arm": "coupling forecast composition (resolved targets) + crosswalk mean program + residual replay",
            "unresolved_target_states_dropped": sorted(
                set(states_e95) - set(donor_by_target)
            ),
            "p1_note": "state birth is not modeled (P1); unresolved E9.5-only states receive no holdout cells",
        },
        "metrics": panels,
        "artifacts": {
            "parent_method_h5ad": {
                "path": str(parent_arm_path.relative_to(ROOT)),
                "sha256": sha256_file(parent_arm_path),
            },
            "l1_h5ad": {
                "path": str(l1_arm_path.relative_to(ROOT)),
                "sha256": sha256_file(l1_arm_path),
            },
            "l2_h5ad": (
                {
                    "path": str(l2_path.relative_to(ROOT)),
                    "sha256": sha256_file(l2_path),
                }
                if l2_path is not None
                else None
            ),
        },
        "interpretation": (
            "source-only chain check with E9.5 as the holdout target; E9.5 is a "
            "training stage, so these numbers validate the machinery and freeze "
            "alpha only -- not a leaderboard preview, not a model-improvement claim"
        ),
    }
    _write_json_atomic(out_dir / "metrics" / "alpha_calibration.json", record)
    return {
        "step": "pseudoholdout",
        "alpha_frozen": alpha,
        "alpha_raw": alpha_record["alpha_raw"],
        "parent_de_score": panels["parent"]["de_score"],
        "l1_de_score": panels["L1_EMPIRICAL_RESIDUAL"]["de_score"],
        "parent_mmd_u": panels["parent"]["mmd_u"],
        "l1_mmd_u": panels["L1_EMPIRICAL_RESIDUAL"]["mmd_u"],
    }


def _write_h5ad_atomic(adata: ad.AnnData, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp.h5ad")
    adata.write_h5ad(temporary)
    temporary.replace(path)


# ---------------------------------------------------------------------------
# Formal generation (ve-core): L1 empirical residual replay, L2 module decoder
# ---------------------------------------------------------------------------

L2_MIN_FIT_CELLS = 20  # pre-declared fit floor; smaller states keep parent residual


def _load_delta_npz(out_dir: Path) -> dict[str, Any]:
    path = Path(out_dir) / "intermediates" / "state_gene_delta.npz"
    if not path.is_file():
        raise FileNotFoundError(f"state_gene_delta.npz missing: {path}; run `forecast` first")
    npz = np.load(path, allow_pickle=False)
    return {
        "var_names": [str(g) for g in npz["var_names"].tolist()],
        "states_e95": [str(s) for s in npz["states_e95"].tolist()],
        "delta_measured_e95": npz["delta_measured_e95"],
        "delta_e105": npz["delta_e105"],
        "rule_e95": [str(r) for r in npz["rule_e95"].tolist()],
        "states_e85": [str(s) for s in npz["states_e85"].tolist()],
        "delta_holdout_e85": npz["delta_holdout_e85"],
        "rule_e85": [str(r) for r in npz["rule_e85"].tolist()],
        "global_delta": npz["global_delta"],
        "sha256": sha256_file(path),
    }


def _load_mass_rows(out_dir: Path) -> list[dict[str, str]]:
    path = Path(out_dir) / "intermediates" / "state_mass.tsv"
    if not path.is_file():
        raise FileNotFoundError(f"state_mass.tsv missing: {path}; run `forecast` first")
    return _read_tsv(path)


def _frozen_alpha(out_dir: Path) -> float:
    path = Path(out_dir) / "metrics" / "alpha_calibration.json"
    if not path.is_file():
        raise FileNotFoundError(
            f"alpha calibration missing: {path}; run `pseudoholdout` before `generate`"
        )
    record = json.loads(path.read_text(encoding="utf-8"))
    return float(record["alpha"]["alpha_frozen"])


def formal_counts(mass_rows: list[dict[str, str]], n_cells: int = N_CELLS) -> dict[str, int]:
    probs = {
        row["state"]: float(row["shrunk_probability"])
        for row in mass_rows
        if row["board"] == BOARD
    }
    return _largest_remainder_counts(probs, n_cells)


def build_formal_sampling_plan(
    parent_labels: np.ndarray,
    mass_rows: list[dict[str, str]],
    growth_detail: Mapping[str, Any] | None = None,
) -> tuple[dict[str, np.ndarray], list[dict[str, Any]]]:
    """Lane-independent plan: forecast counts vs parent supply, fixed seeds."""
    counts = formal_counts(mass_rows)
    growth = {row["state"]: row for row in mass_rows if row["board"] == BOARD}
    detail = dict(growth_detail or {})
    pools = {
        state: np.flatnonzero(parent_labels == state)
        for state in sorted(np.unique(parent_labels).tolist())
    }
    draws = draw_cells_from_pools(pools, counts, seed_parts=("formal", "shared_plan"))
    total_parent = float(len(parent_labels))
    plan_rows: list[dict[str, Any]] = []
    for state in sorted(counts):
        supply = int(len(pools.get(state, [])))
        drawn = draws.get(state, np.asarray([], dtype=np.int64))
        n_unique = int(np.unique(drawn).size)
        info = growth.get(state, {})
        gd = detail.get(state, {})
        plan_rows.append(
            {
                "board": BOARD,
                "state": state,
                "forecast_count": int(counts[state]),
                "parent_supply": supply,
                "n_unique": n_unique,
                "n_duplicated": int(drawn.size - n_unique),
                "parent_share": f"{supply / total_parent:.6f}",
                "forecast_share": info.get("shrunk_probability", ""),
                "growth_raw": f"{gd.get('growth_raw', ''):.6f}" if gd else "",
                "growth_shrunk": f"{gd.get('growth_shrunk', ''):.6f}" if gd else "",
                "growth_rule": info.get("evidence", ""),
            }
        )
    return draws, plan_rows


def _unique_obs_names(source_names: list[str]) -> list[str]:
    """Deterministic unique names: single-use rows keep the parent name."""
    counts: dict[str, int] = {}
    for name in source_names:
        counts[name] = counts.get(name, 0) + 1
    seen: dict[str, int] = {}
    out: list[str] = []
    for name in source_names:
        if counts[name] == 1:
            out.append(name)
        else:
            seen[name] = seen.get(name, 0) + 1
            out.append(f"{name}__rep{seen[name]}")
    if len(set(out)) != len(out):
        raise AssertionError("obs_names uniqueness construction failed")
    return out


def _module_gene_index(out_dir: Path, var_names: list[str]) -> dict[str, list[int]]:
    """Frozen module definition -> column indices (empty when L2 never fitted)."""
    path = Path(out_dir) / "intermediates" / "module_definition.tsv"
    if not path.is_file():
        return {}
    rows = _read_tsv(path)
    index = {gene: i for i, gene in enumerate(var_names)}
    modules: dict[str, list[int]] = {}
    for row in rows:
        if row.get("present_in_panel", "True") != "True":
            continue
        gene = row["gene"]
        if gene in index:
            modules.setdefault(row["module_id"], []).append(index[gene])
    return {m: sorted(cols) for m, cols in sorted(modules.items())}


def apply_l2_module_decoder(
    base: np.ndarray,
    assigned: np.ndarray,
    decoder_params: Mapping[str, Any],
    modules: Mapping[str, list[int]],
    *,
    stage: str,
    seed_parts: Iterable[Any],
) -> tuple[np.ndarray, dict[str, Any]]:
    """Replace module-gene values with copula samples anchored to the state mean.

    scDesign3 (R) fits the per-state marginals and per-module gaussian copulas
    and exports standard simulator parameters; the core samples here.  The
    sampled module mean is anchored exactly at ``mean_target`` supplied in
    ``base`` (already alpha-shifted), so coupling/mass/mean are identical to
    L1; only the residual covariance structure of module genes differs.
    Non-module genes and unfit small states keep the L1 values unchanged.
    """
    out = base.copy()
    fitted = decoder_params.get(f"fits_{stage}", {})
    replaced = 0
    fallback_states: list[str] = []
    for state in sorted(np.unique(assigned).tolist()):
        mask = np.flatnonzero(assigned == state)
        fit = fitted.get(state)
        if fit is None:
            fallback_states.append(state)
            continue
        rng = np.random.default_rng(_derived_seed("l2", *seed_parts, state))
        for module_id, entry in sorted(fit["modules"].items()):
            cols = modules.get(module_id)
            if not cols:
                continue
            corr = np.asarray(entry["corr"], dtype=np.float64)
            mu = np.asarray(entry["mu"], dtype=np.float64)
            sigma = np.asarray(entry["sigma"], dtype=np.float64)
            if corr.shape != (len(cols), len(cols)):
                raise ValueError(f"copula shape mismatch for {state}/{module_id}")
            # exact current module mean of the base matrix (already alpha-shifted)
            anchor = base[mask][:, cols].mean(axis=0)
            z = rng.multivariate_normal(np.zeros(len(cols)), corr, size=len(mask))
            sample = mu + sigma * z
            sample = sample - sample.mean(axis=0) + anchor  # exact mean anchoring
            out[np.ix_(mask, cols)] = sample.astype(np.float32)
            replaced += int(len(mask) * len(cols))
    np.clip(out, 0, None, out=out)
    return out, {
        "module_cells_values_replaced": replaced,
        "fallback_states_keep_parent_residual": fallback_states,
    }


def _candidate_uns(
    lane: str,
    alpha: float,
    plan_rows: list[dict[str, Any]],
    input_hashes: Mapping[str, str],
) -> dict[str, Any]:
    return {
        "ve_contract": {"schema": "ve.contract.v1", "normalization": NORMALIZATION},
        "ve_t1_s2_moscot_decoder": {
            "atom": ATOM,
            "task": "T1",
            "board": BOARD,
            "target_stage": BOARD_TARGET_STAGE,
            "lane": lane,
            "method": (
                "temporal_coupling_state_mass_forecast+state_mean_program+"
                + (
                    "empirical_residual_replay"
                    if lane == "L1_EMPIRICAL_RESIDUAL"
                    else "module_scdesign3_decoder"
                )
            ),
            "parent_candidate": "candidate/T1_val/v0004_strict_pseudobulk_shift",
            "parent_sha256": PARENT_SHA256,
            "seed": SEED,
            "alpha_frozen": alpha,
            "rho_extrap": RHO_EXTRAP,
            "growth_rho": GROWTH_RHO,
            "n_cells": N_CELLS,
            "target_used_for_generation": False,
            "p1_new_states_created": False,
            "inputs": dict(input_hashes),
            "plan_duplicated_rows": int(sum(int(r["n_duplicated"]) for r in plan_rows)),
        },
    }


def command_generate(out_dir: Path, lane: str) -> dict[str, Any]:
    """One full T1:val (E10.5) candidate for one lane; budget: one per lane."""
    out_dir = Path(out_dir)
    if lane not in LANES:
        raise ValueError(f"lane must be one of {LANES}, got {lane!r}")
    candidate_dir = out_dir / "candidates" / lane
    candidate_path = candidate_dir / "submission.h5ad"
    if candidate_path.exists():
        raise FileExistsError(
            f"candidate already exists: {candidate_path}; candidates are immutable"
        )
    alpha = _frozen_alpha(out_dir)
    pre = load_pre_intermediates()
    deltas = _load_delta_npz(out_dir)
    mass_rows = _load_mass_rows(out_dir)
    growth_detail = {}
    forecast_path = out_dir / "metrics" / "mass_forecast.json"
    if forecast_path.is_file():
        growth_detail = json.loads(forecast_path.read_text(encoding="utf-8"))[
            "mass"
        ].get("growth_detail", {})

    parent = _load_stage_dense(PARENT_PATH)
    parent_labels = parent.obs["celltype"].astype(str).to_numpy()
    vocab_states = set(deltas["states_e95"])
    unknown = sorted(set(parent_labels) - vocab_states)
    if unknown:
        raise ValueError(f"parent states outside the frozen vocabulary: {unknown}")

    draws, plan_rows = build_formal_sampling_plan(parent_labels, mass_rows, growth_detail)
    src_rows = np.concatenate([draws[s] for s in sorted(draws)]).astype(np.int64)
    assigned = np.concatenate(
        [[s] * len(draws[s]) for s in sorted(draws)]
    ).astype(str)
    delta_by_state = {
        s: deltas["delta_e105"][i] for i, s in enumerate(deltas["states_e95"])
    }
    delta_rows = np.vstack([delta_by_state[s] for s in assigned]).astype(np.float32)

    parent_X = np.asarray(parent.X, dtype=np.float32)
    pred = parent_X[src_rows] + np.float32(alpha) * delta_rows
    np.clip(pred, 0, None, out=pred)

    decoder_note: dict[str, Any] = {"decoder": "empirical_residual_row_replay"}
    if lane == "L2_MODULE_SCDESIGN3":
        params_path = out_dir / "intermediates" / "l2_decoder_params.json"
        if not params_path.is_file():
            raise FileNotFoundError(
                f"L2 decoder parameters missing: {params_path}; run `fit-l2` first"
            )
        decoder_params = json.loads(params_path.read_text(encoding="utf-8"))
        modules = _module_gene_index(out_dir, deltas["var_names"])
        if not modules:
            raise RuntimeError("module definition empty; cannot run the L2 decoder")
        pred, decoder_note = apply_l2_module_decoder(
            pred, assigned, decoder_params, modules,
            stage="e95", seed_parts=("formal", lane),
        )
        decoder_note["decoder"] = "module_scdesign3_gaussian_copula"
        decoder_note["params_sha256"] = sha256_file(params_path)

    source_names = [str(parent.obs_names[i]) for i in src_rows]
    obs = pd.DataFrame(
        {
            "celltype": pd.Categorical(assigned),
            "assigned_state": assigned,
            "residual_source_index": src_rows.astype(np.int64),
            "residual_source_obs_name": source_names,
            "residual_source_state": parent_labels[src_rows],
        },
        index=pd.Index(_unique_obs_names(source_names), name=parent.obs.index.name),
    )
    candidate = ad.AnnData(X=pred, obs=obs, var=parent.var.copy())
    candidate.uns.update(
        _candidate_uns(
            lane, alpha, plan_rows,
            {
                "state_gene_delta_npz": deltas["sha256"],
                "state_mass_tsv": sha256_file(out_dir / "intermediates" / "state_mass.tsv"),
                **pre["input_hashes"],
            },
        )
    )
    _write_h5ad_atomic(candidate, candidate_path)

    npy_tmp = out_dir / "intermediates" / f"residual_source_index_{lane}.tmp.npy"
    np.save(npy_tmp, src_rows)
    npy_tmp.replace(out_dir / "intermediates" / f"residual_source_index_{lane}.npy")
    if lane == "L1_EMPIRICAL_RESIDUAL":
        # the plan is lane-independent; L1 writes it, L2 verifies identity
        _write_tsv_atomic(
            out_dir / "intermediates" / "sampling_plan.tsv", plan_rows, SAMPLING_PLAN_TSV_FIELDS
        )

    diagnostics = {
        "lane": lane,
        "candidate_path": str(candidate_path.relative_to(ROOT)),
        "candidate_sha256": sha256_file(candidate_path),
        "n_obs": int(candidate.n_obs),
        "n_vars": int(candidate.n_vars),
        "alpha_frozen": alpha,
        "decoder": decoder_note,
        "plan": {
            "n_states": len(plan_rows),
            "duplicated_rows": int(sum(int(r["n_duplicated"]) for r in plan_rows)),
            "states_with_duplicates": sorted(
                r["state"] for r in plan_rows if int(r["n_duplicated"]) > 0
            ),
        },
        "composition": state_counts(assigned),
        "pseudobulk_pearson_vs_parent": float(
            np.corrcoef(pred.mean(axis=0), parent_X.mean(axis=0))[0, 1]
        ),
    }
    _write_json_atomic(candidate_dir / "generation_diagnostics.json", diagnostics)
    return {"step": "generate", **{k: diagnostics[k] for k in ("lane", "candidate_sha256", "n_obs")}}


# ---------------------------------------------------------------------------
# L2 module decoder fit (ve-core exports, R/scDesign3 fits, core samples)
# ---------------------------------------------------------------------------

R_FIT_SCRIPT = r"""#!/usr/bin/env Rscript
# T1-S2 L2 module decoder fit: scDesign3 per-state gaussian marginals on the
# frozen 74-gene module panel + per-module gaussian copula correlation of the
# scDesign3 quantile residuals.  Writes standard simulator parameters as JSON;
# sampling happens in the core environment, never here.
args <- commandArgs(trailingOnly = TRUE)
input_tsv <- args[1]
module_tsv <- args[2]
out_json <- args[3]
min_cells <- as.integer(args[4])

suppressPackageStartupMessages({
  library(scDesign3)
  library(SingleCellExperiment)
})
log <- function(...) cat(format(Sys.time(), "%H:%M:%S"), ..., "\n")

dat <- read.delim(input_tsv, check.names = FALSE, stringsAsFactors = FALSE)
modules <- read.delim(module_tsv, check.names = FALSE, stringsAsFactors = FALSE)
module_genes <- unique(modules$gene[modules$present_in_panel == "True"])
module_map <- split(modules$gene, modules$module_id)
module_map <- lapply(module_map, intersect, module_genes)
log("input cells:", nrow(dat), " module genes:", length(module_genes))

fits <- list()
combos <- unique(dat[, c("stage", "state")])
for (row in seq_len(nrow(combos))) {
  stage <- combos$stage[row]
  state <- combos$state[row]
  key <- paste(stage, state, sep = "||")
  sub <- dat[dat$stage == stage & dat$state == state, , drop = FALSE]
  if (nrow(sub) < min_cells) {
    log("skip (too few cells):", key, nrow(sub))
    next
  }
  mat <- t(as.matrix(sub[, module_genes, drop = FALSE]))
  sce <- SingleCellExperiment(assays = list(logcounts = mat))
  sce$celltype <- "all"  # constant covariate: construct_data requires one of celltype/pseudotime/spatial
  cd <- scDesign3::construct_data(
    sce, assay_use = "logcounts", celltype = "celltype", pseudotime = NULL,
    spatial = NULL, other_covariates = NULL, corr_by = "1"
  )
  # scDesign3 1.6.0 prepends the predictor itself: formulas are RHS-only ("1"),
  # and extract_para needs the covariate frame (cd$dat) plus new_covariate=NULL.
  fit <- scDesign3::fit_marginal(
    cd, predictor = "gene", mu_formula = "1", sigma_formula = "1",
    family_use = "gaussian", n_cores = 1
  )
  para <- scDesign3::extract_para(
    sce, assay_use = "logcounts", marginal_list = fit, n_cores = 1,
    family_use = "gaussian", new_covariate = NULL, data = cd$dat
  )
  # intercept-only fit: every cell shares the per-gene mean/sigma column
  mu <- colMeans(para$mean_mat, na.rm = TRUE)
  sigma <- colMeans(para$sigma_mat, na.rm = TRUE)
  mu <- mu[rownames(mat)]
  sigma <- sigma[rownames(mat)]
  mu[!is.finite(mu)] <- 0
  sigma[!is.finite(sigma) | sigma <= 0] <- 1e-6
  z <- sweep(sweep(mat, 1, mu, "-"), 1, sigma, "/")  # quantile residuals (gaussian)
  state_modules <- list()
  for (module_id in names(module_map)) {
    genes <- module_map[[module_id]]
    if (length(genes) < 2) next
    corr <- cor(t(z[genes, , drop = FALSE]))
    corr[!is.finite(corr)] <- 0
    diag(corr) <- 1
    state_modules[[module_id]] <- list(
      genes = genes, mu = unname(mu[genes]), sigma = unname(sigma[genes]),
      corr = corr
    )
  }
  fits[[key]] <- list(
    stage = stage, state = state, n_cells = nrow(sub), modules = state_modules
  )
  log("fitted:", key, "cells:", nrow(sub))
}
payload <- list(
  fits = fits,
  scdesign3_version = as.character(packageVersion("scDesign3")),
  r_version = R.version.string,
  session_info = paste(capture.output(sessionInfo()), collapse = "\n")
)
writeLines(jsonlite::toJSON(payload, auto_unbox = TRUE, digits = 8), out_json)
log("wrote", out_json)
"""


def command_fit_l2(out_dir: Path, *, smoke: bool = False) -> dict[str, Any]:
    """Freeze the module definition, export the fit panel, run scDesign3 in R.

    The module definition is the frozen T1-PRE marker programs restricted to
    panel genes -- written before any fit/generation.  The R environment only
    exports simulator parameters; it never writes the final H5AD.
    """
    out_dir = Path(out_dir)
    l2_dir = out_dir / "intermediates" / "l2"
    if smoke:  # smoke outputs are fully separated from the formal artifacts
        params_path = l2_dir / "decoder_params_smoke.json"
        raw_path = l2_dir / "decoder_params_smoke_raw.json"
        fit_input = l2_dir / "fit_input_smoke.tsv"
        log_path = l2_dir / "fit_decoder_smoke.log"
        record_path = out_dir / "metrics" / "l2_decoder_fit_smoke.json"
    else:
        params_path = out_dir / "intermediates" / "l2_decoder_params.json"
        raw_path = l2_dir / "decoder_params_raw.json"
        fit_input = l2_dir / "fit_input.tsv"
        log_path = l2_dir / "fit_decoder.log"
        record_path = out_dir / "metrics" / "l2_decoder_fit.json"
    if not smoke and params_path.exists():
        raise FileExistsError(f"L2 decoder parameters already exist: {params_path}")
    l2_dir.mkdir(parents=True, exist_ok=True)

    pre = load_pre_intermediates()
    program_rows = _read_tsv(PRE_PROGRAMS)
    module_rows = [
        {
            "module_id": row["program_id"],
            "lineage": row["lineage"],
            "state_family": row["state_family"],
            "gene": row["gene"],
            "present_in_panel": row["present_in_panel"],
        }
        for row in program_rows
        if row["present_in_panel"] == "True"
    ]
    _write_tsv_atomic(
        out_dir / "intermediates" / "module_definition.tsv",
        module_rows,
        ["module_id", "lineage", "state_family", "gene", "present_in_panel"],
    )
    module_genes = sorted({row["gene"] for row in module_rows})

    frames: list[pd.DataFrame] = []
    for stage, path in (("e85", SOURCE_PATH), ("e95", TARGET_PATH)):
        adata = ad.read_h5ad(path, backed="r")
        try:
            var_names = [str(g) for g in adata.var_names]
            col_index = [var_names.index(g) for g in module_genes]
            sub = adata.X[:, col_index]
            dense = sub.toarray() if sparse.issparse(sub) else np.asarray(sub)
            labels = adata.obs["celltype"].astype(str).to_numpy()
        finally:
            adata.file.close()
        frame = pd.DataFrame(dense, columns=module_genes)
        frame.insert(0, "state", labels)
        frame.insert(0, "stage", stage)
        frames.append(frame)
    panel = pd.concat(frames, ignore_index=True)
    if smoke:  # deterministic smoke subset: two states, few cells
        keep = panel["state"].isin(sorted(panel["state"].unique())[:2])
        panel = panel[keep].groupby(["stage", "state"], observed=True).head(30)
    panel_tmp = fit_input.with_name(fit_input.name + ".tmp")
    panel.to_csv(panel_tmp, sep="\t", index=False)
    panel_tmp.replace(fit_input)

    script_path = l2_dir / "fit_decoder.R"
    _write_bytes_atomic(script_path, R_FIT_SCRIPT.encode("utf-8"))
    command = [
        "Rscript", str(script_path), str(fit_input),
        str(out_dir / "intermediates" / "module_definition.tsv"),
        str(params_path) + ".tmp", str(L2_MIN_FIT_CELLS),
    ]
    started = time.monotonic()
    with log_path.open("w", encoding="utf-8") as log_handle:
        proc = subprocess.run(command, stdout=log_handle, stderr=subprocess.STDOUT)
    if proc.returncode != 0:
        raise RuntimeError(f"scDesign3 fit failed (rc={proc.returncode}); see {log_path}")
    Path(str(params_path) + ".tmp").replace(raw_path)
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    reshaped: dict[str, Any] = {
        "schema": "ve.t1.s2-l2-decoder-params.v1",
        "atom": ATOM,
        "fits_e85": {},
        "fits_e95": {},
        "scdesign3_version": raw.get("scdesign3_version"),
        "r_version": raw.get("r_version"),
        "session_info": raw.get("session_info"),
        "raw_fit_json": str(raw_path.relative_to(ROOT)),
        "raw_fit_sha256": sha256_file(raw_path),
    }
    for key, fit in raw.get("fits", {}).items():
        entry = {"n_cells": fit["n_cells"], "modules": fit["modules"]}
        reshaped[f"fits_{fit['stage']}"][fit["state"]] = entry
    _write_json_atomic(params_path, reshaped)
    record = {
        "schema": "ve.t1.s2-l2-decoder-fit.v1",
        "atom": ATOM,
        "smoke": smoke,
        "n_fits": len(raw.get("fits", {})),
        "states_fitted_e85": sorted(reshaped["fits_e85"]),
        "states_fitted_e95": sorted(reshaped["fits_e95"]),
        "scdesign3_version": reshaped["scdesign3_version"],
        "r_version": reshaped["r_version"],
        "wall_seconds": round(time.monotonic() - started, 3),
        "module_definition_sha256": sha256_file(out_dir / "intermediates" / "module_definition.tsv"),
        "fit_input_sha256": sha256_file(fit_input),
        "params_sha256": sha256_file(params_path),
        "r_script_sha256": sha256_file(script_path),
        "min_fit_cells": L2_MIN_FIT_CELLS,
    }
    _write_json_atomic(record_path, record)
    return {"step": "fit-l2", "smoke": smoke, "n_fits": record["n_fits"], "wall_seconds": record["wall_seconds"]}


# ---------------------------------------------------------------------------
# Contract (locked prepare-builder semantics), scorer wrapper, checks
# ---------------------------------------------------------------------------


def command_contract(out_dir: Path, lane: str) -> dict[str, Any]:
    """P0-locked T1 contract checks (prepare_t1_t3_submission semantics).

    The locked T1 builder validates: exact panel gene order, 2D finite
    non-negative X, board cell limits, and no obsm on T1.  This atom adds the
    batch3 normalisation marker requirement and a serialisation round-trip.
    """
    out_dir = Path(out_dir)
    candidate_path = out_dir / "candidates" / lane / "submission.h5ad"
    if not candidate_path.is_file():
        raise FileNotFoundError(f"candidate missing: {candidate_path}; run `generate` first")
    lock = json.loads(SCORER_LOCK_PATH.read_text(encoding="utf-8"))
    builder = lock["contract_snapshot"]["t1_builder"]
    builder_actual = sha256_file(ROOT / builder["path"])

    checks: dict[str, Any] = {}
    errors: list[str] = []
    panel = [
        line.strip()
        for line in PANEL_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    candidate = ad.read_h5ad(candidate_path)
    observed_genes = [str(g) for g in candidate.var_names]
    checks["shape"] = {"n_obs": int(candidate.n_obs), "n_vars": int(candidate.n_vars)}
    checks["cell_limits"] = {
        "min_cells": BOARD_MIN_CELLS,
        "max_cells": BOARD_MAX_CELLS,
        "ok": BOARD_MIN_CELLS <= candidate.n_obs <= BOARD_MAX_CELLS,
    }
    if not checks["cell_limits"]["ok"]:
        errors.append("candidate cell count outside board limits")
    checks["gene_order"] = {
        "exact": observed_genes == panel,
        "n_genes": len(observed_genes),
        "panel_sha256": sha256_file(PANEL_PATH),
    }
    if observed_genes != panel:
        errors.append("var_names do not exactly match the locked T1:val panel/order")
    X = candidate.X
    values = X.data if sparse.issparse(X) else np.asarray(X)
    finite = bool(np.isfinite(values).all())
    nonnegative = bool((values >= 0).all())
    checks["expression"] = {
        "finite": finite,
        "nonnegative": nonnegative,
        "dtype": str(getattr(X, "dtype", "unknown")),
        "ndim": int(getattr(X, "ndim", -1)),
    }
    if getattr(X, "ndim", None) != 2 or not finite or not nonnegative:
        errors.append("X must be a finite non-negative 2D matrix")
    checks["no_obsm_t1"] = {"n_obsm": len(candidate.obsm.keys())}
    if len(candidate.obsm.keys()) > 0:
        errors.append("T1 candidate must not carry obsm entries")
    checks["normalisation"] = {
        "expected": NORMALIZATION,
        "marker": candidate.uns.get("ve_contract", {}).get("normalization"),
    }
    if checks["normalisation"]["marker"] != NORMALIZATION:
        errors.append("missing uns.ve_contract.normalization marker")
    checks["cell_identity"] = {
        "unique": candidate.obs_names.is_unique,
        "nonempty": bool(all(str(c).strip() for c in candidate.obs_names)),
        "celltype_present": "celltype" in candidate.obs.columns,
    }
    if not (checks["cell_identity"]["unique"] and checks["cell_identity"]["nonempty"]):
        errors.append("obs_names must be unique and non-empty")
    if not checks["cell_identity"]["celltype_present"]:
        errors.append("obs.celltype is required by the scorer")

    # serialisation round-trip re-read (the locked builder re-loads its output)
    reread = ad.read_h5ad(candidate_path)
    checks["round_trip"] = {
        "shape_stable": reread.shape == candidate.shape,
        "gene_order_stable": [str(g) for g in reread.var_names] == observed_genes,
    }
    if not all(checks["round_trip"].values()):
        errors.append("serialisation round-trip changed contract content")

    report = {
        "schema_version": "ve.batch3.contract-report.v1",
        "status": "PASS" if not errors else "FAIL",
        "valid": not errors,
        "path": str(candidate_path.relative_to(ROOT)),
        "candidate_sha256": sha256_file(candidate_path),
        "task": "T1",
        "board": "val",
        "contract_source": {
            "builder": builder["path"],
            "builder_sha256_lock": builder["sha256"],
            "builder_sha256_actual": builder_actual,
            "builder_intact": builder_actual == builder["sha256"],
            "semantics": "prepare_t1_t3_submission._load_board_input + batch3 normalisation marker",
        },
        "checks": checks,
        "errors": errors,
        "warnings": [],
    }
    if builder_actual != builder["sha256"]:
        report["status"] = "FAIL"
        report["valid"] = False
        report["errors"].append("locked T1 builder hash drift detected")
    _write_json_atomic(out_dir / "candidates" / lane / "contract_report.json", report)
    return {"step": "contract", "lane": lane, "status": report["status"]}


def _load_scorer_lock() -> dict[str, Any]:
    lock = json.loads(SCORER_LOCK_PATH.read_text(encoding="utf-8"))
    entry = lock["entrypoint"]
    actual = sha256_file(SCORER_ENTRYPOINT)
    if actual != entry["sha256"]:
        raise RuntimeError(
            f"scorer entrypoint hash drift: lock {entry['sha256']} vs actual {actual}"
        )
    return lock


def scorer_command(out_path: Path, input_path: Path) -> list[str]:
    """Locked full-panel scorer invocation (P0-LOCK command template)."""
    return [
        "env",
        "LD_LIBRARY_PATH=/opt/anaconda3/lib",
        "PYTHONPATH=third_party/veckit",
        "python",
        "third_party/veckit/score_h5ad.py",
        "--task",
        "T1",
        "--input",
        str(input_path),
        "--target",
        "data/E9.5_RNA.h5ad",  # pseudo-target: never the hidden E10.5 truth
        "--reference",
        "data/E8.5_RNA.h5ad",
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
    """RSS of the supervisor plus its descendants (the scorer child holds memory)."""
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


def scorer_launch(out_dir: Path, name: str, input_path: Path) -> dict[str, Any]:
    """Launch the locked scorer as a detached child; record PID and log path.

    A bash supervisor wraps the scorer so its exit code survives the parent
    process: the supervisor writes ``scorer_<name>.rc`` atomically after the
    scorer exits.  Never blocks on completion.
    """
    out_dir = Path(out_dir)
    metrics_dir = out_dir / "metrics"
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
    input_path = Path(input_path)
    if not input_path.is_file():
        raise FileNotFoundError(f"scorer input missing: {input_path}")
    out_tmp = metrics_dir / f"scorer_{name}_output.tmp.json"
    out_final = metrics_dir / f"scorer_{name}_output.json"
    log_path = out_dir / f"scorer_{name}.log"
    rc_tmp = metrics_dir / f"scorer_{name}.rc.tmp"
    rc_file = metrics_dir / f"scorer_{name}.rc"
    for stale in (out_tmp, out_final, rc_tmp, rc_file):
        if stale.exists():
            raise FileExistsError(f"refusing to overwrite existing scorer artifact: {stale}")
    command = scorer_command(out_tmp, input_path)
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
        "schema": "ve.t1.s2-scorer-run.v1",
        "atom": ATOM,
        "name": name,
        "status": "RUNNING",
        "pid": process.pid,
        "command": " ".join(command),
        "pseudo_target": "data/E9.5_RNA.h5ad",
        "pseudo_target_note": (
            "local --target is a pseudo-target (training stage); it cannot "
            "establish leaderboard improvement or hidden-target validity"
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
    return record


def scorer_collect(out_dir: Path, name: str) -> dict[str, Any]:
    """Low-frequency status check: RSS sample when running, result when done."""
    out_dir = Path(out_dir)
    metrics_dir = out_dir / "metrics"
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
            checks = {
                "genes_match": meta.get("genes") == EXPECTED_GENES,
                "truth_cells_match": meta.get("truth_cells") == EXPECTED_TRUTH_CELLS,
                "prediction_cells": meta.get("prediction_cells"),
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


def _safe_version(metadata_module: Any, package: str) -> str | None:
    try:
        return metadata_module.version(package)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Protected checks
# ---------------------------------------------------------------------------


def command_checks(out_dir: Path) -> dict[str, Any]:
    """The atom's protected checks, evaluated over candidates + intermediates."""
    out_dir = Path(out_dir)
    pre = load_pre_intermediates()
    deltas = _load_delta_npz(out_dir)
    mass_rows = _read_tsv(out_dir / "intermediates" / "state_mass.tsv")
    alpha = _frozen_alpha(out_dir)
    vocab_states = set(deltas["states_e95"])
    modules = _module_gene_index(out_dir, deltas["var_names"])
    module_cols = sorted({c for cols in modules.values() for c in cols})

    parent = ad.read_h5ad(PARENT_PATH, backed="r")
    parent_var_names = [str(g) for g in parent.var_names]
    parent.file.close()

    checks: dict[str, Any] = {}
    errors: list[str] = []

    # 1. gene order / normalisation / expression sanity per lane
    lane_data: dict[str, dict[str, Any]] = {}
    for lane in LANES:
        path = out_dir / "candidates" / lane / "submission.h5ad"
        if not path.is_file():
            lane_data[lane] = {"present": False}
            continue
        cand = ad.read_h5ad(path)
        X = np.asarray(cand.X)
        lane_data[lane] = {
            "present": True,
            "X": X,
            "obs": cand.obs.copy(),
            "var_names": [str(g) for g in cand.var_names],
            "normalization": cand.uns.get("ve_contract", {}).get("normalization"),
            "sha256": sha256_file(path),
        }
        checks[f"{lane}.gene_order"] = {
            "ok": lane_data[lane]["var_names"] == parent_var_names,
            "reference": "locked panel order == locked parent var order",
        }
        checks[f"{lane}.normalisation"] = {
            "marker": lane_data[lane]["normalization"],
            "expected": NORMALIZATION,
            "ok": lane_data[lane]["normalization"] == NORMALIZATION,
        }
        checks[f"{lane}.expression"] = {
            "ok": bool(np.isfinite(X).all()) and bool((X >= 0).all()),
            "finite": bool(np.isfinite(X).all()),
            "nonnegative": bool((X >= 0).all()),
        }
        checks[f"{lane}.cell_count"] = {
            "ok": BOARD_MIN_CELLS <= cand.n_obs <= BOARD_MAX_CELLS,
            "n_obs": int(cand.n_obs),
            "limits": [BOARD_MIN_CELLS, BOARD_MAX_CELLS],
        }
        checks[f"{lane}.p1_not_extended"] = {
            "ok": set(cand.obs["celltype"].astype(str)) <= vocab_states,
            "n_states_used": int(cand.obs["celltype"].nunique()),
            "new_states_created": False,
        }
        for name, check in checks.items():
            if name.startswith(f"{lane}.") and check.get("ok") is False:
                errors.append(f"{name} failed")

    # 2. residual traceability: L1 exact replay identity, L2 on non-module genes
    delta_by_state = {
        s: deltas["delta_e105"][i] for i, s in enumerate(deltas["states_e95"])
    }
    parent_full = _load_stage_dense(PARENT_PATH)
    parent_X = np.asarray(parent_full.X, dtype=np.float32)
    for lane in LANES:
        if not lane_data[lane].get("present"):
            continue
        obs = lane_data[lane]["obs"]
        src = obs["residual_source_index"].to_numpy(dtype=np.int64)
        assigned = obs["assigned_state"].astype(str).to_numpy()
        if src.min() < 0 or src.max() >= parent_full.n_obs:
            errors.append(f"{lane}: residual_source_index out of parent range")
            continue
        rebuilt = parent_X[src] + np.float32(alpha) * np.vstack(
            [delta_by_state[s] for s in assigned]
        ).astype(np.float32)
        np.clip(rebuilt, 0, None, out=rebuilt)
        observed = lane_data[lane]["X"]
        if lane == "L1_EMPIRICAL_RESIDUAL":
            identical = bool(np.allclose(observed, rebuilt, rtol=0, atol=1e-5))
            checks[f"{lane}.residual_traceability"] = {
                "identity_replay_exact": identical,
                "max_abs_deviation": float(np.abs(observed - rebuilt).max()),
                "rule": "candidate cell == clip(parent[source] + alpha * delta_e105(assigned), 0)",
            }
            if not identical:
                errors.append(f"{lane}: residual replay identity broken")
        else:
            non_module = np.ones(observed.shape[1], dtype=bool)
            non_module[module_cols] = False
            identical = bool(
                np.allclose(observed[:, non_module], rebuilt[:, non_module], rtol=0, atol=1e-5)
            )
            module_differs = bool(
                module_cols
                and not np.allclose(observed[:, module_cols], rebuilt[:, module_cols], rtol=0, atol=1e-5)
            )
            checks[f"{lane}.residual_traceability"] = {
                "non_module_identity_exact": identical,
                "module_genes_differ_by_design": module_differs,
                "n_module_genes": len(module_cols),
                "rule": "non-module genes keep the parent residual replay; module genes are scDesign3-decoded",
            }
            if not identical:
                errors.append(f"{lane}: non-module genes deviate from the parent residual replay")

    # 3. state mass sums to 1 per board (tsv rounding tolerance)
    for board in sorted({row["board"] for row in mass_rows}):
        total = sum(
            float(row["shrunk_probability"]) for row in mass_rows if row["board"] == board
        )
        checks[f"state_mass_sum.{board}"] = {"sum": total, "ok": abs(total - 1.0) <= 1e-4}
        if abs(total - 1.0) > 1e-4:
            errors.append(f"state mass sum != 1 for {board}: {total}")

    # 4. small-state cap/shrinkage engaged as pre-declared
    forecast = json.loads((out_dir / "metrics" / "mass_forecast.json").read_text(encoding="utf-8"))
    growth_detail = forecast["mass"].get("growth_detail", {})
    small = forecast["mass"]["small_states"]
    small_ok = True
    for state in small:
        row = next(r for r in mass_rows if r["board"] == BOARD and r["state"] == state)
        if float(row["raw_forecast"]) > SMALL_STATE_SHARE_CAP_MULT * float(row["parent_probability"]) + 1e-9:
            small_ok = False
        if abs(growth_detail[state]["growth_shrunk"] - shrink_growth(
            growth_detail[state]["growth_raw"], rho=SMALL_STATE_RHO
        )) > 1e-9:
            small_ok = False
    checks["small_state_cap_shrinkage"] = {
        "small_states": small,
        "cap_mult": SMALL_STATE_SHARE_CAP_MULT,
        "rho": SMALL_STATE_RHO,
        "ok": small_ok,
    }
    if not small_ok:
        errors.append("small-state cap/shrinkage violated")

    # 5. L1/L2 differ only in the decoder
    if all(lane_data[l].get("present") for l in LANES):
        idx_l1 = np.load(out_dir / "intermediates" / "residual_source_index_L1_EMPIRICAL_RESIDUAL.npy")
        idx_l2 = np.load(out_dir / "intermediates" / "residual_source_index_L2_MODULE_SCDESIGN3.npy")
        obs_l1 = lane_data["L1_EMPIRICAL_RESIDUAL"]["obs"]
        obs_l2 = lane_data["L2_MODULE_SCDESIGN3"]["obs"]
        same_plan = bool(np.array_equal(idx_l1, idx_l2))
        same_obs = bool(
            (obs_l1["celltype"].astype(str) == obs_l2["celltype"].astype(str)).all()
            and (obs_l1["assigned_state"].astype(str) == obs_l2["assigned_state"].astype(str)).all()
        )
        X1 = lane_data["L1_EMPIRICAL_RESIDUAL"]["X"]
        X2 = lane_data["L2_MODULE_SCDESIGN3"]["X"]
        non_module = np.ones(X1.shape[1], dtype=bool)
        non_module[module_cols] = False
        same_off_module = bool(np.allclose(X1[:, non_module], X2[:, non_module], rtol=0, atol=0))
        any_module_diff = bool(
            module_cols and not np.allclose(X1[:, module_cols], X2[:, module_cols], rtol=0, atol=0)
        )
        checks["lanes_differ_only_in_decoder"] = {
            "same_sampling_plan": same_plan,
            "same_obs": same_obs,
            "identical_off_module_genes": same_off_module,
            "module_genes_differ": any_module_diff,
            "ok": same_plan and same_obs and same_off_module,
        }
        if not (same_plan and same_obs and same_off_module):
            errors.append("L1/L2 differ beyond the decoder")

    report = {
        "schema": "ve.t1.s2-protected-checks.v1",
        "atom": ATOM,
        "seed": SEED,
        "alpha_frozen": alpha,
        "status": "PASS" if not errors else "FAIL",
        "checks": checks,
        "errors": errors,
    }
    _write_json_atomic(out_dir / "metrics" / "protected_checks.json", report)
    return {"step": "checks", "status": report["status"], "errors": errors}


# ---------------------------------------------------------------------------
# Finalize: config, tool versions, component ablation, manifest
# ---------------------------------------------------------------------------


def _git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def _tool_versions(out_dir: Path) -> dict[str, Any]:
    import importlib.metadata

    payload: dict[str, Any] = {
        "schema": "ve.t1.s2-tool-versions.v1",
        "atom": ATOM,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "ve_core": {
            "interpreter": sys.executable,
            "anndata": importlib.metadata.version("anndata"),
            "numpy": np.__version__,
            "scipy": importlib.metadata.version("scipy"),
            "pandas": importlib.metadata.version("pandas"),
        },
        "implementation": {
            "path": "scripts/t1_s2_moscot_decoder.py",
            "sha256": sha256_file(Path(__file__).resolve()),
        },
        "scorer": {
            "entrypoint": "third_party/veckit/score_h5ad.py",
            "sha256": sha256_file(SCORER_ENTRYPOINT),
            "lock": "artifacts/tool_integration/P0-LOCK/locks/SCORER_LOCK.json",
            "bundle_commit": "46d41e63f42a9aab815db20b742feeccd249cb17",
            "package_version": "0.1.1",
        },
    }
    ot_versions_path = out_dir / "metrics" / "ot_env_versions.json"
    if ot_versions_path.is_file():
        payload["ve_t1_ot"] = json.loads(ot_versions_path.read_text(encoding="utf-8"))
    l2_fit_path = out_dir / "metrics" / "l2_decoder_fit.json"
    if l2_fit_path.is_file():
        fit = json.loads(l2_fit_path.read_text(encoding="utf-8"))
        payload["r_scdesign3"] = {
            "scdesign3_version": fit.get("scdesign3_version"),
            "r_version": fit.get("r_version"),
            "r_script": "intermediates/l2/fit_decoder.R",
            "r_script_sha256": fit.get("r_script_sha256"),
        }
    return payload


def _contribution_split(out_dir: Path, lane: str) -> dict[str, Any]:
    """Pseudobulk-level decomposition: composition vs mean program vs residual."""
    candidate_path = out_dir / "candidates" / lane / "submission.h5ad"
    if not candidate_path.is_file():
        return {"lane": lane, "present": False}
    alpha = _frozen_alpha(out_dir)
    deltas = _load_delta_npz(out_dir)
    delta_by_state = {
        s: deltas["delta_e105"][i] for i, s in enumerate(deltas["states_e95"])
    }
    cand = ad.read_h5ad(candidate_path)
    src = cand.obs["residual_source_index"].to_numpy(dtype=np.int64)
    assigned = cand.obs["assigned_state"].astype(str).to_numpy()
    cand_X = np.asarray(cand.X, dtype=np.float64)
    parent = _load_stage_dense(PARENT_PATH)
    parent_X = np.asarray(parent.X, dtype=np.float64)
    pb_parent = parent_X.mean(axis=0)
    pb_sampled = parent_X[src].mean(axis=0)
    delta_rows = np.vstack([delta_by_state[s] for s in assigned]).astype(np.float64)
    mean_part = alpha * delta_rows.mean(axis=0)
    pb_cand = cand_X.mean(axis=0)
    composition_part = pb_sampled - pb_parent
    residual_part = pb_cand - pb_sampled - mean_part
    return {
        "lane": lane,
        "present": True,
        "pb_total_shift_l2": float(np.linalg.norm(pb_cand - pb_parent)),
        "composition_part_l2": float(np.linalg.norm(composition_part)),
        "mean_program_part_l2": float(np.linalg.norm(mean_part)),
        "residual_part_l2": float(np.linalg.norm(residual_part)),
        "residual_part_note": (
            "L1: non-negativity clip truncation on the replayed rows (the replay "
            "itself is deterministic); L2: additionally the module-copula sampling deviation"
        ),
        "alpha_frozen": alpha,
    }


def command_finalize(out_dir: Path) -> dict[str, Any]:
    out_dir = Path(out_dir)
    alpha_path = out_dir / "metrics" / "alpha_calibration.json"
    holdout = json.loads(alpha_path.read_text(encoding="utf-8")) if alpha_path.is_file() else None

    ablation: dict[str, Any] = {
        "schema": "ve.t1.s2-component-ablation.v1",
        "atom": ATOM,
        "seed": SEED,
        "pseudo_holdout": {
            "description": (
                "one source-only E8.5->E9.5 holdout; official metric panel computed "
                "in-process with the locked bundle code and seed; E9.5 is a training "
                "stage, so this validates machinery and freezes alpha only"
            ),
            "metric_mapping": {"DES": "de_score", "DCS": "de_direction", "MMD": "mmd_u", "CSS": "composition_JSD"},
            "arms": holdout["metrics"] if holdout else None,
            "alpha": holdout["alpha"] if holdout else None,
        },
        "formal_candidates": {},
        "interpretation": (
            "pseudo-holdout numbers are source-only validation-chain evidence; the "
            "formal candidates target hidden E10.5 and their local scores use the "
            "E9.5 pseudo-target -- no leaderboard improvement can be claimed locally"
        ),
    }
    for lane in LANES:
        diag_path = out_dir / "candidates" / lane / "generation_diagnostics.json"
        contract_path = out_dir / "candidates" / lane / "contract_report.json"
        scorer_path = out_dir / "metrics" / f"scorer_formal_{lane}_run.json"
        entry: dict[str, Any] = {"contribution_split": _contribution_split(out_dir, lane)}
        if diag_path.is_file():
            diag = json.loads(diag_path.read_text(encoding="utf-8"))
            entry["candidate_sha256"] = diag["candidate_sha256"]
            entry["composition"] = diag["composition"]
            entry["decoder"] = diag["decoder"]
        if contract_path.is_file():
            entry["contract_status"] = json.loads(contract_path.read_text(encoding="utf-8"))["status"]
        if scorer_path.is_file():
            run = json.loads(scorer_path.read_text(encoding="utf-8"))
            entry["scorer"] = {
                "status": run.get("status"),
                "result_metrics": run.get("result_metrics"),
                "result_meta": run.get("result_meta"),
                "result_sha256": run.get("result_sha256"),
                "pseudo_target": run.get("pseudo_target"),
            }
        ablation["formal_candidates"][lane] = entry
    _write_json_atomic(out_dir / "metrics" / "component_ablation.json", ablation)

    config_text = "\n".join(
        [
            f"atom: {ATOM}",
            "task: T1-S2-MOSCOT-DECODER",
            f"seed: {SEED}",
            "allow_network: true  # pip/R package installation only; no external data downloads",
            "allow_server_submission: false",
            "candidate_generation: true",
            "board: T1:val",
            f"board_target_stage: {BOARD_TARGET_STAGE}  # hidden; never read",
            "source_stage: E8.5",
            "target_stage: E9.5",
            "parent_candidate: candidate/T1_val/v0004_strict_pseudobulk_shift",
            f"parent_sha256: {PARENT_SHA256}",
            f"n_cells: {N_CELLS}",
            f"lineage_penalty: {LINEAGE_PENALTY}",
            f"ot_cost_normalisation: {OT_COST_NORMALISATION}",
            f"ot_epsilon: {OT_EPSILON}",
            f"ot_tau_a: {OT_TAU_A}",
            f"ot_tau_b: {OT_TAU_B}",
            f"growth_rho: {GROWTH_RHO}",
            f"growth_clip: [{GROWTH_CLIP_LO}, {GROWTH_CLIP_HI}]",
            f"small_state_min_cells: {SMALL_STATE_MIN_CELLS}",
            f"small_state_rho: {SMALL_STATE_RHO}",
            f"small_state_share_cap_mult: {SMALL_STATE_SHARE_CAP_MULT}",
            f"rho_extrap: {RHO_EXTRAP}",
            f"alpha_clip: [{ALPHA_CLIP_LO}, {ALPHA_CLIP_HI}]",
            "alpha_resolution: single analytic source-only pseudo-holdout, then frozen",
            "lanes: [L1_EMPIRICAL_RESIDUAL, L2_MODULE_SCDESIGN3]",
            "lane_difference: decoder only (module genes)",
            "scorer_local_target: data/E9.5_RNA.h5ad  # pseudo-target per SCORER_LOCK",
            "deviations: []",
            "",
        ]
    )
    _write_bytes_atomic(out_dir / "config_resolved.yaml", config_text.encode("utf-8"))
    _write_json_atomic(out_dir / "TOOL_VERSIONS.json", _tool_versions(out_dir))
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
            "implementation": "scripts/t1_s2_moscot_decoder.py",
            "implementation_sha256": sha256_file(Path(__file__).resolve()),
            "test_module": "tests/test_t1_s2_moscot_decoder.py",
            "test_module_sha256": sha256_file(ROOT / "tests" / "test_t1_s2_moscot_decoder.py")
            if (ROOT / "tests" / "test_t1_s2_moscot_decoder.py").is_file()
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


def command_input_lock(out_dir: Path) -> dict[str, Any]:
    """Hash-lock every input this atom reads (including T1-PRE intermediates)."""
    out_dir = Path(out_dir)
    inputs: dict[str, Any] = {}
    for name, path in (
        ("source_e85", SOURCE_PATH),
        ("target_e95", TARGET_PATH),
        ("parent_v0004", PARENT_PATH),
        ("panel_t1_val", PANEL_PATH),
        ("scorer_lock", SCORER_LOCK_PATH),
        ("board_registry", ROOT / "artifacts/tool_integration/P0-LOCK/locks/BOARD_REGISTRY.yaml"),
        ("pre_state_centroids", PRE_CENTROIDS),
        ("pre_state_vocabulary", PRE_VOCABULARY),
        ("pre_state_crosswalk", PRE_CROSSWALK),
        ("pre_program_definition", PRE_PROGRAMS),
    ):
        if not path.is_file():
            raise FileNotFoundError(f"required input missing: {path}")
        inputs[name] = {
            "path": str(path.relative_to(ROOT)),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    if inputs["parent_v0004"]["sha256"] != PARENT_SHA256:
        raise RuntimeError("parent v0004 hash drift vs P0-LOCK registry")
    lock = {
        "schema": "ve.t1.s2-input-lock.v1",
        "atom": ATOM,
        "locked_at": datetime.now(timezone.utc).isoformat(),
        "allow_network": True,
        "network_scope": "pip/R package installation only; no external data downloads",
        "inputs": inputs,
    }
    _write_json_atomic(out_dir / "inputs" / "input_lock.json", lock)
    return {"step": "input-lock", "n_inputs": len(inputs)}


def _append_run_log(out_dir: Path, line: str) -> None:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "run.log").open("a", encoding="utf-8") as handle:
        handle.write(
            f"{datetime.now(timezone.utc).isoformat()} {line}\n"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=[
            "input-lock", "couple", "forecast", "fit-l2", "pseudoholdout",
            "generate", "contract", "score-launch", "score-collect", "checks",
            "finalize", "manifest", "verify",
        ],
    )
    parser.add_argument("--out-dir", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--lane", choices=LANES, default=None)
    parser.add_argument("--name", default=None, help="scorer run name")
    parser.add_argument("--input", type=Path, default=None, help="scorer input h5ad")
    parser.add_argument("--smoke", action="store_true", help="fit-l2 smoke subset")
    args = parser.parse_args(argv)

    started = time.monotonic()
    if args.command == "input-lock":
        summary = command_input_lock(args.out_dir)
    elif args.command == "couple":
        summary = command_couple(args.out_dir)
    elif args.command == "forecast":
        summary = command_forecast(args.out_dir)
    elif args.command == "fit-l2":
        summary = command_fit_l2(args.out_dir, smoke=args.smoke)
    elif args.command == "pseudoholdout":
        summary = command_pseudoholdout(args.out_dir)
    elif args.command == "generate":
        if not args.lane:
            raise ValueError("generate requires --lane")
        summary = command_generate(args.out_dir, args.lane)
    elif args.command == "contract":
        if not args.lane:
            raise ValueError("contract requires --lane")
        summary = command_contract(args.out_dir, args.lane)
    elif args.command == "score-launch":
        if not args.name or not args.input:
            raise ValueError("score-launch requires --name and --input")
        record = scorer_launch(args.out_dir, args.name, args.input)
        summary = {"step": "score-launch", "name": args.name, "pid": record["pid"]}
    elif args.command == "score-collect":
        if not args.name:
            raise ValueError("score-collect requires --name")
        record = scorer_collect(args.out_dir, args.name)
        summary = {
            "step": "score-collect",
            "name": args.name,
            "status": record.get("status"),
            "peak_rss_bytes": record.get("peak_rss_bytes"),
        }
    elif args.command == "checks":
        summary = command_checks(args.out_dir)
    elif args.command == "finalize":
        summary = command_finalize(args.out_dir)
    elif args.command == "manifest":
        manifest = write_manifest(
            args.out_dir,
            exclude=(
                "run.log",
                "metrics/scorer_formal_L1_EMPIRICAL_RESIDUAL_run.json",
                "metrics/scorer_formal_L2_MODULE_SCDESIGN3_run.json",
                "scorer_formal_L1_EMPIRICAL_RESIDUAL.log",
                "scorer_formal_L2_MODULE_SCDESIGN3.log",
            ),
        )
        summary = {
            "step": "manifest",
            "n_files": len(manifest["files"]),
            "self_verify_ok": manifest["self_verify"]["ok"],
        }
    else:
        summary = verify_manifest(args.out_dir)
    summary["wall_seconds"] = round(time.monotonic() - started, 3)
    _append_run_log(args.out_dir, json.dumps(
        {"command": args.command, "lane": args.lane, "name": args.name,
         "summary_status": summary.get("status"), "wall_seconds": summary["wall_seconds"]},
        ensure_ascii=False, sort_keys=True,
    ))
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
