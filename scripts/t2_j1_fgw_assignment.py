#!/usr/bin/env python3
"""T2-J1-FGW-ASSIGNMENT: formal FGW soft-assignment candidates on fixed parents.

On each locked T2 interpolation parent this atom keeps the predicted expression
row SET and the 3D point cloud fixed, and re-decides *which expression row sits
at which coordinate* with the frozen J1-PROXY objective (POT entropic fused
Gromov-Wasserstein: expression state cost + internal-distance cost, alpha=0.5,
epsilon=0.005, square_loss, PGD, uniform marginals, max-normalised costs;
spec SHA256 4cf86109...).  The soft transport plan is converted to a hard
bijection by one pre-declared deterministic rule (column argmax with
margin-ordered greedy conflict resolution); any non-bijection, non-finite
value, or ledger mismatch fails closed.

Permutation semantics (batch3 contract): only ``X`` rows are permuted; ``obs``,
``var``, ``obsm`` and ``uns`` stay identical to the locked parent (the batch3
contract adapter requires ``obs_exact``/``obs_names_exact``), plus an additive
``uns["ve_j1_fgw_assignment"]`` provenance entry.  This deliberately differs
from B1-A4's writer, which moved ``obs.celltype`` with the row; here the
parent's per-position metadata stays at its position.

The heart board is gated by a mandatory pre-declared reference-quality audit
(J1-PROXY recorded a negative per-position nbhd_pearson on the wide heart
holdout bracket): thresholds are frozen in config_resolved.yaml BEFORE any
heart computation; if they are not met (and no authorised remediation holds)
the heart board is an explicit HOLD and only the embryo candidate is built.

Environment split (toolchain rule): the ``solve-worker`` runs under the
isolated ``.venvs/ve-t1-ot`` interpreter (POT) on plain npz problems and writes
only coupling npz intermediates; every other subcommand runs under the ve-core
interpreter with ``LD_LIBRARY_PATH`` set (system libstdc++ predates
GLIBCXX_3.4.29).

Subcommands (atomic writes; no-clobber on published candidates):

* ``input-lock``    -- hash-lock every input (parents, stages, panels, mirrors)
* ``env-probe``     -- record ve-t1-ot tool versions
* ``config-freeze`` -- write config_resolved.yaml with every pre-declared
                       threshold/rule BEFORE any audit or generation
* ``audit``         -- source-only heart reference-quality audit (no FGW)
* ``prepare``       -- build frozen problem.npz (M/C1/C2/p/q) + field meta
* ``solve``         -- dispatch the POT FGW worker for one board
* ``solve-worker``  -- worker: one POT entropic-FGW solve from npz to npz
* ``assign``        -- soft plan -> deterministic hard bijection (+ ledger)
* ``generate``      -- write the candidate h5ad through the batch3 writer
* ``contract``      -- batch3 contract adapter report
* ``checks``        -- geometry/protected checks + aggregate status
* ``nfs-proxy``     -- in-process locked NFS mirror vs pseudo-target
* ``determinism``   -- same-seed re-solve + re-assign + re-generate comparison
* ``score``         -- locked scorer wrapper (pseudo-target; budget 1/board)
* ``finalize``      -- TOOL_VERSIONS.json + deviations ledger
* ``manifest`` / ``verify`` -- stable artifact manifest + self-verify

Pre-declared constants below are fixed before any run; no grid search, no
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
        _knn_fingerprint,
        _labels,
        _matrix_digest,
        _matrix_equal,
        _names_digest,
        _nfs_like,
        _row_multiset_digest,
        _spatial_knn,
        _take_rows,
    )
    from scripts.t2_j1_proxy import (
        FGW_ALPHA,
        FGW_EPSILON,
        FGW_LOSS,
        FGW_MAX_ITER,
        FGW_SOLVER,
        FGW_TOL,
        KNN_K,
        N_REF,
        PCA_COMPONENTS,
        REG_K,
        VENV_PYTHON,
        _effective_sources,
        _worker_env,
        barycentric_expression,
        expression_latent,
        fgw_loss,
        fgw_loss_permutation,
        knn_neighbourhood_pseudobulk,
        max_normalise,
        neighbourhood_pearson,
        solve_fgw,
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
except ImportError:  # direct ``python scripts/t2_j1_fgw_assignment.py`` execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts.t2_j1_pairing import (
        _balanced_indices,
        _coords,
        _dense_float32,
        _knn_fingerprint,
        _labels,
        _matrix_digest,
        _matrix_equal,
        _names_digest,
        _nfs_like,
        _row_multiset_digest,
        _spatial_knn,
        _take_rows,
    )
    from scripts.t2_j1_proxy import (
        FGW_ALPHA,
        FGW_EPSILON,
        FGW_LOSS,
        FGW_MAX_ITER,
        FGW_SOLVER,
        FGW_TOL,
        KNN_K,
        N_REF,
        PCA_COMPONENTS,
        REG_K,
        VENV_PYTHON,
        _effective_sources,
        _worker_env,
        barycentric_expression,
        expression_latent,
        fgw_loss,
        fgw_loss_permutation,
        knn_neighbourhood_pseudobulk,
        max_normalise,
        neighbourhood_pearson,
        solve_fgw,
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
ATOM = "T2-J1-FGW-ASSIGNMENT-20260903-v1"
OUTPUT_DEFAULT = ROOT / "artifacts" / "tool_integration" / ATOM
SEED = 20260830
NORMALIZATION = "log_normalized"  # batch3 contract marker for T2

INTERFACE_ROOT = ROOT / "docs" / "batch3" / "interfaces"
VECKIT_ROOT = ROOT / "third_party" / "veckit"
T2_METRICS_PATH = VECKIT_ROOT / "T2" / "metrics.py"
CORE_METRICS_PATH = VECKIT_ROOT / "common" / "core_metrics.py"
SCORER_ENTRYPOINT = VECKIT_ROOT / "score_h5ad.py"
SCORER_LOCK_PATH = ROOT / "artifacts" / "tool_integration" / "P0-LOCK" / "locks" / "SCORER_LOCK.json"
TOOLCHAIN_LOCK_PATH = ROOT / "artifacts" / "tool_integration" / "P0-LOCK" / "locks" / "TOOLCHAIN_LOCK.json"
BOARD_INDEX_PATH = ROOT / "data" / "gene_panel" / "index.json"
CONTRACT_ADAPTER_PATH = INTERFACE_ROOT / "virtual_embryo_tools" / "contract_io.py"
PROXY_ATOM_DIR = ROOT / "artifacts" / "tool_integration" / "T2-J1-PROXY-20260903-v1"
PROXY_OBJECTIVE_SPEC = PROXY_ATOM_DIR / "intermediates" / "objective_spec.yaml"
PROXY_OBJECTIVE_SPEC_SHA256 = (
    "4cf861092b02fc1f2100350174051a16137228a533440c164f01d38f158110e7"
)

STAGE_FILES: dict[float, str] = {
    6.75: "data/E6.75.h5ad",
    7.25: "data/E7.25.h5ad",
    8.0: "data/E8.0.h5ad",
    8.25: "data/E8.25_late.h5ad",
    8.75: "data/E8.75.h5ad",
    9.5: "data/E9.5.h5ad",
}

# ---------------------------------------------------------------------------
# Pre-declared heart reference-audit thresholds (frozen in config_resolved.yaml
# BEFORE any heart computation; J1-PROXY H2 failure anchors: span 1.25 days,
# label intersection 5, fgw_full nbhd_pearson -0.102 vs H1 +0.370).
# ---------------------------------------------------------------------------
AUDIT_MAX_BRACKET_SPAN_DAYS = 0.75
AUDIT_MIN_LABEL_INTERSECTION = 10
AUDIT_MIN_CROSS_PEARSON = 0.0      # strictly greater, both directions
AUDIT_MIN_STAGE_SUPPORT = N_REF    # each bracket stage must provide >= 8000 cells
HEART_CONTROL_PROBE = (9.5, 8.75)  # H2 weak-side context probe, no threshold

# Coupling validation tolerance (fail closed beyond it).
MARGINAL_REL_TOL = 1e-6
NEGATIVE_MASS_TOL = 1e-12

ASSIGNMENT_RULE_ID = "column_argmax_margin_greedy_v1"
ASSIGNMENT_RULE_TEXT = (
    "column_argmax_margin_greedy_v1: (1) rank rows per position column by "
    "(-T[i,j], i) via np.argsort(-T, axis=0, kind='stable') so mass ties break "
    "to the lowest row index; (2) margin_j = T[top,j] - T[second,j]; "
    "(3) visit positions in (-margin_j, j) order via np.lexsort((arange(n), "
    "-margin)) so the most confident column is placed first and ties break to "
    "the lowest position index; (4) each position takes its highest-ranked "
    "still-unassigned row; (5) the result is a bijection by construction "
    "(n positions, n rows, greedy never strands a position) and is asserted. "
    "conflicts = positions whose top-ranked row was already taken. Fail closed "
    "on non-finite T, any T < -1e-12, wrong shape, or row/column marginal "
    "relative deviation > 1e-6 from uniform 1/n."
)


@dataclass(frozen=True)
class BoardSpec:
    slug: str
    board_key: str         # contract board key inside task T2
    task: str              # scorer --setting
    panel: str
    parent_path: str
    parent_sha256: str
    target_stage: float
    left_stage: float
    right_stage: float
    left_path: str
    right_path: str
    min_cells: int
    max_cells: int
    scorer_pseudo_target: str
    scorer_pseudo_reference: str
    scorer_truth_cells: int
    panel_genes: int
    intended_version: str  # coordinator-side registration version (advisory)

    @property
    def time_weight(self) -> float:
        """lambda: position of the target stage between the bracketing stages."""
        span = self.right_stage - self.left_stage
        if span <= 0:
            raise ValueError(f"{self.slug}: bracketing stages must be ordered")
        if not (self.left_stage < self.target_stage < self.right_stage):
            raise ValueError(f"{self.slug}: target stage must be interior")
        return (self.target_stage - self.left_stage) / span


BOARD_SPECS: dict[str, BoardSpec] = {
    "T2_embryo_val_interp": BoardSpec(
        slug="T2_embryo_val_interp",
        board_key="embryo:val_interp",
        task="embryo",
        panel="data/gene_panel/T2__embryo__val_interp.genes.txt",
        parent_path="submissions/candidates/T2_embryo_val_interp/v0002_g1_formal_log_rms/submission.h5ad",
        parent_sha256="392c470e4af35797ad27c100e773c1a7695c989baed95c911fceb0b5d7965fd4",
        target_stage=7.5,
        left_stage=7.25,
        right_stage=8.0,
        left_path=STAGE_FILES[7.25],
        right_path=STAGE_FILES[8.0],
        min_cells=583,
        max_cells=5000,
        scorer_pseudo_target="data/E7.25.h5ad",
        scorer_pseudo_reference="data/E6.75.h5ad",
        scorer_truth_cells=13295,
        panel_genes=498,
        intended_version="v0008",
    ),
    "T2_heart_val_interp": BoardSpec(
        slug="T2_heart_val_interp",
        board_key="heart:val_interp",
        task="heart",
        panel="data/gene_panel/T2__heart__val_interp.genes.txt",
        parent_path="submissions/candidates/T2_heart_val_interp/v0007_t2_s3_l1_pycpd/submission.h5ad",
        parent_sha256="0ca4f217915ed53dfa35370cc8026704531eefd5e701f63b976433b9ce4dd416",
        target_stage=8.5,
        left_stage=8.25,
        right_stage=8.75,
        left_path=STAGE_FILES[8.25],
        right_path=STAGE_FILES[8.75],
        min_cells=1000,
        max_cells=17616,
        scorer_pseudo_target="data/E8.75.h5ad",
        scorer_pseudo_reference="data/E8.25_late.h5ad",
        scorer_truth_cells=24826,
        panel_genes=500,
        intended_version="v0009",
    ),
}
BOARD_ORDER = tuple(BOARD_SPECS)

# ---------------------------------------------------------------------------
# Frozen pre-declaration (written verbatim by config-freeze; drift = new atom).
# ---------------------------------------------------------------------------


def _config_text() -> str:
    lines = [
        f"atom: {ATOM}",
        "task: T2-J1-FGW-ASSIGNMENT",
        f"seed: {SEED}",
        "allow_network: false",
        "allow_external_downloads: false",
        "allow_server_submission: false",
        "candidate_generation: true",
        "budgets: {small_smoke: 1, full_generation_per_lane: 1, "
        "final_local_score_per_lane: 1}",
        "derived_from:",
        "  atom: T2-J1-PROXY-20260903-v1",
        "  gate: J1_PROXY_PASS",
        "  objective_spec: artifacts/tool_integration/T2-J1-PROXY-20260903-v1/"
        "intermediates/objective_spec.yaml",
        f"  objective_spec_sha256: {PROXY_OBJECTIVE_SPEC_SHA256}",
        "objective: >",
        "  frozen entropic FGW (POT ot.gromov.entropic_fused_gromov_wasserstein):",
        f"  alpha={FGW_ALPHA} epsilon={FGW_EPSILON} max_iter={FGW_MAX_ITER} "
        f"tol={FGW_TOL} loss={FGW_LOSS} solver={FGW_SOLVER}; uniform marginals;",
        "  costs max-normalised (each matrix divided by its own max); expression",
        f"  features PCA(n_components={PCA_COMPONENTS}, random_state=0) fit on the",
        "  parent expression row set; C1 = pairwise euclidean between row",
        "  features; C2 = pairwise euclidean between parent target positions (3D);",
        "  M = squared euclidean between row features and the time-weighted",
        f"  kNN(k={REG_K}) position reference features. Pairwise matrices use the",
        "  Gram identity with non-negativity floor (same math as the proxy's",
        "  broadcasting, memory-safe at n~6000).",
        "reference_construction:",
        "  source: bracketing observed stages only (never hidden-target expression)",
        f"  n_ref_per_stage: {N_REF} (celltype-stratified, derived seed; if a stage",
        "    has fewer cells use all and fail the audit support criterion)",
        "  frame: per-stage canonical (centre + PCA + RMS,",
        "    t2_s3_shape_field.canonicalize); det=+1 axis flip chosen by symmetric",
        "    Chamfer against the parent target cloud (best_proper_flip)",
        f"  regression: kNN(k={REG_K}) mean of bracketing-stage expression at each",
        "    parent position, time-weighted lambda=(t_target-t_left)/(t_right-t_left)",
        "  embryo: bracket [7.25, 8.0], target 7.5, lambda=0.333333",
        "  heart: bracket [8.25, 8.75], target 8.5, lambda=0.500000",
        "assignment_rule: >",
        f"  {ASSIGNMENT_RULE_TEXT}",
        "heart_reference_audit:  # pre-declared BEFORE any heart computation",
        "  rationale: J1-PROXY H2 (bracket [8.25, 9.5], 1.25 days, label",
        "    intersection 5) recorded fgw_full nbhd_pearson -0.102 vs H1 +0.370;",
        "    the heart candidate must not repeat a weak wide-bracket reference",
        "  measurements (source data only, no FGW solve, fixed seeds; the audit",
        "    supports are the same stratified n_ref subsamples the reference",
        "    construction will use):",
        f"  A1_bracket_span_days: candidate [8.25, 8.75] = 0.50 must be "
        f"<= {AUDIT_MAX_BRACKET_SPAN_DAYS}",
        f"  A2_label_intersection: |vocab(left support) ∩ vocab(right support)| "
        f">= {AUDIT_MIN_LABEL_INTERSECTION}",
        f"  A3_cross_stage_probe: neighbourhood_pearson (kNN{KNN_K} self-inclusive",
        "    pseudobulk, gene-centred on truth means; the J1-PROXY mirror) of the",
        f"    single-stage kNN(k={REG_K}) regressed reference from one bracket stage",
        "    at the other bracket stage's full observed cloud vs that stage's true",
        f"    expression must be > {AUDIT_MIN_CROSS_PEARSON} in BOTH directions",
        "    (8.25->8.75 and 8.75->8.25); context control 9.5->8.75 (the H2 weak",
        "    side) is recorded without a threshold",
        f"  A4_support: each bracket stage provides >= {AUDIT_MIN_STAGE_SUPPORT} cells",
        "  decision_rule: A1..A4 all PASS -> heart candidate with the frozen",
        "    two-stage reference; else exactly one authorised remediation may be",
        "    applied once (single adjacent-stage reference / enlarged label",
        "    intersection / larger support sampling) and recorded as a deviation;",
        "    if none holds -> heart board explicit HOLD, embryo-only atom",
        "  embryo_note: the same quantities are computed for the embryo bracket",
        "    [7.25, 8.0] for the record; the embryo board is not gated by this",
        "    audit (J1-PROXY H1 already evidenced a good reference at +0.370)",
        "boards:",
    ]
    for slug in BOARD_ORDER:
        spec = BOARD_SPECS[slug]
        lines.extend(
            [
                f"  {slug}:",
                f"    parent_path: {spec.parent_path}",
                f"    parent_sha256: {spec.parent_sha256}",
                f"    panel: {spec.panel}  # {spec.panel_genes} genes",
                f"    target_stage: {spec.target_stage}",
                f"    bracket: [{spec.left_stage}, {spec.right_stage}]",
                f"    time_weight: {spec.time_weight:.6f}",
                f"    contract_cells: [{spec.min_cells}, {spec.max_cells}]",
                f"    intended_version: {spec.intended_version}  # advisory; coordinator registers",
                f"    scorer_pseudo_target: {spec.scorer_pseudo_target}",
                f"    scorer_pseudo_reference: {spec.scorer_pseudo_reference}",
            ]
        )
    lines.extend(
        [
            "permutation_semantics: only X rows are permuted; obs/var/obsm/uns are",
            "  identical to the locked parent (batch3 contract obs_exact) plus an",
            "  additive uns.ve_j1_fgw_assignment provenance entry; expression row",
            "  multiset digest must match the parent exactly",
            "protected_checks:",
            "  - coordinate/obs_names/var/gene-order hashes identical to parent",
            "  - expression row multiset identical (permutation semantics)",
            "  - X replay exact: candidate.X == parent.X[placement]",
            "  - bijection asserted; conflict count recorded",
            f"  - kNN{KNN_K} spatial graph fingerprint identical (coords unchanged)",
            f"  - kNN{KNN_K} neighbourhood expression-row overlap recorded (effect",
            "    size, not a quality gate)",
            "  - determinism: same-seed re-solve must reproduce the coupling",
            "    bit-identically and the regenerated h5ad must be byte-identical",
            "  - NFS proxy: locked veckit neighborhood_mmd mirror (n=2000, seed=0)",
            "    of candidate AND parent against the board pseudo-target; direction",
            "    recorded, no leaderboard claim",
            "scorer: locked third_party/veckit/score_h5ad.py (hash-checked against",
            "  P0-LOCK SCORER_LOCK.json), P0 command template, --seed 20260830;",
            "  pseudo-target is a training stage AND part of the reference",
            "  construction (circularity caveat declared in RESULT); local numbers",
            "  are not leaderboard previews",
            "deviations: []  # filled only via metrics/deviations.json if needed",
            "",
        ]
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# small shared helpers
# ---------------------------------------------------------------------------


def _relative(path: Path) -> str:
    return Path(path).resolve().relative_to(ROOT).as_posix()


def _rel_or_abs(path: Path) -> str:
    try:
        return _relative(path)
    except ValueError:
        return str(Path(path).resolve())


def _gram_pairwise_euclidean(features: np.ndarray) -> np.ndarray:
    """Pairwise euclidean distances via the Gram identity (memory-safe)."""
    values = np.asarray(features, dtype=np.float64)
    sq = np.sum(values * values, axis=1)
    d2 = sq[:, None] + sq[None, :] - 2.0 * (values @ values.T)
    return np.sqrt(np.maximum(d2, 0.0))


def _gram_squared_cross(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """Squared euclidean cross-distances via the Gram identity."""
    a = np.asarray(left, dtype=np.float64)
    b = np.asarray(right, dtype=np.float64)
    aa = np.sum(a * a, axis=1)
    bb = np.sum(b * b, axis=1)
    d2 = aa[:, None] + bb[None, :] - 2.0 * (a @ b.T)
    return np.maximum(d2, 0.0)


def _ref_seed(board: str, side: str) -> int:
    return _derived_seed(SEED, ATOM, board, "ref", side)


# ---------------------------------------------------------------------------
# reference construction (frozen machinery; mirrors J1-PROXY prepare_holdout)
# ---------------------------------------------------------------------------


def load_stage_support(
    stage_path: Path, panel_path: Path, *, board: str, side: str
) -> dict[str, Any]:
    """Panel-aligned observed stage, celltype-stratified support subsample."""
    stage = load_t2_input(stage_path, panel_path)
    labels_all = _labels(stage, stage_path)
    seed = _ref_seed(board, side)
    if len(labels_all) > N_REF:
        sub = _balanced_indices(labels_all, N_REF, seed)
    else:
        sub = np.arange(len(labels_all), dtype=np.int64)
    return {
        "X": _dense_float32(stage.X)[sub].astype(np.float64),
        "coords": _coords(stage, stage_path)[sub],
        "labels": labels_all[sub],
        "vocabulary_full": sorted(set(map(str, labels_all))),
        "n_cells_stage": int(len(labels_all)),
        "n_support": int(len(sub)),
        "subsample_indices": sub,
        "seed": int(seed),
        "path": str(stage_path),
    }


def build_position_reference(
    spec: BoardSpec, z_target: np.ndarray, *, preloaded: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Time-weighted kNN-regressed expression reference at each target position.

    Both bracketing stages are canonicalised and proper-flip aligned into the
    parent target frame; only observed source stages are used.
    """
    from sklearn.neighbors import NearestNeighbors

    panel_path = ROOT / spec.panel
    lam = spec.time_weight
    supports: dict[str, dict[str, Any]] = {}
    if preloaded is not None:
        supports = dict(preloaded)
    for side, stage_path in (("left", ROOT / spec.left_path), ("right", ROOT / spec.right_path)):
        if side not in supports:
            supports[side] = load_stage_support(
                stage_path, panel_path, board=spec.slug, side=side
            )
    g_hat: np.ndarray | None = None
    meta: dict[str, Any] = {}
    for side in ("left", "right"):
        support = supports[side]
        if support["n_support"] < REG_K:
            raise ValueError(
                f"{spec.slug}/{side}: support {support['n_support']} < REG_K={REG_K}"
            )
        z_ref, _c, _r, _a = canonicalize(support["coords"])
        flip, flip_scores = best_proper_flip(z_ref, z_target)
        z_ref = z_ref * flip
        weight = (1.0 - lam) if side == "left" else lam
        knn = NearestNeighbors(n_neighbors=REG_K).fit(z_ref)
        idx = knn.kneighbors(z_target, return_distance=False)
        contribution = weight * support["X"][idx].mean(axis=1)
        g_hat = contribution if g_hat is None else g_hat + contribution
        meta[side] = {
            "stage": spec.left_stage if side == "left" else spec.right_stage,
            "path": _rel_or_abs(Path(support["path"])),
            "n_cells_stage": support["n_cells_stage"],
            "n_support": support["n_support"],
            "support_seed": support["seed"],
            "weight": float(weight),
            "flip": [int(v) for v in flip],
            "flip_chamfer": {k: float(v) for k, v in flip_scores.items()},
            "vocabulary_size_full": len(support["vocabulary_full"]),
            "vocabulary_size_support": int(len(set(map(str, support["labels"])))),
        }
    assert g_hat is not None
    if not np.isfinite(g_hat).all():
        raise ValueError(f"{spec.slug}: reference contains non-finite values")
    return {"g_hat": g_hat, "meta": meta, "supports": supports}


# ---------------------------------------------------------------------------
# heart reference audit (mandatory first step; source data only, no FGW)
# ---------------------------------------------------------------------------


def single_stage_cross_probe(
    src_support: Mapping[str, Any], eval_stage_path: Path, panel_path: Path
) -> dict[str, Any]:
    """Reference from ONE stage at another stage's positions vs that truth.

    The source support is the same stratified subsample the candidate reference
    will use; evaluation runs on the full observed eval-stage cloud with the
    J1-PROXY nbhd_pearson mirror (kNN15 self-inclusive pseudobulk, gene-centred
    on truth means).
    """
    from sklearn.neighbors import NearestNeighbors

    ev = load_t2_input(eval_stage_path, panel_path)
    X_true = _dense_float32(ev.X).astype(np.float64)
    coords_true = _coords(ev, eval_stage_path)
    z_true, _c, _r, _a = canonicalize(coords_true)
    z_src, _c2, _r2, _a2 = canonicalize(np.asarray(src_support["coords"], dtype=np.float64))
    flip, flip_scores = best_proper_flip(z_src, z_true)
    z_src = z_src * flip
    knn = NearestNeighbors(n_neighbors=REG_K).fit(z_src)
    idx = knn.kneighbors(z_true, return_distance=False)
    reference = np.asarray(src_support["X"], dtype=np.float64)[idx].mean(axis=1)
    pearson = neighbourhood_pearson(reference, X_true, coords_true)
    return {
        "eval_stage_path": _rel_or_abs(eval_stage_path),
        "n_eval_cells": int(len(coords_true)),
        "n_support": int(src_support["n_support"]),
        "flip": [int(v) for v in flip],
        "flip_chamfer": {k: float(v) for k, v in flip_scores.items()},
        "nbhd_pearson": pearson,
    }


def command_audit(out_dir: Path) -> dict[str, Any]:
    """Pre-declared heart reference-quality audit + embryo record values."""
    out_dir = Path(out_dir)
    started = time.time()
    report: dict[str, Any] = {
        "schema": "ve.t2.j1-fgw-assignment.reference-audit.v1",
        "atom": ATOM,
        "seed": SEED,
        "thresholds": {
            "A1_max_bracket_span_days": AUDIT_MAX_BRACKET_SPAN_DAYS,
            "A2_min_label_intersection": AUDIT_MIN_LABEL_INTERSECTION,
            "A3_min_cross_pearson_strictly_greater": AUDIT_MIN_CROSS_PEARSON,
            "A4_min_stage_support": AUDIT_MIN_STAGE_SUPPORT,
        },
        "anchors": {
            "j1_proxy_H1_fgw_full_nbhd_pearson": 0.36993638,
            "j1_proxy_H2_fgw_full_nbhd_pearson": -0.10215440,
            "j1_proxy_H2_bracket_span_days": 1.25,
            "j1_proxy_H2_label_intersection": 5,
        },
        "target_used": False,
        "boards": {},
    }
    for slug in BOARD_ORDER:
        spec = BOARD_SPECS[slug]
        panel_path = ROOT / spec.panel
        left = load_stage_support(ROOT / spec.left_path, panel_path, board=slug, side="left")
        right = load_stage_support(ROOT / spec.right_path, panel_path, board=slug, side="right")
        support_intersection = sorted(
            set(map(str, left["labels"])) & set(map(str, right["labels"]))
        )
        full_intersection = sorted(
            set(left["vocabulary_full"]) & set(right["vocabulary_full"])
        )
        probe_lr = single_stage_cross_probe(left, ROOT / spec.right_path, panel_path)
        probe_rl = single_stage_cross_probe(right, ROOT / spec.left_path, panel_path)
        span = spec.right_stage - spec.left_stage
        a1 = bool(span <= AUDIT_MAX_BRACKET_SPAN_DAYS)
        a2 = bool(len(support_intersection) >= AUDIT_MIN_LABEL_INTERSECTION)
        a3 = bool(
            probe_lr["nbhd_pearson"] > AUDIT_MIN_CROSS_PEARSON
            and probe_rl["nbhd_pearson"] > AUDIT_MIN_CROSS_PEARSON
        )
        a4 = bool(
            left["n_support"] >= AUDIT_MIN_STAGE_SUPPORT
            and right["n_support"] >= AUDIT_MIN_STAGE_SUPPORT
        )
        report["boards"][slug] = {
            "bracket": [spec.left_stage, spec.right_stage],
            "bracket_span_days": float(span),
            "time_weight": spec.time_weight,
            "label_intersection_support": {
                "n": len(support_intersection),
                "labels": support_intersection,
            },
            "label_intersection_full_stage": {
                "n": len(full_intersection),
                "labels": full_intersection,
            },
            "support": {
                "left": {"stage": spec.left_stage, "n_cells": left["n_cells_stage"],
                         "n_support": left["n_support"], "seed": left["seed"]},
                "right": {"stage": spec.right_stage, "n_cells": right["n_cells_stage"],
                          "n_support": right["n_support"], "seed": right["seed"]},
            },
            "probe_left_to_right": probe_lr,
            "probe_right_to_left": probe_rl,
            "criteria": {"A1_span": a1, "A2_intersection": a2, "A3_cross_pearson": a3, "A4_support": a4},
            "all_pass": bool(a1 and a2 and a3 and a4),
        }
        _append_run_log(
            out_dir,
            f"audit {slug}: span={span:.2f} inter={len(support_intersection)} "
            f"pearson_lr={probe_lr['nbhd_pearson']:+.4f} pearson_rl={probe_rl['nbhd_pearson']:+.4f} "
            f"all_pass={report['boards'][slug]['all_pass']}",
        )

    # heart context control: the H2 weak side (E9.5 -> E8.75), no threshold
    heart = BOARD_SPECS["T2_heart_val_interp"]
    panel_path = ROOT / heart.panel
    control_src = load_stage_support(
        ROOT / STAGE_FILES[HEART_CONTROL_PROBE[0]], panel_path,
        board=heart.slug, side="control_e9.5",
    )
    control = single_stage_cross_probe(
        control_src, ROOT / STAGE_FILES[HEART_CONTROL_PROBE[1]], panel_path
    )
    control["note"] = (
        "H2 weak-side context probe (E9.5 reference at E8.75 positions); "
        "recorded for comparison with the J1-PROXY H2 negative pearson; no threshold"
    )
    report["heart_control_probe_9.5_to_8.75"] = control

    heart_pass = report["boards"]["T2_heart_val_interp"]["all_pass"]
    report["heart_verdict"] = "PROCEED" if heart_pass else "HOLD"
    report["decision_rule"] = (
        "A1..A4 all PASS -> heart candidate with the frozen two-stage reference; "
        "else one authorised remediation once, else heart HOLD (embryo-only atom)"
    )
    report["wall_seconds"] = time.time() - started
    _write_json_atomic(out_dir / "metrics" / "reference_audit.json", report)
    _append_run_log(out_dir, f"audit: heart_verdict={report['heart_verdict']}")
    return {"step": "audit", "heart_verdict": report["heart_verdict"]}


# ---------------------------------------------------------------------------
# frozen problem construction + POT solve
# ---------------------------------------------------------------------------


def prepare_board(spec: BoardSpec) -> dict[str, Any]:
    """Load the parent, build the frozen FGW problem (M/C1/C2/p/q) in memory."""
    parent_path = ROOT / spec.parent_path
    if sha256_file(parent_path) != spec.parent_sha256:
        raise RuntimeError(f"{spec.slug}: parent SHA256 drift vs locked value")
    parent = load_t2_input(parent_path, ROOT / spec.panel)
    if not spec.min_cells <= parent.n_obs <= spec.max_cells:
        raise ValueError(f"{spec.slug}: parent n_obs outside board limits")
    X = _dense_float32(parent.X).astype(np.float64)
    coords = _coords(parent, parent_path)

    z_target, center, rms, _axes = canonicalize(coords)
    reference = build_position_reference(spec, z_target)
    g_hat = reference["g_hat"]

    latent, pca = expression_latent(X, PCA_COMPONENTS)
    feat_ref = np.asarray(pca.transform(g_hat), dtype=np.float64)
    C1 = max_normalise(_gram_pairwise_euclidean(latent))
    C2 = max_normalise(_gram_pairwise_euclidean(coords))
    M = max_normalise(_gram_squared_cross(latent, feat_ref))
    n = len(X)
    p = np.full(n, 1.0 / n)
    q = np.full(n, 1.0 / n)
    return {
        "spec": spec,
        "n": n,
        "M": M,
        "C1": C1,
        "C2": C2,
        "p": p,
        "q": q,
        "g_hat": g_hat,
        "reference_meta": reference["meta"],
        "frame": {"center": center, "rms": rms},
        "pca_components": int(getattr(pca, "n_components_", PCA_COMPONENTS)),
    }


def command_prepare(out_dir: Path, *, board: str) -> dict[str, Any]:
    out_dir = Path(out_dir)
    _heart_gate_guard(out_dir, board)
    spec = BOARD_SPECS[board]
    hold_dir = out_dir / "intermediates" / board
    hold_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    prepared = prepare_board(spec)
    payload = {"M": prepared["M"], "C1": prepared["C1"], "C2": prepared["C2"],
               "p": prepared["p"], "q": prepared["q"]}
    problem_path = hold_dir / "problem.npz"
    if problem_path.is_file():
        existing = np.load(problem_path)
        if not all(np.array_equal(existing[k], payload[k]) for k in payload):
            raise RuntimeError(
                f"problem drift for {board}: frozen problem npz differs; refusing silent overwrite"
            )
        _append_run_log(out_dir, f"prepare {board}: problem.npz verified identical (resume)")
    else:
        _write_npz_atomic(problem_path, **payload)
    field_meta = {
        "schema": "ve.t2.j1-fgw-assignment.field-meta.v1",
        "atom": ATOM,
        "board": board,
        "seed": SEED,
        "n_cells": prepared["n"],
        "parent_path": spec.parent_path,
        "parent_sha256": spec.parent_sha256,
        "target_stage": spec.target_stage,
        "bracket": [spec.left_stage, spec.right_stage],
        "time_weight": spec.time_weight,
        "reference": prepared["reference_meta"],
        "frame": {
            "center": [float(v) for v in prepared["frame"]["center"]],
            "rms": float(prepared["frame"]["rms"]),
            "convention": "parent canonical frame (centre + PCA + RMS); bracket clouds proper-flip aligned",
        },
        "pca_components": prepared["pca_components"],
        "objective": {
            "alpha": FGW_ALPHA,
            "epsilon": FGW_EPSILON,
            "max_iter": FGW_MAX_ITER,
            "tol": FGW_TOL,
            "loss": FGW_LOSS,
            "solver": FGW_SOLVER,
            "marginals": "uniform",
            "normalisation": "each cost matrix divided by its own max entry",
            "spec": _relative(PROXY_OBJECTIVE_SPEC),
            "spec_sha256": PROXY_OBJECTIVE_SPEC_SHA256,
        },
        "target_used": False,
        "wall_seconds": time.time() - started,
    }
    _write_json_atomic(hold_dir / "field_meta.json", field_meta)
    _append_run_log(
        out_dir,
        f"prepare {board}: n={prepared['n']} lambda={spec.time_weight:.4f} "
        f"wall={field_meta['wall_seconds']:.1f}s",
    )
    return {"step": "prepare", "board": board, "n": prepared["n"]}


def command_solve_worker(
    *, problem_path: Path, coupling_path: Path, meta_path: Path, board: str
) -> dict[str, Any]:
    """Worker entry (ve-t1-ot): solve the frozen problem with POT, write npz."""
    bundle = np.load(Path(problem_path))
    T, meta = solve_fgw(
        bundle["M"], bundle["C1"], bundle["C2"], bundle["p"], bundle["q"],
        alpha=FGW_ALPHA, epsilon=FGW_EPSILON, max_iter=FGW_MAX_ITER, tol=FGW_TOL,
    )
    meta.update(
        {
            "schema": "ve.t2.j1-fgw-assignment.solve-meta.v1",
            "atom": ATOM,
            "board": board,
            "seed": SEED,
            "problem_sha256": sha256_file(problem_path),
        }
    )
    _write_npz_atomic(Path(coupling_path), T=T)
    _write_json_atomic(Path(meta_path), meta)
    return {"step": "solve-worker", "board": board, "wall_seconds": meta["wall_seconds"]}


def command_solve(out_dir: Path, *, board: str) -> dict[str, Any]:
    out_dir = Path(out_dir)
    hold_dir = out_dir / "intermediates" / board
    problem_path = hold_dir / "problem.npz"
    coupling_path = hold_dir / "transport_plan.npz"
    meta_path = hold_dir / "solve_meta.json"
    if not problem_path.is_file():
        raise FileNotFoundError(f"missing problem for {board}; run prepare first")
    if coupling_path.is_file() and meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("problem_sha256") == sha256_file(problem_path):
            return {"step": "solve", "board": board, "status": "already_solved"}
        raise RuntimeError(f"stale coupling for {board}: problem changed since solve")
    if not VENV_PYTHON.is_file():
        raise RuntimeError(f"missing tool interpreter: {VENV_PYTHON}")
    t0 = time.time()
    command = [
        str(VENV_PYTHON),
        "-m",
        "scripts.t2_j1_fgw_assignment",
        "solve-worker",
        "--problem",
        str(problem_path),
        "--coupling",
        str(coupling_path),
        "--meta",
        str(meta_path),
        "--board",
        board,
    ]
    proc = subprocess.run(
        command, cwd=ROOT, capture_output=True, text=True, env=_worker_env(), timeout=14400
    )
    if proc.returncode != 0:
        raise RuntimeError(f"FGW solve failed for {board}: {proc.stderr[-2000:]}")
    wall = time.time() - t0
    _append_run_log(out_dir, f"solve {board}: wall={wall:.1f}s")
    return {"step": "solve", "board": board, "wall_seconds": wall}


# ---------------------------------------------------------------------------
# deterministic soft -> discrete assignment (pre-declared rule; fail closed)
# ---------------------------------------------------------------------------


def validate_coupling(T: np.ndarray, n: int) -> dict[str, float]:
    coupling = np.asarray(T, dtype=np.float64)
    if coupling.shape != (n, n):
        raise ValueError(f"coupling shape {coupling.shape} != ({n}, {n})")
    if not np.isfinite(coupling).all():
        raise ValueError("coupling contains non-finite values")
    if (coupling < -NEGATIVE_MASS_TOL).any():
        raise ValueError("coupling contains negative mass beyond tolerance")
    expected = 1.0 / n
    row_dev = float(np.max(np.abs(coupling.sum(axis=1) - expected)) / expected)
    col_dev = float(np.max(np.abs(coupling.sum(axis=0) - expected)) / expected)
    if max(row_dev, col_dev) > MARGINAL_REL_TOL:
        raise ValueError(
            f"coupling marginals deviate from uniform by more than {MARGINAL_REL_TOL}: "
            f"row {row_dev:.3e}, col {col_dev:.3e}"
        )
    return {"row_marginal_rel_dev_max": row_dev, "col_marginal_rel_dev_max": col_dev}


def assign_from_plan(T: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
    """Pre-declared deterministic soft->discrete rule (see ASSIGNMENT_RULE_TEXT)."""
    coupling = np.asarray(T, dtype=np.float64)
    n = coupling.shape[0]
    marginals = validate_coupling(coupling, n)
    order = np.argsort(-coupling, axis=0, kind="stable").astype(np.int32)
    top_mass = coupling[order[0].astype(np.int64), np.arange(n)]
    second_mass = coupling[order[1].astype(np.int64), np.arange(n)]
    margin = top_mass - second_mass
    visit = np.lexsort((np.arange(n), -margin))
    placement = np.full(n, -1, dtype=np.int64)
    taken = np.zeros(n, dtype=bool)
    conflicts = 0
    depth_sum = 0
    max_depth = 0
    for j_raw in visit:
        j = int(j_raw)
        column = order[:, j]
        for depth in range(n):
            row = int(column[depth])
            if not taken[row]:
                placement[j] = row
                taken[row] = True
                if depth > 0:
                    conflicts += 1
                depth_sum += depth
                if depth > max_depth:
                    max_depth = depth
                break
        else:  # pragma: no cover - unreachable with n positions and n rows
            raise RuntimeError("assignment stranded a position; not a bijection")
    if not np.array_equal(np.sort(placement), np.arange(n, dtype=np.int64)):
        raise AssertionError("assignment is not a bijection")
    stats: dict[str, Any] = {
        "rule": ASSIGNMENT_RULE_ID,
        "n": n,
        "conflicts": int(conflicts),
        "conflict_rate": float(conflicts / n),
        "mean_rank_depth": float(depth_sum / n),
        "max_rank_depth": int(max_depth),
        "mass_captured": float(np.sum(coupling[placement, np.arange(n)])),
        "mass_top_sum": float(np.sum(top_mass)),
        "mass_capture_ratio": float(
            np.sum(coupling[placement, np.arange(n)]) / np.sum(top_mass)
        ),
        "n_moved_vs_parent": int(np.sum(placement != np.arange(n))),
        "effective_sources": _effective_sources(coupling),
        **marginals,
    }
    return placement, stats


def command_assign(out_dir: Path, *, board: str) -> dict[str, Any]:
    out_dir = Path(out_dir)
    hold_dir = out_dir / "intermediates" / board
    coupling_path = hold_dir / "transport_plan.npz"
    meta_path = hold_dir / "solve_meta.json"
    problem_path = hold_dir / "problem.npz"
    for required in (coupling_path, meta_path, problem_path):
        if not required.is_file():
            raise FileNotFoundError(f"missing {required}; run prepare/solve first")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("problem_sha256") != sha256_file(problem_path):
        raise RuntimeError(f"stale coupling for {board}: problem npz changed since solve")
    assignment_npz = hold_dir / "assignment.npz"
    assignment_tsv = hold_dir / "assignment.tsv"
    assignment_meta_path = hold_dir / "assignment_meta.json"
    if assignment_npz.is_file() or assignment_tsv.is_file():
        raise FileExistsError(f"refusing to overwrite existing assignment for {board}")

    started = time.time()
    T = np.load(coupling_path)["T"]
    placement, stats = assign_from_plan(T)
    _write_npz_atomic(assignment_npz, placement=placement)

    spec = BOARD_SPECS[board]
    import anndata as ad

    obs_names = [str(v) for v in ad.read_h5ad(ROOT / spec.parent_path).obs_names]
    order = np.argsort(-np.asarray(T, dtype=np.float64), axis=0, kind="stable")
    lines = [
        "position_index\tposition_obs_name\tdonor_row_index\tdonor_obs_name\t"
        "coupling_mass\tcolumn_top_mass\tmargin\trank_depth\tconflict"
    ]
    for j in range(len(placement)):
        row = int(placement[j])
        top = float(T[order[0, j], j])
        second = float(T[order[1, j], j])
        depth = int(np.flatnonzero(order[:, j] == row)[0])
        lines.append(
            f"{j}\t{obs_names[j]}\t{row}\t{obs_names[row]}\t{T[row, j]:.10e}\t"
            f"{top:.10e}\t{top - second:.10e}\t{depth}\t{int(depth > 0)}"
        )
    temporary = assignment_tsv.with_name(assignment_tsv.name + ".tmp")
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    temporary.replace(assignment_tsv)

    bundle = np.load(problem_path)
    identity_loss = fgw_loss_permutation(
        bundle["M"], bundle["C1"], bundle["C2"], np.arange(len(placement)), FGW_ALPHA
    )
    assigned_loss = fgw_loss_permutation(
        bundle["M"], bundle["C1"], bundle["C2"], placement, FGW_ALPHA
    )
    soft_loss = fgw_loss(bundle["M"], bundle["C1"], bundle["C2"], T, FGW_ALPHA)
    ledger = {
        "schema": "ve.t2.j1-fgw-assignment.assignment-meta.v1",
        "atom": ATOM,
        "board": board,
        "seed": SEED,
        "coupling_sha256": sha256_file(coupling_path),
        "problem_sha256": sha256_file(problem_path),
        "solve_meta": meta,
        "assignment": stats,
        "fgw_objective": {
            "soft_plan": soft_loss,
            "identity_parent_pairing": identity_loss,
            "hard_assignment": assigned_loss,
        },
        "wall_seconds": time.time() - started,
        "target_used": False,
    }
    _write_json_atomic(assignment_meta_path, ledger)
    _append_run_log(
        out_dir,
        f"assign {board}: conflicts={stats['conflicts']} "
        f"mass_capture={stats['mass_capture_ratio']:.4f} moved={stats['n_moved_vs_parent']}",
    )
    return {"step": "assign", "board": board, **stats}


# ---------------------------------------------------------------------------
# candidate generation through the batch3 writer + contract + checks
# ---------------------------------------------------------------------------


def _contract_io() -> Any:
    if str(INTERFACE_ROOT) not in sys.path:
        sys.path.insert(0, str(INTERFACE_ROOT))
    from virtual_embryo_tools import contract_io

    return contract_io


def _provenance(spec: BoardSpec, assignment_meta: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "atom_id": ATOM,
        "board": spec.slug,
        "official_board_key": f"T2:{spec.board_key}",
        "method": "j1_fgw_soft_assignment_permutation",
        "assignment_rule": ASSIGNMENT_RULE_ID,
        "parent_submission": spec.parent_path,
        "parent_sha256": spec.parent_sha256,
        "objective_spec": _relative(PROXY_OBJECTIVE_SPEC),
        "objective_spec_sha256": PROXY_OBJECTIVE_SPEC_SHA256,
        "objective": f"entropic FGW (POT) alpha={FGW_ALPHA} epsilon={FGW_EPSILON} "
        f"max_iter={FGW_MAX_ITER} tol={FGW_TOL} loss={FGW_LOSS} solver={FGW_SOLVER}",
        "reference": {
            "bracket": [spec.left_stage, spec.right_stage],
            "time_weight": spec.time_weight,
            "n_ref_per_stage": N_REF,
            "reg_k": REG_K,
        },
        "permutation_semantics": "only X rows permuted; obs/var/obsm/uns identical to parent",
        "conflicts": assignment_meta["assignment"]["conflicts"],
        "n_moved_vs_parent": assignment_meta["assignment"]["n_moved_vs_parent"],
        "seed": SEED,
        "source_only": True,
        "target_used": False,
    }


def _heart_gate_guard(out_dir: Path, board: str) -> None:
    """Fail closed: heart compute requires a recorded PROCEED audit verdict."""
    if board != "T2_heart_val_interp":
        return
    audit_path = Path(out_dir) / "metrics" / "reference_audit.json"
    if not audit_path.is_file():
        raise RuntimeError("heart board requires the pre-declared reference audit first")
    verdict = json.loads(audit_path.read_text(encoding="utf-8")).get("heart_verdict")
    if verdict != "PROCEED":
        raise RuntimeError(
            f"heart reference audit verdict is {verdict!r} (not PROCEED); heart board is HOLD"
        )


def command_generate(out_dir: Path, *, board: str) -> dict[str, Any]:
    out_dir = Path(out_dir)
    _heart_gate_guard(out_dir, board)
    spec = BOARD_SPECS[board]
    hold_dir = out_dir / "intermediates" / board
    placement = np.load(hold_dir / "assignment.npz")["placement"]
    assignment_meta = json.loads((hold_dir / "assignment_meta.json").read_text(encoding="utf-8"))
    parent_path = ROOT / spec.parent_path
    candidate_path = out_dir / "candidates" / board / "submission.h5ad"
    if candidate_path.exists():
        raise FileExistsError(f"refusing to overwrite candidate {candidate_path}")

    import anndata as ad

    parent = ad.read_h5ad(parent_path)
    X_new = _take_rows(parent.X, placement)
    row_names = [str(name) for name in parent.obs_names]
    provenance = _provenance(spec, assignment_meta)
    contract_io = _contract_io()
    contract_io.write_candidate_from_parent(
        parent_path=parent_path,
        output_path=candidate_path,
        expression=X_new,
        row_names=row_names,
        normalization=NORMALIZATION,
        parent_sha256=spec.parent_sha256,
        metadata_updates={"ve_j1_fgw_assignment": json.dumps(provenance, sort_keys=True)},
    )
    diagnostics = {
        "schema": "ve.t2.j1-fgw-assignment.generation-diagnostics.v1",
        "atom": ATOM,
        "board": board,
        "candidate_path": _relative(candidate_path),
        "candidate_sha256": sha256_file(candidate_path),
        "model": {
            "n_obs_parent": int(parent.n_obs),
            "n_obs_candidate": int(len(placement)),
            "n_vars": int(parent.n_vars),
        },
        "provenance": provenance,
        "target_used": False,
    }
    _write_json_atomic(candidate_path.parent / "generation_diagnostics.json", diagnostics)
    _append_run_log(
        out_dir, f"generate {board}: candidate sha256={diagnostics['candidate_sha256'][:16]}"
    )
    return {"step": "generate", "board": board, "sha256": diagnostics["candidate_sha256"]}


def command_contract(out_dir: Path, *, board: str) -> dict[str, Any]:
    out_dir = Path(out_dir)
    spec = BOARD_SPECS[board]
    candidate_path = out_dir / "candidates" / board / "submission.h5ad"
    if not candidate_path.is_file():
        raise FileNotFoundError(f"candidate missing: {candidate_path}")
    contract_io = _contract_io()
    report = dict(
        contract_io.validate_h5ad_contract(
            candidate_path,
            task="T2",
            board=spec.board_key,
            scorer_lock=SCORER_LOCK_PATH,
            parent_path=ROOT / spec.parent_path,
            parent_sha256=spec.parent_sha256,
        )
    )
    report["atom"] = ATOM
    report["candidate_sha256"] = sha256_file(candidate_path)
    _write_json_atomic(candidate_path.parent / "contract_report.json", report)
    _append_run_log(out_dir, f"contract {board}: status={report['status']}")
    return {"step": "contract", "board": board, "status": report["status"]}


def _knn_expression_overlap(coords: np.ndarray, placement: np.ndarray, k: int = KNN_K) -> dict[str, float]:
    """Mean/median/min per-position overlap of expression-row sets in the kNN
    neighbourhood before (identity) and after the placement.  Coordinates are
    unchanged, so the graph is identical; this is an effect-size statistic."""
    graph = _spatial_knn(np.asarray(coords, dtype=np.float64), k=k)
    moved = placement[graph]  # candidate row ids in each neighbourhood
    base = graph              # parent row ids in each neighbourhood (identity placement)
    overlaps = np.empty(len(graph), dtype=np.float64)
    for j in range(len(graph)):
        overlaps[j] = len(set(moved[j].tolist()) & set(base[j].tolist())) / float(k)
    return {
        "k": int(k),
        "mean": float(overlaps.mean()),
        "median": float(np.median(overlaps)),
        "min": float(overlaps.min()),
    }


def command_checks(out_dir: Path, *, board: str) -> dict[str, Any]:
    """Protected invariants, re-verified from disk against the locked parent."""
    out_dir = Path(out_dir)
    spec = BOARD_SPECS[board]
    candidate_path = out_dir / "candidates" / board / "submission.h5ad"
    placement = np.load(out_dir / "intermediates" / board / "assignment.npz")["placement"]
    parent_path = ROOT / spec.parent_path
    parent = load_t2_input(parent_path, ROOT / spec.panel)
    candidate = load_t2_input(candidate_path, ROOT / spec.panel)
    parent_coords = _coords(parent, parent_path)
    candidate_coords = _coords(candidate, candidate_path)

    expression_exact = _matrix_equal(candidate.X, _take_rows(parent.X, placement))
    obs_exact = bool(candidate.obs.equals(parent.obs))
    checks: dict[str, Any] = {
        "schema": "ve.t2.j1-fgw-assignment.geometry-checks.v1",
        "atom": ATOM,
        "board": board,
        "candidate_sha256": sha256_file(candidate_path),
        "parent_sha256": sha256_file(parent_path),
        "placement_bijection": bool(
            np.array_equal(np.sort(placement), np.arange(len(placement), dtype=np.int64))
        ),
        "expression_replay_exact": bool(expression_exact),
        "expression_multiset_parent": _row_multiset_digest(parent.X),
        "expression_multiset_candidate": _row_multiset_digest(candidate.X),
        "expression_multiset_exact": _row_multiset_digest(parent.X)
        == _row_multiset_digest(candidate.X),
        "obs_exact": obs_exact,
        "obs_names_digest_parent": _names_digest(parent.obs_names),
        "obs_names_digest_candidate": _names_digest(candidate.obs_names),
        "obs_order_unchanged": _names_digest(parent.obs_names)
        == _names_digest(candidate.obs_names),
        "var_names_digest_parent": _names_digest(parent.var_names),
        "var_names_digest_candidate": _names_digest(candidate.var_names),
        "var_order_unchanged": _names_digest(parent.var_names)
        == _names_digest(candidate.var_names),
        "coordinate_digest_parent": _matrix_digest(parent_coords),
        "coordinate_digest_candidate": _matrix_digest(candidate_coords),
        "coordinate_values_exact": bool(np.array_equal(parent_coords, candidate_coords)),
        "knn15_fingerprint_parent": _knn_fingerprint(parent_coords),
        "knn15_fingerprint_candidate": _knn_fingerprint(candidate_coords),
        "knn15_graph_exact": _knn_fingerprint(parent_coords)
        == _knn_fingerprint(candidate_coords),
        "n_obs_parent": int(parent.n_obs),
        "n_obs_candidate": int(candidate.n_obs),
        "cell_limits": [spec.min_cells, spec.max_cells],
        "cell_limits_ok": bool(spec.min_cells <= candidate.n_obs <= spec.max_cells),
        "knn15_expression_overlap": _knn_expression_overlap(candidate_coords, placement),
        "target_used": False,
    }
    checks["status"] = (
        "PASS"
        if all(
            checks[key]
            for key in (
                "placement_bijection",
                "expression_replay_exact",
                "expression_multiset_exact",
                "obs_exact",
                "obs_order_unchanged",
                "var_order_unchanged",
                "coordinate_values_exact",
                "knn15_graph_exact",
                "cell_limits_ok",
            )
        )
        else "FAIL"
    )
    metrics_dir = out_dir / "metrics" / board
    _write_json_atomic(metrics_dir / "geometry_checks.json", checks)
    _append_run_log(out_dir, f"checks {board}: status={checks['status']}")
    return checks


def command_nfs_proxy(out_dir: Path, *, board: str) -> dict[str, Any]:
    """Locked NFS mirror of candidate AND parent against the board pseudo-target."""
    out_dir = Path(out_dir)
    spec = BOARD_SPECS[board]
    candidate_path = out_dir / "candidates" / board / "submission.h5ad"
    parent_path = ROOT / spec.parent_path
    parent = load_t2_input(parent_path, ROOT / spec.panel)
    candidate = load_t2_input(candidate_path, ROOT / spec.panel)
    truth = load_t2_input(ROOT / spec.scorer_pseudo_target, ROOT / spec.panel)
    parent_X = _dense_float32(parent.X)
    candidate_X = _dense_float32(candidate.X)
    truth_X = _dense_float32(truth.X)
    parent_coords = _coords(parent, parent_path)
    truth_coords = _coords(truth, ROOT / spec.scorer_pseudo_target)
    started = time.time()
    nfs_parent = _nfs_like(parent_X, parent_coords, truth_X, truth_coords)
    nfs_candidate = _nfs_like(candidate_X, parent_coords, truth_X, truth_coords)
    report = {
        "schema": "ve.t2.j1-fgw-assignment.nfs-proxy.v1",
        "atom": ATOM,
        "board": board,
        "seed": SEED,
        "metric": "veckit neighborhood_mmd mirror (T2/metrics.py::_knn_neighborhood_pb "
        f"k={KNN_K} self-inclusive + common/core_metrics.py::mmd_unbiased n=2000 seed=0)",
        "pseudo_target": spec.scorer_pseudo_target,
        "nfs_parent": nfs_parent,
        "nfs_candidate": nfs_candidate,
        "delta_candidate_minus_parent": nfs_candidate - nfs_parent,
        "direction": "improvement" if nfs_candidate < nfs_parent else "no_improvement",
        "j1_proxy_holdout_context": {
            "note": "source-only leave-one-stage-out evidence from T2-J1-PROXY "
            "(different setting; cited for direction context only)",
            "H1_embryo": {"fgw_full": 0.01168094, "random_median": 0.1368},
            "H2_heart": {"fgw_full": 0.01522078, "random_median": 0.1723},
        },
        "declarations": [
            "the pseudo-target is a training-stage observed cloud, never the hidden target",
            "the pseudo-target stage is also a bracket stage of the reference "
            "construction, so the comparison is partially circular by design; "
            "local numbers are not leaderboard previews and claim no improvement",
        ],
        "target_used": False,
        "wall_seconds": time.time() - started,
    }
    _write_json_atomic(out_dir / "metrics" / board / "nfs_proxy.json", report)
    _append_run_log(
        out_dir,
        f"nfs-proxy {board}: parent={nfs_parent:.5f} candidate={nfs_candidate:.5f} "
        f"direction={report['direction']}",
    )
    return report


def command_determinism(out_dir: Path, *, board: str) -> dict[str, Any]:
    """Same-seed re-solve + re-assign + re-generate; outputs must be identical."""
    out_dir = Path(out_dir)
    hold_dir = out_dir / "intermediates" / board
    problem_path = hold_dir / "problem.npz"
    coupling_path = hold_dir / "transport_plan.npz"
    candidate_path = out_dir / "candidates" / board / "submission.h5ad"
    rerun_coupling = hold_dir / "determinism_rerun_coupling.npz"
    rerun_meta = hold_dir / "determinism_rerun_meta.json"
    rerun_h5ad = candidate_path.parent / "determinism_rerun.h5ad"
    for stale in (rerun_coupling, rerun_meta, rerun_h5ad):
        if stale.exists():
            raise FileExistsError(f"determinism scratch exists: {stale}")
    if not VENV_PYTHON.is_file():
        raise RuntimeError(f"missing tool interpreter: {VENV_PYTHON}")
    started = time.time()
    command = [
        str(VENV_PYTHON),
        "-m",
        "scripts.t2_j1_fgw_assignment",
        "solve-worker",
        "--problem",
        str(problem_path),
        "--coupling",
        str(rerun_coupling),
        "--meta",
        str(rerun_meta),
        "--board",
        board,
    ]
    proc = subprocess.run(
        command, cwd=ROOT, capture_output=True, text=True, env=_worker_env(), timeout=14400
    )
    if proc.returncode != 0:
        raise RuntimeError(f"determinism re-solve failed for {board}: {proc.stderr[-2000:]}")
    T_first = np.load(coupling_path)["T"]
    T_second = np.load(rerun_coupling)["T"]
    coupling_identical = bool(np.array_equal(T_first, T_second))
    placement_first = np.load(hold_dir / "assignment.npz")["placement"]
    placement_second, _stats = assign_from_plan(T_second)
    placement_identical = bool(np.array_equal(placement_first, placement_second))

    spec = BOARD_SPECS[board]
    import anndata as ad

    parent = ad.read_h5ad(ROOT / spec.parent_path)
    X_new = _take_rows(parent.X, placement_second)
    assignment_meta = json.loads((hold_dir / "assignment_meta.json").read_text(encoding="utf-8"))
    provenance = _provenance(spec, assignment_meta)
    contract_io = _contract_io()
    h5ad_identical = False
    try:
        contract_io.write_candidate_from_parent(
            parent_path=ROOT / spec.parent_path,
            output_path=rerun_h5ad,
            expression=X_new,
            row_names=[str(name) for name in parent.obs_names],
            normalization=NORMALIZATION,
            parent_sha256=spec.parent_sha256,
            metadata_updates={"ve_j1_fgw_assignment": json.dumps(provenance, sort_keys=True)},
        )
        h5ad_identical = sha256_file(rerun_h5ad) == sha256_file(candidate_path)
    finally:
        for scratch in (rerun_coupling, rerun_meta, rerun_h5ad):
            if scratch.exists():
                scratch.unlink()
    report = {
        "schema": "ve.t2.j1-fgw-assignment.determinism.v1",
        "atom": ATOM,
        "board": board,
        "seed": SEED,
        "coupling_bit_identical": coupling_identical,
        "placement_identical": placement_identical,
        "h5ad_byte_identical": h5ad_identical,
        "candidate_sha256": sha256_file(candidate_path),
        "wall_seconds": time.time() - started,
    }
    _write_json_atomic(out_dir / "metrics" / board / "determinism.json", report)
    _append_run_log(
        out_dir,
        f"determinism {board}: coupling_bit_identical={coupling_identical} "
        f"placement_identical={placement_identical} h5ad_byte_identical={h5ad_identical}",
    )
    return report


# ---------------------------------------------------------------------------
# locked scorer wrapper (pseudo-target; budget 1 per board)
# ---------------------------------------------------------------------------


def _load_scorer_lock() -> dict[str, Any]:
    lock = json.loads(SCORER_LOCK_PATH.read_text(encoding="utf-8"))
    entry = lock["entrypoint"]
    actual = sha256_file(SCORER_ENTRYPOINT)
    if actual != entry["sha256"]:
        raise RuntimeError(
            f"scorer entrypoint hash drift: lock {entry['sha256']} vs actual {actual}"
        )
    return lock


def command_score(out_dir: Path, *, board: str) -> dict[str, Any]:
    out_dir = Path(out_dir)
    spec = BOARD_SPECS[board]
    metrics_dir = out_dir / "metrics" / board
    name = f"{board}__FGW_ASSIGN"
    out_final = metrics_dir / f"scorer_{name}_output.json"
    if out_final.exists():
        raise FileExistsError(f"scorer budget spent for {board}: {out_final} exists")
    _load_scorer_lock()
    candidate_path = out_dir / "candidates" / board / "submission.h5ad"
    if not candidate_path.is_file():
        raise FileNotFoundError(f"scorer input missing: {candidate_path}")
    out_tmp = metrics_dir / f"scorer_{name}_output.tmp.json"
    log_path = metrics_dir / f"scorer_{name}.log"
    command = [
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
        str(candidate_path),
        "--target",
        spec.scorer_pseudo_target,
        "--reference",
        spec.scorer_pseudo_reference,
        "--seed",
        str(SEED),
        "--out",
        str(out_tmp),
    ]
    started = time.time()
    with log_path.open("w", encoding="utf-8") as log_handle:
        proc = subprocess.run(
            command, cwd=ROOT, stdout=log_handle, stderr=subprocess.STDOUT, timeout=7200
        )
    wall = time.time() - started
    record: dict[str, Any] = {
        "schema": "ve.t2.j1-fgw-assignment.scorer-run.v1",
        "atom": ATOM,
        "board": board,
        "command": " ".join(command),
        "pseudo_target": spec.scorer_pseudo_target,
        "pseudo_reference": spec.scorer_pseudo_reference,
        "pseudo_target_note": (
            "local --target is a pseudo-target (a training stage); it cannot "
            "establish leaderboard improvement or hidden-target validity. The "
            "pseudo-target stage is also a bracket stage of the reference "
            "construction, so the comparison is partially circular by design."
        ),
        "scorer_lock_path": str(SCORER_LOCK_PATH),
        "scorer_lock_sha256": sha256_file(SCORER_LOCK_PATH),
        "input_path": str(candidate_path),
        "input_sha256": sha256_file(candidate_path),
        "seed": SEED,
        "exit_code": proc.returncode,
        "wall_seconds": wall,
    }
    if proc.returncode == 0 and out_tmp.is_file():
        out_tmp.replace(out_final)
        payload = json.loads(out_final.read_text(encoding="utf-8"))
        meta = payload.get("meta", {})
        record["status"] = "DONE"
        record["result_path"] = str(out_final)
        record["result_sha256"] = sha256_file(out_final)
        record["result_meta"] = meta
        record["result_metrics"] = payload.get("metrics", {})
        record["result_checks"] = {
            "genes_match": meta.get("genes") == spec.panel_genes,
            "truth_cells_match": meta.get("truth_cells") == spec.scorer_truth_cells,
            "prediction_cells": meta.get("prediction_cells"),
        }
    else:
        record["status"] = "FAILED"
        record["failure_reason"] = f"scorer exit_code={proc.returncode}; see {log_path}"
    _write_json_atomic(metrics_dir / f"scorer_{name}_run.json", record)
    _append_run_log(
        out_dir, f"score {board}: status={record['status']} wall={wall:.1f}s"
    )
    if record["status"] != "DONE":
        raise RuntimeError(record["failure_reason"])
    return record


# ---------------------------------------------------------------------------
# input lock, env probe, config freeze, finalize, manifest
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

    for slug in BOARD_ORDER:
        spec = BOARD_SPECS[slug]
        _add(f"parent_{slug}", ROOT / spec.parent_path)
        if inputs[f"parent_{slug}"]["sha256"] != spec.parent_sha256:
            raise RuntimeError(f"{slug}: parent SHA256 drift vs locked value")
        _add(f"panel_{slug}", ROOT / spec.panel)
    for stage in (7.25, 8.0, 8.25, 8.75, 9.5):
        _add(f"stage_{stage_label(stage)}", ROOT / STAGE_FILES[stage])
    _add("stage_E6.75", ROOT / STAGE_FILES[6.75])
    for name, path in (
        ("t2_metrics", T2_METRICS_PATH),
        ("core_metrics", CORE_METRICS_PATH),
        ("scorer_entrypoint", SCORER_ENTRYPOINT),
        ("scorer_lock", SCORER_LOCK_PATH),
        ("toolchain_lock", TOOLCHAIN_LOCK_PATH),
        ("board_index", BOARD_INDEX_PATH),
        ("contract_adapter", CONTRACT_ADAPTER_PATH),
        ("proxy_objective_spec", PROXY_OBJECTIVE_SPEC),
        ("t2_loader", ROOT / "scripts" / "t2_baseline.py"),
        ("t2_j1_pairing", ROOT / "scripts" / "t2_j1_pairing.py"),
        ("t2_j1_proxy", ROOT / "scripts" / "t2_j1_proxy.py"),
        ("t2_s3_shape_field", ROOT / "scripts" / "t2_s3_shape_field.py"),
        ("implementation", ROOT / "scripts" / "t2_j1_fgw_assignment.py"),
    ):
        _add(name, path)

    if inputs["proxy_objective_spec"]["sha256"] != PROXY_OBJECTIVE_SPEC_SHA256:
        raise RuntimeError("frozen objective spec SHA256 mismatch vs J1-PROXY record")
    lock = json.loads(SCORER_LOCK_PATH.read_text(encoding="utf-8"))
    expected_loader = lock["contract_snapshot"]["t2_loader"]["sha256"]
    if inputs["t2_loader"]["sha256"] != expected_loader:
        raise RuntimeError("t2_baseline.py drift vs SCORER_LOCK")
    expected_scorer = lock["entrypoint"]["sha256"]
    if inputs["scorer_entrypoint"]["sha256"] != expected_scorer:
        raise RuntimeError("score_h5ad.py drift vs SCORER_LOCK")

    payload = {
        "schema": "ve.t2.j1-fgw-assignment.input-lock.v1",
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
            "schema": "ve.t2.j1-fgw-assignment.env-probe.v1",
            "atom": ATOM,
            "probed_at": datetime.now(timezone.utc).isoformat(),
            "wall_seconds": time.time() - started,
            "ld_library_path": os.environ.get("LD_LIBRARY_PATH"),
            "worker_threads": "8",
        }
    )
    _write_json_atomic(out_dir / "metrics" / "env_versions.json", payload)
    _append_run_log(out_dir, f"env-probe: POT={payload['packages'].get('POT')}")
    return {"step": "env-probe"}


def command_config_freeze(out_dir: Path, *, overwrite: bool = False) -> dict[str, Any]:
    """Freeze config_resolved.yaml with every pre-declared rule; refuse drift."""
    out_dir = Path(out_dir)
    path = out_dir / "config_resolved.yaml"
    text = _config_text()
    if path.is_file() and not overwrite:
        if path.read_bytes() != text.encode("utf-8"):
            raise RuntimeError(
                "config_resolved.yaml already exists with different content; "
                "freezing violation — bump the atom version instead"
            )
        return {"step": "config-freeze", "status": "already_frozen"}
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)
    _append_run_log(out_dir, f"config-freeze: sha256={sha256_file(path)[:16]}")
    return {"step": "config-freeze", "sha256": sha256_file(path)}


def _safe_version(metadata_module: Any, package: str) -> str | None:
    try:
        return metadata_module.version(package)
    except Exception:
        return None


def command_finalize(out_dir: Path) -> dict[str, Any]:
    import importlib.metadata

    out_dir = Path(out_dir)
    payload: dict[str, Any] = {
        "schema": "ve.t2.j1-fgw-assignment.tool-versions.v1",
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
            "path": "scripts/t2_j1_fgw_assignment.py",
            "sha256": sha256_file(Path(__file__).resolve()),
        },
        "nfs_mirror_sources": {
            "t2_metrics": "third_party/veckit/T2/metrics.py",
            "t2_metrics_sha256": sha256_file(T2_METRICS_PATH),
            "core_metrics": "third_party/veckit/common/core_metrics.py",
            "core_metrics_sha256": sha256_file(CORE_METRICS_PATH),
            "scorer_lock": "artifacts/tool_integration/P0-LOCK/locks/SCORER_LOCK.json",
        },
        "contract_adapter": {
            "path": "docs/batch3/interfaces/virtual_embryo_tools/contract_io.py",
            "sha256": sha256_file(CONTRACT_ADAPTER_PATH),
        },
        "objective_spec": {
            "path": _relative(PROXY_OBJECTIVE_SPEC),
            "sha256": PROXY_OBJECTIVE_SPEC_SHA256,
        },
    }
    env_path = out_dir / "metrics" / "env_versions.json"
    if env_path.is_file():
        payload["ve_t1_ot"] = json.loads(env_path.read_text(encoding="utf-8"))
    _write_json_atomic(out_dir / "TOOL_VERSIONS.json", payload)
    deviations_path = out_dir / "metrics" / "deviations.json"
    if not deviations_path.is_file():
        _write_json_atomic(deviations_path, {"schema": "ve.t2.j1-fgw-assignment.deviations.v1",
                                             "atom": ATOM, "deviations": []})
    _append_run_log(out_dir, "finalize: TOOL_VERSIONS.json + deviations ledger")
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
            "implementation": "scripts/t2_j1_fgw_assignment.py",
            "implementation_sha256": sha256_file(Path(__file__).resolve()),
            "test_module": "tests/test_t2_j1_fgw_assignment.py",
            "test_module_sha256": sha256_file(ROOT / "tests" / "test_t2_j1_fgw_assignment.py")
            if (ROOT / "tests" / "test_t2_j1_fgw_assignment.py").is_file()
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
            "config-freeze",
            "audit",
            "prepare",
            "solve",
            "solve-worker",
            "assign",
            "generate",
            "contract",
            "checks",
            "nfs-proxy",
            "determinism",
            "score",
            "finalize",
            "manifest",
            "verify",
        ],
    )
    parser.add_argument("--out-dir", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--board", default=None)  # validated per command
    parser.add_argument("--problem", type=Path, default=None)
    parser.add_argument("--coupling", type=Path, default=None)
    parser.add_argument("--meta", type=Path, default=None)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir)

    def _need_board() -> str:
        if args.board not in BOARD_SPECS:
            raise ValueError(f"{args.command} requires --board one of {list(BOARD_SPECS)}")
        return args.board

    if args.command == "input-lock":
        result = command_input_lock(out_dir)
    elif args.command == "env-probe":
        result = command_env_probe(out_dir)
    elif args.command == "config-freeze":
        result = command_config_freeze(out_dir, overwrite=args.overwrite)
    elif args.command == "audit":
        result = command_audit(out_dir)
    elif args.command == "prepare":
        result = command_prepare(out_dir, board=_need_board())
    elif args.command == "solve":
        result = command_solve(out_dir, board=_need_board())
    elif args.command == "solve-worker":
        if args.problem is None or args.coupling is None or args.meta is None:
            raise ValueError("solve-worker requires --problem, --coupling and --meta")
        result = command_solve_worker(
            problem_path=args.problem,
            coupling_path=args.coupling,
            meta_path=args.meta,
            board=args.board or "unknown",
        )
    elif args.command == "assign":
        result = command_assign(out_dir, board=_need_board())
    elif args.command == "generate":
        result = command_generate(out_dir, board=_need_board())
    elif args.command == "contract":
        result = command_contract(out_dir, board=_need_board())
    elif args.command == "checks":
        result = {"step": "checks", "status": command_checks(out_dir, board=_need_board())["status"]}
    elif args.command == "nfs-proxy":
        report = command_nfs_proxy(out_dir, board=_need_board())
        result = {"step": "nfs-proxy", "board": report["board"], "direction": report["direction"]}
    elif args.command == "determinism":
        report = command_determinism(out_dir, board=_need_board())
        result = {
            "step": "determinism",
            "board": report["board"],
            "coupling_bit_identical": report["coupling_bit_identical"],
            "placement_identical": report["placement_identical"],
            "h5ad_byte_identical": report["h5ad_byte_identical"],
        }
    elif args.command == "score":
        record = command_score(out_dir, board=_need_board())
        result = {"step": "score", "board": record["board"], "status": record["status"]}
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
