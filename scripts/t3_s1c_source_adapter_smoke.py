#!/usr/bin/env python3
"""Run a structural CellOracle TFdict adapter smoke on synthetic data only."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ATOM = "T3-S1C-B-SOURCE-ADAPTER-SMOKE-20260901-v3"
PRIOR_ATOM = "T3-S1C-A-REGULATOR-PRIOR-BUILD-20260901-v1"
OUTPUT_DEFAULT = ROOT / "artifacts/tool_integration" / ATOM
PRIOR_DEFAULT = ROOT / "artifacts/tool_integration" / PRIOR_ATOM
SCRIPT_PATH = Path(__file__).resolve()
SEED = 20260830
FIXTURE_GENES = (
    "Gata4", "Gata6", "Ctnnb1", "Pitx2", "Nkx2-5", "Tbx5", "Bmp4",
    "Cav1", "Dkk1", "Nppa", "Wnt2", "Wnt6", "Lefty1", "Lefty2",
    "Acta2", "Hcn4", "Nos3", "Tnc", "Isl1", "Mef2c",
)
TARGETS = ("Gata6", "Ctnnb1")
STABLE_MANIFEST_EXCLUDED_PREFIXES = (
    "deployment/runtime/cache",
    "deployment/runtime/mpl",
    "deployment/runtime/numba",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def repo_relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def _artifact_manifest(output_dir: Path) -> dict[str, Any]:
    files = []
    for path in sorted(output_dir.rglob("*")):
        if not path.is_file() or path.name == "artifact_manifest.stable.json":
            continue
        relative = path.relative_to(output_dir).as_posix()
        if any(relative == prefix or relative.startswith(prefix + "/") for prefix in STABLE_MANIFEST_EXCLUDED_PREFIXES):
            continue
        if relative.endswith((".db-shm", ".db-wal")):
            continue
        files.append({"path": relative, "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    return {
        "schema": "ve.t3.s1c-b-source-adapter-smoke-artifact-manifest.v2",
        "task": "T3-S1C-B-SOURCE-ADAPTER-SMOKE",
        "atom": ATOM,
        "stable_manifest_excluded_prefixes": list(STABLE_MANIFEST_EXCLUDED_PREFIXES),
        "files": files,
    }


def load_prior(prior_dir: Path = PRIOR_DEFAULT) -> tuple[dict[str, list[str]], dict[str, Any]]:
    gate_path = prior_dir / "metrics/gate_report.json"
    payload_path = prior_dir / "grn/augmented_tfdict.json"
    manifest_path = prior_dir / "metrics/artifact_manifest.stable.json"
    for path in (gate_path, payload_path, manifest_path):
        if not path.is_file():
            raise FileNotFoundError(path)
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    if gate.get("status") != "PASS" or gate.get("candidate_generation") is not False:
        raise ValueError("S1C-A prior is not a PASS component with candidate generation disabled")
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    if payload.get("schema") != "ve.t3.s1c-a-augmented-tfdict.v1":
        raise ValueError("unsupported S1C-A TFdict schema")
    tfdict = {
        str(gene): [str(regulator) for regulator in regulators]
        for gene, regulators in payload.get("tfdict", {}).items()
    }
    if payload.get("augmented_tfdict_digest") is None:
        raise ValueError("S1C-A TFdict digest is missing")
    return tfdict, {
        "gate_path": gate_path,
        "gate_sha256": sha256_file(gate_path),
        "payload_path": payload_path,
        "payload_sha256": sha256_file(payload_path),
        "manifest_path": manifest_path,
        "manifest_sha256": sha256_file(manifest_path),
        "prior_atom": PRIOR_ATOM,
    }


def fixture_tfdict(tfdict: Mapping[str, list[str]], genes: tuple[str, ...] = FIXTURE_GENES) -> dict[str, list[str]]:
    missing = [gene for gene in genes if gene not in tfdict]
    if missing:
        raise ValueError(f"synthetic fixture genes missing from prior TFdict: {missing}")
    gene_set = set(genes)
    return {
        gene: [regulator for regulator in tfdict[gene] if regulator in gene_set and regulator != gene]
        for gene in genes
    }


def _runtime_environment(output_dir: Path) -> dict[str, str]:
    runtime = output_dir / "deployment/runtime"
    values = {
        "XDG_CONFIG_HOME": runtime / "config",
        "XDG_CACHE_HOME": runtime / "cache",
        "MPLCONFIGDIR": runtime / "mpl",
        "NUMBA_CACHE_DIR": runtime / "numba",
    }
    for path in values.values():
        path.mkdir(parents=True, exist_ok=True)
    for key, value in values.items():
        os.environ[key] = str(value)
    os.environ["NUMBA_DISABLE_CACHING"] = "1"
    os.environ["LD_LIBRARY_PATH"] = "/opt/anaconda3/lib:" + os.environ.get("LD_LIBRARY_PATH", "")
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[key] = "1"
    return {key: str(value) for key, value in values.items()}


def _fixture_adata(genes: tuple[str, ...], seed: int):
    import anndata as ad

    rng = np.random.default_rng(seed)
    n_cells = 24
    counts = rng.poisson(lam=5.0, size=(n_cells, len(genes))).astype(np.float32) + 1.0
    cell_ids = [f"synthetic_cell_{index:02d}" for index in range(n_cells)]
    obs = pd.DataFrame(
        {"state": ["synthetic_state_a"] * 12 + ["synthetic_state_b"] * 12},
        index=cell_ids,
    )
    adata = ad.AnnData(X=counts, obs=obs, var=pd.DataFrame(index=list(genes)))
    adata.obsm["X_pca"] = rng.normal(size=(n_cells, 2)).astype(np.float32)
    return adata, counts, cell_ids


def run_one_target(target: str, tfdict: Mapping[str, list[str]], output_dir: Path) -> dict[str, Any]:
    environment = _runtime_environment(output_dir)
    result: dict[str, Any] = {
        "target": target,
        "status": "NOT_RUN",
        "semantic_scope": "synthetic structural smoke only; no biological sample, sign, rank, or state response",
        "environment": environment,
    }
    try:
        import celloracle as co
    except Exception as exc:
        result.update({"status": "BLOCKED_TOOLCHAIN", "phase": "import", "error": repr(exc)})
        return result
    try:
        oracle = co.Oracle()
        adata, counts, cell_ids = _fixture_adata(FIXTURE_GENES, SEED)
        oracle.import_anndata_as_raw_count(
            adata=adata,
            cluster_column_name="state",
            embedding_name="X_pca",
        )
        oracle.import_TF_data(TFdict=dict(tfdict))
        source_present = any(target in set(regulators) for regulators in oracle.TFdict.values())
        if not source_present:
            raise RuntimeError(f"TFdict source membership missing for {target}")
        n_components = min(10, oracle.adata.shape[0] - 1, oracle.adata.shape[1] - 1)
        oracle.perform_PCA(n_components=n_components)
        oracle.knn_imputation(
            k=min(5, oracle.adata.shape[0] - 1),
            n_pca_dims=min(5, n_components),
            n_jobs=1,
        )
        oracle.fit_GRN_for_simulation(
            GRN_unit="cluster",
            alpha=10,
            use_cluster_specific_TFdict=False,
            verbose_level=0,
        )
        oracle.simulate_shift(
            perturb_condition={target: 0.0},
            GRN_unit="cluster",
            n_propagation=3,
            ignore_warning=True,
            clip_delta_X=True,
        )
        delta = oracle.adata.layers.get("delta_X")
        if delta is None:
            raise RuntimeError("CellOracle did not publish delta_X")
        delta = delta.toarray() if hasattr(delta, "toarray") else np.asarray(delta)
        if delta.shape != oracle.adata.shape or not np.isfinite(delta).all():
            raise RuntimeError(f"delta_X structural check failed: shape={delta.shape}")
        result.update(
            {
                "status": "PASS",
                "phase": "fit_and_simulate",
                "celloracle_version": importlib.metadata.version("celloracle"),
                "input_shape": list(oracle.adata.shape),
                "cell_id_count": len(cell_ids),
                "cell_id_unique": len(set(cell_ids)) == len(cell_ids),
                "counts_sha256": hashlib.sha256(counts.tobytes()).hexdigest(),
                "source_membership": source_present,
                "delta_x_shape": list(delta.shape),
                "delta_x_finite": bool(np.isfinite(delta).all()),
            }
        )
    except Exception as exc:
        result.update({"status": "FAIL", "phase": "fit_and_simulate", "error": repr(exc)})
    return result


def run(*, output_dir: Path = OUTPUT_DEFAULT, prior_dir: Path = PRIOR_DEFAULT) -> dict[str, Any]:
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise FileExistsError(f"S1C-B output already exists: {output_dir}")
    output_dir.mkdir(parents=True)
    try:
        prior, prior_lock = load_prior(prior_dir)
        fixture = fixture_tfdict(prior)
        metrics = output_dir / "metrics"
        inputs = output_dir / "inputs"
        write_json(
            inputs / "input_lock.json",
            {
                "schema": "ve.t3.s1c-b-input-lock.v1",
                "atom": ATOM,
                "prior": {key: repo_relative(value) if isinstance(value, Path) else value for key, value in prior_lock.items()},
                "fixture_seed": SEED,
                "fixture_genes": list(FIXTURE_GENES),
                "target_truth_used": False,
                "candidate_generation": False,
                "server_submission": False,
            },
        )
        write_json(
            inputs / "synthetic_fixture.json",
            {
                "schema": "ve.t3.s1c-b-synthetic-fixture.v1",
                "seed": SEED,
                "genes": list(FIXTURE_GENES),
                "cells": 24,
                "cell_ids": [f"synthetic_cell_{index:02d}" for index in range(24)],
                "biological_sample": False,
                "barcode_umi_status": "NOT_APPLICABLE",
                "tf_dict": fixture,
            },
        )
        target_results = {
            target: run_one_target(target, fixture, output_dir)
            for target in TARGETS
        }
        statuses = [result["status"] for result in target_results.values()]
        all_pass = all(status == "PASS" for status in statuses)
        gate = {
            "schema": "ve.t3.s1c-b-source-adapter-smoke-gate.v1",
            "task": "T3-S1C-B-SOURCE-ADAPTER-SMOKE",
            "atom": ATOM,
            "prior_atom": PRIOR_ATOM,
            "status": "PASS" if all_pass else "HOLD",
            "network_availability": "AVAILABLE_CONTEXTUAL",
            "method_source_compatibility": "PASS" if all_pass else "PARTIAL_OR_BLOCKED",
            "loader_fit_simulation_smoke": target_results,
            "biological_activity_status": "NOT_VALIDATED",
            "state_specificity_status": "NOT_EVALUATED",
            "signed_family_stability": "NOT_IDENTIFIABLE",
            "candidate_generation": False,
            "server_submission": False,
            "blocks_submission": False,
            "outcome": "HOLD_AS_COMPONENT",
            "scientific_statement": "Synthetic fit/simulation proves only structural API compatibility, not biological activity or target validity.",
        }
        write_json(metrics / "target_results.json", target_results)
        write_json(metrics / "gate_report.json", gate)
        write_json(
            metrics / "completion_report.json",
            {
                "schema": "ve.t3.s1c-b-completion.v1",
                "task": "T3-S1C-B-SOURCE-ADAPTER-SMOKE",
                "atom": ATOM,
                "prior_atom": PRIOR_ATOM,
                "status": gate["status"],
                "script": {"path": repo_relative(SCRIPT_PATH), "sha256": sha256_file(SCRIPT_PATH)},
                "target_statuses": {target: result["status"] for target, result in target_results.items()},
                "biological_activity_status": "NOT_VALIDATED",
                "candidate_generation": False,
                "server_submission": False,
                "blocks_submission": False,
            },
        )
        (output_dir / "RESULT.md").write_text(
            f"# {ATOM}\n\n"
            f"Synthetic structural smoke status: `{gate['status']}`. Targets: "
            + ", ".join(f"{target}={result['status']}" for target, result in target_results.items())
            + ".\n\nNo biological sample, candidate, scorer run or server submission was created.\n",
            encoding="utf-8",
        )
        manifest = _artifact_manifest(output_dir)
        write_json(metrics / "artifact_manifest.stable.json", manifest)
        return {"gate": gate, "manifest": manifest}
    except Exception:
        shutil.rmtree(output_dir, ignore_errors=True)
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--prior", type=Path, default=PRIOR_DEFAULT)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = run(output_dir=args.output, prior_dir=args.prior)
    print(json.dumps(result["gate"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
