#!/usr/bin/env python3
"""Audit exact-stage GEO perturbation matrices for T3 S1D.

This atom is deliberately separate from the earlier context-only S1D atom.
It audits only official processed GEO series matrices and platform annotations;
the matrices are not merged into the E8.75 challenge input and do not open a
candidate-generation gate by themselves.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
from pathlib import Path
from statistics import fmean
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
ATOM = "T3-S1D-INDEPENDENT-ACTIVITY-EVIDENCE-20260901-v3"
OUTPUT_DEFAULT = ROOT / "artifacts/tool_integration" / ATOM
SCRIPT_PATH = Path(__file__).resolve()
PANEL_PATH = ROOT / "data/gene_panel/T3__gata4.genes.txt"
DATA_ROOT = ROOT / "infra/external_data/quarantine/T3-S1D-INDEPENDENT-ACTIVITY-EVIDENCE"
CONTRACT_PATH = ROOT / "docs/batch3/T3_S1D_EXACT_ACTIVITY_EVIDENCE_CONTRACT_20260901_v3.json"
SEED: None = None


STUDIES: tuple[dict[str, Any], ...] = (
    {
        "accession": "GSE5298",
        "target_gene": "Gata4",
        "stage": "E9.5",
        "tissue": "microdissected atrioventricular canal",
        "perturbation": "Tie2-Cre conditional Gata4 loss-of-function vs flox/flox control",
        "matrix_file": "GSE5298/GSE5298_series_matrix.txt.gz",
        "platform_file": "platforms/GPL1261.annot.gz",
        "platform": "GPL1261",
        "effect_scale": "linear_expression_log2_ratio",
        "control_accessions": ["GSM120064", "GSM120065", "GSM120066", "GSM120067"],
        "perturbation_accessions": ["GSM120068", "GSM120069", "GSM120070", "GSM120071"],
        "excluded_accessions": [],
        "source_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE5298",
        "matrix_url": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE5nnn/GSE5298/matrix/GSE5298_series_matrix.txt.gz",
        "platform_url": "https://ftp.ncbi.nlm.nih.gov/geo/platforms/GPL1nnn/GPL1261/annot/GPL1261.annot.gz",
        "sample_design_note": "Each RNA sample is a pool of microdissected AVC material; all four matrix controls were retained, while a literature-reported post hoc noisy-control exclusion was not applied.",
        "evidence_grade": "B_EARLY_CONTEXT_POOLED_TISSUE",
    },
    {
        "accession": "GSE9652",
        "target_gene": "Gata4",
        "stage": "E9.5",
        "tissue": "pooled mouse heart",
        "perturbation": "Nkx2-5-Cre conditional Gata4 loss-of-function vs flox/+ control",
        "matrix_file": "GSE9652/GSE9652_series_matrix.txt.gz",
        "platform_file": "platforms/GPL1261.annot.gz",
        "platform": "GPL1261",
        "effect_scale": "linear_expression_log2_ratio",
        "control_accessions": ["GSM243911", "GSM243912", "GSM243913"],
        "perturbation_accessions": ["GSM243917", "GSM243918", "GSM243919", "GSM243920", "GSM243921"],
        "excluded_accessions": ["GSM243914", "GSM243915", "GSM243916"],
        "source_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE9652",
        "matrix_url": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE9nnn/GSE9652/matrix/GSE9652_series_matrix.txt.gz",
        "platform_url": "https://ftp.ncbi.nlm.nih.gov/geo/platforms/GPL1nnn/GPL1261/annot/GPL1261.annot.gz",
        "sample_design_note": "The three Nkx2-5-Cre heterozygous branch samples were excluded from the binary control-vs-Gata4-KO contrast and remain listed explicitly.",
        "evidence_grade": "B_EARLY_CONTEXT_POOLED_TISSUE",
    },
    {
        "accession": "GSE78125",
        "target_gene": "Ctnnb1",
        "stage": "E9.5 (19-21 somites)",
        "tissue": "microdissected anterior secondary heart field mesoderm",
        "perturbation": "Mef2c-AHF-Cre conditional Ctnnb1 loss-of-function vs Bcat control",
        "matrix_file": "GSE78125/GSE78125_series_matrix.txt.gz",
        "platform_file": "platforms/GPL6246.annot.gz",
        "platform": "GPL6246",
        "effect_scale": "RMA_log2_difference",
        "control_accessions": ["GSM2067665", "GSM2067666", "GSM2067667", "GSM2067668"],
        "perturbation_accessions": ["GSM2067661", "GSM2067662", "GSM2067663", "GSM2067664"],
        "excluded_accessions": [
            "GSM2067653", "GSM2067654", "GSM2067655", "GSM2067656",
            "GSM2067657", "GSM2067658", "GSM2067659", "GSM2067660",
            "GSM2067669", "GSM2067670", "GSM2067671", "GSM2067672",
            "GSM2067673", "GSM2067674", "GSM2067675", "GSM2067676",
        ],
        "source_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE78125",
        "matrix_url": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE78nnn/GSE78125/matrix/GSE78125_series_matrix.txt.gz",
        "platform_url": "https://ftp.ncbi.nlm.nih.gov/geo/platforms/GPL6nnn/GPL6246/annot/GPL6246.annot.gz",
        "sample_design_note": "Only the Bcat KO and Bcat control branches were used; Tbx1 and rescue branches were excluded explicitly.",
        "evidence_grade": "B_EARLY_CONTEXT_TISSUE_LIMITED",
    },
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def repo_relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_tsv(path: Path, rows: Iterable[Mapping[str, Any]], fields: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    field_list = list(fields)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=field_list, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in field_list})


def panel_genes() -> list[str]:
    genes = [line.strip() for line in PANEL_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(genes) != 500 or len(set(genes)) != 500:
        raise ValueError("T3 panel must contain exactly 500 unique genes")
    return genes


def load_contract() -> dict[str, Any]:
    if not CONTRACT_PATH.is_file():
        raise FileNotFoundError(CONTRACT_PATH)
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if contract.get("schema") != "ve.t3.s1d-exact-activity-contract.v1":
        raise ValueError("S1D v2 contract schema mismatch")
    if contract.get("atom") != ATOM:
        raise ValueError("S1D v2 contract atom mismatch")
    if contract.get("panel_path") != repo_relative(PANEL_PATH):
        raise ValueError("S1D v2 contract panel path mismatch")
    if contract.get("panel_sha256") != sha256_file(PANEL_PATH):
        raise ValueError("S1D v2 contract panel hash mismatch")
    frozen = {item.get("accession"): item for item in contract.get("studies", [])}
    if set(frozen) != {study["accession"] for study in STUDIES}:
        raise ValueError("S1D v2 contract study set mismatch")
    compare_fields = (
        "matrix_file", "platform_file", "platform", "effect_scale",
        "control_accessions", "perturbation_accessions", "excluded_accessions",
    )
    for study in STUDIES:
        expected = frozen[study["accession"]]
        for field in compare_fields:
            if expected.get(field) != study.get(field):
                raise ValueError(f"S1D v2 contract mismatch for {study['accession']}: {field}")
    return contract


def _csv_line(raw: str) -> list[str]:
    return next(csv.reader([raw], delimiter="\t"))


def load_platform_annotations(path: Path, symbols: set[str]) -> dict[str, dict[str, list[str]]]:
    mapping: dict[str, dict[str, set[str]]] = {
        symbol: {"probe_ids": set(), "entrez_ids": set()} for symbol in symbols
    }
    in_table = False
    header: list[str] | None = None
    with path.open("rb") as binary:
        import gzip

        with gzip.open(binary, "rt", encoding="utf-8", newline="") as handle:
            for raw in handle:
                row = _csv_line(raw)
                if row and row[0] == "!platform_table_begin":
                    in_table = True
                    continue
                if row and row[0] == "!platform_table_end":
                    break
                if not in_table:
                    continue
                if header is None:
                    header = row
                    continue
                if len(row) < 3:
                    raise ValueError(f"{path}: malformed platform row")
                probe = row[0].strip()
                for symbol in row[2].split("///"):
                    symbol = symbol.strip()
                    if symbol in mapping and probe:
                        mapping[symbol]["probe_ids"].add(probe)
                        for entrez_id in row[3].split("///"):
                            entrez_id = entrez_id.strip()
                            if entrez_id and entrez_id not in {"---", "-"}:
                                mapping[symbol]["entrez_ids"].add(entrez_id)
    if header is None:
        raise ValueError(f"{path}: platform table is missing")
    return {
        symbol: {
            "probe_ids": sorted(value["probe_ids"]),
            "entrez_ids": sorted(value["entrez_ids"]),
        }
        for symbol, value in mapping.items()
    }


def load_platform_symbols(path: Path, symbols: set[str]) -> dict[str, list[str]]:
    """Compatibility helper for small unit tests and callers needing probes only."""
    return {
        symbol: annotation["probe_ids"]
        for symbol, annotation in load_platform_annotations(path, symbols).items()
    }


def load_series_matrix(path: Path, wanted_probes: set[str]) -> dict[str, Any]:
    metadata: dict[str, list[list[str]]] = {}
    table_header: list[str] | None = None
    values: dict[str, list[float]] = {}
    in_table = False
    n_rows = 0
    with path.open("rb") as binary:
        import gzip

        with gzip.open(binary, "rt", encoding="utf-8", newline="") as handle:
            for raw in handle:
                row = _csv_line(raw)
                if row and row[0] == "!series_matrix_table_begin":
                    in_table = True
                    continue
                if row and row[0] == "!series_matrix_table_end":
                    in_table = False
                    continue
                if not in_table:
                    if row and row[0].startswith("!"):
                        metadata.setdefault(row[0], []).append(row[1:])
                    continue
                if table_header is None:
                    table_header = row
                    continue
                if len(row) != len(table_header):
                    raise ValueError(f"{path}: matrix row has {len(row)} fields, expected {len(table_header)}")
                n_rows += 1
                probe = row[0].strip()
                if probe not in wanted_probes:
                    continue
                if probe in values:
                    raise ValueError(f"{path}: duplicate selected probe {probe}")
                parsed: list[float] = []
                for raw_value in row[1:]:
                    if raw_value.strip().lower() in {"", "na", "null", "nan"}:
                        parsed.append(math.nan)
                    else:
                        parsed.append(float(raw_value))
                values[probe] = parsed
    if table_header is None:
        raise ValueError(f"{path}: series matrix table is missing")
    if not table_header or table_header[0] != "ID_REF":
        raise ValueError(f"{path}: first matrix column is not ID_REF")
    accessions = table_header[1:]
    if len(set(accessions)) != len(accessions):
        raise ValueError(f"{path}: duplicate sample accession in matrix header")
    return {"metadata": metadata, "accessions": accessions, "values": values, "n_rows": n_rows}


def _metadata_first(metadata: Mapping[str, list[list[str]]], key: str) -> list[str]:
    rows = metadata.get(key, [])
    return list(rows[0]) if rows else []


def _sign(value: float) -> int:
    return -1 if value < 0 else 1 if value > 0 else 0


def _effect(control: list[float], perturbation: list[float], scale: str) -> float:
    if not control or not perturbation:
        raise ValueError("both groups must contain values")
    control_mean = fmean(control)
    perturbation_mean = fmean(perturbation)
    if scale == "linear_expression_log2_ratio":
        if control_mean <= 0 or perturbation_mean <= 0:
            raise ValueError("linear expression must be positive for log2 ratio")
        return math.log2(perturbation_mean / control_mean)
    if scale == "RMA_log2_difference":
        return perturbation_mean - control_mean
    raise ValueError(f"unknown effect scale: {scale}")


def _gene_values(
    matrix_values: Mapping[str, list[float]],
    probe_ids: list[str],
) -> list[float]:
    available = [matrix_values[probe] for probe in probe_ids if probe in matrix_values]
    if not available:
        raise KeyError("none of the annotated probes are present in the matrix")
    n = len(available[0])
    if any(len(row) != n for row in available):
        raise ValueError("selected probe rows have inconsistent sample counts")
    # Multiple probes are collapsed within each sample, never treated as
    # additional biological replicates.  Median is robust to probe conflicts.
    from statistics import median

    values = [median(row[i] for row in available) for i in range(n)]
    if not all(math.isfinite(value) for value in values):
        raise ValueError("selected expression values contain non-finite values")
    return values


def _metadata_value(metadata: Mapping[str, list[list[str]]], key: str, index: int) -> str:
    values = [row[index] for row in metadata.get(key, []) if index < len(row) and row[index]]
    return " || ".join(values)


def _audit_study(
    study: Mapping[str, Any], panel: list[str]
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    matrix_path = DATA_ROOT / str(study["matrix_file"])
    platform_path = DATA_ROOT / str(study["platform_file"])
    for path in (matrix_path, platform_path):
        if not path.is_file():
            raise FileNotFoundError(path)
    symbols = set(panel) | {str(study["target_gene"])}
    annotations = load_platform_annotations(platform_path, symbols)
    symbol_to_probes = {symbol: value["probe_ids"] for symbol, value in annotations.items()}
    wanted_probes = {probe for probes in symbol_to_probes.values() for probe in probes}
    matrix = load_series_matrix(matrix_path, wanted_probes)
    accessions = matrix["accessions"]
    accession_to_index = {accession: i for i, accession in enumerate(accessions)}
    control_accessions = list(study["control_accessions"])
    perturb_accessions = list(study["perturbation_accessions"])
    excluded_accessions = list(study["excluded_accessions"])
    selected = control_accessions + perturb_accessions
    if len(set(selected)) != len(selected):
        raise ValueError(f"{study['accession']}: control and perturbation groups overlap")
    if any(accession not in accession_to_index for accession in selected + excluded_accessions):
        raise ValueError(f"{study['accession']}: configured accession is absent from matrix")
    control_indices = [accession_to_index[accession] for accession in control_accessions]
    perturb_indices = [accession_to_index[accession] for accession in perturb_accessions]
    control_set = set(control_accessions)
    perturbation_set = set(perturb_accessions)
    excluded_set = set(excluded_accessions)
    sample_titles = _metadata_first(matrix["metadata"], "!Sample_title")
    sample_rows: list[dict[str, Any]] = []
    for index, accession in enumerate(accessions):
        if accession in control_set:
            group_id, include, exclude_reason = "CONTROL", True, ""
        elif accession in perturbation_set:
            group_id, include, exclude_reason = "PERTURBATION", True, ""
        elif accession in excluded_set:
            group_id, include, exclude_reason = "EXCLUDED_BRANCH", False, "explicitly excluded non-target contrast branch"
        else:
            group_id, include, exclude_reason = "UNCONFIGURED", False, "matrix sample not present in frozen contrast configuration"
        sample_rows.append(
            {
                "study": study["accession"],
                "platform": study["platform"],
                "gsm": accession,
                "matrix_column_index": index,
                "matrix_column_name": accession,
                "title": sample_titles[index] if index < len(sample_titles) else "",
                "source_name": _metadata_value(matrix["metadata"], "!Sample_source_name_ch1", index),
                "characteristics": _metadata_value(matrix["metadata"], "!Sample_characteristics_ch1", index),
                "group_id": group_id,
                "contrast_id": f"{study['accession']}_perturbation_minus_control",
                "include": include,
                "exclude_reason": exclude_reason,
                "biological_sample_id": f"GSM:{accession};pooling_semantics_unconfirmed",
                "technical_replicate_id": "NOT_RECORDED_IN_SERIES_MATRIX",
                "causal_class": "DIRECT_PERTURBATION_CONTEXT",
                "metadata_basis": "!Sample_title;!Sample_source_name_ch1;!Sample_characteristics_ch1",
            }
        )
    rows: list[dict[str, Any]] = []
    target = str(study["target_gene"])
    target_probe_ids = symbol_to_probes.get(target, [])
    if not target_probe_ids:
        raise ValueError(f"{study['accession']}: target {target} has no platform annotation")
    target_gene_values = _gene_values(matrix["values"], target_probe_ids)
    target_control = [target_gene_values[i] for i in control_indices]
    target_perturbation = [target_gene_values[i] for i in perturb_indices]
    target_effect = _effect(target_control, target_perturbation, str(study["effect_scale"]))
    target_control_center = fmean(target_control)
    target_signs = [_sign(value - target_control_center) for value in target_perturbation]
    target_down_count = sum(sign == -1 for sign in target_signs)
    target_summary = {
        "target_gene": target,
        "target_probe_ids": target_probe_ids,
        "target_entrez_ids": annotations[target]["entrez_ids"],
        "target_probe_count": len(target_probe_ids),
        "target_effect": target_effect,
        "effect_scale": study["effect_scale"],
        "expected_target_direction_after_loss_of_function": "DOWN",
        "target_replicate_direction_signs_vs_control_mean": target_signs,
        "target_replicate_down_count": target_down_count,
        "target_replicate_count": len(target_signs),
        "target_replicate_down_fraction": target_down_count / len(target_signs),
        "target_expression_readout_interpretation": "DESCRIPTIVE_ONLY; target probe signal is not used as a gate because deletion-probe placement and tissue composition can decouple transcript signal from functional loss.",
    }
    for gene in panel:
        probes = symbol_to_probes.get(gene, [])
        present_probes = [probe for probe in probes if probe in matrix["values"]]
        if not present_probes:
            continue
        gene_values = _gene_values(matrix["values"], present_probes)
        control = [gene_values[i] for i in control_indices]
        perturbation = [gene_values[i] for i in perturb_indices]
        effect = _effect(control, perturbation, str(study["effect_scale"]))
        rows.append(
            {
                "study": study["accession"],
                "target_gene": target,
                "response_gene": gene,
                "is_target_gene": gene == target,
                "probe_count": len(present_probes),
                "probe_ids": "|".join(present_probes),
                "control_n": len(control),
                "perturbation_n": len(perturbation),
                "effect_scale": study["effect_scale"],
                "effect_perturbation_minus_control": effect,
                "direction": "DOWN" if effect < 0 else "UP" if effect > 0 else "ZERO",
                "activity_eligible_for_E875": False,
                "signed_family_eligible": False,
            }
        )
    panel_effects = [row["effect_perturbation_minus_control"] for row in rows if not row["is_target_gene"]]
    study_summary = {
        "accession": study["accession"],
        "target_gene": target,
        "stage": study["stage"],
        "tissue": study["tissue"],
        "perturbation": study["perturbation"],
        "platform": study["platform"],
        "matrix_rows": matrix["n_rows"],
        "matrix_columns": len(accessions),
        "matrix_accessions": accessions,
        "control_accessions": control_accessions,
        "perturbation_accessions": perturb_accessions,
        "excluded_accessions": excluded_accessions,
        "metadata_titles": _metadata_first(matrix["metadata"], "!Sample_title"),
        "metadata_source_names": sorted(set(_metadata_first(matrix["metadata"], "!Sample_source_name_ch1"))),
        "metadata_processing": sorted(set(_metadata_first(matrix["metadata"], "!Sample_data_processing"))),
        "target": target_summary,
        "panel_present_count_including_target": len(rows),
        "panel_present_count_excluding_target": len(panel_effects),
        "panel_down_count_excluding_target": sum(effect < 0 for effect in panel_effects),
        "panel_up_count_excluding_target": sum(effect > 0 for effect in panel_effects),
        "panel_zero_count_excluding_target": sum(effect == 0 for effect in panel_effects),
        "panel_median_abs_effect_excluding_target": sorted(abs(effect) for effect in panel_effects)[len(panel_effects) // 2] if panel_effects else None,
        "exact_gate_status": "PASS_METADATA_AND_PROCESSED_MATRIX",
        "evidence_grade": study["evidence_grade"],
        "sample_design_note": study["sample_design_note"],
        "signed_family_eligible": False,
        "activity_eligible_for_E875": False,
    }
    inventory = dict(study)
    inventory.update(
        {
            "matrix_path": repo_relative(matrix_path),
            "matrix_bytes": matrix_path.stat().st_size,
            "matrix_sha256": sha256_file(matrix_path),
            "platform_path": repo_relative(platform_path),
            "platform_bytes": platform_path.stat().st_size,
            "platform_sha256": sha256_file(platform_path),
            "matrix_shape": [matrix["n_rows"], len(accessions)],
            "target_probe_ids": "|".join(target_probe_ids),
            "target_effect": target_effect,
            "target_down_fraction": target_summary["target_replicate_down_fraction"],
        }
    )
    mapping_rows = []
    for gene in sorted(symbols):
        annotation = annotations[gene]
        matrix_probe_ids = [probe for probe in annotation["probe_ids"] if probe in matrix["values"]]
        mapping_rows.append(
            {
                "study": study["accession"],
                "platform": study["platform"],
                "gene_symbol": gene,
                "entrez_ids": "|".join(annotation["entrez_ids"]),
                "platform_probe_ids": "|".join(annotation["probe_ids"]),
                "matrix_probe_ids": "|".join(matrix_probe_ids),
                "probe_count_in_platform": len(annotation["probe_ids"]),
                "probe_count_in_matrix": len(matrix_probe_ids),
                "mapping_status": "PASS" if matrix_probe_ids else "NOT_PRESENT_IN_MATRIX",
                "aggregation": "within_sample_median_across_probes" if matrix_probe_ids else "NA",
                "is_target_gene": gene == target,
            }
        )
    return rows, study_summary, inventory, sample_rows, mapping_rows


def _artifact_manifest(output_dir: Path) -> dict[str, Any]:
    files = []
    for path in sorted(output_dir.rglob("*")):
        if not path.is_file() or path.name == "artifact_manifest.stable.json":
            continue
        files.append({"path": path.relative_to(output_dir).as_posix(), "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    return {
        "schema": "ve.t3.s1d-exact-activity-artifact-manifest.v1",
        "task": "T3-S1D-INDEPENDENT-ACTIVITY-EVIDENCE",
        "atom": ATOM,
        "files": files,
    }


def run(*, output_dir: Path = OUTPUT_DEFAULT) -> dict[str, Any]:
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise FileExistsError(f"S1D v2 output already exists: {output_dir}")
    output_dir.mkdir(parents=True)
    try:
        contract = load_contract()
        panel = panel_genes()
        all_rows: list[dict[str, Any]] = []
        summaries: dict[str, Any] = {}
        inventory: list[dict[str, Any]] = []
        all_sample_rows: list[dict[str, Any]] = []
        all_mapping_rows: list[dict[str, Any]] = []
        frozen_studies = {item["accession"]: item for item in contract["studies"]}
        for study in STUDIES:
            rows, summary, study_inventory, sample_rows, mapping_rows = _audit_study(study, panel)
            frozen = frozen_studies[study["accession"]]
            if study_inventory["matrix_sha256"] != frozen["matrix_sha256"]:
                raise ValueError(f"{study['accession']}: matrix hash does not match frozen contract")
            if study_inventory["platform_sha256"] != frozen["platform_sha256"]:
                raise ValueError(f"{study['accession']}: platform hash does not match frozen contract")
            all_rows.extend(rows)
            summaries[study["accession"]] = summary
            inventory.append(study_inventory)
            all_sample_rows.extend(sample_rows)
            all_mapping_rows.extend(mapping_rows)
        output_data = output_dir / "data"
        metrics = output_dir / "metrics"
        write_json(metrics / "contract.json", contract)
        write_tsv(
            output_data / "sample_qc.tsv",
            all_sample_rows,
            [
                "study", "platform", "gsm", "matrix_column_index", "matrix_column_name", "title", "source_name",
                "characteristics", "group_id", "contrast_id", "include", "exclude_reason", "biological_sample_id",
                "technical_replicate_id", "causal_class", "metadata_basis",
            ],
        )
        write_tsv(
            output_data / "mapping_qc.tsv",
            all_mapping_rows,
            [
                "study", "platform", "gene_symbol", "entrez_ids", "platform_probe_ids", "matrix_probe_ids",
                "probe_count_in_platform", "probe_count_in_matrix", "mapping_status", "aggregation", "is_target_gene",
            ],
        )
        write_tsv(
            output_data / "evidence_inventory.tsv",
            inventory,
            [
                "accession", "target_gene", "stage", "tissue", "perturbation", "platform", "matrix_file",
                "platform_file", "matrix_path", "matrix_bytes", "matrix_sha256", "platform_path", "platform_bytes",
                "platform_sha256", "matrix_shape", "control_accessions", "perturbation_accessions", "excluded_accessions",
                "target_probe_ids", "target_effect", "target_down_fraction", "evidence_grade", "exact_gate_status",
                "source_url", "matrix_url", "platform_url", "sample_design_note",
            ],
        )
        write_tsv(
            output_data / "gene_effects.tsv",
            all_rows,
            [
                "study", "target_gene", "response_gene", "is_target_gene", "probe_count", "probe_ids", "control_n",
                "perturbation_n", "effect_scale", "effect_perturbation_minus_control", "direction",
                "activity_eligible_for_E875", "signed_family_eligible",
            ],
        )
        study_evidence_rows = []
        for summary in summaries.values():
            target_summary = summary["target"]
            study_evidence_rows.append(
                {
                    "study": summary["accession"],
                    "target_gene": summary["target_gene"],
                    "stage": summary["stage"],
                    "tissue": summary["tissue"],
                    "platform": summary["platform"],
                    "matrix_shape": f"{summary['matrix_rows']}x{summary['matrix_columns']}",
                    "control_n": len(summary["control_accessions"]),
                    "perturbation_n": len(summary["perturbation_accessions"]),
                    "excluded_n": len(summary["excluded_accessions"]),
                    "target_probe_ids": "|".join(target_summary["target_probe_ids"]),
                    "target_entrez_ids": "|".join(target_summary["target_entrez_ids"]),
                    "target_effect": target_summary["target_effect"],
                    "target_down_fraction": target_summary["target_replicate_down_fraction"],
                    "panel_present_excluding_target": summary["panel_present_count_excluding_target"],
                    "panel_down_excluding_target": summary["panel_down_count_excluding_target"],
                    "panel_up_excluding_target": summary["panel_up_count_excluding_target"],
                    "exact_gate_status": summary["exact_gate_status"],
                    "evidence_grade": summary["evidence_grade"],
                    "signed_family_eligible": summary["signed_family_eligible"],
                    "activity_eligible_for_E875": summary["activity_eligible_for_E875"],
                }
            )
        write_tsv(
            output_data / "study_evidence.tsv",
            study_evidence_rows,
            [
                "study", "target_gene", "stage", "tissue", "platform", "matrix_shape", "control_n",
                "perturbation_n", "excluded_n", "target_probe_ids", "target_entrez_ids", "target_effect",
                "target_down_fraction", "panel_present_excluding_target", "panel_down_excluding_target",
                "panel_up_excluding_target", "exact_gate_status", "evidence_grade", "signed_family_eligible",
                "activity_eligible_for_E875",
            ],
        )
        source_audit = {
            "schema": "ve.t3.s1d-exact-source-audit.v1",
            "retrieved_at": "2026-09-01",
            "source_type": "NCBI GEO public series metadata, official series matrices, and official platform annotations",
            "raw_data_downloaded": False,
            "new_external_data_downloaded": True,
            "panel_path": repo_relative(PANEL_PATH),
            "panel_sha256": sha256_file(PANEL_PATH),
            "panel_gene_count": len(panel),
            "contract_path": repo_relative(CONTRACT_PATH),
            "contract_sha256": sha256_file(CONTRACT_PATH),
            "gene_level_aggregation": "within_sample_median_across_probes",
            "studies": inventory,
            "method_constraints": [
                "Only explicit GEO sample accessions in the study configuration were used.",
                "Probe-to-symbol mapping came from the matching NCBI GEO platform annotation.",
                "Linear-scale GPL1261 values use log2(mean perturbation / mean control); GPL6246 RMA values use mean log2 difference.",
                "No raw CEL download, deconvolution, cross-study normalization, or E8.75 input modification was performed.",
            ],
        }
        write_json(metrics / "source_audit.json", source_audit)
        write_json(metrics / "processed_effects.json", summaries)
        target_family_counts = {
            target: sum(summary["target_gene"] == target for summary in summaries.values())
            for target in sorted({summary["target_gene"] for summary in summaries.values()} | {"Gata6"})
        }
        gate = {
            "schema": "ve.t3.s1d-exact-activity-gate.v1",
            "task": "T3-S1D-INDEPENDENT-ACTIVITY-EVIDENCE",
            "atom": ATOM,
            "status": "HOLD_EXACT_STAGE_CONTEXTUAL_ACTIVITY_NOT_STATE_MATCHED",
            "metadata_evidence": "PASS",
            "processed_matrix_integrity": "PASS_FOR_THREE_EXACT_STAGE_CONTEXTS",
            "target_perturbation_context": "PASS_FOR_GATA4_TWO_FAMILIES_AND_CTNNB1_ONE_FAMILY",
            "target_family_counts": target_family_counts,
            "target_expression_direction_gate": "NOT_USED_AS_FUNCTIONAL_GATE",
            "state_matched_activity_for_E875": "NOT_IDENTIFIABLE",
            "independent_signed_family_count_for_E875": 0,
            "signed_family_eligible_studies": [],
            "candidate_generation": False,
            "server_submission": False,
            "blocks_submission": False,
            "reason": "The three exact-stage records are tissue-limited E9.5 perturbation contexts, not the challenge's E8.75 state. Target probe signals are descriptive and are not uniformly reduced after perturbation; no prevalidated state-specific signed family is established.",
            "scientific_statement": "GSE5298 and GSE9652 provide two independent early Gata4 cardiac-tissue perturbation contexts; GSE78125 provides one early Ctnnb1 AHF context. They support context-specific response auditing but do not transfer a signed state-specific effect into T3 E8.75 or unlock candidate generation.",
        }
        # Keep the target symbol spelling stable in the JSON contract.
        gate["target_perturbation_context"] = "PASS_FOR_GATA4_TWO_FAMILIES_AND_CTNNB1_ONE_FAMILY"
        write_json(metrics / "gate_report.json", gate)
        write_json(metrics / "decision.json", gate)
        completion = {
            "schema": "ve.t3.s1d-exact-completion.v1",
            "task": "T3-S1D-INDEPENDENT-ACTIVITY-EVIDENCE",
            "atom": ATOM,
            "status": gate["status"],
            "script": {"path": repo_relative(SCRIPT_PATH), "sha256": sha256_file(SCRIPT_PATH)},
            "processed_studies": [study["accession"] for study in STUDIES],
            "metadata_only_targets": ["Gata6"],
            "sample_qc_path": repo_relative(output_data / "sample_qc.tsv"),
            "mapping_qc_path": repo_relative(output_data / "mapping_qc.tsv"),
            "gene_effects_path": repo_relative(output_data / "gene_effects.tsv"),
            "study_evidence_path": repo_relative(output_data / "study_evidence.tsv"),
            "candidate_generation": False,
            "server_submission": False,
            "blocks_submission": False,
        }
        write_json(metrics / "completion_report.json", completion)
        (output_dir / "run.log").write_text(
            "execution_status=COMPLETE\n"
            "study_count=3\n"
            "raw_data_downloaded=false\n"
            "e8_75_inference_started=false\n"
            "candidate_generation=false\n"
            "server_submission=false\n",
            encoding="utf-8",
        )
        write_json(
            metrics / "run_manifest.json",
            {
                "schema": "ve.t3.s1d-exact-run-manifest.v1",
                "atom": ATOM,
                "script": {"path": repo_relative(SCRIPT_PATH), "sha256": sha256_file(SCRIPT_PATH)},
                "contract": {"path": repo_relative(CONTRACT_PATH), "sha256": sha256_file(CONTRACT_PATH)},
                "panel": {"path": repo_relative(PANEL_PATH), "sha256": sha256_file(PANEL_PATH)},
                "random_seed": SEED,
                "study_accessions": [study["accession"] for study in STUDIES],
                "execution_status": "COMPLETE",
                "evidence_gate": gate["status"],
            },
        )
        (output_dir / "RESULT.md").write_text(
            f"# {ATOM}\n\n"
            "Three official E9.5 perturbation contexts were audited with matching "
            "GEO platform annotations: two Gata4 cardiac-tissue families and one "
            "Ctnnb1 AHF family. Matrix integrity and probe mapping pass. The records "
            "remain tissue-limited contextual evidence, target expression is "
            "descriptive only, and the E8.75 state-matched activity gate remains "
            "closed. No candidate or server submission was created.\n",
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
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = run(output_dir=args.output)
    print(json.dumps(result["gate"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
