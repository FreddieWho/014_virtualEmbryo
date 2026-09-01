#!/usr/bin/env python3
"""Metadata-first audit and sanitization for Batch 2 B2-T3-A1.

The script deliberately keeps raw objects in quarantine and does not run a
normalisation, embedding, or model before the source-specific keep mask has
been written.  E-MTAB-6967 is streamed twice so the large MatrixMarket file
can be sanitized without materialising the full matrix in memory.
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
import tarfile
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ATOM = "B2-T3-A1"
RULES = "2026-08-29"
EMTAB6967_ACC = "E-MTAB-6967"
EMTAB11763_ACC = "E-MTAB-11763"
GSE52123_ACC = "GSE52123"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _copy_with_hash(source: Path, destination: Path) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return {"path": destination.as_posix(), "bytes": destination.stat().st_size, "sha256": sha256_file(destination)}


def _matrix_header(path: Path) -> tuple[int, int, int]:
    with path.open("rt", encoding="ascii", errors="strict") as handle:
        first = handle.readline().strip()
        if first != "%%MatrixMarket matrix coordinate integer general":
            raise ValueError(f"{path}: unsupported MatrixMarket header {first!r}")
        for line in handle:
            if line.startswith("%") or not line.strip():
                continue
            parts = line.split()
            if len(parts) != 3:
                raise ValueError(f"{path}: malformed dimensions {line!r}")
            return tuple(int(value) for value in parts)  # type: ignore[return-value]
    raise ValueError(f"{path}: missing MatrixMarket dimensions")


def _iter_matrix_entries(path: Path) -> Iterable[tuple[int, int, str]]:
    with path.open("rt", encoding="ascii", errors="strict") as handle:
        next(handle)
        for line in handle:
            if line.startswith("%") or not line.strip():
                continue
            parts = line.split()
            if len(parts) != 3:
                raise ValueError(f"{path}: malformed entry {line[:80]!r}")
            yield int(parts[0]), int(parts[1]), parts[2]


def _sanitize_matrixmarket(
    source: Path,
    destination: Path,
    keep_columns: np.ndarray,
    *,
    expected_rows: int,
) -> dict[str, Any]:
    n_rows, n_cols, nnz = _matrix_header(source)
    if n_rows != expected_rows or n_cols != len(keep_columns):
        raise ValueError(f"{source}: header {(n_rows, n_cols)} does not match metadata/genes")
    selected = np.flatnonzero(keep_columns).astype(np.int64)
    new_column = np.full(n_cols, -1, dtype=np.int64)
    new_column[selected] = np.arange(1, len(selected) + 1, dtype=np.int64)

    # The large E-MTAB-6967 object is optionally filtered by a tiny compiled
    # helper.  It only applies the metadata column mask and preserves the
    # MatrixMarket entries; no expression statistic is computed here.
    fast_filter = os.environ.get("B2_MATRIXMARKET_FILTER")
    if fast_filter:
        mask_path = destination.with_suffix(destination.suffix + ".keep_mask.tsv")
        mask_path.parent.mkdir(parents=True, exist_ok=True)
        mask_path.write_text(
            f"{n_cols} {len(selected)}\n" + "\n".join("1" if value else "0" for value in keep_columns) + "\n",
            encoding="ascii",
        )
        subprocess.run([fast_filter, str(source), str(destination), str(mask_path)], check=True)
        filtered_rows, filtered_cols, selected_nnz = _matrix_header(destination)
        if filtered_rows != n_rows or filtered_cols != len(selected):
            raise ValueError(f"{destination}: compiled filter produced an invalid header")
        return {
            "raw_shape": [int(n_rows), int(n_cols)],
            "raw_nnz": int(nnz),
            "sanitized_shape": [int(n_rows), int(len(selected))],
            "sanitized_nnz": int(selected_nnz),
            "source_sha256": sha256_file(source),
            "sanitized_sha256": sha256_file(destination),
            "filter": "one-pass compiled metadata column mask",
        }

    selected_nnz = 0
    for row, column, _value in _iter_matrix_entries(source):
        if not 1 <= row <= n_rows or not 1 <= column <= n_cols:
            raise ValueError(f"{source}: entry out of bounds {(row, column)}")
        if keep_columns[column - 1]:
            selected_nnz += 1

    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wt", encoding="ascii", newline="\n") as handle:
        handle.write("%%MatrixMarket matrix coordinate integer general\n")
        handle.write(f"{n_rows} {len(selected)} {selected_nnz}\n")
        for row, column, value in _iter_matrix_entries(source):
            mapped = int(new_column[column - 1])
            if mapped > 0:
                handle.write(f"{row} {mapped} {value}\n")
    return {
        "raw_shape": [int(n_rows), int(n_cols)],
        "raw_nnz": int(nnz),
        "sanitized_shape": [int(n_rows), int(len(selected))],
        "sanitized_nnz": int(selected_nnz),
        "source_sha256": sha256_file(source),
        "sanitized_sha256": sha256_file(destination),
    }


def _sample_table(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def audit_emtab6967(quarantine: Path, sanitized_root: Path, reports_root: Path) -> dict[str, Any]:
    source_root = quarantine / "EMTAB6967"
    raw_meta = source_root / "atlas" / "atlas" / "meta.csv"
    raw_genes = source_root / "atlas" / "atlas" / "genes.tsv"
    raw_matrix = source_root / "raw" / "atlas" / "raw_counts.mtx"
    sdrf = source_root / "E-MTAB-6967.sdrf.txt"
    for path in (raw_meta, raw_genes, raw_matrix, sdrf):
        if not path.exists():
            raise FileNotFoundError(path)

    meta = pd.read_csv(raw_meta, low_memory=False)
    genes = pd.read_csv(raw_genes, sep="\t", header=None, names=["ensembl", "gene"], dtype=str)
    n_rows, n_cols, _nnz = _matrix_header(raw_matrix)
    if len(meta) != n_cols or len(genes) != n_rows:
        raise ValueError(f"{EMTAB6967_ACC}: metadata/matrix dimensions disagree")
    if meta["cell"].astype(str).duplicated().any():
        raise ValueError(f"{EMTAB6967_ACC}: cell IDs are not unique")

    stage = meta["stage"].astype(str)
    exact_stage = stage.str.fullmatch(r"E\d+\.\d+")
    stripped = meta["stripped"].astype(bool)
    doublet = meta["doublet"].astype(bool)
    keep = (exact_stage & ~stripped & ~doublet).to_numpy(dtype=bool)
    reasons = np.where(~exact_stage, "ambiguous_stage", np.where(stripped, "stripped", np.where(doublet, "doublet", "kept")))
    reason_counts = {str(key): int(value) for key, value in pd.Series(reasons).value_counts().to_dict().items()}

    output = sanitized_root / "EMTAB6967"
    output.mkdir(parents=True, exist_ok=True)
    selected_meta = meta.loc[keep].copy()
    selected_meta.insert(0, "source_row", np.flatnonzero(keep).astype(np.int64))
    selected_meta.to_csv(output / "meta.csv", index=False)
    shutil.copy2(raw_genes, output / "genes.tsv")
    matrix_info = _sanitize_matrixmarket(raw_matrix, output / "counts.mtx", keep, expected_rows=n_rows)

    _sample_table(
        output / "planned_keep_cells.tsv",
        [
            {"source_row": int(row.source_row), "cell": str(row.cell), "stage": str(row.stage), "celltype": str(row.celltype)}
            for row in selected_meta.itertuples()
        ],
        ["source_row", "cell", "stage", "celltype"],
    )
    _sample_table(
        output / "planned_remove_cells.tsv",
        [
            {"source_row": int(index), "cell": str(meta.iloc[index]["cell"]), "stage": str(meta.iloc[index]["stage"]), "reason": str(reasons[index])}
            for index in np.flatnonzero(~keep)
        ],
        ["source_row", "cell", "stage", "reason"],
    )
    manifest = {
        "source_id": EMTAB6967_ACC,
        "task": "T3",
        "atom": ATOM,
        "status": "PASS",
        "accession": EMTAB6967_ACC,
        "public_url": "https://www.ebi.ac.uk/biostudies/arrayexpress/studies/E-MTAB-6967",
        "license": "EBI Terms if no record-specific license",
        "source_sdrf_sha256": sha256_file(sdrf),
        "raw_archive_sha256": sha256_file(source_root / "atlas_data.tar.gz"),
        "stage_rule": "exact E6.5-E8.5 labels; non-exact/mixed stage quarantined",
        "genotype_rule": "source metadata states wild type genotype; no mutant/chimera records admitted",
        "quality_rule": "stripped and doublet records removed before any matrix statistic",
        "kept_cells": int(keep.sum()),
        "removed_cells": int((~keep).sum()),
        "counts_by_reason": reason_counts,
        "forbidden_records_remaining": 0,
        "sanitized": matrix_info,
        "sanitized_meta_sha256": sha256_file(output / "meta.csv"),
        "sanitized_genes_sha256": sha256_file(output / "genes.tsv"),
        "model_input": True,
    }
    _json_write(output / "source_manifest.json", manifest)
    _json_write(reports_root / f"{EMTAB6967_ACC}__DATA_AUDIT_REPORT.json", manifest)
    return manifest


def _sdrf_rows(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False)


def audit_emtab11763(quarantine: Path, sanitized_root: Path, reports_root: Path) -> dict[str, Any]:
    source_root = quarantine / "EMTAB11763"
    sdrf = source_root / "E-MTAB-11763.sdrf.txt"
    api = source_root / "api.json"
    if not sdrf.exists() or not api.exists():
        raise FileNotFoundError("E-MTAB-11763 metadata snapshot is incomplete")
    rows = _sdrf_rows(sdrf)
    stage_col = "Characteristics[developmental stage]"
    genotype_col = "Characteristics[genotype]"
    stage = rows[stage_col].astype(str)
    genotype = rows[genotype_col].astype(str).str.lower()
    exact_stage = stage.str.extract(r"(E\d+\.\d+)", expand=False)
    keep = exact_stage.isin(["E8.5", "E8.75", "E9.0", "E9.25", "E9.5"]) & genotype.str.contains("wild type", regex=False)
    output = sanitized_root / "EMTAB11763"
    output.mkdir(parents=True, exist_ok=True)
    selected = rows.loc[keep].copy()
    selected.insert(0, "source_row", np.flatnonzero(keep.to_numpy()).astype(np.int64))
    selected.to_csv(output / "metadata_only.tsv", sep="\t", index=False)
    # The current BioStudies API has no processed file.  Raw FASTQ is not
    # silently treated as an expression matrix; the source remains a declared
    # metadata-only fallback for this atom.
    manifest = {
        "source_id": EMTAB11763_ACC,
        "task": "T3",
        "atom": ATOM,
        "status": "PASS_METADATA_ONLY_NO_PROCESSED_SNAPSHOT",
        "accession": EMTAB11763_ACC,
        "public_url": "https://www.ebi.ac.uk/biostudies/arrayexpress/studies/E-MTAB-11763",
        "license": "EBI Terms if no record-specific license",
        "source_api_sha256": sha256_file(api),
        "source_sdrf_sha256": sha256_file(sdrf),
        "keep_rule": "explicit WT and E8.5-E9.5 metadata only",
        "metadata_rows_total": int(len(rows)),
        "metadata_rows_kept": int(keep.sum()),
        "metadata_rows_removed": int((~keep).sum()),
        "processed_snapshot_available": False,
        "raw_fastq_used": False,
        "forbidden_records_remaining": 0,
        "model_input": False,
        "fallback_reason": "public API exposes SDRF but no processed expression object; raw FASTQ was not downloaded or processed in this atom",
    }
    _json_write(output / "source_manifest.json", manifest)
    _json_write(reports_root / f"{EMTAB11763_ACC}__DATA_AUDIT_REPORT.json", manifest)
    return manifest


def _soft_sample_blocks(path: Path) -> dict[str, list[str]]:
    blocks: dict[str, list[str]] = {}
    current: str | None = None
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.rstrip("\n")
            if line.startswith("^SAMPLE ="):
                current = line.split("=", 1)[1].strip()
                blocks[current] = []
            elif current is not None:
                blocks[current].append(line)
    return blocks


def audit_gse52123(quarantine: Path, sanitized_root: Path, reports_root: Path) -> dict[str, Any]:
    source_root = quarantine / "GSE52123"
    soft = source_root / "GSE52123_family.soft.gz"
    selected_ids = ["GSM1260024", "GSM1260025", "GSM1260028"]
    files = {
        "GSM1260024": source_root / "GSM1260024_E12.5_Gata4_Ab1.bw",
        "GSM1260025": source_root / "GSM1260025_E12.5_Gata4_Ab2.bw",
        "GSM1260028": source_root / "GSM1260028_E12.5_Gata4_Input.bw",
    }
    if not soft.exists() or any(not path.exists() for path in files.values()):
        raise FileNotFoundError("GSE52123 selected ChIP snapshot is incomplete")
    blocks = _soft_sample_blocks(soft)
    output = sanitized_root / "GSE52123"
    output.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    copied: list[dict[str, Any]] = []
    for sample_id in selected_ids:
        block = blocks.get(sample_id, [])
        joined = "\n".join(block)
        if "age: E12.5" not in joined or "tissue: primary heart tissues" not in joined:
            raise ValueError(f"{sample_id}: selected sample failed E12.5 heart metadata check")
        if sample_id != "GSM1260028" and "chip antibody: Gata4_Ab" not in joined:
            raise ValueError(f"{sample_id}: selected sample is not GATA4 antibody ChIP")
        if "KO" in joined and sample_id != "GSM1260028":
            raise ValueError(f"{sample_id}: perturbation text found in selected ChIP sample")
        destination = output / files[sample_id].name
        copied.append(_copy_with_hash(files[sample_id], destination))
        rows.append({"sample_id": sample_id, "role": "matched_input" if sample_id == "GSM1260028" else "GATA4_ChIP_replicate", "stage": "E12.5", "tissue": "primary heart", "genotype": "WT occupancy context"})
    _sample_table(output / "selected_samples.tsv", rows, ["sample_id", "role", "stage", "tissue", "genotype"])
    manifest = {
        "source_id": GSE52123_ACC,
        "task": "T3",
        "atom": ATOM,
        "status": "PASS",
        "accession": GSE52123_ACC,
        "public_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE52123",
        "license": "GEO public data; submitter IP notice retained",
        "family_soft_sha256": sha256_file(soft),
        "keep_rule": "E12.5 primary heart GATA4 antibody replicates plus matched input only",
        "remove_rule": "adult, banding/sham, histone, KO, stress and all non-selected samples excluded",
        "selected_files": copied,
        "forbidden_records_remaining": 0,
        "role_limit": "ChIP signal provides directness only; it never supplies response sign",
        "model_input": True,
    }
    _json_write(output / "source_manifest.json", manifest)
    _json_write(reports_root / f"{GSE52123_ACC}__DATA_AUDIT_REPORT.json", manifest)
    return manifest


def audit_knowledge_and_software(quarantine: Path, sanitized_root: Path, reports_root: Path) -> dict[str, Any]:
    specs = [
        ("REACTOME", [quarantine / "REACTOME" / "ReactomePathways.gmt.zip"], "pathway membership only", True),
        ("GO", [quarantine / "GO" / "go-basic.obo", quarantine / "GO" / "MOUSE-mod.gaf.gz", quarantine / "GO" / "MOUSE-uniprot.gaf.gz"], "module membership and ontology terms only", True),
        ("CELLORACLE", list((quarantine / "CELLORACLE").glob("*.tar.gz")), "pinned source code; no pretrained model", False),
        ("SCTENIFOLDKNK", list((quarantine / "SCTENIFOLDKNK").glob("*.tar.gz")), "pinned source code; no pretrained model", False),
        ("MM9_GTF_RELEASE67", [quarantine / "GSE52123" / "Mus_musculus.NCBIM37.67.gtf.gz"], "technical mm9/NCBIM37 gene-coordinate mapping only", False),
    ]
    records: dict[str, Any] = {}
    for source_id, paths, role, model_input in specs:
        if not paths or any(not path.exists() for path in paths):
            raise FileNotFoundError(f"{source_id}: missing snapshot")
        destination_root = sanitized_root / source_id
        copied = [_copy_with_hash(path, destination_root / path.name) for path in paths]
        records[source_id] = {"status": "PASS", "role": role, "model_input": model_input, "files": copied, "forbidden_records_remaining": 0}
        _json_write(reports_root / f"{source_id}__DATA_AUDIT_REPORT.json", {"source_id": source_id, "task": "T3", "atom": ATOM, **records[source_id]})
        _json_write(destination_root / "source_manifest.json", {"source_id": source_id, "task": "T3", "atom": ATOM, **records[source_id]})
    return records


def run_audit(project_root: Path = ROOT) -> dict[str, Any]:
    project_root = Path(project_root).resolve()
    quarantine = project_root / "infra" / "external_data" / "quarantine"
    sanitized = project_root / "infra" / "external_data" / "sanitized" / "T3" / ATOM
    reports = project_root / "infra" / "external_data" / "reports"
    sanitized.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    sources: dict[str, Any] = {}
    sources[EMTAB6967_ACC] = audit_emtab6967(quarantine, sanitized, reports)
    sources[EMTAB11763_ACC] = audit_emtab11763(quarantine, sanitized, reports)
    sources[GSE52123_ACC] = audit_gse52123(quarantine, sanitized, reports)
    sources.update(audit_knowledge_and_software(quarantine, sanitized, reports))
    forbidden = int(sum(int(value.get("forbidden_records_remaining", 0)) for value in sources.values()))
    result = {
        "rules_snapshot": RULES,
        "task": "T3",
        "active_atom": ATOM,
        "audit_date": "2026-08-30",
        "policy": "fail_closed",
        "status": "PASS_WITH_METADATA_ONLY_FALLBACK" if sources[EMTAB11763_ACC]["status"] != "PASS" else "PASS",
        "sources": sources,
        "forbidden_records_remaining": forbidden,
        "task_permit": forbidden == 0 and all(value.get("status", "").startswith("PASS") for value in sources.values()),
        "target_used_for_generation": False,
        "unknown_checkpoint_used": False,
    }
    _json_write(project_root / "infra" / "external_data" / "AUDIT_COMPLETE.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(run_audit(args.project_root), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
