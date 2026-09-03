#!/usr/bin/env python3
"""HX-DYNAMICS-KILLTEST: single-hypothesis kill test for MIOFlow dynamics.

Replaces ONLY the moscot static transport coupling of the frozen T1-S2 pipeline
with MIOFlow (mioflow==0.1.14, SDE + growth/death) and asks one pre-declared
question on the source-only E8.5->E9.5 holdout:

    kill metric: per-state mass distribution L1 error over the frozen 28-state
    union vocabulary; the MIOFlow arm must strictly beat BOTH frozen control
    arms (strict-shift parent arm AND moscot-decoder arm), otherwise REJECT.

No H5AD candidate is generated, the server is never contacted, and the hidden
stages (E10.5/E12.5) are never read.  Control arms are arithmetic on frozen
T1-PRE/T1-S2 artifacts (no pipeline re-run; sources hash-recorded).

Environment split (toolchain rule):

* ``prepare`` / ``evaluate`` / ``manifest`` / ``verify`` run under the ve-core
  interpreter (/opt/anaconda3/bin/python) and reuse frozen helpers from
  ``scripts/t1_s2_moscot_decoder.py`` and ``scripts/t1_pre_harmonize.py``.
* ``train`` launches the isolated ``.venvs/ve-hx-mioflow`` interpreter on
  ``scripts/hx_mioflow_worker.py`` (one training run, hard 2h wall-clock cap);
  the worker only reads/writes standard npz intermediates.

Pre-declared in ``config_resolved.yaml`` before any run: kill metric
definition, decision rule, scale caps (3000 cells/stage, 100 epochs, dt=0.1),
library-default hyperparameters, seed 20260830.  No grid search.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from scripts.t1_s2_moscot_decoder import (
    _derived_seed,
    _read_tsv,
    _write_json_atomic,
    _write_tsv_atomic,
    load_pre_intermediates,
    reverse_matches,
    sha256_file,
)
from scripts.t1_pre_harmonize import load_stage_marker_view
from scripts.t1_temporal_model import select_indices_by_shares

ROOT = Path(__file__).resolve().parents[1]
ATOM = "HX-DYNAMICS-KILLTEST-20260904-v1"
OUTPUT_DEFAULT = ROOT / "artifacts" / "tool_integration" / ATOM
SEED = 20260830

SOURCE_PATH = ROOT / "data" / "E8.5_RNA.h5ad"
TARGET_PATH = ROOT / "data" / "E9.5_RNA.h5ad"
PRE_DIR = ROOT / "artifacts" / "tool_integration" / "T1-PRE-HARMONIZE-20260902-v1"
S2_DIR = ROOT / "artifacts" / "tool_integration" / "T1-S2-MOSCOT-DECODER-20260902-v1"
S2_STATE_MASS = S2_DIR / "intermediates" / "state_mass.tsv"
VENV_PYTHON = ROOT / ".venvs" / "ve-hx-mioflow" / "bin" / "python"
WORKER_SCRIPT = ROOT / "scripts" / "hx_mioflow_worker.py"

# Pre-declared scale caps (config_resolved.yaml; no search, no second run).
CELLS_PER_STAGE_MAX = 3000
N_EPOCHS = 100
GROWTH_PRETRAIN_EPOCHS = 50
WALL_CLOCK_CAP_SECONDS = 7200  # hard cap on the train subprocess; over -> BLOCKED

TRAIN_INPUT_NPZ = "mioflow_train_input.npz"
GENERATED_NPZ = "mioflow_generated.npz"
TRAIN_SUMMARY_JSON = "mioflow_train_summary.json"

STATE_MASS_PREDICTIONS_FIELDS = [
    "state", "lineage", "support", "truth_share_e95",
    "parent_arm_share", "moscot_arm_share", "mioflow_arm_share",
    "abs_err_parent", "abs_err_moscot", "abs_err_mioflow",
    "signed_err_parent", "signed_err_moscot", "signed_err_mioflow",
]


# ---------------------------------------------------------------------------
# Pure metric primitives (unit-tested on toy data)
# ---------------------------------------------------------------------------


def vocabulary_shares(vocabulary: list[dict[str, str]], column: str) -> dict[str, float]:
    """Observed per-state shares from the frozen 28-state vocabulary."""
    counts = {row["fine_state"]: int(row[column]) for row in vocabulary}
    total = sum(counts.values())
    if total <= 0:
        raise ValueError(f"vocabulary column {column!r} sums to zero")
    return {state: n / total for state, n in counts.items()}


def parent_arm_vector(vocabulary: list[dict[str, str]]) -> dict[str, float]:
    """Strict-shift parent arm: composition preserved -> observed E8.5 shares."""
    return vocabulary_shares(vocabulary, "n_cells_e85")


def truth_vector(vocabulary: list[dict[str, str]]) -> dict[str, float]:
    """Observed E9.5 holdout composition over the 28 union states."""
    return vocabulary_shares(vocabulary, "n_cells_e95")


def moscot_arm_vector(
    mass_rows: list[dict[str, str]], vocabulary: list[dict[str, str]]
) -> dict[str, float]:
    """Frozen T1-S2 pseudo-holdout mass (14 resolved targets, renormalised)."""
    vec = {row["fine_state"]: 0.0 for row in vocabulary}
    n = 0
    for row in mass_rows:
        if row["board"] != "T1:pseudo_holdout":
            continue
        if row["state"] not in vec:
            raise ValueError(f"mass row state outside vocabulary: {row['state']!r}")
        vec[row["state"]] = float(row["shrunk_probability"])
        n += 1
    if n == 0:
        raise ValueError("no T1:pseudo_holdout rows in state_mass.tsv")
    total = sum(vec.values())
    if abs(total - 1.0) > 1e-3:
        raise ValueError(f"moscot arm shares not normalised (sum={total})")
    return vec


def assign_to_states(
    points: np.ndarray, centroids: np.ndarray
) -> np.ndarray:
    """Nearest-centroid index per point (euclidean, ties -> lowest index)."""
    points = np.asarray(points, dtype=np.float64)
    centroids = np.asarray(centroids, dtype=np.float64)
    if points.ndim != 2 or centroids.ndim != 2 or points.shape[1] != centroids.shape[1]:
        raise ValueError("points/centroids dimension mismatch")
    dists = ((points[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2)
    return dists.argmin(axis=1)


def weighted_state_shares(
    assignments: np.ndarray, weights: np.ndarray, n_states: int
) -> np.ndarray:
    """Growth-weighted per-state mass, renormalised over the assignment support."""
    assignments = np.asarray(assignments, dtype=np.int64)
    weights = np.asarray(weights, dtype=np.float64)
    if assignments.shape[0] != weights.shape[0]:
        raise ValueError("assignments/weights length mismatch")
    if (weights < 0).any():
        raise ValueError("growth weights must be non-negative")
    shares = np.zeros(n_states, dtype=np.float64)
    np.add.at(shares, assignments, weights)
    total = shares.sum()
    if total <= 0:
        raise ValueError("total generated mass is zero")
    return shares / total


def l1_distance(p: Mapping[str, float], q: Mapping[str, float], states: list[str]) -> float:
    """The one pre-declared kill metric: sum_s |p_s - q_s| over the 28 states."""
    return float(sum(abs(float(p.get(s, 0.0)) - float(q.get(s, 0.0))) for s in states))


def verdict(l1_mioflow: float, l1_parent: float, l1_moscot: float) -> dict[str, Any]:
    """SUPPORTED iff MIOFlow is strictly better than BOTH control arms."""
    beats_parent = l1_mioflow < l1_parent
    beats_moscot = l1_mioflow < l1_moscot
    supported = beats_parent and beats_moscot
    return {
        "verdict": "SUPPORTED" if supported else "REJECT",
        "beats_parent_strictly": beats_parent,
        "beats_moscot_strictly": beats_moscot,
        "rule": "L1_mioflow < L1_parent AND L1_mioflow < L1_moscot (strict; ties reject)",
    }


# ---------------------------------------------------------------------------
# prepare (ve-core): stratified subsample + frozen marker program space
# ---------------------------------------------------------------------------


def command_prepare(out_dir: Path) -> dict[str, Any]:
    out_dir = Path(out_dir)
    pre = load_pre_intermediates()
    markers = pre["marker_genes"]
    vocab = pre["vocabulary"]

    per_stage: dict[str, dict[str, Any]] = {}
    embeds: dict[str, np.ndarray] = {}
    labels: dict[str, np.ndarray] = {}
    for tag, path in (("e85", SOURCE_PATH), ("e95", TARGET_PATH)):
        view, stage_labels, _ = load_stage_marker_view(path, markers)
        counts = {s: int((stage_labels == s).sum()) for s in np.unique(stage_labels)}
        total = sum(counts.values())
        shares = {s: n / total for s, n in counts.items()}
        idx = select_indices_by_shares(
            stage_labels, shares, n_cells=CELLS_PER_STAGE_MAX,
            seed=_derived_seed("hx", "subsample", tag),
        )
        embeds[tag] = view[idx]
        labels[tag] = stage_labels[idx]
        per_stage[tag] = {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha256_file(path),
            "n_cells_total": int(total),
            "n_cells_subsampled": int(idx.size),
            "state_counts_subsampled": {
                s: int((labels[tag] == s).sum()) for s in sorted(np.unique(labels[tag]))
            },
        }

    union = np.vstack([embeds["e85"], embeds["e95"]])
    mean = union.mean(axis=0)
    std = union.std(axis=0)
    std[std == 0] = 1.0
    z0 = ((embeds["e85"] - mean) / std).astype(np.float32)
    z1 = ((embeds["e95"] - mean) / std).astype(np.float32)

    rev = reverse_matches(pre["crosswalk"])
    resolved_targets = sorted(rev)
    states_e95 = pre["states_e95"]
    cent_idx = [states_e95.index(s) for s in resolved_targets]
    centroids_resolved = pre["centroids_e95_marker"][cent_idx]
    centroids_resolved_z = ((centroids_resolved - mean) / std).astype(np.float32)

    npz_path = out_dir / "intermediates" / TRAIN_INPUT_NPZ
    npz_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = npz_path.with_suffix(".tmp.npz")
    np.savez(
        tmp,
        X0=z0, X1=z1,
        labels0=labels["e85"], labels1=labels["e95"],
        marker_genes=np.asarray(markers),
        zscore_mean=mean.astype(np.float64), zscore_std=std.astype(np.float64),
        centroids_resolved_z=centroids_resolved_z,
        resolved_targets=np.asarray(resolved_targets),
    )
    tmp.replace(npz_path)

    record = {
        "schema": "ve.hx.prepare.v1",
        "atom": ATOM,
        "seed": SEED,
        "cells_per_stage_max": CELLS_PER_STAGE_MAX,
        "n_markers": len(markers),
        "zscore": "per-marker mean/std over the union of the two subsampled stages",
        "resolved_targets": resolved_targets,
        "n_resolved_targets": len(resolved_targets),
        "stages": per_stage,
        "pre_input_hashes": pre["input_hashes"],
        "output": {"path": str(npz_path.relative_to(ROOT)), "sha256": sha256_file(npz_path)},
    }
    _write_json_atomic(out_dir / "metrics" / "prepare.json", record)
    return {"step": "prepare", "npz": str(npz_path), "sha256": record["output"]["sha256"]}


# ---------------------------------------------------------------------------
# train: one MIOFlow run in the isolated venv (hard wall-clock cap)
# ---------------------------------------------------------------------------


def command_train(out_dir: Path) -> dict[str, Any]:
    out_dir = Path(out_dir)
    npz_in = out_dir / "intermediates" / TRAIN_INPUT_NPZ
    npz_out = out_dir / "intermediates" / GENERATED_NPZ
    summary_out = out_dir / "intermediates" / TRAIN_SUMMARY_JSON
    log_path = out_dir / "logs" / "mioflow_train.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if not npz_in.is_file():
        raise FileNotFoundError(f"training input missing: {npz_in}; run `prepare` first")
    if not VENV_PYTHON.is_file():
        raise FileNotFoundError(f"venv interpreter missing: {VENV_PYTHON}")

    cmd = [
        str(VENV_PYTHON), str(WORKER_SCRIPT),
        "--input", str(npz_in),
        "--out", str(npz_out),
        "--summary", str(summary_out),
        "--seed", str(_derived_seed("hx", "mioflow")),
        "--epochs", str(N_EPOCHS),
        "--growth-epochs", str(GROWTH_PRETRAIN_EPOCHS),
    ]
    started = time.monotonic()
    with log_path.open("w", encoding="utf-8") as log:
        log.write("command: " + " ".join(cmd) + "\n")
        log.write(f"wall_clock_cap_seconds: {WALL_CLOCK_CAP_SECONDS}\n")
        log.flush()
        try:
            proc = subprocess.run(
                cmd, stdout=log, stderr=subprocess.STDOUT,
                timeout=WALL_CLOCK_CAP_SECONDS, cwd=str(ROOT),
            )
            rc = proc.returncode
            timed_out = False
        except subprocess.TimeoutExpired:
            rc = None
            timed_out = True
    wall = time.monotonic() - started

    record: dict[str, Any] = {
        "schema": "ve.hx.train.v1",
        "atom": ATOM,
        "command": cmd,
        "wall_seconds": wall,
        "wall_clock_cap_seconds": WALL_CLOCK_CAP_SECONDS,
        "timed_out": timed_out,
        "returncode": rc,
        "log": str(log_path.relative_to(ROOT)),
    }
    if timed_out:
        record["status"] = "BLOCKED"
        record["blocked"] = {
            "object": "mioflow_training_run",
            "completed": "growth pretrain/training partial; see log tail",
            "min_unblock": "GPU instance or reduced scale caps with a NEW authorisation "
                           "(budget allows exactly one training run; it hit the 2h cap)",
        }
        _write_json_atomic(out_dir / "metrics" / "train_run.json", record)
        raise RuntimeError("MIOFlow training exceeded the 2h wall-clock cap -> BLOCKED")
    if rc != 0 or not npz_out.is_file():
        record["status"] = "BLOCKED"
        record["blocked"] = {
            "object": "mioflow_training_run",
            "completed": "worker exited nonzero or wrote no output; see log",
            "min_unblock": "fix the worker/toolchain error and rerun the single training run",
        }
        _write_json_atomic(out_dir / "metrics" / "train_run.json", record)
        raise RuntimeError(f"MIOFlow worker failed (rc={rc}); see {log_path}")

    summary = json.loads(summary_out.read_text(encoding="utf-8"))
    record.update(
        status="DONE",
        worker_summary=summary,
        outputs={
            "generated_npz": {
                "path": str(npz_out.relative_to(ROOT)), "sha256": sha256_file(npz_out)
            },
            "summary_json": {
                "path": str(summary_out.relative_to(ROOT)), "sha256": sha256_file(summary_out)
            },
        },
    )
    _write_json_atomic(out_dir / "metrics" / "train_run.json", record)
    return {"step": "train", "wall_seconds": wall, "summary": summary}


# ---------------------------------------------------------------------------
# evaluate (budget: 1): three-arm per-state mass L1 on the E9.5 holdout
# ---------------------------------------------------------------------------


def command_evaluate(out_dir: Path) -> dict[str, Any]:
    out_dir = Path(out_dir)
    pre = load_pre_intermediates()
    vocab = pre["vocabulary"]
    states = sorted(row["fine_state"] for row in vocab)
    lineage_by_state = {row["fine_state"]: row["lineage"] for row in vocab}

    q = truth_vector(vocab)
    p_parent = parent_arm_vector(vocab)
    mass_rows = _read_tsv(S2_STATE_MASS)
    p_moscot = moscot_arm_vector(mass_rows, vocab)

    gen = np.load(out_dir / "intermediates" / GENERATED_NPZ, allow_pickle=False)
    endpoints = gen["endpoints_z"]
    weights = gen["weights"]
    centroids = gen["centroids_resolved_z"]
    resolved = [str(s) for s in gen["resolved_targets"].tolist()]
    assignments = assign_to_states(endpoints, centroids)
    shares = weighted_state_shares(assignments, weights, len(resolved))
    p_mioflow = {s: 0.0 for s in states}
    for i, s in enumerate(resolved):
        p_mioflow[s] = float(shares[i])

    l1_parent = l1_distance(p_parent, q, states)
    l1_moscot = l1_distance(p_moscot, q, states)
    l1_mio = l1_distance(p_mioflow, q, states)
    decision = verdict(l1_mio, l1_parent, l1_moscot)

    support = {
        s: ("source_only" if int(v["n_cells_e85"]) > 0 and int(v["n_cells_e95"]) == 0
            else "target_only" if int(v["n_cells_e85"]) == 0
            else "shared")
        for v in vocab for s in [v["fine_state"]]
    }
    rows = []
    for s in states:
        rows.append({
            "state": s,
            "lineage": lineage_by_state[s],
            "support": support[s],
            "truth_share_e95": f"{q[s]:.6f}",
            "parent_arm_share": f"{p_parent[s]:.6f}",
            "moscot_arm_share": f"{p_moscot[s]:.6f}",
            "mioflow_arm_share": f"{p_mioflow[s]:.6f}",
            "abs_err_parent": f"{abs(p_parent[s] - q[s]):.6f}",
            "abs_err_moscot": f"{abs(p_moscot[s] - q[s]):.6f}",
            "abs_err_mioflow": f"{abs(p_mioflow[s] - q[s]):.6f}",
            "signed_err_parent": f"{p_parent[s] - q[s]:+.6f}",
            "signed_err_moscot": f"{p_moscot[s] - q[s]:+.6f}",
            "signed_err_mioflow": f"{p_mioflow[s] - q[s]:+.6f}",
        })
    _write_tsv_atomic(
        out_dir / "intermediates" / "mass_predictions.tsv", rows, STATE_MASS_PREDICTIONS_FIELDS
    )

    record: dict[str, Any] = {
        "schema": "ve.hx.killtest.v1",
        "atom": ATOM,
        "seed": SEED,
        "kill_metric": {
            "name": "holdout_state_mass_l1",
            "formula": "sum_s |p_s - q_s| over the frozen 28 union fine_states; lower is better",
            "definition_frozen_in": "config_resolved.yaml (written before any run)",
        },
        "holdout": {
            "design": "source-only leave-one-stage-out (E9.5 held out); E9.5 is a training "
                      "stage, so this validates the hypothesis machinery only -- never a "
                      "leaderboard preview, never a model-improvement claim by itself",
            "truth": "observed E9.5 per-state shares from the frozen T1-PRE vocabulary",
        },
        "arms": {
            "parent": {
                "construction": "strict-shift preserves composition -> observed E8.5 shares",
                "l1": l1_parent,
                "source": {
                    "path": str((PRE_DIR / "intermediates" / "state_vocabulary.tsv").relative_to(ROOT)),
                    "sha256": sha256_file(PRE_DIR / "intermediates" / "state_vocabulary.tsv"),
                    "reuse": "frozen artifact arithmetic (no pipeline re-run)",
                },
            },
            "moscot": {
                "construction": "T1-S2 frozen T1:pseudo_holdout shrunk_probability "
                                "(14 resolved targets renormalised; P1 boundary: 0 elsewhere)",
                "l1": l1_moscot,
                "source": {
                    "path": str(S2_STATE_MASS.relative_to(ROOT)),
                    "sha256": sha256_file(S2_STATE_MASS),
                    "reuse": "frozen artifact arithmetic (no pipeline re-run)",
                },
            },
            "mioflow": {
                "construction": "mioflow 0.1.14 SDE + GrowthRateModel, library defaults, one "
                                "training run; 3000 seeded paths from all subsampled E8.5 cells, "
                                "growth-weighted endpoints, nearest resolved E9.5 centroid in the "
                                "z-scored 74-marker space, renormalised over the same 14 targets",
                "l1": l1_mio,
                "n_paths": int(endpoints.shape[0]),
                "weight_summary": {
                    "min": float(weights.min()),
                    "mean": float(weights.mean()),
                    "max": float(weights.max()),
                },
                "source": {
                    "path": f"artifacts/tool_integration/{ATOM}/intermediates/{GENERATED_NPZ}",
                    "sha256": sha256_file(out_dir / "intermediates" / GENERATED_NPZ),
                },
            },
        },
        "decision": decision,
    }

    if decision["verdict"] == "SUPPORTED":
        # Complementarity is evaluated ONLY when the kill metric improves.
        err_mio = np.array([p_mioflow[s] - q[s] for s in states])
        err_par = np.array([p_parent[s] - q[s] for s in states])
        err_mos = np.array([p_moscot[s] - q[s] for s in states])
        record["complementarity"] = {
            "corr_signed_error_mioflow_vs_parent": float(np.corrcoef(err_mio, err_par)[0, 1]),
            "corr_signed_error_mioflow_vs_moscot": float(np.corrcoef(err_mio, err_mos)[0, 1]),
            "states_where_mioflow_best_of_three": sorted(
                s for s in states
                if abs(p_mioflow[s] - q[s]) < abs(p_parent[s] - q[s])
                and abs(p_mioflow[s] - q[s]) < abs(p_moscot[s] - q[s])
            ),
        }

    _write_json_atomic(out_dir / "metrics" / "holdout_mass_l1.json", record)
    return {"step": "evaluate", "l1": {"parent": l1_parent, "moscot": l1_moscot, "mioflow": l1_mio},
            "verdict": decision["verdict"]}


# ---------------------------------------------------------------------------
# manifest / verify (stable artifact manifest, self-verified)
# ---------------------------------------------------------------------------


def _git_commit() -> str | None:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=str(ROOT),
            capture_output=True, text=True, check=True,
        )
        return proc.stdout.strip()
    except Exception:
        return None


def write_manifest(out_dir: Path, *, exclude: tuple[str, ...] = ()) -> dict[str, Any]:
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
        files.append({
            "path": relative,
            "bytes": path.stat().st_size,
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
            "role": relative.split("/", 1)[0],
        })
    manifest: dict[str, Any] = {
        "schema": "ve.tool-integration-artifact-manifest.v1",
        "task_id": ATOM,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "repo_commit": _git_commit(),
        "seed": SEED,
        "files": files,
        "excluded_live_paths": sorted(exclude),
        "provenance": {
            "implementation": "scripts/hx_dynamics_killtest.py",
            "implementation_sha256": sha256_file(Path(__file__).resolve()),
            "worker": "scripts/hx_mioflow_worker.py",
            "worker_sha256": sha256_file(WORKER_SCRIPT) if WORKER_SCRIPT.is_file() else None,
            "test_module": "tests/test_hx_dynamics_killtest.py",
            "test_module_sha256": sha256_file(ROOT / "tests" / "test_hx_dynamics_killtest.py")
            if (ROOT / "tests" / "test_hx_dynamics_killtest.py").is_file() else None,
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


# ---------------------------------------------------------------------------
# input lock: hash every file this atom reads
# ---------------------------------------------------------------------------


def command_input_lock(out_dir: Path) -> dict[str, Any]:
    out_dir = Path(out_dir)
    inputs: dict[str, Any] = {}
    for name, path in (
        ("source_e85", SOURCE_PATH),
        ("target_e95", TARGET_PATH),
        ("pre_state_vocabulary", PRE_DIR / "intermediates" / "state_vocabulary.tsv"),
        ("pre_state_crosswalk", PRE_DIR / "intermediates" / "state_crosswalk.tsv"),
        ("pre_state_centroids", PRE_DIR / "intermediates" / "state_centroids.npz"),
        ("pre_program_definition", PRE_DIR / "intermediates" / "program_definition.tsv"),
        ("s2_state_mass", S2_STATE_MASS),
    ):
        inputs[name] = {
            "path": str(path.relative_to(ROOT)),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    record = {
        "schema": "ve.hx-input-lock.v1",
        "atom": ATOM,
        "allow_network": False,
        "note": "parent v0004 is never opened by this atom (parent arm = observed E8.5 "
                "composition from the frozen vocabulary); its P0-LOCK hash is "
                "1bc069d9aecd4b9b15f3ff91c328ef27a9773bfd0d3c890f36f5f1b6fb4f49bd",
        "inputs": inputs,
        "locked_at": datetime.now(timezone.utc).isoformat(),
    }
    _write_json_atomic(out_dir / "inputs" / "input_lock.json", record)
    return {"step": "input-lock", "n_inputs": len(inputs)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["input-lock", "prepare", "train", "evaluate",
                                            "manifest", "verify"])
    parser.add_argument("--out", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--exclude", nargs="*", default=())
    args = parser.parse_args(argv)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "metrics").mkdir(exist_ok=True)
    (out_dir / "intermediates").mkdir(exist_ok=True)
    (out_dir / "inputs").mkdir(exist_ok=True)

    if args.command == "input-lock":
        result = command_input_lock(out_dir)
    elif args.command == "prepare":
        result = command_prepare(out_dir)
    elif args.command == "train":
        result = command_train(out_dir)
    elif args.command == "evaluate":
        result = command_evaluate(out_dir)
    elif args.command == "manifest":
        result = write_manifest(out_dir, exclude=tuple(args.exclude))
    else:
        result = verify_manifest(out_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
