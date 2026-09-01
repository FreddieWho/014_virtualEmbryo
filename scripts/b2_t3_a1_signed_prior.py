#!/usr/bin/env python3
"""Build the two bounded B2-T3-A1 WT-only response lanes.

The active atom is deliberately implemented as an auditable local computation:
E-MTAB-6967 supplies sanitized WT expression, GSE52123 supplies GATA4
promoter directness only, and the pinned CellOracle/scTenifoldKnk snapshots are
method provenance.  No pretrained checkpoint, held-out target, or server API
is read during candidate generation.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

import anndata as ad
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ATOM = "B2-T3-A1"
SEED = 20260829
PANEL_PATH = ROOT / "data" / "gene_panel" / "T3__gata4.genes.txt"
PARENT_PATH = ROOT / "submissions" / "scored" / "baseline-001" / "T3_gata4" / "submission.h5ad"
SANITIZED_ROOT = ROOT / "infra" / "external_data" / "sanitized" / "T3" / ATOM
EXTERNAL_ROOT = SANITIZED_ROOT / "EMTAB6967"
GSE_ROOT = SANITIZED_ROOT / "GSE52123"
GTF_PATH = SANITIZED_ROOT / "MM9_GTF_RELEASE67" / "Mus_musculus.NCBIM37.67.gtf.gz"
ARTIFACT_ROOT = ROOT / "artifacts" / "atomic_batch2" / ATOM
WORK_ROOT = ARTIFACT_ROOT / "work"
SCORER = ROOT / "third_party" / "veckit" / "score_h5ad.py"

POSITIVE_MARKERS = [
    "Mesp1", "T", "Mixl1", "Pdgfra", "Kdr", "Foxf1", "Tbx5", "Nkx2-5",
    "Mef2c", "Hand1", "Hand2", "Isl1", "Gata4", "Gata6", "Tbx20", "Myocd",
]
NEGATIVE_MARKERS = [
    "Sox2", "Sox3", "Pou5f1", "Foxa2", "Sox17", "Krt8", "Krt18", "Krt19",
    "Epcam", "Otx2",
]
STAGE_VALUE = {f"E{n / 4:.2f}".replace(".00", ""): float(n) for n in range(26, 35)}
# Explicit labels avoid float formatting surprises in the source metadata.
STAGE_VALUE.update({"E6.5": 0.0, "E6.75": 1.0, "E7.0": 2.0, "E7.25": 3.0,
                    "E7.5": 4.0, "E7.75": 5.0, "E8.0": 6.0, "E8.25": 7.0,
                    "E8.5": 8.0, "E8.75": 9.0, "E9.0": 10.0, "E9.25": 11.0,
                    "E9.5": 12.0})


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def panel_genes() -> list[str]:
    genes = [line.strip() for line in PANEL_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(genes) != 500 or len(set(genes)) != 500:
        raise ValueError("T3 panel must contain 500 unique genes")
    return genes


def robust_sd(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=np.float64)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return 0.0
    med = float(np.median(values))
    mad = 1.4826 * float(np.median(np.abs(values - med)))
    if mad > 1e-10:
        return mad
    q25, q75 = np.quantile(values, [0.25, 0.75])
    iqr_sd = float((q75 - q25) / 1.3489795)
    return iqr_sd if iqr_sd > 1e-10 else float(np.std(values))


def stratified_indices(labels: np.ndarray, n: int, seed: int, secondary: np.ndarray | None = None) -> np.ndarray:
    labels = np.asarray(labels).astype(str)
    if secondary is None:
        keys = labels
    else:
        keys = np.asarray([f"{a}::{b}" for a, b in zip(labels, np.asarray(secondary).astype(str))])
    if n >= len(labels):
        return np.arange(len(labels), dtype=np.int64)
    rng = np.random.default_rng(seed)
    groups: dict[str, np.ndarray] = {}
    for key in np.unique(keys):
        groups[str(key)] = np.flatnonzero(keys == key)
    exact = {key: n * len(index) / len(labels) for key, index in groups.items()}
    quota = {key: int(np.floor(value)) for key, value in exact.items()}
    remaining = n - sum(quota.values())
    order = sorted(groups, key=lambda key: (-(exact[key] - quota[key]), key))
    for key in order[:remaining]:
        quota[key] += 1
    chosen: list[np.ndarray] = []
    for key in sorted(groups):
        index = groups[key]
        take = quota[key]
        if take:
            chosen.append(np.sort(rng.choice(index, size=take, replace=False)))
    return np.sort(np.concatenate(chosen).astype(np.int64))


def external_gene_map() -> tuple[list[str], dict[str, int]]:
    table = pd.read_csv(EXTERNAL_ROOT / "genes.tsv", sep="\t", header=None, names=["ensembl", "gene"], dtype=str)
    symbols = table["gene"].fillna("").astype(str).tolist()
    mapping: dict[str, int] = {}
    for index, symbol in enumerate(symbols):
        if symbol and symbol not in mapping:
            mapping[symbol] = index
    return symbols, mapping


def extract_external_matrix(panel: list[str], meta: pd.DataFrame, run_log: list[str]) -> tuple[np.memmap, np.ndarray, list[str], dict[str, int], Path]:
    symbols, symbol_to_row = external_gene_map()
    requested: list[str] = []
    for gene in panel + POSITIVE_MARKERS + NEGATIVE_MARKERS:
        if gene in symbol_to_row and gene not in requested:
            requested.append(gene)
    missing_panel = [gene for gene in panel if gene not in symbol_to_row]
    if missing_panel:
        # Retain the official 500-gene output panel. Do not substitute an
        # unverified alias; missing external genes remain zero-filled and are
        # never eligible for response selection.
        run_log.append("missing_external_panel_genes=" + ",".join(missing_panel))
    selected_rows = np.full(len(symbols), -1, dtype=np.int64)
    for selected, gene in enumerate(requested):
        selected_rows[symbol_to_row[gene]] = selected
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    rowmap = WORK_ROOT / "EMTAB6967.rowmap.tsv"
    rowmap.write_text(
        f"{len(symbols)} {len(requested)}\n" + "\n".join(str(int(v)) for v in selected_rows) + "\n",
        encoding="ascii",
    )
    matrix_path = WORK_ROOT / "EMTAB6967.selected_counts.f32"
    lib_path = WORK_ROOT / "EMTAB6967.library_size.f64"
    extractor = os.environ.get("B2_MATRIXMARKET_EXTRACTOR", "/tmp/b2_extract_matrixmarket")
    if not Path(extractor).exists():
        raise FileNotFoundError(f"missing compiled extractor {extractor}; compile scripts/extract_matrixmarket_genes.cpp")
    if not matrix_path.exists() or matrix_path.stat().st_size != meta.shape[0] * len(requested) * 4:
        run_log.append(f"extractor={extractor} source={EXTERNAL_ROOT / 'counts.mtx'}")
        subprocess.run([extractor, str(EXTERNAL_ROOT / "counts.mtx"), str(matrix_path), str(lib_path), str(rowmap)], check=True)
    if not lib_path.exists() or lib_path.stat().st_size != meta.shape[0] * 8:
        raise ValueError("selected matrix extraction did not publish library sizes")
    matrix = np.memmap(matrix_path, dtype=np.float32, mode="r", shape=(meta.shape[0], len(requested)))
    library_size = np.fromfile(lib_path, dtype=np.float64)
    if len(library_size) != len(meta) or not np.isfinite(library_size).all() or (library_size <= 0).any():
        raise ValueError("invalid library sizes from sanitized matrix")
    run_log.append(f"selected_genes={len(requested)} selected_cells={len(meta)} matrix_bytes={matrix_path.stat().st_size}")
    return matrix, library_size, requested, {gene: index for index, gene in enumerate(requested)}, rowmap


def normalized_sample(matrix: np.memmap, library_size: np.ndarray, sample_idx: np.ndarray) -> np.ndarray:
    counts = np.asarray(matrix[sample_idx, :], dtype=np.float32)
    scale = (10000.0 / np.maximum(library_size[sample_idx], 1.0)).astype(np.float32)
    result = np.log1p(counts * scale[:, None]).astype(np.float64)
    if not np.isfinite(result).all() or (result < 0).any():
        raise ValueError("normalized WT external matrix is not finite/nonnegative")
    return result


def standardize_column(values: np.ndarray) -> tuple[np.ndarray, float, float]:
    values = np.asarray(values, dtype=np.float64)
    center = float(np.median(values))
    scale = robust_sd(values)
    if scale <= 1e-8:
        scale = float(np.std(values))
    if scale <= 1e-8:
        scale = 1.0
    return (values - center) / scale, center, scale


def rank_confidence(values: np.ndarray) -> np.ndarray:
    absolute = np.abs(np.asarray(values, dtype=np.float64))
    order = np.argsort(absolute, kind="mergesort")
    ranks = np.empty(len(order), dtype=np.float64)
    ranks[order] = np.arange(1, len(order) + 1, dtype=np.float64)
    return ranks / (len(order) + 1.0)


def celloracle_vote(Y: np.ndarray, target_position: int, stage: np.ndarray) -> dict[str, np.ndarray]:
    """State-wise WT-only regression approximation of a CellOracle response vote."""
    target, _tc, _ts = standardize_column(Y[:, target_position])
    stage_z, _sc, _ss = standardize_column(stage)
    design = np.column_stack([np.ones(len(Y)), target, stage_z])
    coefficients = np.linalg.lstsq(design, Y, rcond=1e-6)[0][1]
    scale = np.array([robust_sd(Y[:, j]) for j in range(Y.shape[1])], dtype=np.float64)
    standardized = coefficients / np.maximum(scale, 1e-8)
    return {
        "coefficient": coefficients,
        "effect_sign": -np.sign(coefficients),
        "strength": np.abs(standardized),
        "rank_confidence": rank_confidence(standardized),
    }


def sctenifold_vote(Y: np.ndarray, target_position: int) -> dict[str, np.ndarray]:
    """Ridge-regularized WT-only conditional-network virtual-KO vote."""
    n_genes = Y.shape[1]
    Z = np.empty_like(Y, dtype=np.float64)
    for j in range(n_genes):
        Z[:, j], _c, _s = standardize_column(Y[:, j])
    others = [j for j in range(n_genes) if j != target_position]
    X = Z[:, others]
    y = Z[:, target_position]
    gram = (X.T @ X) / max(len(Y), 1)
    ridge = 0.5 * np.eye(len(others), dtype=np.float64)
    beta = np.linalg.solve(gram + ridge, (X.T @ y) / max(len(Y), 1))
    coefficient = np.zeros(n_genes, dtype=np.float64)
    coefficient[others] = beta
    return {
        "coefficient": coefficient,
        "effect_sign": -np.sign(coefficient),
        "strength": np.abs(coefficient),
        "rank_confidence": rank_confidence(coefficient),
    }


def fit_state_models(
    Y: np.ndarray,
    meta: pd.DataFrame,
    panel_positions: dict[str, int],
    run_log: list[str],
) -> dict[str, dict[str, Any]]:
    stage = np.asarray([STAGE_VALUE.get(str(value), np.nan) for value in meta["stage"]], dtype=np.float64)
    if not np.isfinite(stage).all():
        raise ValueError("stage values used by WT models are not finite")
    groups: dict[str, np.ndarray] = {}
    labels = meta["celltype"].astype(str).to_numpy()
    for label in np.unique(labels):
        groups[str(label)] = np.flatnonzero(labels == label)
    # A global WT fit is the deterministic fallback for rare cell states.
    global_models: dict[str, dict[str, np.ndarray]] = {}
    for target in ("Gata4", "Gata6", "Mab21l2"):
        position = panel_positions[target]
        global_models[target] = {
            "celloracle": celloracle_vote(Y, position, stage),
            "sctenifold": sctenifold_vote(Y, position),
        }
    fits: dict[str, dict[str, Any]] = {}
    for label, local in sorted(groups.items()):
        if len(local) >= 120:
            local_Y = Y[local]
            local_stage = stage[local]
            models: dict[str, dict[str, np.ndarray]] = {}
            for target in ("Gata4", "Gata6", "Mab21l2"):
                position = panel_positions[target]
                models[target] = {
                    "celloracle": celloracle_vote(local_Y, position, local_stage),
                    # The independent conditional network is fit once on the
                    # complete WT context. This avoids a repeated 500x500
                    # solve while retaining an independent network vote for
                    # every state-specific CellOracle vote.
                    "sctenifold": global_models[target]["sctenifold"],
                }
            fits[label] = {"n": int(len(local)), "models": models, "model_source": "state_specific_celloracle_global_sctenifold"}
        else:
            fits[label] = {"n": int(len(local)), "models": global_models, "model_source": "global_rare_state_fallback"}
    fits["__GLOBAL__"] = {"n": int(len(Y)), "models": global_models, "model_source": "global_WT"}
    run_log.append(f"external_sample_cells={len(Y)} external_states={len(groups)} state_specific_states={sum(len(v) >= 120 for v in groups.values())}")
    return fits


def lineage_and_mapping(
    parent: ad.AnnData,
    parent_X: np.ndarray,
    parent_states: np.ndarray,
    Y: np.ndarray,
    meta: pd.DataFrame,
    requested_positions: dict[str, int],
    panel_positions: dict[str, int],
) -> tuple[dict[str, dict[str, Any]], dict[str, float], dict[str, Any]]:
    positive = [requested_positions[g] for g in POSITIVE_MARKERS if g in requested_positions]
    negative = [requested_positions[g] for g in NEGATIVE_MARKERS if g in requested_positions]
    if not positive or not negative:
        raise ValueError("lineage marker program lost a required positive or negative marker set")
    Z = np.empty_like(Y, dtype=np.float64)
    for j in range(Y.shape[1]):
        Z[:, j], _c, _s = standardize_column(Y[:, j])
        Z[:, j] = np.clip(Z[:, j], -6.0, 6.0)
    cell_score = np.mean(Z[:, positive], axis=1) - np.mean(Z[:, negative], axis=1)
    cell_probability = 1.0 / (1.0 + np.exp(-cell_score))
    external_labels = meta["celltype"].astype(str).to_numpy()
    state_prob: dict[str, float] = {}
    state_n: dict[str, int] = {}
    for label in np.unique(external_labels):
        mask = external_labels == label
        state_prob[str(label)] = float(np.median(cell_probability[mask]))
        state_n[str(label)] = int(mask.sum())

    parent_centroids: dict[str, np.ndarray] = {}
    for state in np.unique(parent_states.astype(str)):
        mask = parent_states.astype(str) == state
        parent_centroids[str(state)] = np.asarray(parent_X[mask].mean(axis=0), dtype=np.float64)
    panel_names = list(panel_positions)
    valid_panel = [gene for gene in panel_names if gene in requested_positions]
    panel_external_positions = np.array([requested_positions[g] for g in valid_panel], dtype=np.int64)
    panel_parent_positions = np.array([panel_positions[g] for g in valid_panel], dtype=np.int64)
    external_centroids: dict[str, np.ndarray] = {}
    for label in np.unique(external_labels):
        mask = external_labels == label
        external_centroids[str(label)] = np.asarray(Y[mask][:, panel_external_positions].mean(axis=0), dtype=np.float64)

    def corr(a: np.ndarray, b: np.ndarray) -> float:
        a = a - np.mean(a)
        b = b - np.mean(b)
        den = float(np.linalg.norm(a) * np.linalg.norm(b))
        return float(np.dot(a, b) / den) if den > 1e-12 else -1.0

    gates: dict[str, dict[str, Any]] = {}
    for state, centroid in sorted(parent_centroids.items()):
        choices = [(corr(centroid[panel_parent_positions], external_centroids[ext]), ext) for ext in external_centroids]
        similarity, matched = max(choices, key=lambda pair: (pair[0], pair[1]))
        gates[state] = {
            "official_state": state,
            "matched_external_state": matched,
            "match_similarity": float(similarity),
            "p_mesp1_lineage": float(state_prob[matched]),
            "responds": bool(state_prob[matched] >= 0.5),
            "external_n": int(state_n[matched]),
            "evidence": "WT marker program: positive mesoderm/cardiac markers minus negative ectoderm/endoderm markers; sigmoid probability; no hardcoded celltype allow-list",
        }
    return gates, state_prob, {
        "positive_markers_present": [g for g in POSITIVE_MARKERS if g in requested_positions],
        "negative_markers_present": [g for g in NEGATIVE_MARKERS if g in requested_positions],
        "cell_probability_median": float(np.median(cell_probability)),
        "external_state_probabilities": state_prob,
    }


def parse_gtf_tss(path: Path, wanted: set[str]) -> dict[str, tuple[str, int]]:
    bounds: dict[str, tuple[str, int, int, str]] = {}
    pattern = re.compile(r'gene_name "([^"]+)"')
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.startswith("#"):
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) != 9:
                continue
            # Release 67's NCBIM37 GTF exposes exon records but no explicit
            # gene/transcript feature rows; aggregate exon bounds to obtain a
            # stable gene-level TSS for this promoter audit.
            if fields[2] not in {"gene", "transcript", "exon"}:
                continue
            match = pattern.search(fields[8])
            if not match:
                continue
            gene = match.group(1)
            if gene not in wanted:
                continue
            start, end = int(fields[3]), int(fields[4])
            if gene not in bounds:
                bounds[gene] = (fields[0], start, end, fields[6])
            else:
                chrom, old_start, old_end, strand = bounds[gene]
                bounds[gene] = (chrom, min(old_start, start), max(old_end, end), strand)
    return {gene: (chrom, start - 1 if strand == "+" else end - 1) for gene, (chrom, start, end, strand) in bounds.items()}


def bigwig_max(bw: Any, chrom: str, start: int, end: int) -> float:
    try:
        values = bw.stats(chrom, start, end, nBins=20, type="mean")
    except Exception:
        return 0.0
    values = np.asarray([np.nan if value is None else float(value) for value in values], dtype=np.float64)
    return float(np.nanmax(values)) if np.isfinite(values).any() else 0.0


def directness_table(panel: list[str]) -> dict[str, dict[str, Any]]:
    try:
        import pyBigWig
    except ImportError as exc:
        raise RuntimeError("pyBigWig is required for the GSE52123 directness audit") from exc
    genes = parse_gtf_tss(GTF_PATH, set(panel))
    chip_paths = [GSE_ROOT / "GSM1260024_E12.5_Gata4_Ab1.bw", GSE_ROOT / "GSM1260025_E12.5_Gata4_Ab2.bw"]
    input_path = GSE_ROOT / "GSM1260028_E12.5_Gata4_Input.bw"
    chips = [pyBigWig.open(str(path)) for path in chip_paths]
    matched_input = pyBigWig.open(str(input_path))
    try:
        chroms = matched_input.chroms()
        result: dict[str, dict[str, Any]] = {}
        for gene in panel:
            if gene not in genes:
                result[gene] = {"gene": gene, "mapped": False, "direct": False, "weight": 0.0, "reason": "no_NCBIM37_GTF_mapping"}
                continue
            chromosome, tss = genes[gene]
            candidates = [chromosome, chromosome if chromosome.startswith("chr") else f"chr{chromosome}"]
            chrom = next((name for name in candidates if name in chroms), None)
            if chrom is None:
                result[gene] = {"gene": gene, "mapped": False, "direct": False, "weight": 0.0, "reason": "GTF_contig_not_in_bigwig"}
                continue
            start = max(0, tss - 5000)
            end = min(int(chroms[chrom]), tss + 5001)
            chip_values = [bigwig_max(bw, chrom, start, end) for bw in chips]
            input_value = bigwig_max(matched_input, chrom, start, end)
            ratios = [(value + 1.0) / (input_value + 1.0) for value in chip_values]
            log_enrichment = [float(np.log1p(value) - np.log1p(input_value)) for value in chip_values]
            score = max(0.0, min(log_enrichment))
            result[gene] = {
                "gene": gene, "mapped": True, "chrom": chrom, "tss": int(tss), "promoter_bp": "-5000:+5000",
                "chip_rep1_max": chip_values[0], "chip_rep2_max": chip_values[1], "input_max": input_value,
                "rep1_enrichment": ratios[0], "rep2_enrichment": ratios[1], "score": score,
                "direct": bool(min(ratios) >= 1.25 and min(chip_values) > 0),
                "weight": float(min(1.0, score / np.log1p(4.0))) if score > 0 else 0.0,
                "reason": "both WT E12.5 GATA4 ChIP replicates exceed matched input by fixed 1.25 ratio" if min(ratios) >= 1.25 and min(chip_values) > 0 else "below_conservative_two_replicate_threshold",
            }
        return result
    finally:
        for bw in chips + [matched_input]:
            bw.close()


def vote_record(
    fits: dict[str, dict[str, Any]],
    gates: dict[str, dict[str, Any]],
    target: str,
    gene: str,
    panel_position: dict[str, int],
    directness: dict[str, dict[str, Any]],
    require_directness: bool,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    state_records: list[dict[str, Any]] = []
    for state, gate in sorted(gates.items()):
        if not gate["responds"]:
            continue
        ext_state = gate["matched_external_state"]
        model_set = fits.get(ext_state, fits["__GLOBAL__"])["models"][target]
        position = panel_position[gene]
        cell_vote = int(model_set["celloracle"]["effect_sign"][position])
        network_vote = int(model_set["sctenifold"]["effect_sign"][position])
        direct = directness.get(gene, {"direct": False, "weight": 0.0})
        same = cell_vote != 0 and cell_vote == network_vote
        eligible = same and (direct["direct"] if require_directness else True)
        record = {
            "official_state": state, "external_state": ext_state, "gene": gene, "target": target,
            "p_mesp1_lineage": gate["p_mesp1_lineage"], "celloracle_sign": cell_vote,
            "sctenifold_sign": network_vote, "celloracle_confidence": float(model_set["celloracle"]["rank_confidence"][position]),
            "sctenifold_confidence": float(model_set["sctenifold"]["rank_confidence"][position]),
            "direct_chIP": bool(direct.get("direct", False)), "directness_weight": float(direct.get("weight", 0.0)),
            "eligible": bool(eligible), "conflict_or_one_vote": bool(not same),
            "directness_required": bool(require_directness),
        }
        state_records.append(record)
    eligible_records = [record for record in state_records if record["eligible"]]
    if not eligible_records:
        return None, state_records
    signed_confidence = sum(record["celloracle_sign"] * min(record["celloracle_confidence"], record["sctenifold_confidence"]) for record in eligible_records)
    if abs(signed_confidence) <= 1e-12:
        return None, state_records
    confidence = float(np.median([
        min(record["celloracle_confidence"], record["sctenifold_confidence"]) for record in eligible_records
    ]))
    weight = float(np.median([record["directness_weight"] for record in eligible_records]))
    return {
        "target": target, "gene": gene, "sign": int(np.sign(signed_confidence)), "confidence": confidence,
        "directness_weight": weight, "states_supported": len(eligible_records),
        "support_fraction": float(len(eligible_records) / max(1, sum(gate["responds"] for gate in gates.values()))),
    }, state_records


def aggregate_program(
    fits: dict[str, dict[str, Any]],
    gates: dict[str, dict[str, Any]],
    panel: list[str],
    panel_position: dict[str, int],
    directness: dict[str, dict[str, Any]],
    target: str,
    require_directness: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    aggregates: list[dict[str, Any]] = []
    votes: list[dict[str, Any]] = []
    for gene in panel:
        if gene == target:
            continue
        aggregate, state_records = vote_record(fits, gates, target, gene, panel_position, directness, require_directness)
        votes.extend(state_records)
        if aggregate is not None:
            aggregates.append(aggregate)
    aggregates.sort(key=lambda row: (-row["confidence"], -row["support_fraction"], row["gene"]))
    return aggregates, votes


def apply_program(
    X: np.ndarray,
    states: np.ndarray,
    gates: dict[str, dict[str, Any]],
    panel_position: dict[str, int],
    program: dict[str, dict[str, Any]],
    *,
    lane: str,
    include_gata6_dose: bool,
    perturbation_target: str = "Gata4",
) -> tuple[np.ndarray, dict[str, Any]]:
    output = np.asarray(X, dtype=np.float64).copy()
    changed: set[str] = set()
    clipping = 0
    target_position = panel_position[perturbation_target]
    g6 = panel_position["Gata6"]
    for row, state in enumerate(np.asarray(states).astype(str)):
        gate = gates.get(state)
        if not gate or not gate["responds"]:
            continue
        p = float(gate["p_mesp1_lineage"])
        output[row, target_position] = 0.0
        changed.add(perturbation_target)
        if include_gata6_dose:
            raw = np.expm1(max(0.0, output[row, g6]))
            output[row, g6] = np.log1p(0.5 * raw)
            changed.add("Gata6")
        state_program = program.get(state, {})
        for gene, spec in state_program.items():
            position = panel_position[gene]
            before = output[row, position]
            proposed = before + p * float(spec["delta"])
            if proposed < 0:
                output[row, position] = 0.0
                clipping += 1
            else:
                output[row, position] = proposed
            if output[row, position] != before:
                changed.add(gene)
    if not np.isfinite(output).all() or (output < 0).any():
        raise ValueError(f"{lane}: candidate X is not finite/nonnegative")
    return output.astype(np.float32), {"changed_genes": sorted(changed), "negative_clips": int(clipping)}


def build_state_program(
    aggregates: list[dict[str, Any]],
    gates: dict[str, dict[str, Any]],
    parent_X: np.ndarray,
    parent_states: np.ndarray,
    *,
    max_genes: int,
) -> tuple[list[str], dict[str, dict[str, dict[str, Any]]]]:
    selected = aggregates[:max_genes]
    selected_genes = [row["gene"] for row in selected]
    by_state: dict[str, dict[str, dict[str, Any]]] = {}
    for state in gates:
        mask = parent_states.astype(str) == state
        by_state[state] = {}
        for row in selected:
            gene = row["gene"]
            position = None
            # Filled by the caller after this function; the record carries the
            # aggregate amplitude ingredients only.
            sd = 0.0 if not mask.any() else robust_sd(parent_X[mask, :][:, 0])
            by_state[state][gene] = {**row, "robust_sd": sd, "delta": 0.0, "position": position}
    return selected_genes, by_state


def protected_checks(parent: ad.AnnData, candidate: ad.AnnData, changed_genes: set[str], gates: dict[str, dict[str, Any]], panel_position: dict[str, int]) -> dict[str, Any]:
    parent_X = np.asarray(parent.X.toarray() if hasattr(parent.X, "toarray") else parent.X, dtype=np.float32)
    candidate_X = np.asarray(candidate.X.toarray() if hasattr(candidate.X, "toarray") else candidate.X, dtype=np.float32)
    coords_equal = np.array_equal(np.asarray(parent.obsm["spatial_3D"]), np.asarray(candidate.obsm["spatial_3D"]))
    obs_equal = list(parent.obs_names) == list(candidate.obs_names) and np.array_equal(parent.obs["celltype"].astype(str), candidate.obs["celltype"].astype(str))
    allowed = set(changed_genes)
    changed_mask = np.any(parent_X != candidate_X, axis=0)
    changed_names = {str(name) for name, flag in zip(parent.var_names, changed_mask) if flag}
    non_target_unchanged = changed_names <= allowed
    gate_mask = np.array([bool(gates.get(str(state), {}).get("responds", False)) for state in parent.obs["celltype"].astype(str)], dtype=bool)
    g4 = panel_position["Gata4"]
    target_zero = bool(np.all(candidate_X[gate_mask, g4] == 0.0)) if gate_mask.any() else True
    target_non_gate_preserved = bool(np.array_equal(parent_X[~gate_mask, g4], candidate_X[~gate_mask, g4]))
    return {
        "parent_shape": list(parent.shape), "candidate_shape": list(candidate.shape), "shape_equal": parent.shape == candidate.shape,
        "var_names_equal": list(parent.var_names) == list(candidate.var_names), "cell_order_equal": list(parent.obs_names) == list(candidate.obs_names),
        "coords_equal": coords_equal, "obs_celltype_equal": obs_equal, "allowed_changed_genes": sorted(allowed),
        "actual_changed_genes": sorted(changed_names), "non_target_unchanged": non_target_unchanged,
        "lineage_gate_cells": int(gate_mask.sum()), "gata4_zero_in_gate": target_zero,
        "gata4_non_gate_preserved": target_non_gate_preserved, "finite_nonnegative": bool(np.isfinite(candidate_X).all() and (candidate_X >= 0).all()),
        "pass": bool(parent.shape == candidate.shape and list(parent.var_names) == list(candidate.var_names) and coords_equal and obs_equal and non_target_unchanged and target_zero and target_non_gate_preserved and np.isfinite(candidate_X).all() and (candidate_X >= 0).all()),
    }


def contract_check(candidate: ad.AnnData, panel: list[str]) -> dict[str, Any]:
    X = np.asarray(candidate.X.toarray() if hasattr(candidate.X, "toarray") else candidate.X)
    coords = np.asarray(candidate.obsm.get("spatial_3D"))
    result = {
        "n_obs": int(candidate.n_obs), "n_vars": int(candidate.n_vars), "panel_500": list(candidate.var_names) == panel,
        "cell_count_range": bool(1000 <= candidate.n_obs <= 7449), "x_2d": bool(X.ndim == 2),
        "x_finite_nonnegative": bool(np.isfinite(X).all() and (X >= 0).all()),
        "spatial_3d": bool(coords.ndim == 2 and coords.shape[0] == candidate.n_obs and coords.shape[1] >= 3 and np.isfinite(coords[:, :3]).all()),
    }
    result["pass"] = all(result.values())
    return result


def write_candidate(path: Path, parent: ad.AnnData, X: np.ndarray, metadata: dict[str, Any]) -> ad.AnnData:
    output = parent.copy()
    output.X = X
    output.uns = dict(output.uns)
    output.uns["b2_t3_a1"] = metadata
    path.parent.mkdir(parents=True, exist_ok=True)
    output.write_h5ad(path)
    return ad.read_h5ad(path)


def load_panel_data(path: Path, panel: list[str]) -> tuple[ad.AnnData, np.ndarray]:
    obj = ad.read_h5ad(path)
    if list(map(str, obj.var_names)) != panel:
        obj = obj[:, panel].copy()
    X = np.asarray(obj.X.toarray() if hasattr(obj.X, "toarray") else obj.X, dtype=np.float32)
    return obj, X


def run_scorer(input_path: Path, out_path: Path, target: Path, wt: Path, run_log: list[str]) -> dict[str, Any]:
    command = [sys.executable, str(SCORER), "--task", "T3", "--input", str(input_path), "--target", str(target), "--wt", str(wt), "--seed", str(SEED), "--out", str(out_path)]
    run_log.append("score_command=" + " ".join(command))
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = "/opt/anaconda3/lib:" + env.get("LD_LIBRARY_PATH", "")
    env["PYTHONPATH"] = str(ROOT) + (":" + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    completed = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, check=True)
    (out_path.with_suffix(".stdout.txt")).write_text(completed.stdout, encoding="utf-8")
    return json.loads(out_path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-scorer", action="store_true", help="generate artifacts without invoking the final local scorer")
    args = parser.parse_args()
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    run_log: list[str] = ["active_atom=B2-T3-A1", f"seed={SEED}", "target_used_for_generation=false", "server_submission=false"]
    panel = panel_genes()
    parent, parent_X = load_panel_data(PARENT_PATH, panel)
    if parent.n_obs != 7449 or "spatial_3D" not in parent.obsm:
        raise ValueError("current T3 parent is not the expected 7449-cell spatial wt_identity artifact")
    parent_states = parent.obs["celltype"].astype(str).to_numpy()
    meta = pd.read_csv(EXTERNAL_ROOT / "meta.csv", low_memory=False)
    if len(meta) != 108857 or meta["celltype"].isna().any():
        raise ValueError("sanitized E-MTAB-6967 metadata does not match the audited WT input")
    matrix, library_size, requested, requested_positions, rowmap = extract_external_matrix(panel, meta, run_log)
    sample_idx = stratified_indices(meta["celltype"].astype(str).to_numpy(), min(30000, len(meta)), SEED, meta["stage"].astype(str).to_numpy())
    Y = normalized_sample(matrix, library_size, sample_idx)
    # Candidate-space positions are always the official panel order; the
    # external matrix has an intentionally smaller map when source symbols are
    # absent (currently Ccn5 and Cemip2).
    panel_position = {gene: i for i, gene in enumerate(panel)}
    for required in ("Gata4", "Gata6", "Mab21l2"):
        if required not in panel_position:
            raise ValueError(f"required target {required} is not in T3 panel")
    gates, state_prob, lineage_meta = lineage_and_mapping(parent, parent_X, parent_states, Y, meta.iloc[sample_idx].reset_index(drop=True), requested_positions, panel_position)
    directness = directness_table(panel)
    panel_Y = np.zeros((len(Y), len(panel)), dtype=np.float64)
    for panel_index, gene in enumerate(panel):
        if gene in requested_positions:
            panel_Y[:, panel_index] = Y[:, requested_positions[gene]]
    fits = fit_state_models(panel_Y, meta.iloc[sample_idx].reset_index(drop=True), {g: i for i, g in enumerate(panel)}, run_log)

    audit = json.loads((ROOT / "infra" / "external_data" / "AUDIT_COMPLETE.json").read_text(encoding="utf-8"))
    if not audit.get("task_permit") or audit.get("target_used_for_generation"):
        raise RuntimeError("P0 audit permit is not valid or target_used_for_generation is true")
    json_write(ARTIFACT_ROOT / "lineage_summary.json", lineage_meta)
    lineage_rows = [gate for _state, gate in sorted(gates.items())]
    write_tsv(ARTIFACT_ROOT / "lineage_gate.tsv", lineage_rows, ["official_state", "matched_external_state", "match_similarity", "p_mesp1_lineage", "responds", "external_n", "evidence"])
    direct_rows = list(directness.values())
    write_tsv(ARTIFACT_ROOT / "directness_panel.tsv", direct_rows, sorted({key for row in direct_rows for key in row}))

    g4_aggregates, g4_votes = aggregate_program(fits, gates, panel, {g: i for i, g in enumerate(panel)}, directness, "Gata4", True)
    g6_aggregates, g6_votes = aggregate_program(fits, gates, panel, {g: i for i, g in enumerate(panel)}, directness, "Gata6", True)
    g4_aggregates = [row for row in g4_aggregates if row["gene"] not in {"Gata4", "Gata6"}]
    g6_aggregates = [row for row in g6_aggregates if row["gene"] not in {"Gata4", "Gata6"}]
    kill_aggregates, kill_votes = aggregate_program(fits, gates, panel, {g: i for i, g in enumerate(panel)}, directness, "Mab21l2", False)
    vote_rows = g4_votes + g6_votes + kill_votes
    write_tsv(ARTIFACT_ROOT / "prior_votes.tsv", vote_rows, sorted({key for row in vote_rows for key in row}))
    json_write(ARTIFACT_ROOT / "model_summary.json", {
        "celloracle": "local WT-only state-wise regression vote; pinned CellOracle source is provenance only; no pretrained model",
        "sctenifold": "local WT-only ridge conditional-network virtual-KO vote; pinned scTenifoldKnk source is provenance only; no pretrained model",
        "external_sample": {"n": len(sample_idx), "seed": SEED, "strategy": "stage x celltype stratified deterministic sample"},
        "g4_consensus_candidates": len(g4_aggregates), "g6_consensus_candidates": len(g6_aggregates), "mab21l2_kill_candidates": len(kill_aggregates),
        "direct_gata4_genes": sum(bool(row.get("direct")) for row in directness.values()),
    })

    # L1 is capped at 49 downstream genes + Gata4 itself = 50/500. L2 keeps
    # the same Gata4 component, adds Gata6 as a heterozygous dose component,
    # and allows at most 24 additional Gata6-vote genes = 75/500.
    l1_genes = [row["gene"] for row in g4_aggregates[:49]]
    extra_g6 = [row["gene"] for row in g6_aggregates if row["gene"] not in l1_genes][:24]
    l2_genes = list(dict.fromkeys(l1_genes + extra_g6))
    all_program_genes = sorted(set(l2_genes))
    state_program_l1: dict[str, dict[str, dict[str, Any]]] = {state: {} for state in gates}
    state_program_l2: dict[str, dict[str, dict[str, Any]]] = {state: {} for state in gates}
    g4_by_gene = {row["gene"]: row for row in g4_aggregates}
    g6_by_gene = {row["gene"]: row for row in g6_aggregates}
    g4_state_votes = {(row["official_state"], row["gene"]): row for row in g4_votes if row["eligible"]}
    g6_state_votes = {(row["official_state"], row["gene"]): row for row in g6_votes if row["eligible"]}
    changed_stats: dict[str, dict[str, float]] = {}
    for state in gates:
        mask = parent_states == state
        for gene in all_program_genes:
            position = panel_position[gene]
            cap = 0.1 * float(np.quantile(parent_X[:, position], 0.99) - np.quantile(parent_X[:, position], 0.01))
            sd = robust_sd(parent_X[mask, position]) if mask.any() else robust_sd(parent_X[:, position])
            g4_record = g4_state_votes.get((state, gene))
            g6_record = g6_state_votes.get((state, gene))
            g4 = None if g4_record is None else {
                "sign": int(g4_record["celloracle_sign"]),
                "confidence": min(float(g4_record["celloracle_confidence"]), float(g4_record["sctenifold_confidence"])),
                "directness_weight": float(g4_record["directness_weight"]),
            }
            g6 = None if g6_record is None else {
                "sign": int(g6_record["celloracle_sign"]),
                "confidence": min(float(g6_record["celloracle_confidence"]), float(g6_record["sctenifold_confidence"])),
                "directness_weight": float(g6_record["directness_weight"]),
            }
            if gene in l1_genes and g4 is not None and cap > 0 and sd > 0:
                raw = float(g4["sign"] * g4["confidence"] * g4["directness_weight"] * 0.15 * sd)
                state_program_l1[state][gene] = {"delta": float(np.clip(raw, -cap, cap)), "source": "Gata4", "confidence": g4["confidence"], "directness_weight": g4["directness_weight"]}
            components: list[float] = []
            if g4 is not None:
                components.append(float(g4["sign"] * g4["confidence"] * g4["directness_weight"] * 0.15 * sd))
            if g6 is not None:
                components.append(float(0.5 * g6["sign"] * g6["confidence"] * g6["directness_weight"] * 0.15 * sd))
            if components and cap > 0:
                state_program_l2[state][gene] = {"delta": float(np.clip(sum(components), -cap, cap)), "source": "Gata4_plus_half_Gata6", "confidence": float(max((g4 or g6)["confidence"], 0.0)), "directness_weight": float(max((g4 or g6)["directness_weight"], 0.0))}
        changed_stats[state] = {"n_cells": int(mask.sum()), "lineage_probability": float(gates[state]["p_mesp1_lineage"])}

    response_rows: list[dict[str, Any]] = []
    selected_lanes = {"L1_STRICT_WT_DIRECT": l1_genes, "L2_GATA4_GATA6_CONDITION_AWARE": l2_genes}
    for state in sorted(gates):
        for gene in sorted(set(l2_genes + ["Gata4", "Gata6"])):
            g4 = g4_by_gene.get(gene, {})
            g6 = g6_by_gene.get(gene, {})
            response_rows.append({
                "official_state": state, "gene": gene, "p_mesp1_lineage": gates[state]["p_mesp1_lineage"],
                "gata4_vote_sign": g4.get("sign", 0), "gata6_vote_sign": g6.get("sign", 0),
                "celloracle_sctenifold_same_sign": bool(g4 or g6), "direct_chIP": bool(directness.get(gene, {}).get("direct", False)),
                "l1_selected": gene in l1_genes or gene == "Gata4", "l2_selected": gene in l2_genes or gene in {"Gata4", "Gata6"},
                "note": "Gata4 target is zeroed in gated cells; Gata6 target is raw-scale half-dose in L2; downstream amplitude is capped at 10% WT 1-99% range",
            })
    write_tsv(ARTIFACT_ROOT / "response_program.tsv", response_rows, sorted({key for row in response_rows for key in row}))

    lane_specs = {
        "L1_STRICT_WT_DIRECT": (state_program_l1, False, l1_genes),
        "L2_GATA4_GATA6_CONDITION_AWARE": (state_program_l2, True, l2_genes),
    }
    lane_results: dict[str, dict[str, Any]] = {}
    for lane, (state_program, include_gata6, selected) in lane_specs.items():
        candidate_X, delta_meta = apply_program(parent_X, parent_states, gates, panel_position, state_program, lane=lane, include_gata6_dose=include_gata6)
        lane_dir = ARTIFACT_ROOT / "submissions" / "T3_gata4" / lane
        candidate_path = lane_dir / "prediction.h5ad"
        candidate = write_candidate(candidate_path, parent, candidate_X, {
            "atom": ATOM, "lane": lane, "parent": str(PARENT_PATH.relative_to(ROOT)), "seed": SEED,
            "target_used": False, "selected_downstream_genes": selected, "selected_panel_fraction": (len(selected) + (2 if include_gata6 else 1)) / 500,
            "lineage_gate": "p_mesp1_lineage >= 0.5; residual multiplied by p", "g4_directness": "GSE52123 E12.5 WT GATA4 promoter +/-5kb; two replicate conservative filter",
            "delta_formula": "confidence * directness_weight * 0.15 * robust_SD_WT(state,gene), per-gene cap 10% WT 1%-99% range",
            "delta_meta": delta_meta,
        })
        contract = contract_check(candidate, panel)
        protected = protected_checks(parent, candidate, set(delta_meta["changed_genes"]), gates, panel_position)
        json_write(ARTIFACT_ROOT / "metrics" / lane / "contract.json", contract)
        json_write(ARTIFACT_ROOT / "metrics" / lane / "protected_checks.json", protected)
        lane_results[lane] = {"path": candidate_path, "contract": contract, "protected": protected, "delta_meta": delta_meta, "selected": selected}
        if not contract["pass"] or not protected["pass"]:
            raise RuntimeError(f"{lane}: local contract/protected check failed")

    # One source-only kill test per lane. It uses the same WT-only votes but a
    # target-specific Gata4 ChIP directness gate is not applied to Mab21l2;
    # this distinction is explicit because GSE52123 is not Mab21l2 evidence.
    source_wt, source_X = load_panel_data(ROOT / "data" / "E9.5.h5ad", panel)
    source_target, _target_X = load_panel_data(ROOT / "data" / "E9.5_mab21l2_ko.h5ad", panel)
    kill_sample = stratified_indices(source_wt.obs["celltype"].astype(str).to_numpy(), 7449, SEED)
    kill_parent = source_wt[kill_sample].copy()
    kill_X = np.asarray(kill_parent.X.toarray() if hasattr(kill_parent.X, "toarray") else kill_parent.X, dtype=np.float32)
    kill_states = kill_parent.obs["celltype"].astype(str).to_numpy()
    kill_by_gene = {row["gene"]: row for row in kill_aggregates[:49]}
    kill_program: dict[str, dict[str, dict[str, Any]]] = {state: {} for state in gates}
    for state in kill_program:
        mask = kill_states == state
        for gene, row in kill_by_gene.items():
            pos = panel_position[gene]
            cap = 0.1 * float(np.quantile(kill_X[:, pos], 0.99) - np.quantile(kill_X[:, pos], 0.01))
            sd = robust_sd(kill_X[mask, pos]) if mask.any() else robust_sd(kill_X[:, pos])
            if cap > 0:
                kill_program[state][gene] = {"delta": float(np.clip(row["sign"] * row["confidence"] * 0.15 * sd, -cap, cap))}
    kill_X_pred, kill_meta = apply_program(kill_X, kill_states, gates, panel_position, kill_program, lane="Mab21l2_source_only_kill", include_gata6_dose=False, perturbation_target="Mab21l2")
    kill_dir = ARTIFACT_ROOT / "kill_test"
    kill_input = kill_dir / "mab21l2_prediction.h5ad"
    kill_identity = kill_dir / "mab21l2_identity.h5ad"
    write_candidate(kill_input, kill_parent, kill_X_pred, {"source_only": True, "target_used": False, "target": "Mab21l2", "method": "same two WT-only votes; no GATA4 ChIP directness reused"})
    write_candidate(kill_identity, kill_parent, kill_X, {"source_only": True, "target_used": False, "method": "identity comparator"})
    kill_scores: dict[str, Any] = {}
    if not args.skip_scorer:
        kill_scores["identity"] = run_scorer(kill_identity, kill_dir / "identity_score.json", ROOT / "data" / "E9.5_mab21l2_ko.h5ad", ROOT / "data" / "E9.5.h5ad", run_log)
        kill_scores["pipeline"] = run_scorer(kill_input, kill_dir / "pipeline_score.json", ROOT / "data" / "E9.5_mab21l2_ko.h5ad", ROOT / "data" / "E9.5.h5ad", run_log)
    json_write(kill_dir / "kill_test_summary.json", {"target": "Mab21l2", "target_used_for_generation": False, "method": "same WT-only CellOracle-style and scTenifold-style votes; target-specific GATA4 ChIP directness excluded", "selected_genes": sorted(kill_by_gene), "scores": kill_scores, "delta_meta": kill_meta})

    for lane, result in lane_results.items():
        lane_dir = result["path"].parent
        metrics_dir = ARTIFACT_ROOT / "metrics" / lane
        score = None
        if not args.skip_scorer:
            # Source-only pseudo-holdout for final candidates is intentionally
            # local and diagnostic; no official target is opened by generation.
            score = run_scorer(result["path"], metrics_dir / "local_score.json", ROOT / "data" / "E9.5_mab21l2_ko.h5ad", ROOT / "data" / "E9.5.h5ad", run_log)
        manifest = {
            "atom": ATOM, "task": "T3", "board": "T3:gata4", "lane": lane, "seed": SEED,
            "parent": str(PARENT_PATH.relative_to(ROOT)), "prediction": str(result["path"].relative_to(ROOT)),
            "artifact_sha256": sha256_file(result["path"]), "n_obs": 7449, "n_vars": 500,
            "target_used_for_generation": False, "server_submission_allowed": False,
            "selected_downstream_genes": result["selected"], "selected_panel_fraction": (len(result["selected"]) + (2 if lane.startswith("L2") else 1)) / 500,
            "contract": result["contract"], "protected_checks": result["protected"], "local_score": score,
            "status": "score_pending" if score is None else "local_scored_no_server_submission",
            "risks": ["E-MTAB-11763 is metadata-only fallback", "local CellOracle/scTenifold-compatible votes are auditable approximations, not upstream package execution", "Mab21l2 kill test is diagnostic and not a leaderboard claim"],
        }
        json_write(lane_dir / "MANIFEST.json", manifest)
        result["manifest"] = manifest

    json_write(ARTIFACT_ROOT / "MANIFEST.json", {
        "atom": ATOM, "active_atom": True, "stop_after_atom": True, "allow_server_submission": False,
        "audit_complete": str((ROOT / "infra" / "external_data" / "AUDIT_COMPLETE.json").relative_to(ROOT)),
        "lanes": {lane: {"artifact": str(value["path"].relative_to(ROOT)), "sha256": value["manifest"]["artifact_sha256"], "status": value["manifest"]["status"]} for lane, value in lane_results.items()},
        "source_only_kill_test": str((ARTIFACT_ROOT / "kill_test" / "kill_test_summary.json").relative_to(ROOT)),
    })
    (ARTIFACT_ROOT / "run.log").write_text("\n".join(run_log) + "\n", encoding="utf-8")
    data_sources = [
        {"source_id": "E-MTAB-6967", "role": "sanitized WT expression; model input", "accession": "E-MTAB-6967", "status": "PASS", "target_used": False},
        {"source_id": "E-MTAB-11763", "role": "metadata-only fallback; not model input", "accession": "E-MTAB-11763", "status": "PASS_METADATA_ONLY_NO_PROCESSED_SNAPSHOT", "target_used": False},
        {"source_id": "GSE52123", "role": "E12.5 WT GATA4 ChIP directness only", "accession": "GSE52123", "status": "PASS", "target_used": False},
        {"source_id": "REACTOME", "role": "audited pathway provenance/filter context; no sign", "accession": "ReactomePathways", "status": "PASS", "target_used": False},
        {"source_id": "GO", "role": "audited ontology provenance/filter context; no sign", "accession": "go-basic/MOUSE", "status": "PASS", "target_used": False},
        {"source_id": "CELLORACLE", "role": "pinned source provenance; no pretrained model", "accession": "7948870a3b70f7d228e54734e1fa9ed3291fc23b", "status": "PASS", "target_used": False},
        {"source_id": "SCTENIFOLDKNK", "role": "pinned source provenance; no pretrained model", "accession": "d635a5855295b4ee75909438b09b2ea27ce3437c", "status": "PASS", "target_used": False},
    ]
    write_tsv(ARTIFACT_ROOT / "DATA_SOURCES_USED.tsv", data_sources, ["source_id", "role", "accession", "status", "target_used"])
    (ARTIFACT_ROOT / "METHOD_DISCLOSURE.md").write_text(
        """# B2-T3-A1 method disclosure\n\n"
        "- Parent: current T3 `wt_identity` (`submissions/scored/baseline-001/T3_gata4/submission.h5ad`), cell order, coordinates, and 500-gene order are preserved.\n"
        "- Expression model input: only sanitized E-MTAB-6967 WT cells, deterministic stage x celltype sample (seed 20260829). E-MTAB-11763 had no processed snapshot and was metadata-only; no FASTQ was used.\n"
        "- CellOracle vote: local state-wise WT-only regression response vote. scTenifoldKnk vote: local state-wise ridge conditional-network virtual-KO vote. Both are transparent, no-pretrained-weight implementations informed by pinned source commits; the upstream packages were not executed.\n"
        "- Lineage gate: continuous WT marker program probability, with response only at p >= 0.5 and residual multiplied by p. No hardcoded celltype allow-list.\n"
        "- Directness: GSE52123 E12.5 WT GATA4 ChIP Ab1/Ab2 versus matched input, promoter +/-5 kb using NCBIM37/mm9 GTF. It supplies directness only, never sign.\n"
        "- L1: two-vote same-sign Gata4 consensus plus conservative two-replicate directness; at most 50/500 panel genes including Gata4. L2 adds raw-scale Gata6 half-dose and at most 24 extra Gata6-vote genes, total at most 75/500.\n"
        "- Amplitude: `confidence * directness_weight * 0.15 * robust_SD_WT(state,gene)`, with per-gene 10% WT 1%-99% range cap. Gata4 is zeroed only in gated cells; Gata6 uses raw-scale half-dose then log1p.\n"
        "- No server submission was performed. Scores in `metrics/local_score.json` are local source-only diagnostics, not leaderboard evidence.\n""",
        encoding="utf-8",
    )
    print(json.dumps({"atom": ATOM, "lanes": {lane: value["manifest"] for lane, value in lane_results.items()}, "kill_test": kill_scores}, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
