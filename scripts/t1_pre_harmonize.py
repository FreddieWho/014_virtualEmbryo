#!/usr/bin/env python3
"""T1-PRE-HARMONIZE: reusable E8.5/E9.5 state vocabulary, stable crosswalk,
source-only pseudo-holdout projection, and full-panel scorer chain check.

This atom runs BEFORE any moscot/WOT work.  It does not generate a formal
future-stage candidate and never submits to the server.  Reuse priority follows
the task prompt: the released stages already ship frozen ``obs['celltype']``
state labels (route 1), so no re-clustering and no new representation is
trained; the vocabulary only harmonises those frozen labels into a
``lineage -> state_family -> fine_state`` hierarchy and a crosswalk built from
pre-declared marker-program cosine + mutual-nearest-centroid rules.  Low
confidence states are explicitly ``UNRESOLVED``; nothing is force-matched.

Subcommands (each writes atomically so interruption cannot create false PASS):

* ``build``        -- vocabulary/program TSVs, state centroids npz, crosswalk TSV, input lock
* ``stability``    -- pre-declared single stability pass (bootstrap, projection
                      mutual consistency, small-state threshold sensitivity,
                      parent residual extractability)
* ``project``      -- source-only E8.5->E9.5 pseudo-holdout projection h5ad
                      (per-state centroid shift + real-cell residual replay)
* ``score-launch`` -- launch the locked full-panel scorer as a detached
                      background child (PID + log recorded; no waiting)
* ``score-collect``-- collect scorer status/result into the run record and
                      update metrics/projection_pseudoholdout.json
* ``finalize``     -- config_resolved.yaml, TOOL_VERSIONS.json,
                      metrics/full_panel_scorer_check.json (P0 evidence reuse
                      + wrapper verification)
* ``manifest``     -- stable artifact manifest (path/bytes/sha256) + self-verify
* ``verify``       -- re-check the stable manifest hashes

Seed is fixed at 20260830; no grid search, no network, no server submission.
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
from scipy import sparse

try:
    from scripts.t1_temporal_model import select_indices_by_shares
except ImportError:  # direct ``python scripts/t1_pre_harmonize.py`` execution
    from t1_temporal_model import select_indices_by_shares

ROOT = Path(__file__).resolve().parents[1]
ATOM = "T1-PRE-HARMONIZE-20260902-v1"
OUTPUT_DEFAULT = ROOT / "artifacts" / "tool_integration" / ATOM
SEED = 20260830
SOURCE_STAGE = "E8.5"
TARGET_STAGE = "E9.5"
SOURCE_PATH = ROOT / "data" / "E8.5_RNA.h5ad"
TARGET_PATH = ROOT / "data" / "E9.5_RNA.h5ad"
PARENT_PATH = ROOT / "submissions/candidates/T1_val/v0004_strict_pseudobulk_shift/submission.h5ad"
PARENT_SHA256 = "1bc069d9aecd4b9b15f3ff91c328ef27a9773bfd0d3c890f36f5f1b6fb4f49bd"
PANEL_PATH = ROOT / "data" / "gene_panel" / "T1__val.genes.txt"
SCORER_LOCK_PATH = ROOT / "artifacts/tool_integration/P0-LOCK/locks/SCORER_LOCK.json"
SCORER_ENTRYPOINT = ROOT / "third_party/veckit/score_h5ad.py"
P0_FULL_PANEL_RESULT = ROOT / "artifacts/tool_integration/P0-LOCK/metrics/t1_full_panel_score.json"
P0_FULL_PANEL_SHA256 = "bab80fcb72c2dc6d684327bd1e1f2ea1d1d43850858b593432dca34b66e48c74"
EXPECTED_GENES = 32285
EXPECTED_TRUTH_CELLS = 17057

# Pre-declared analysis constants (single announced check, no grid search).
COSINE_TAU = 0.70
BOOTSTRAP_ROUNDS = 20
MIN_STATE_CELLS = 50
PROJECTION_N_CELLS = 5118  # T1:val board max, identical to the current parent
UNRESOLVED = "UNRESOLVED"

VOCABULARY_TSV_FIELDS = [
    "fine_state", "lineage", "state_family", "stage_presence",
    "n_cells_e85", "n_cells_e95", "share_e85", "share_e95", "vocabulary_status",
]
PROGRAM_TSV_FIELDS = [
    "program_id", "lineage", "state_family", "gene", "role", "present_in_panel",
]
CROSSWALK_TSV_FIELDS = [
    "fine_state", "direction", "lineage", "state_family", "n_cells",
    "stage_presence", "matched_state", "match_rule", "cosine_similarity",
    "forward_rank", "reverse_rank", "mutual_nearest", "confidence",
    "resolution_reason",
]

# Pre-declared harmonisation of the frozen official celltype labels into
# lineage -> state_family -> fine_state.  Curated from the heart-scope domain
# meaning of the released labels; any unmapped label fails closed.
STATE_HIERARCHY: dict[str, tuple[str, str]] = {
    "OFT/RV-CM": ("cardiac_mesoderm", "cardiomyocyte"),
    "IFT-CM": ("cardiac_mesoderm", "cardiomyocyte"),
    "AVC-CM": ("cardiac_mesoderm", "cardiomyocyte"),
    "RV-CM": ("cardiac_mesoderm", "cardiomyocyte"),
    "LV-CM": ("cardiac_mesoderm", "cardiomyocyte"),
    "SV-CM": ("cardiac_mesoderm", "cardiomyocyte"),
    "V-CM": ("cardiac_mesoderm", "cardiomyocyte"),
    "pSHF": ("cardiac_mesoderm", "second_heart_field"),
    "aSHF": ("cardiac_mesoderm", "second_heart_field"),
    "JCF": ("cardiac_mesoderm", "juxta_cardiac_field"),
    "pPHM": ("cardiac_mesoderm", "pharyngeal_mesoderm"),
    "aPHM": ("cardiac_mesoderm", "pharyngeal_mesoderm"),
    "Endothelium": ("vascular_endothelial", "endothelium"),
    "Endocardium": ("vascular_endothelial", "endocardium"),
    "BEC": ("vascular_endothelial", "blood_endothelial"),
    "Pericardium": ("pericardial_mesoderm", "pericardium"),
    "Proepicardium": ("pericardial_mesoderm", "proepicardium"),
    "ST": ("pericardial_mesoderm", "septum_transversum"),
    "Foregut": ("endoderm", "foregut"),
    "Hepatocyte": ("endoderm", "hepatocyte"),
    "Epithelium": ("endoderm", "epithelium"),
    "Surface Ectoderm": ("ectoderm", "surface_ectoderm"),
    "Neural Tube": ("neuroectoderm", "neural_tube"),
    "NCC": ("neural_crest", "neural_crest"),
    "NCC-derived": ("neural_crest", "neural_crest_derived"),
    "Paraxial Mesoderm": ("paraxial_mesoderm", "paraxial_mesoderm"),
    "EXEM": ("extraembryonic_mesoderm", "extraembryonic_mesoderm"),
    "Blood": ("hematopoietic", "blood"),
}

# Pre-declared positive marker programs per state_family.  The crosswalk cosine
# is computed on the union of these markers only; membership is validated
# against the released var_names at runtime and missing genes are recorded
# (present_in_panel=false) rather than silently dropped from the audit trail.
MARKER_PROGRAMS: dict[str, tuple[str, ...]] = {
    "cardiomyocyte": ("Tnnt2", "Myh6", "Myh7", "Myl2", "Myl7", "Tnni3", "Actc1", "Nppa"),
    "second_heart_field": ("Tbx1", "Fgf8", "Fgf10", "Isl1", "Mef2c"),
    "juxta_cardiac_field": ("Mesp1", "Mesp2", "Mab21l2"),
    "pharyngeal_mesoderm": ("Hoxa2", "Hoxb2", "Pax9", "Tbx1"),
    "endothelium": ("Pecam1", "Cdh5", "Kdr", "Flt1", "Tal1", "Emcn"),
    "endocardium": ("Npr3", "Sox17", "Nfatc1", "Pecam1"),
    "blood_endothelial": ("Cdh5", "Emcn", "Flt4", "Lyve1"),
    "pericardium": ("Tbx18", "Wt1", "Tcf21", "Msln"),
    "proepicardium": ("Tbx18", "Wt1", "Tcf21", "Upk3b", "Rspo3"),
    "septum_transversum": ("Wt1", "Msln", "Aldh1a2", "Upk3b"),
    "foregut": ("Foxa2", "Sox17", "Shh", "Epcam", "Nkx2-1"),
    "hepatocyte": ("Afp", "Alb", "Ttr", "Apoa1"),
    "epithelium": ("Epcam", "Krt8", "Krt18", "Krt19"),
    "surface_ectoderm": ("Trp63", "Krt14", "Krt5", "Krt15"),
    "neural_tube": ("Sox1", "Sox2", "Sox3", "Pax6", "Nes"),
    "neural_crest": ("Sox10", "Pax3", "Tfap2a", "Tfap2b", "Snai2"),
    "neural_crest_derived": ("Sox10", "Pax3", "Tfap2a", "Tfap2b"),
    "paraxial_mesoderm": ("Tbx6", "Msgn1", "Meox1", "T"),
    "extraembryonic_mesoderm": ("Hand1", "Bmp4", "Aplnr"),
    "blood": ("Hba-x", "Hbb-bh1", "Gypa", "Klf1", "Runx1"),
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


def _write_tsv_atomic(path: Path, rows: Iterable[Mapping[str, Any]], fields: list[str]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
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


def state_counts(labels: np.ndarray) -> dict[str, int]:
    values, counts = np.unique(np.asarray(labels).astype(str), return_counts=True)
    return {str(v): int(c) for v, c in zip(values, counts)}


def hierarchy_for(state: str) -> tuple[str, str]:
    if state not in STATE_HIERARCHY:
        raise ValueError(f"state label missing from pre-declared hierarchy: {state!r}")
    return STATE_HIERARCHY[state]


def vocabulary_rows(
    counts_e85: Mapping[str, int], counts_e95: Mapping[str, int]
) -> list[dict[str, Any]]:
    """One row per union fine-state with lineage/family and per-stage support."""
    union = sorted(set(counts_e85) | set(counts_e95))
    total_e85 = float(sum(counts_e85.values())) or 1.0
    total_e95 = float(sum(counts_e95.values())) or 1.0
    rows: list[dict[str, Any]] = []
    for state in union:
        lineage, family = hierarchy_for(state)
        in_e85 = state in counts_e85
        in_e95 = state in counts_e95
        if in_e85 and in_e95:
            presence, status = "both", "SHARED_EXACT"
        elif in_e85:
            presence, status = "E8.5_only", "SOURCE_ONLY"
        else:
            presence, status = "E9.5_only", "TARGET_ONLY"
        rows.append(
            {
                "fine_state": state,
                "lineage": lineage,
                "state_family": family,
                "stage_presence": presence,
                "n_cells_e85": int(counts_e85.get(state, 0)),
                "n_cells_e95": int(counts_e95.get(state, 0)),
                "share_e85": f"{counts_e85.get(state, 0) / total_e85:.6f}",
                "share_e95": f"{counts_e95.get(state, 0) / total_e95:.6f}",
                "vocabulary_status": status,
            }
        )
    return rows


def program_rows(var_names: Iterable[str]) -> tuple[list[dict[str, Any]], list[str]]:
    """Expand marker programs to one row per gene; return rows + present union."""
    present = set(str(g) for g in var_names)
    lineage_by_family: dict[str, str] = {}
    for state, (lineage, family) in STATE_HIERARCHY.items():
        lineage_by_family.setdefault(family, lineage)
    rows: list[dict[str, Any]] = []
    union: list[str] = []
    for family in sorted(MARKER_PROGRAMS):
        for gene in MARKER_PROGRAMS[family]:
            rows.append(
                {
                    "program_id": f"markers_{family}",
                    "lineage": lineage_by_family.get(family, ""),
                    "state_family": family,
                    "gene": gene,
                    "role": "positive_marker",
                    "present_in_panel": str(gene in present),
                }
            )
            if gene in present and gene not in union:
                union.append(gene)
    return rows, sorted(union)


def _normalize_rows(matrix: np.ndarray) -> np.ndarray:
    matrix = np.asarray(matrix, dtype=np.float64)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


def marker_matrix(X: Any, var_names: list[str], markers: list[str]) -> np.ndarray:
    """Dense cells x markers float64 view of X restricted to present markers."""
    index = {str(g): i for i, g in enumerate(var_names)}
    columns = [index[g] for g in markers]
    sub = X[:, columns]
    dense = sub.toarray() if sparse.issparse(sub) else np.asarray(sub)
    return np.asarray(dense, dtype=np.float64)


def state_centroids(marker_view: np.ndarray, labels: np.ndarray) -> dict[str, np.ndarray]:
    """Per-state marker-space mean; states sorted lexically, deterministic."""
    labels = np.asarray(labels).astype(str)
    if marker_view.shape[0] != labels.shape[0]:
        raise ValueError("marker matrix and labels disagree on cell count")
    centroids: dict[str, np.ndarray] = {}
    for state in sorted(np.unique(labels).tolist()):
        mask = labels == state
        centroids[state] = np.asarray(marker_view[mask].mean(axis=0), dtype=np.float64)
    return centroids


def full_panel_centroids(X: Any, labels: np.ndarray) -> dict[str, np.ndarray]:
    """Per-state full-panel column means; sparse-safe, never fully densified."""
    labels = np.asarray(labels).astype(str)
    centroids: dict[str, np.ndarray] = {}
    for state in sorted(np.unique(labels).tolist()):
        mean = X[labels == state].mean(axis=0)
        centroids[state] = np.asarray(mean).ravel().astype(np.float32)
    return centroids


def _ranked_targets(
    similarities: np.ndarray, names: list[str]
) -> list[tuple[str, float]]:
    """Deterministic ranking: descending similarity, lexical tie-break."""
    order = sorted(range(len(names)), key=lambda j: (-float(similarities[j]), names[j]))
    return [(names[j], float(similarities[j])) for j in order]


def build_crosswalk_rows(
    centroids_e85: Mapping[str, np.ndarray],
    centroids_e95: Mapping[str, np.ndarray],
    counts_e85: Mapping[str, int],
    counts_e95: Mapping[str, int],
    *,
    tau: float = COSINE_TAU,
) -> list[dict[str, Any]]:
    """Marker-cosine + mutual-nearest crosswalk over the union vocabulary.

    Rules (pre-declared, no tuning):
    1. a label present in both stages maps to itself (``SHARED_EXACT``);
    2. otherwise the nearest opposite-stage centroid must also point back
       (mutual nearest) AND reach cosine >= tau (``MUTUAL_NEAREST``);
    3. every other state is explicitly ``UNRESOLVED`` -- one-way nearest or
       low-cosine mutual matches are never force-paired.
    """
    if not 0 <= tau <= 1:
        raise ValueError("tau must be in [0, 1]")
    states_e85 = sorted(centroids_e85)
    states_e95 = sorted(centroids_e95)
    if not states_e85 or not states_e95:
        raise ValueError("crosswalk needs non-empty centroid sets on both sides")
    c85 = _normalize_rows(np.vstack([centroids_e85[s] for s in states_e85]))
    c95 = _normalize_rows(np.vstack([centroids_e95[s] for s in states_e95]))
    similarity = c85 @ c95.T
    forward_ranked = [_ranked_targets(similarity[i], states_e95) for i in range(len(states_e85))]
    backward_ranked = [
        _ranked_targets(similarity[:, j], states_e85) for j in range(len(states_e95))
    ]
    forward_best = {states_e85[i]: forward_ranked[i][0][0] for i in range(len(states_e85))}
    backward_best = {states_e95[j]: backward_ranked[j][0][0] for j in range(len(states_e95))}

    def rank_of(ranked: list[tuple[str, float]], name: str) -> int:
        for position, (candidate, _) in enumerate(ranked, start=1):
            if candidate == name:
                return position
        raise AssertionError(f"{name} missing from its own ranking")

    rows: list[dict[str, Any]] = []
    shared = set(states_e85) & set(states_e95)
    for i, state in enumerate(states_e85):
        lineage, family = hierarchy_for(state)
        j = states_e95.index(state) if state in shared else None
        base = {
            "fine_state": state,
            "direction": "e85_to_e95",
            "lineage": lineage,
            "state_family": family,
            "n_cells": int(counts_e85.get(state, 0)),
            "stage_presence": "both" if state in shared else "E8.5_only",
        }
        if state in shared:
            cosine_self = float(similarity[i, j])
            rows.append(
                {
                    **base,
                    "matched_state": state,
                    "match_rule": "SHARED_EXACT",
                    "cosine_similarity": f"{cosine_self:.6f}",
                    "forward_rank": rank_of(forward_ranked[i], state),
                    "reverse_rank": rank_of(backward_ranked[j], state),
                    "mutual_nearest": str(forward_best[state] == state and backward_best[state] == state),
                    "confidence": "HIGH",
                    "resolution_reason": "exact label present in both stages",
                }
            )
            continue
        target = forward_best[state]
        cosine = float(similarity[i, states_e95.index(target)])
        mutual = backward_best[target] == state
        if mutual and cosine >= tau:
            rows.append(
                {
                    **base,
                    "matched_state": target,
                    "match_rule": "MUTUAL_NEAREST",
                    "cosine_similarity": f"{cosine:.6f}",
                    "forward_rank": 1,
                    "reverse_rank": 1,
                    "mutual_nearest": "True",
                    "confidence": "HIGH",
                    "resolution_reason": f"mutual nearest centroid, cosine {cosine:.4f} >= tau {tau}",
                }
            )
        else:
            reason = (
                f"nearest target {target} does not point back"
                if not mutual
                else f"mutual nearest cosine {cosine:.4f} below tau {tau}"
            )
            rows.append(
                {
                    **base,
                    "matched_state": UNRESOLVED,
                    "match_rule": "NONE",
                    "cosine_similarity": f"{cosine:.6f}",
                    "forward_rank": 1,
                    "reverse_rank": rank_of(backward_ranked[states_e95.index(target)], state),
                    "mutual_nearest": str(mutual),
                    "confidence": "LOW",
                    "resolution_reason": f"UNRESOLVED: {reason} (best candidate {target})",
                }
            )
    for j, state in enumerate(states_e95):
        if state in shared:
            continue
        lineage, family = hierarchy_for(state)
        source = backward_best[state]
        cosine = float(similarity[states_e85.index(source), j])
        mutual = forward_best[source] == state
        resolved = mutual and cosine >= tau
        rows.append(
            {
                "fine_state": state,
                "direction": "e95_to_e85",
                "lineage": lineage,
                "state_family": family,
                "n_cells": int(counts_e95.get(state, 0)),
                "stage_presence": "E9.5_only",
                "matched_state": source if resolved else UNRESOLVED,
                "match_rule": "MUTUAL_NEAREST" if resolved else "NONE",
                "cosine_similarity": f"{cosine:.6f}",
                "forward_rank": rank_of(
                    forward_ranked[states_e85.index(source)], state
                ),
                "reverse_rank": 1,
                "mutual_nearest": str(mutual),
                "confidence": "HIGH" if resolved else "LOW",
                "resolution_reason": (
                    f"mutual nearest centroid, cosine {cosine:.4f} >= tau {tau}"
                    if resolved
                    else (
                        f"UNRESOLVED: nearest source {source} does not point back"
                        if not mutual
                        else f"UNRESOLVED: mutual nearest cosine {cosine:.4f} below tau {tau}"
                    )
                ),
            }
        )
    return rows


def crosswalk_matches(rows: Iterable[Mapping[str, Any]]) -> dict[str, str]:
    """Resolved forward matches only: {e85_state: e95_state}; UNRESOLVED omitted."""
    matches: dict[str, str] = {}
    for row in rows:
        if row["direction"] == "e85_to_e95" and row["matched_state"] != UNRESOLVED:
            matches[str(row["fine_state"])] = str(row["matched_state"])
    return matches


def bootstrap_crosswalk_stability(
    marker_e85: np.ndarray,
    labels_e85: np.ndarray,
    marker_e95: np.ndarray,
    labels_e95: np.ndarray,
    *,
    rounds: int = BOOTSTRAP_ROUNDS,
    seed: int = SEED,
    tau: float = COSINE_TAU,
) -> dict[str, Any]:
    """Cell-level bootstrap of marker centroids; per-edge recovery of the crosswalk.

    One pre-declared pass: ``rounds`` resamples with replacement within each
    state; round seeds derive deterministically from the atom seed.
    """
    if rounds < 1:
        raise ValueError("rounds must be >= 1")
    labels_e85 = np.asarray(labels_e85).astype(str)
    labels_e95 = np.asarray(labels_e95).astype(str)
    full_rows = build_crosswalk_rows(
        state_centroids(marker_e85, labels_e85),
        state_centroids(marker_e95, labels_e95),
        state_counts(labels_e85),
        state_counts(labels_e95),
        tau=tau,
    )
    full_match = {
        (row["fine_state"], row["direction"]): row["matched_state"]
        for row in full_rows
        if row["match_rule"] == "MUTUAL_NEAREST"
    }
    recovery = {key: 0 for key in full_match}
    for round_index in range(rounds):
        rng = np.random.default_rng(np.random.SeedSequence([seed, round_index]))

        def resample(marker: np.ndarray, labels: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
            indices: list[np.ndarray] = []
            for state in sorted(np.unique(labels).tolist()):
                pool = np.flatnonzero(labels == state)
                indices.append(rng.choice(pool, size=len(pool), replace=True))
            take = np.concatenate(indices)
            return marker[take], labels[take]

        boot_e85 = resample(marker_e85, labels_e85)
        boot_e95 = resample(marker_e95, labels_e95)
        boot_rows = build_crosswalk_rows(
            state_centroids(boot_e85[0], boot_e85[1]),
            state_centroids(boot_e95[0], boot_e95[1]),
            state_counts(boot_e85[1]),
            state_counts(boot_e95[1]),
            tau=tau,
        )
        boot_match = {
            (row["fine_state"], row["direction"]): row["matched_state"]
            for row in boot_rows
            if row["match_rule"] == "MUTUAL_NEAREST"
        }
        for key, matched in full_match.items():
            if boot_match.get(key) == matched:
                recovery[key] += 1
    per_edge = [
        {
            "fine_state": key[0],
            "direction": key[1],
            "full_match": full_match[key],
            "recovered_rounds": recovery[key],
            "recovery_fraction": recovery[key] / rounds,
        }
        for key in sorted(full_match)
    ]
    fractions = [edge["recovery_fraction"] for edge in per_edge]
    return {
        "rounds": rounds,
        "seed": seed,
        "tau": tau,
        "n_mutual_nearest_edges": len(full_match),
        "per_edge": per_edge,
        "mean_recovery": float(np.mean(fractions)) if fractions else None,
        "min_recovery": float(np.min(fractions)) if fractions else None,
        "all_edges_fully_recovered": bool(fractions) and all(f == 1.0 for f in fractions),
    }


def projection_mutual_consistency(
    marker_e85: np.ndarray,
    labels_e85: np.ndarray,
    marker_e95: np.ndarray,
    labels_e95: np.ndarray,
    matches: Mapping[str, str],
) -> dict[str, Any]:
    """Cell-level nearest-centroid assignment agreement with the crosswalk.

    Forward: fraction of each matched E8.5 state's cells whose nearest E9.5
    centroid is the crosswalk target.  Reverse: for each E9.5 state, the top
    E8.5 assignment share.  UNRESOLVED states are reported as diffusion, not
    forced into agreement.
    """
    labels_e85 = np.asarray(labels_e85).astype(str)
    labels_e95 = np.asarray(labels_e95).astype(str)
    cent_e85 = state_centroids(marker_e85, labels_e85)
    cent_e95 = state_centroids(marker_e95, labels_e95)
    states_e85 = sorted(cent_e85)
    states_e95 = sorted(cent_e95)
    c85 = _normalize_rows(np.vstack([cent_e85[s] for s in states_e85]))
    c95 = _normalize_rows(np.vstack([cent_e95[s] for s in states_e95]))
    cells_e85 = _normalize_rows(np.asarray(marker_e85, dtype=np.float64))
    cells_e95 = _normalize_rows(np.asarray(marker_e95, dtype=np.float64))
    assign_to_e95 = np.argmax(cells_e85 @ c95.T, axis=1)
    assign_to_e85 = np.argmax(cells_e95 @ c85.T, axis=1)

    forward: list[dict[str, Any]] = []
    for state in states_e85:
        mask = labels_e85 == state
        top = states_e95[int(np.argmax(np.bincount(assign_to_e95[mask], minlength=len(states_e95))))]
        row: dict[str, Any] = {
            "fine_state": state,
            "n_cells": int(mask.sum()),
            "top_assigned_e95": top,
            "top_share": float(np.mean(assign_to_e95[mask] == states_e95.index(top))),
        }
        if state in matches:
            row["crosswalk_match"] = matches[state]
            row["fraction_assigned_to_match"] = float(
                np.mean(assign_to_e95[mask] == states_e95.index(matches[state]))
            )
        else:
            row["crosswalk_match"] = UNRESOLVED
        forward.append(row)
    matched_fractions = [
        row["fraction_assigned_to_match"] for row in forward if "fraction_assigned_to_match" in row
    ]
    reverse: list[dict[str, Any]] = []
    for state in states_e95:
        mask = labels_e95 == state
        counts = np.bincount(assign_to_e85[mask], minlength=len(states_e85))
        top_index = int(np.argmax(counts))
        reverse.append(
            {
                "fine_state": state,
                "n_cells": int(mask.sum()),
                "top_assigned_e85": states_e85[top_index],
                "top_share": float(counts[top_index] / mask.sum()),
            }
        )
    return {
        "forward_per_state": forward,
        "reverse_per_state": reverse,
        "matched_state_mean_cell_agreement": float(np.mean(matched_fractions)) if matched_fractions else None,
        "matched_state_min_cell_agreement": float(np.min(matched_fractions)) if matched_fractions else None,
        "n_matched_states": len(matched_fractions),
        "n_unresolved_e85_states": sum(1 for row in forward if row["crosswalk_match"] == UNRESOLVED),
    }


def small_state_sensitivity(
    counts_e85: Mapping[str, int],
    counts_e95: Mapping[str, int],
    crosswalk: list[dict[str, Any]],
    *,
    min_cells: int = MIN_STATE_CELLS,
) -> dict[str, Any]:
    """Flag states below the pre-declared size floor and report affected edges."""
    if min_cells < 1:
        raise ValueError("min_cells must be >= 1")
    below = sorted(
        [s for s, n in counts_e85.items() if n < min_cells]
        + [s for s, n in counts_e95.items() if n < min_cells]
    )
    affected = [
        row["fine_state"]
        for row in crosswalk
        if row["fine_state"] in below
        or (row["matched_state"] != UNRESOLVED and row["matched_state"] in below)
    ]
    return {
        "min_cells_threshold": min_cells,
        "states_below_threshold": below,
        "n_states_below": len(below),
        "crosswalk_rows_touching_small_states": sorted(set(affected)),
        "note": "single pre-declared threshold; small states keep their rule-based resolution, no re-derivation",
    }


def residual_extractability(
    parent_path: Path, vocabulary: Iterable[Mapping[str, Any]]
) -> dict[str, Any]:
    """Check that per-state residuals remain extractable from the parent cells."""
    parent_path = Path(parent_path)
    parent = ad.read_h5ad(parent_path, backed="r")
    try:
        if "celltype" not in parent.obs.columns:
            return {
                "parent_path": str(parent_path),
                "extractable": False,
                "reason": "parent obs lacks a celltype/state column",
            }
        parent_counts = state_counts(parent.obs["celltype"].to_numpy())
    finally:
        parent.file.close()
    known = {str(row["fine_state"]) for row in vocabulary}
    uncovered = sorted(set(parent_counts) - known)
    return {
        "parent_path": str(parent_path),
        "parent_sha256": sha256_file(parent_path),
        "parent_n_obs": int(sum(parent_counts.values())),
        "parent_states": {k: parent_counts[k] for k in sorted(parent_counts)},
        "states_not_in_vocabulary": uncovered,
        "extractable": not uncovered,
        "note": "parent rows are real E9.5 cells with frozen labels; per-state residual replay needs vocabulary coverage only",
    }


def load_stage_marker_view(path: Path, markers: list[str]) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Load only the marker columns + labels of a released stage (CSC-friendly)."""
    backed = ad.read_h5ad(path, backed="r")
    try:
        var_names = [str(g) for g in backed.var_names]
        labels = backed.obs["celltype"].astype(str).to_numpy()
        view = marker_matrix(backed.X, var_names, markers)
    finally:
        backed.file.close()
    return view, labels, var_names


def run_projection(
    *,
    source_path: Path,
    crosswalk_rows: list[dict[str, Any]],
    centroids_full_e85: Mapping[str, np.ndarray],
    centroids_full_e95: Mapping[str, np.ndarray],
    output_path: Path,
    counts_e85: Mapping[str, int] | None = None,
    counts_e95: Mapping[str, int] | None = None,
    n_cells: int = PROJECTION_N_CELLS,
    seed: int = SEED,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Source-only E8.5->E9.5 pseudo-holdout projection.

    Real E8.5 cells are replayed (immutable rows) and shifted by the per-state
    full-panel centroid delta of their resolved crosswalk match; UNRESOLVED
    states receive the global all-cell delta (B1-A3 ``unmapped-delta global``
    behaviour).  Sampling follows the observed E8.5 composition only; E9.5
    composition is never used.  Values are clipped at zero per the T1 contract.
    """
    source_path = Path(source_path)
    output_path = Path(output_path)
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output_path}; pass overwrite=True to replace it")
    if n_cells < 1:
        raise ValueError("n_cells must be >= 1")
    matches = crosswalk_matches(crosswalk_rows)
    source = ad.read_h5ad(source_path)
    labels = source.obs["celltype"].astype(str).to_numpy()
    counts = state_counts(labels)
    shares = {state: n / float(sum(counts.values())) for state, n in counts.items()}
    indices = select_indices_by_shares(labels, shares, n_cells=n_cells, seed=seed)
    sampled = source[indices].copy()
    sampled_labels = labels[indices]

    def _weighted_global(
        centroids: Mapping[str, np.ndarray], counts: Mapping[str, int] | None
    ) -> np.ndarray:
        # cell-count-weighted global centroid (B1-A3 global-delta semantics);
        # uniform weighting is only a toy-fixture fallback
        if counts:
            total = float(sum(counts.get(s, 0) for s in centroids)) or 1.0
            weights = np.asarray([counts.get(s, 0) / total for s in centroids])
            stacked = np.vstack([centroids[s] for s in centroids])
            return (weights[:, None] * stacked).sum(axis=0)
        return np.mean(np.vstack(list(centroids.values())), axis=0)

    global_delta = (
        _weighted_global(centroids_full_e95, counts_e95)
        - _weighted_global(centroids_full_e85, counts_e85)
    ).astype(np.float32)
    X = sampled.X
    pred = X.toarray() if sparse.issparse(X) else np.asarray(X, dtype=np.float32)
    pred = pred.astype(np.float32, copy=True)
    rule_counts = {"matched_state_delta": 0, "unresolved_global_delta": 0}
    for state in sorted(np.unique(sampled_labels).tolist()):
        mask = sampled_labels == state
        if state in matches:
            delta = (
                centroids_full_e95[matches[state]] - centroids_full_e85[state]
            ).astype(np.float32)
            rule_counts["matched_state_delta"] += int(mask.sum())
        else:
            delta = global_delta
            rule_counts["unresolved_global_delta"] += int(mask.sum())
        pred[mask] += delta
    np.clip(pred, 0, None, out=pred)

    out = sampled.copy()
    out.X = pred
    out.obsm.clear()
    out.obs["state_family"] = [hierarchy_for(s)[1] for s in sampled_labels]
    out.obs["lineage"] = [hierarchy_for(s)[0] for s in sampled_labels]
    out.obs["projection_rule"] = [
        "matched_state_delta" if s in matches else "unresolved_global_delta"
        for s in sampled_labels
    ]
    metadata: dict[str, Any] = {
        "atom": ATOM,
        "task": "T1",
        "method": "crosswalk_state_centroid_shift_residual_replay",
        "source_stage": SOURCE_STAGE,
        "target_stage": TARGET_STAGE,
        "source_path": str(source_path.resolve()),
        "n_cells": int(n_cells),
        "seed": int(seed),
        "parent_candidate": "candidate/T1_val/v0004_strict_pseudobulk_shift",
        "target_used_for_generation": False,
        "composition_source": "E8.5 observed shares only",
        "rule_counts": rule_counts,
        "matched_states": {k: matches[k] for k in sorted(matches)},
        "is_validation_chain_check": True,
        "is_formal_candidate": False,
    }
    out.uns["ve_t1_pre_harmonize"] = metadata
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_name(output_path.name + ".tmp.h5ad")
    out.write_h5ad(temporary)
    temporary.replace(output_path)

    base_dense = X.toarray() if sparse.issparse(X) else np.asarray(X, dtype=np.float32)
    pb_base = np.asarray(base_dense, dtype=np.float64).mean(axis=0)
    pb_pred = pred.astype(np.float64).mean(axis=0)
    moved = np.abs(pb_pred - pb_base)
    pearson = None
    if pb_base.std() > 0 and pb_pred.std() > 0:
        pearson = float(np.corrcoef(pb_pred, pb_base)[0, 1])
    diagnostics = {
        "output_path": str(output_path.resolve()),
        "output_sha256": sha256_file(output_path),
        "n_obs": int(out.n_obs),
        "n_vars": int(out.n_vars),
        "pseudobulk_mean_abs_delta": float(moved.mean()),
        "pseudobulk_max_abs_delta": float(moved.max()),
        "pseudobulk_pearson_vs_source": pearson,
        "library_size_ratio_vs_source": float(
            pred.sum(axis=1).mean() / max(base_dense.sum(axis=1).mean(), 1e-9)
        ),
        "output_composition": state_counts(sampled_labels),
        "metadata": metadata,
    }
    return diagnostics


def _load_scorer_lock() -> dict[str, Any]:
    lock = json.loads(SCORER_LOCK_PATH.read_text(encoding="utf-8"))
    entry = lock["entrypoint"]
    actual = sha256_file(SCORER_ENTRYPOINT)
    if actual != entry["sha256"]:
        raise RuntimeError(
            f"scorer entrypoint hash drift: lock {entry['sha256']} vs actual {actual}"
        )
    return lock


def scorer_command(out_path: Path, projection_path: Path) -> list[str]:
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
        str(projection_path),
        "--target",
        "data/E9.5_RNA.h5ad",
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


def scorer_launch(out_dir: Path, projection_path: Path) -> dict[str, Any]:
    """Launch the locked scorer as a detached child; record PID and log path.

    A bash supervisor wraps the scorer so its exit code survives the parent
    process: the supervisor writes ``scorer.rc`` atomically after the scorer
    exits.  Never blocks on completion.
    """
    out_dir = Path(out_dir)
    metrics_dir = out_dir / "metrics"
    run_record_path = metrics_dir / "scorer_run.json"
    if run_record_path.exists():
        record = json.loads(run_record_path.read_text(encoding="utf-8"))
        if record.get("status") == "RUNNING" and _pid_alive(int(record["pid"])):
            raise FileExistsError(
                f"scorer already running as pid {record['pid']}; collect or wait first"
            )
        raise FileExistsError(
            f"run record exists at {run_record_path}; refusing to overwrite an immutable run"
        )
    _load_scorer_lock()  # fail closed on scorer bundle drift
    projection_path = Path(projection_path)
    if not projection_path.is_file():
        raise FileNotFoundError(f"projection h5ad missing: {projection_path}")
    out_tmp = metrics_dir / "scorer_output.tmp.json"
    out_final = metrics_dir / "scorer_output.json"
    log_path = out_dir / "scorer_run.log"
    rc_tmp = metrics_dir / "scorer.rc.tmp"
    rc_file = metrics_dir / "scorer.rc"
    for stale in (out_tmp, out_final, rc_tmp, rc_file):
        if stale.exists():
            raise FileExistsError(f"refusing to overwrite existing scorer artifact: {stale}")
    command = scorer_command(out_tmp, projection_path)
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
        "schema": "ve.t1.pre-harmonize-scorer-run.v1",
        "atom": ATOM,
        "status": "RUNNING",
        "pid": process.pid,
        "command": " ".join(command),
        "scorer_lock_path": str(SCORER_LOCK_PATH),
        "scorer_lock_sha256": sha256_file(SCORER_LOCK_PATH),
        "projection_path": str(projection_path),
        "projection_sha256": sha256_file(projection_path),
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


def scorer_collect(out_dir: Path) -> dict[str, Any]:
    """Low-frequency status check: RSS sample when running, result when done."""
    out_dir = Path(out_dir)
    metrics_dir = out_dir / "metrics"
    run_record_path = metrics_dir / "scorer_run.json"
    if not run_record_path.is_file():
        return {"status": "NOT_LAUNCHED", "reason": "no scorer run record"}
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
        record["peak_rss_bytes"] = max(
            [record.get("peak_rss_bytes") or 0] + [rss]
        )
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
            "implementation": "scripts/t1_pre_harmonize.py",
            "implementation_sha256": sha256_file(Path(__file__).resolve()),
            "test_module": "tests/test_t1_pre_harmonize.py",
            "test_module_sha256": sha256_file(ROOT / "tests" / "test_t1_pre_harmonize.py")
            if (ROOT / "tests" / "test_t1_pre_harmonize.py").is_file()
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


def _tool_versions() -> dict[str, Any]:
    import importlib.metadata
    import scipy

    return {
        "schema": "ve.t1.pre-harmonize-tool-versions.v1",
        "atom": ATOM,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "anndata": importlib.metadata.version("anndata"),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "implementation": {
            "path": "scripts/t1_pre_harmonize.py",
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


def command_build(out_dir: Path) -> dict[str, Any]:
    out_dir = Path(out_dir)
    intermediates = out_dir / "intermediates"
    summary: dict[str, Any] = {"step": "build", "atom": ATOM, "seed": SEED}

    input_lock = {
        "schema": "ve.t1.pre-harmonize-input-lock.v1",
        "atom": ATOM,
        "locked_at": datetime.now(timezone.utc).isoformat(),
        "allow_network": False,
        "inputs": {},
    }
    for name, path in (
        ("source_e85", SOURCE_PATH),
        ("target_e95", TARGET_PATH),
        ("parent_v0004", PARENT_PATH),
        ("panel_t1_val", PANEL_PATH),
        ("scorer_lock", SCORER_LOCK_PATH),
    ):
        if not path.is_file():
            raise FileNotFoundError(f"required input missing: {path}")
        input_lock["inputs"][name] = {
            "path": str(path.relative_to(ROOT)),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    if input_lock["inputs"]["parent_v0004"]["sha256"] != PARENT_SHA256:
        raise RuntimeError("parent v0004 hash drift vs P0-LOCK registry")
    _write_json_atomic(out_dir / "inputs" / "input_lock.json", input_lock)

    source = ad.read_h5ad(SOURCE_PATH)
    target = ad.read_h5ad(TARGET_PATH)
    var_names = [str(g) for g in source.var_names]
    if var_names != [str(g) for g in target.var_names]:
        raise ValueError("E8.5/E9.5 var_names differ; harmonisation requires the released order")
    labels_e85 = source.obs["celltype"].astype(str).to_numpy()
    labels_e95 = target.obs["celltype"].astype(str).to_numpy()
    counts_e85 = state_counts(labels_e85)
    counts_e95 = state_counts(labels_e95)

    vocabulary = vocabulary_rows(counts_e85, counts_e95)
    _write_tsv_atomic(intermediates / "state_vocabulary.tsv", vocabulary, VOCABULARY_TSV_FIELDS)

    programs, markers = program_rows(var_names)
    _write_tsv_atomic(intermediates / "program_definition.tsv", programs, PROGRAM_TSV_FIELDS)

    marker_e85 = marker_matrix(source.X, var_names, markers)
    marker_e95 = marker_matrix(target.X, var_names, markers)
    cent_marker_e85 = state_centroids(marker_e85, labels_e85)
    cent_marker_e95 = state_centroids(marker_e95, labels_e95)
    cent_full_e85 = full_panel_centroids(source.X, labels_e85)
    cent_full_e95 = full_panel_centroids(target.X, labels_e95)

    crosswalk = build_crosswalk_rows(
        cent_marker_e85, cent_marker_e95, counts_e85, counts_e95, tau=COSINE_TAU
    )
    _write_tsv_atomic(intermediates / "state_crosswalk.tsv", crosswalk, CROSSWALK_TSV_FIELDS)

    npz_tmp = intermediates / "state_centroids.tmp.npz"  # np.savez appends .npz itself
    np.savez(
        npz_tmp,
        var_names=np.asarray(var_names),
        marker_genes=np.asarray(markers),
        states_e85=np.asarray(sorted(cent_full_e85)),
        states_e95=np.asarray(sorted(cent_full_e95)),
        centroids_e85_full=np.vstack([cent_full_e85[s] for s in sorted(cent_full_e85)]),
        centroids_e95_full=np.vstack([cent_full_e95[s] for s in sorted(cent_full_e95)]),
        centroids_e85_marker=np.vstack([cent_marker_e85[s] for s in sorted(cent_marker_e85)]),
        centroids_e95_marker=np.vstack([cent_marker_e95[s] for s in sorted(cent_marker_e95)]),
    )
    npz_tmp.replace(intermediates / "state_centroids.npz")

    matched = crosswalk_matches(crosswalk)
    unresolved_e85 = [
        row["fine_state"]
        for row in crosswalk
        if row["direction"] == "e85_to_e95" and row["matched_state"] == UNRESOLVED
    ]
    summary.update(
        {
            "n_union_states": len(vocabulary),
            "n_shared_exact": sum(1 for r in vocabulary if r["vocabulary_status"] == "SHARED_EXACT"),
            "n_source_only": sum(1 for r in vocabulary if r["vocabulary_status"] == "SOURCE_ONLY"),
            "n_target_only": sum(1 for r in vocabulary if r["vocabulary_status"] == "TARGET_ONLY"),
            "n_markers_present": len(markers),
            "n_mutual_nearest_matches": sum(
                1 for r in crosswalk if r["match_rule"] == "MUTUAL_NEAREST"
            ),
            "unresolved_e85_states": sorted(unresolved_e85),
            "matched_forward": {k: matched[k] for k in sorted(matched)},
        }
    )
    return summary


def command_stability(out_dir: Path) -> dict[str, Any]:
    out_dir = Path(out_dir)
    intermediates = out_dir / "intermediates"
    _program_rows, markers = program_rows(
        np.load(intermediates / "state_centroids.npz", allow_pickle=False)["var_names"].tolist()
    )
    marker_e85, labels_e85, _ = load_stage_marker_view(SOURCE_PATH, markers)
    marker_e95, labels_e95, _ = load_stage_marker_view(TARGET_PATH, markers)
    with (intermediates / "state_crosswalk.tsv").open(encoding="utf-8") as handle:
        crosswalk = list(csv.DictReader(handle, delimiter="\t"))
    with (intermediates / "state_vocabulary.tsv").open(encoding="utf-8") as handle:
        vocabulary = list(csv.DictReader(handle, delimiter="\t"))
    matches = crosswalk_matches(crosswalk)
    counts_e85 = state_counts(labels_e85)
    counts_e95 = state_counts(labels_e95)

    stability = {
        "schema": "ve.t1.pre-harmonize-state-stability.v1",
        "atom": ATOM,
        "seed": SEED,
        "predeclared": {
            "cosine_tau": COSINE_TAU,
            "bootstrap_rounds": BOOTSTRAP_ROUNDS,
            "min_state_cells": MIN_STATE_CELLS,
            "single_pass_no_grid": True,
        },
        "bootstrap": bootstrap_crosswalk_stability(
            marker_e85, labels_e85, marker_e95, labels_e95,
            rounds=BOOTSTRAP_ROUNDS, seed=SEED, tau=COSINE_TAU,
        ),
        "projection_mutual_consistency": projection_mutual_consistency(
            marker_e85, labels_e85, marker_e95, labels_e95, matches
        ),
        "small_state_sensitivity": small_state_sensitivity(counts_e85, counts_e95, crosswalk),
        "residual_extractability": residual_extractability(PARENT_PATH, vocabulary),
    }
    _write_json_atomic(out_dir / "metrics" / "state_stability.json", stability)
    return {
        "step": "stability",
        "bootstrap_mean_recovery": stability["bootstrap"]["mean_recovery"],
        "bootstrap_min_recovery": stability["bootstrap"]["min_recovery"],
        "matched_state_mean_cell_agreement": stability["projection_mutual_consistency"][
            "matched_state_mean_cell_agreement"
        ],
        "residual_extractable": stability["residual_extractability"]["extractable"],
    }


def command_project(out_dir: Path) -> dict[str, Any]:
    out_dir = Path(out_dir)
    intermediates = out_dir / "intermediates"
    with (intermediates / "state_crosswalk.tsv").open(encoding="utf-8") as handle:
        crosswalk = list(csv.DictReader(handle, delimiter="\t"))
    with (intermediates / "state_vocabulary.tsv").open(encoding="utf-8") as handle:
        vocabulary = list(csv.DictReader(handle, delimiter="\t"))
    counts_e85 = {row["fine_state"]: int(row["n_cells_e85"]) for row in vocabulary if int(row["n_cells_e85"])}
    counts_e95 = {row["fine_state"]: int(row["n_cells_e95"]) for row in vocabulary if int(row["n_cells_e95"])}
    npz = np.load(intermediates / "state_centroids.npz", allow_pickle=False)
    states_e85 = npz["states_e85"].tolist()
    states_e95 = npz["states_e95"].tolist()
    cent_full_e85 = {
        state: npz["centroids_e85_full"][i] for i, state in enumerate(states_e85)
    }
    cent_full_e95 = {
        state: npz["centroids_e95_full"][i] for i, state in enumerate(states_e95)
    }
    projection_path = intermediates / "projection_e85_to_e95.h5ad"
    diagnostics = run_projection(
        source_path=SOURCE_PATH,
        crosswalk_rows=crosswalk,
        centroids_full_e85=cent_full_e85,
        centroids_full_e95=cent_full_e95,
        output_path=projection_path,
        counts_e85=counts_e85,
        counts_e95=counts_e95,
        n_cells=PROJECTION_N_CELLS,
        seed=SEED,
    )
    record = {
        "schema": "ve.t1.pre-harmonize-projection-pseudoholdout.v1",
        "atom": ATOM,
        "seed": SEED,
        "generation": diagnostics,
        "scorer": {"status": "NOT_LAUNCHED"},
        "interpretation": (
            "source-only E8.5->E9.5 projection with the same vocabulary; validates the "
            "representation and the full-panel scorer chain only -- not a leaderboard preview "
            "and not a future-state candidate"
        ),
    }
    _write_json_atomic(out_dir / "metrics" / "projection_pseudoholdout.json", record)
    return {
        "step": "project",
        "output": diagnostics["output_path"],
        "output_sha256": diagnostics["output_sha256"],
        "n_obs": diagnostics["n_obs"],
        "pseudobulk_pearson_vs_source": diagnostics["pseudobulk_pearson_vs_source"],
    }


def command_score_launch(out_dir: Path) -> dict[str, Any]:
    out_dir = Path(out_dir)
    projection = out_dir / "intermediates" / "projection_e85_to_e95.h5ad"
    record = scorer_launch(out_dir, projection)
    return {"step": "score-launch", "pid": record["pid"], "log_path": record["log_path"]}


def command_score_collect(out_dir: Path) -> dict[str, Any]:
    out_dir = Path(out_dir)
    record = scorer_collect(out_dir)
    pseudoholdout_path = out_dir / "metrics" / "projection_pseudoholdout.json"
    if pseudoholdout_path.is_file():
        payload = json.loads(pseudoholdout_path.read_text(encoding="utf-8"))
        payload["scorer"] = {
            key: record.get(key)
            for key in (
                "status", "pid", "command", "log_path", "started_at", "finished_at",
                "wall_seconds", "peak_rss_bytes", "exit_code", "result_path",
                "result_sha256", "result_meta", "result_metrics", "result_checks",
                "failure_reason",
            )
            if key in record
        }
        _write_json_atomic(pseudoholdout_path, payload)
    return {
        "step": "score-collect",
        "status": record.get("status"),
        "pid": record.get("pid"),
        "peak_rss_bytes": record.get("peak_rss_bytes"),
    }


def command_finalize(out_dir: Path) -> dict[str, Any]:
    out_dir = Path(out_dir)
    lock = _load_scorer_lock()
    run_record_path = out_dir / "metrics" / "scorer_run.json"
    run_record = (
        json.loads(run_record_path.read_text(encoding="utf-8"))
        if run_record_path.is_file()
        else None
    )
    p0_result_ok = (
        P0_FULL_PANEL_RESULT.is_file()
        and sha256_file(P0_FULL_PANEL_RESULT) == P0_FULL_PANEL_SHA256
    )
    wrapper_status = (run_record or {}).get("status", "NOT_LAUNCHED")
    if wrapper_status == "DONE" and (run_record or {}).get("result_checks", {}).get(
        "genes_match"
    ):
        overall = "PASS"
    elif wrapper_status == "RUNNING":
        overall = "RUNNING_BACKGROUND"
    elif wrapper_status in ("FAILED",):
        overall = "BLOCKED_VALIDATION"
    else:
        overall = "NOT_LAUNCHED"
    check = {
        "schema": "ve.t1.pre-harmonize-scorer-check.v1",
        "atom": ATOM,
        "p0_evidence_reuse": {
            "scorer_lock_path": str(SCORER_LOCK_PATH.relative_to(ROOT)),
            "scorer_lock_sha256": sha256_file(SCORER_LOCK_PATH),
            "full_panel_result_path": str(P0_FULL_PANEL_RESULT.relative_to(ROOT)),
            "full_panel_result_sha256_locked": P0_FULL_PANEL_SHA256,
            "full_panel_result_sha256_observed": sha256_file(P0_FULL_PANEL_RESULT)
            if P0_FULL_PANEL_RESULT.is_file()
            else None,
            "p0_result_intact": p0_result_ok,
            "p0_status": lock["status"],
        },
        "wrapper_validation": run_record,
        "overall_status": overall,
        "note": (
            "wrapper reuses the P0-locked command/env/seed; only --input/--out differ "
            "(projection instead of parent). A DONE wrapper run with matching meta proves "
            "the full-panel scorer is runnable in this atom's chain."
        ),
    }
    _write_json_atomic(out_dir / "metrics" / "full_panel_scorer_check.json", check)

    config_text = "\n".join(
        [
            f"atom: {ATOM}",
            "task: T1-PRE-HARMONIZE",
            f"seed: {SEED}",
            "allow_network: false",
            "allow_server_submission: false",
            "candidate_generation: false",
            "source_stage: E8.5",
            "target_stage: E9.5",
            f"parent_candidate: candidate/T1_val/v0004_strict_pseudobulk_shift",
            f"parent_sha256: {PARENT_SHA256}",
            f"cosine_tau: {COSINE_TAU}",
            f"bootstrap_rounds: {BOOTSTRAP_ROUNDS}",
            f"min_state_cells: {MIN_STATE_CELLS}",
            f"projection_n_cells: {PROJECTION_N_CELLS}",
            "representation_route: frozen official obs['celltype'] labels (route 1)",
            "crosswalk_rule: marker cosine + mutual nearest centroid; low confidence -> UNRESOLVED",
            "deviations: []",
            "",
        ]
    )
    _write_bytes_atomic(out_dir / "config_resolved.yaml", config_text.encode("utf-8"))
    _write_json_atomic(out_dir / "TOOL_VERSIONS.json", _tool_versions())
    return {"step": "finalize", "overall_status": overall}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=[
            "build", "stability", "project", "score-launch", "score-collect",
            "finalize", "manifest", "verify",
        ],
    )
    parser.add_argument("--out-dir", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)

    started = time.monotonic()
    if args.command == "build":
        summary = command_build(args.out_dir)
    elif args.command == "stability":
        summary = command_stability(args.out_dir)
    elif args.command == "project":
        summary = command_project(args.out_dir)
    elif args.command == "score-launch":
        summary = command_score_launch(args.out_dir)
    elif args.command == "score-collect":
        summary = command_score_collect(args.out_dir)
    elif args.command == "finalize":
        summary = command_finalize(args.out_dir)
    elif args.command == "manifest":
        manifest = write_manifest(
            args.out_dir,
            exclude=("run.log", "scorer_run.log", "metrics/scorer_run.json"),
        )
        summary = {
            "step": "manifest",
            "n_files": len(manifest["files"]),
            "self_verify_ok": manifest["self_verify"]["ok"],
        }
    else:
        summary = verify_manifest(args.out_dir)
    summary["wall_seconds"] = round(time.monotonic() - started, 3)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
