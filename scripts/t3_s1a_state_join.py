#!/usr/bin/env python3
"""Run the bounded T3-S1A state-joined prior/gate computation.

This module is deliberately a prior/gate runner, not a candidate generator.
It accepts a raw-count AnnData view that has already been restricted to the
exact E8.75 WT records by the metadata-first firewall.  CellOracle is called
through its installed API.  scTenifoldKnk is called through R and its output
is retained as unsigned network-rank evidence; it never supplies a causal
sign in this adapter.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import multiprocessing as mp
import os
import re
import resource
import subprocess
import sys
import tarfile
import time
import traceback
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.io import mmwrite
from sklearn.decomposition import TruncatedSVD

ROOT = Path(__file__).resolve().parents[1]
ATOM = "T3-S1A-STATE-JOIN-20260901-v7"
OUTPUT_DEFAULT = ROOT / "artifacts" / "tool_integration" / ATOM
ARCHIVE_DEFAULT = ROOT / "infra/external_data/quarantine/T3-S1A-STATE-JOIN/ExtendedMouseAtlas/ExtendedMouseAtlas.tar.gz"
METADATA_DEFAULT = ROOT / "infra/external_data/quarantine/T3-S1A-STATE-JOIN/ExtendedMouseAtlas/metadata_cells.csv"
SOURCE_H5AD_DEFAULT = ROOT / "infra/external_data/quarantine/T3-S1A-STATE-JOIN/ExtendedMouseAtlas/embryo_complete.h5ad"
PANEL_PATH = ROOT / "data/gene_panel/T3__gata4.genes.txt"
PANEL_ALIAS_MANIFEST = ROOT / "infra/external_data/manifests/T3-S1A-STATE-JOIN/panel_gene_aliases.json"
CELLORACLE_GRN_DIR = ROOT / "infra/external_data/sanitized/T3-S1A-STATE-JOIN/CELLORACLE/promoter_base_GRN"
CELLORACLE_GRN_FILE = CELLORACLE_GRN_DIR / "mm10_TFinfo_dataframe_gimmemotifsv5_fpr2_threshold_10_20210630.parquet"
CELLORACLE_GRN_SHA256 = "32de319419199f53bbdbf7c8545394a70052c7d14918d59b54c96593000dea40"
PARENT_PATH = ROOT / "data/E8.75.h5ad"
COLLECTRI_DIR = ROOT / "infra/external_data/sanitized/T3-S1A-STATE-JOIN/COLLECTRI"
OMNIPATH_DIR = ROOT / "infra/external_data/sanitized/T3-S1A-STATE-JOIN/OMNIPATH"
OLD_RLIB = ROOT / ".venvs/ve-t3-prior/Rlib"
NEW_RLIB = OUTPUT_DEFAULT / "deployment/Rlib"
USER_RLIB = Path("/home/huyudi/R/x86_64-pc-linux-gnu-library/4.5")
SEED = 20260830
EXACT_STAGE = "E8.75"
EXPECTED_MD5 = "442645308463a64c3bb947c25921199e"
CELLORACLE_TARGET_TIMEOUT_MINUTES = 60
CELLORACLE_TARGET_CHECK_INTERVAL_SECONDS = 60
CELLORACLE_TARGET_START_METHOD = "fork"

ROUTES = (
    "GATA4_GATA6_VALIDATION_E875::L1_STRICT_AGREEMENT",
    "GATA4_GATA6_VALIDATION_E875::L2_CONDITION_AWARE",
    "BETA_CATENIN_HIDDEN_E875::L1_STRICT_AGREEMENT",
    "BETA_CATENIN_HIDDEN_E875::L2_CONDITION_AWARE",
)
CONDITIONS = {
    "GATA4_GATA6_VALIDATION_E875": {"targets": ("Gata4", "Gata6")},
    "BETA_CATENIN_HIDDEN_E875": {"targets": ("Ctnnb1",)},
}
POSITIVE_MARKERS = (
    "Mesp1", "T", "Mixl1", "Pdgfra", "Kdr", "Foxf1", "Tbx5", "Nkx2-5",
    "Mef2c", "Hand1", "Hand2", "Isl1", "Gata4", "Gata6", "Tbx20", "Myocd",
)
NEGATIVE_MARKERS = (
    "Sox2", "Sox3", "Pou5f1", "Foxa2", "Sox17", "Krt8", "Krt18", "Krt19",
    "Epcam", "Otx2",
)
BLACKLIST_RE = re.compile(
    r"(?:\b(?:ko|knockout|kd|knockdown|oe|overexpression|overexpressed|mutant|"
    r"chimera|crispr|drug|perturb|treated|treatment)\b|gata4|gata6|ctnnb1|"
    r"beta.?catenin|mesp1|canonical\s*wnt|\b(?:apc|axin1|axin2|gsk3a|gsk3b|"
    r"dvl1|dvl2|dvl3|lrp5|lrp6|tcf7l1|tcf7l2|lef1)\b)",
    re.IGNORECASE,
)
REQUIRED_VOTE_FIELDS = (
    "target_gene", "condition_id", "stage", "state", "response_gene",
    "sign", "rank_score", "confidence", "evidence_family", "dosage_fraction",
    "directness_score", "lineage_gate", "provenance", "conflict_flag",
)
STATE_GATE_FIELDS = (
    "condition_id", "stage", "state", "lineage_gate", "p_mesp1_lineage",
    "gate_pass", "state_join_status", "state_sample_n", "activity_gate_pass",
    "target_gene", "target_expression", "tf_activity",
    "pathway_activity", "activity_evidence_status", "matched_external_state",
    "match_similarity", "external_n", "provenance",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def md5_file(path: Path) -> str:
    digest = hashlib.md5()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_official_md5_manifest(manifest_path: Path, archive: Path) -> dict[str, Any]:
    if not manifest_path.is_file():
        raise FileNotFoundError(f"official MD5 manifest is missing: {manifest_path}")
    entries = [line.split() for line in manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(entries) != 1 or len(entries[0]) != 2:
        raise ValueError(f"official MD5 manifest is not a single checksum entry: {manifest_path}")
    expected, filename = entries[0]
    if filename != archive.name or expected.lower() != EXPECTED_MD5:
        raise ValueError(f"official MD5 manifest disagrees with locked archive: {entries[0]}")
    return {
        "path": str(manifest_path),
        "sha256": sha256_file(manifest_path),
        "filename": filename,
        "md5": expected.lower(),
    }


def json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def write_tsv(path: Path, rows: Iterable[Mapping[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _write_tsv_atomic(path: Path, rows: Iterable[Mapping[str, Any]], fields: list[str]) -> None:
    """Publish one target output only after the complete file is written."""
    if path.exists():
        raise FileExistsError(f"refusing to overwrite target output: {path}")
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        write_tsv(temporary, rows, fields)
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _write_json_atomic(path: Path, value: Any) -> None:
    """Publish a checkpoint atomically so interruption cannot create a false PASS."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        temporary.write_text(
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def panel_genes() -> list[str]:
    genes = [line.strip() for line in PANEL_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(genes) != 500 or len(set(genes)) != 500:
        raise ValueError("T3 panel must contain 500 unique genes")
    return genes


def verify_source_wt_attestation(evidence_path: Path) -> dict[str, Any]:
    """Verify the captured official method text before using source-level WT."""
    if not evidence_path.is_file():
        raise FileNotFoundError(f"WT attestation source is missing: {evidence_path}")
    text = evidence_path.read_text(encoding="utf-8", errors="replace")
    phrase = "Following wild-type C57BL/6 matings"
    if phrase not in text:
        raise ValueError(f"WT attestation phrase is absent from {evidence_path}")
    return {
        "path": str(evidence_path),
        "sha256": sha256_file(evidence_path),
        "matched_phrase": phrase,
        "source_scope": "E8.5-E9.5 embryo collection for the extended atlas",
    }


def extract_outer_metadata(
    archive: Path,
    destination: Path,
    *,
    include_source_h5ad: bool = False,
) -> dict[str, Any]:
    """Extract auditable metadata/raw members, optionally the official source H5AD.

    The H5AD is an upstream input artifact, not a generated candidate.  It is
    extracted only for the execution path that consumes its documented
    ``.raw`` count layer; metadata-only inspection does not copy it.
    """
    destination.mkdir(parents=True, exist_ok=True)
    wanted = {
        "ExtendedMouseAtlas/metadata_cells.csv": "metadata_cells.csv",
        "ExtendedMouseAtlas/metadata_genes.csv": "metadata_genes.csv",
        "ExtendedMouseAtlas/embryo_counts.tar.gz": "embryo_counts.tar.gz",
        "ExtendedMouseAtlas/Readme.md": "Readme.md",
        "ExtendedMouseAtlas/desc.conf": "desc.conf",
    }
    if include_source_h5ad:
        wanted["ExtendedMouseAtlas/embryo_complete.h5ad"] = "embryo_complete.h5ad"
    extracted: dict[str, Any] = {}
    with tarfile.open(archive, "r:gz") as handle:
        for member in handle:
            name = member.name.lstrip("./")
            if name not in wanted:
                continue
            if not member.isfile():
                raise ValueError(f"outer archive member is not a regular file: {name}")
            target = (destination / wanted[name]).resolve()
            if destination.resolve() not in target.parents:
                raise ValueError("archive member escaped extraction directory")
            source = handle.extractfile(member)
            if source is None:
                raise ValueError(f"cannot read archive member: {name}")
            digest = hashlib.sha256()
            byte_count = 0
            if target.exists():
                # Quarantine inputs are immutable provenance artifacts.  Do
                # not overwrite a cached member; prove byte identity instead.
                while True:
                    block = source.read(1024 * 1024)
                    if not block:
                        break
                    digest.update(block)
                    byte_count += len(block)
                if target.stat().st_size != byte_count or sha256_file(target) != digest.hexdigest():
                    raise ValueError(f"cached archive member differs from official archive: {target}")
            else:
                with target.open("wb") as out:
                    while True:
                        block = source.read(1024 * 1024)
                        if not block:
                            break
                        digest.update(block)
                        byte_count += len(block)
                        out.write(block)
            extracted[name] = {
                "path": str(target),
                "bytes": byte_count,
                "sha256": digest.hexdigest(),
            }
    missing = sorted(set(wanted) - set(extracted))
    if missing:
        raise ValueError(f"outer archive missing required members: {missing}")
    return extracted


def _norm_column(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def _choose_column(columns: Iterable[str], candidates: Iterable[str]) -> str | None:
    normalised = {_norm_column(col): str(col) for col in columns}
    for candidate in candidates:
        if _norm_column(candidate) in normalised:
            return normalised[_norm_column(candidate)]
    return None


def _text_columns(frame: pd.DataFrame) -> list[str]:
    names = []
    for col in frame.columns:
        token = _norm_column(col)
        if any(key in token for key in ("genotype", "condition", "perturb", "treatment", "disease", "intervention")):
            names.append(str(col))
    return names


def exact_stage_and_firewall(
    metadata: pd.DataFrame,
    *,
    source_wt_attested: bool = False,
    wt_evidence: str = "",
) -> tuple[pd.Series, dict[str, Any]]:
    stage_col = _choose_column(
        metadata.columns,
        ("stage", "embryonic_stage", "embryonic_day", "developmental_stage", "timepoint"),
    )
    if stage_col is None:
        raise ValueError("metadata has no auditable stage column")
    stage_text = metadata[stage_col].fillna("").astype(str).str.strip()
    exact_mask = stage_text.str.fullmatch(r"(?i)E?8\.75")
    ambiguous = stage_text.str.contains(r"(?i)8\.75.*[-/]|[-/]\s*8\.75|8\.5\s*[-/]\s*9", regex=True, na=False)

    condition_columns = _text_columns(metadata)
    wt_attestation = {
        "used": bool(source_wt_attested),
        "evidence": wt_evidence,
        "basis": "official publication method states wild-type C57BL/6 matings",
    }
    if not condition_columns and not source_wt_attested:
        raise ValueError("metadata has no genotype/condition column; WT status is not auditable")
    if condition_columns:
        condition_text = metadata[condition_columns].fillna("").astype(str).agg(" | ".join, axis=1)
        forbidden = condition_text.str.contains(BLACKLIST_RE, na=False)
        condition_missing = condition_text.str.strip().str.casefold().isin(
            {"", "na", "n/a", "nan", "none", "null"}
        )
        wt_tokens = condition_text.str.contains(
            r"(?i)(?:wild.?type|\bWT\b|control|normal|untreated|vehicle)",
            regex=True,
        ) & ~condition_missing
        # Empty/NA condition values are not explicit WT evidence.  If the
        # official source attestation is present and the column is entirely
        # non-informative, retain source-level WT scope without relabelling
        # each row as a per-cell WT observation.
        if source_wt_attested and not bool(wt_tokens.any()) and not bool(forbidden.any()):
            condition_auditable = pd.Series(True, index=metadata.index)
            wt_status = "PASS_SOURCE_ATTESTED" if bool(exact_mask.any()) else "BLOCKED"
            condition_audit_mode = "source_attestation_noninformative_condition_column"
        else:
            condition_auditable = wt_tokens & ~forbidden
            wt_status = "PASS" if bool(condition_auditable.any()) else "BLOCKED"
            condition_audit_mode = "per_row_condition"
        mask_definition = "exact E8.75; no ambiguous interval; explicit WT/control/untreated condition; target/phenocopy blacklist excluded"
        condition_not_auditable_rows = int((~condition_auditable).sum())
        forbidden_remaining = None
    else:
        # The Extended Mouse Atlas has a source-level WT method attestation but
        # may omit a per-cell genotype column.  Do not manufacture a WT token
        # in metadata; retain the distinction in the audit report.
        forbidden = pd.Series(False, index=metadata.index)
        condition_auditable = pd.Series(bool(source_wt_attested), index=metadata.index)
        wt_status = "PASS_SOURCE_ATTESTED" if source_wt_attested and bool(exact_mask.any()) else "BLOCKED"
        mask_definition = "exact E8.75; no ambiguous interval; WT source attestation; no per-cell condition column"
        condition_audit_mode = "source_attestation_no_per_cell_condition"
        condition_not_auditable_rows = int(len(metadata))
        forbidden_remaining = None
    keep = exact_mask & ~ambiguous & condition_auditable
    if condition_columns:
        forbidden_remaining = int((keep & forbidden).sum())
    report = {
        "stage_column": stage_col,
        "condition_columns": condition_columns,
        "requested_stage": EXACT_STAGE,
        "rows_total": int(len(metadata)),
        "exact_stage_rows": int(exact_mask.sum()),
        "ambiguous_stage_rows": int((exact_mask & ambiguous).sum()),
        "condition_forbidden_rows": int(forbidden.sum()),
        "condition_audit_mode": condition_audit_mode,
        "condition_not_auditable_rows": condition_not_auditable_rows,
        "kept_rows": int(keep.sum()),
        "removed_rows": int((~keep).sum()),
        "forbidden_records_remaining": forbidden_remaining,
        "blacklist_scan_status": "PASS_PER_ROW_CONDITION" if condition_columns else "NOT_APPLICABLE_NO_PER_CELL_CONDITION",
        "wt_status": wt_status if bool(keep.any()) and not bool((keep & forbidden).any()) else "BLOCKED",
        "wt_attestation": wt_attestation,
        "mask_definition": mask_definition,
    }
    if report["wt_status"] not in {"PASS", "PASS_SOURCE_ATTESTED"}:
        raise ValueError(f"metadata firewall did not produce an auditable WT view: {report}")
    return keep, report


def _align_metadata(adata: ad.AnnData, metadata: pd.DataFrame) -> pd.DataFrame:
    candidates = [
        _choose_column(metadata.columns, ("cell_id", "cell", "cellid", "barcode", "cellbarcode", "obs_name")),
    ]
    identifier = next((value for value in candidates if value is not None), None)
    if identifier is None:
        raise ValueError("metadata has no cell identifier column")
    lookup = metadata.copy()
    lookup[identifier] = lookup[identifier].astype(str)
    if lookup[identifier].duplicated().any():
        raise ValueError("metadata cell identifier is not unique")
    obs = pd.DataFrame(index=adata.obs_names.astype(str))
    expected_ids = set(lookup[identifier].astype(str))
    obs[identifier] = obs.index
    if set(obs[identifier]) != expected_ids:
        # The official Extended Mouse Atlas stores numeric AnnData
        # obs_names but keeps the stable ``cell_*`` identifier in an obs
        # column.  Accept that alternate key only after exact set equality;
        # never use a positional or partial join.
        matched_obs_column = None
        for column in adata.obs.columns:
            values = adata.obs[column].astype(str)
            if values.is_unique and set(values) == expected_ids:
                matched_obs_column = str(column)
                obs[identifier] = values.to_numpy()
                break
        if matched_obs_column is None:
            metadata_only = sorted(expected_ids - set(obs[identifier].astype(str)))[:5]
            adata_only = sorted(set(obs[identifier].astype(str)) - expected_ids)[:5]
            raise ValueError(
                "metadata and AnnData cell identifiers do not align exactly: "
                f"metadata_only={metadata_only}, adata_only={adata_only}"
            )
    aligned = obs.merge(lookup, on=identifier, how="left", sort=False, validate="one_to_one")
    if aligned[identifier].isna().any():
        raise ValueError("metadata and AnnData cell identifiers do not align exactly")
    matched_ids = set(aligned[identifier].astype(str))
    if matched_ids != expected_ids:
        metadata_only = sorted(expected_ids - matched_ids)[:5]
        adata_only = sorted(matched_ids - expected_ids)[:5]
        raise ValueError(
            "metadata and AnnData cell identifiers do not align exactly: "
            f"metadata_only={metadata_only}, adata_only={adata_only}"
        )
    aligned.index = adata.obs_names
    return aligned


def _apply_panel_alias_manifest(
    resolved_symbols: list[str],
    var_names: list[str],
    genes: pd.DataFrame,
    identifier_col: str | None,
    symbol_col: str,
    panel: set[str],
    manifest_path: Path,
) -> tuple[list[str], dict[str, Any]]:
    """Apply only cached, exact-ID aliases needed to close the 500-gene panel."""
    if not manifest_path.is_file():
        raise FileNotFoundError(f"panel alias manifest is missing: {manifest_path}")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if payload.get("schema") != "ve.t3.s1a-panel-alias-manifest.v1":
        raise ValueError("panel alias manifest schema mismatch")
    if payload.get("task") != "T3-S1A-STATE-JOIN":
        raise ValueError("panel alias manifest task mismatch")
    if payload.get("panel_path") != "data/gene_panel/T3__gata4.genes.txt":
        raise ValueError("panel alias manifest panel path mismatch")
    if payload.get("panel_sha256") != sha256_file(PANEL_PATH):
        raise ValueError("panel alias manifest does not bind the active panel hash")
    if identifier_col is None:
        raise ValueError("panel alias manifest requires an Ensembl/gene identifier column")
    declared_metadata = payload.get("source_gene_metadata_path")
    expected_metadata = (ROOT / str(declared_metadata)).resolve()
    if expected_metadata != Path(genes.attrs.get("source_path", "")).resolve():
        raise ValueError("panel alias manifest source metadata path mismatch")
    if payload.get("source_gene_metadata_sha256") != sha256_file(expected_metadata):
        raise ValueError("panel alias manifest does not bind the source gene metadata hash")

    identifiers = genes[identifier_col].astype(str).tolist()
    symbols = genes[symbol_col].astype(str).tolist()
    id_to_symbol: dict[str, str] = {}
    for identifier, symbol in zip(identifiers, symbols):
        if identifier in id_to_symbol and id_to_symbol[identifier] != symbol:
            raise ValueError(f"source gene metadata has conflicting symbols for {identifier}")
        id_to_symbol[identifier] = symbol

    entries = payload.get("mappings")
    if not isinstance(entries, list) or not entries:
        raise ValueError("panel alias manifest has no mappings")
    by_panel: dict[str, Mapping[str, Any]] = {}
    by_id: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise ValueError("panel alias manifest contains a malformed mapping")
        panel_symbol = str(entry.get("panel_symbol", ""))
        ensembl_id = str(entry.get("ensembl_id", ""))
        dataset_symbol = str(entry.get("dataset_symbol", ""))
        source_cache_path = Path(str(entry.get("source_cache_path", "")))
        if panel_symbol not in panel or not ensembl_id or not dataset_symbol:
            raise ValueError("panel alias manifest contains an out-of-panel or incomplete mapping")
        if panel_symbol in by_panel or ensembl_id in by_id:
            raise ValueError("panel alias manifest contains duplicate panel symbols or IDs")
        if ensembl_id not in var_names:
            raise ValueError(f"panel alias Ensembl ID is absent from the official input: {ensembl_id}")
        if id_to_symbol.get(ensembl_id) != dataset_symbol:
            raise ValueError(
                f"panel alias metadata mismatch for {panel_symbol}: "
                f"expected {dataset_symbol!r}, got {id_to_symbol.get(ensembl_id)!r}"
            )
        if not str(entry.get("source_url", "")):
            raise ValueError(f"panel alias has no authoritative source URL: {panel_symbol}")
        if not source_cache_path.is_absolute():
            source_cache_path = ROOT / source_cache_path
        try:
            source_cache_path.resolve().relative_to(ROOT.resolve())
        except ValueError as exc:
            raise ValueError(f"panel alias source cache is outside repository: {source_cache_path}") from exc
        if not source_cache_path.is_file():
            raise FileNotFoundError(f"panel alias source cache is missing: {source_cache_path}")
        if str(entry.get("source_cache_sha256", "")) != sha256_file(source_cache_path):
            raise ValueError(f"panel alias source cache hash mismatch: {source_cache_path}")
        source_text = source_cache_path.read_text(encoding="utf-8", errors="replace").lower()
        if panel_symbol.lower() not in source_text or dataset_symbol.lower() not in source_text:
            raise ValueError(f"panel alias source does not contain both names: {panel_symbol}")
        by_panel[panel_symbol] = entry
        by_id[ensembl_id] = panel_symbol

    missing = sorted(panel - set(resolved_symbols))
    if set(by_panel) != set(missing):
        raise ValueError(
            "panel alias manifest does not exactly cover unresolved panel symbols: "
            f"missing={missing}, declared={sorted(by_panel)}"
        )
    output = list(resolved_symbols)
    index_by_id = {identifier: index for index, identifier in enumerate(var_names)}
    for panel_symbol, entry in by_panel.items():
        index = index_by_id[str(entry["ensembl_id"])]
        if output[index] in panel and output[index] != panel_symbol:
            raise ValueError(f"panel alias would overwrite a different panel symbol: {panel_symbol}")
        output[index] = panel_symbol
    if len(set(output)) != len(output):
        raise ValueError("panel alias application creates duplicate gene identifiers")
    return output, {
        "mode": "official_mgi_alias_manifest",
        "manifest_path": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "mappings": [
            {
                "panel_symbol": str(entry["panel_symbol"]),
                "ensembl_id": str(entry["ensembl_id"]),
                "dataset_symbol": str(entry["dataset_symbol"]),
                "authoritative_source": str(entry["authoritative_source"]),
                "source_url": str(entry["source_url"]),
            }
            for entry in sorted(by_panel.values(), key=lambda item: str(item["panel_symbol"]))
        ],
    }


def _resolve_gene_symbols(
    var_names: list[str],
    gene_metadata_csv: Path | None,
    *,
    alias_manifest_path: Path | None = None,
) -> tuple[list[str], dict[str, Any]]:
    """Resolve official gene IDs to symbols without accepting partial maps."""
    if len(set(var_names)) != len(var_names):
        raise ValueError("input AnnData gene identifiers are not unique")
    panel = set(panel_genes())
    panel_overlap = len(set(var_names).intersection(panel))
    if panel_overlap >= 450:
        return var_names, {"mode": "identity", "panel_overlap": panel_overlap}
    if gene_metadata_csv is None or not gene_metadata_csv.is_file():
        return var_names, {"mode": "unresolved", "panel_overlap": panel_overlap}
    genes = pd.read_csv(gene_metadata_csv, dtype=str, keep_default_na=False)
    symbol_col = _choose_column(
        genes.columns,
        ("gene_short_name", "gene_symbol", "gene_symbols", "symbol", "gene_name", "gene", "mgi_symbol"),
    )
    if symbol_col is None:
        raise ValueError("gene metadata has no gene-symbol column")
    identifier_columns = [
        column for column in (
            _choose_column(genes.columns, ("ensembl_id", "ensembl", "gene_id", "geneid", "id")),
            symbol_col,
        ) if column is not None
    ]
    metadata_identifier_col = _choose_column(
        genes.columns, ("ensembl_id", "ensembl", "gene_id", "geneid", "id")
    )
    genes.attrs["source_path"] = str(gene_metadata_csv)
    candidates: list[tuple[str, list[str]]] = []
    for candidate_identifier_col in identifier_columns:
        identifiers = genes[candidate_identifier_col].astype(str).tolist()
        symbols = genes[symbol_col].astype(str).tolist()
        if len(identifiers) == len(var_names) and identifiers == var_names:
            symbol_counts = pd.Series(symbols).value_counts()
            resolved_symbols: list[str] = []
            used_symbols: set[str] = set()
            for identifier, symbol in zip(identifiers, symbols):
                # Official gene annotations can contain repeated MGI symbols
                # for distinct Ensembl records.  Keep unique symbols where
                # possible and retain the stable ID for non-panel duplicates;
                # silently creating duplicate AnnData var names would make
                # downstream state joins ambiguous.
                if (
                    symbol
                    and int(symbol_counts.get(symbol, 0)) == 1
                    and symbol not in used_symbols
                ) or (symbol in panel and symbol not in used_symbols):
                    resolved = symbol
                else:
                    resolved = identifier
                resolved_symbols.append(resolved)
                used_symbols.add(resolved)
            candidates.append((f"row_order:{candidate_identifier_col}", resolved_symbols))
            continue
        mapping: dict[str, str] = {}
        duplicate = False
        for identifier, symbol in zip(identifiers, symbols):
            if identifier in mapping and mapping[identifier] != symbol:
                duplicate = True
                break
            mapping[identifier] = symbol
        if not duplicate and all(name in mapping for name in var_names):
            mapped_symbols = [mapping[name] for name in var_names]
            symbol_counts = pd.Series(mapped_symbols).value_counts()
            resolved_symbols = []
            used_symbols = set()
            for identifier, symbol in zip(var_names, mapped_symbols):
                if (
                    symbol
                    and int(symbol_counts.get(symbol, 0)) == 1
                    and symbol not in used_symbols
                ) or (symbol in panel and symbol not in used_symbols):
                    resolved = symbol
                else:
                    resolved = identifier
                resolved_symbols.append(resolved)
                used_symbols.add(resolved)
            candidates.append((f"lookup:{candidate_identifier_col}", resolved_symbols))
    valid = [item for item in candidates if all(item[1]) and len(set(item[1])) == len(item[1])]
    if len(valid) != 1:
        raise ValueError(f"gene-symbol mapping is ambiguous or incomplete: {len(valid)} valid mappings")
    mode, symbols = valid[0]
    alias_audit: dict[str, Any] = {}
    if alias_manifest_path is not None:
        symbols, alias_audit = _apply_panel_alias_manifest(
            symbols,
            var_names,
            genes,
            metadata_identifier_col,
            symbol_col,
            panel,
            alias_manifest_path,
        )
    symbol_overlap = len(set(symbols).intersection(panel))
    if symbol_overlap < 450:
        raise ValueError(f"gene-symbol mapping leaves too few T3 panel genes: {symbol_overlap}")
    report = {
        "mode": mode,
        "panel_overlap_before": panel_overlap,
        "panel_overlap_after": symbol_overlap,
        "metadata_path": str(gene_metadata_csv),
    }
    if alias_audit:
        report["alias_manifest"] = alias_audit
    return symbols, report


def load_exact_stage_input(
    input_h5ad: Path,
    metadata_csv: Path,
    output_dir: Path,
    *,
    source_wt_attested: bool = False,
    wt_evidence: str = "",
    gene_metadata_csv: Path | None = None,
    alias_manifest_path: Path | None = None,
) -> tuple[ad.AnnData, pd.DataFrame, dict[str, Any]]:
    metadata = pd.read_csv(metadata_csv, dtype=str, keep_default_na=False)
    keep_meta, audit = exact_stage_and_firewall(
        metadata,
        source_wt_attested=source_wt_attested,
        wt_evidence=wt_evidence,
    )
    source = ad.read_h5ad(input_h5ad, backed="r")
    input_shape = list(source.shape)
    aligned = _align_metadata(source, metadata)
    stage_col = audit["stage_column"]
    # The aligned frame preserves AnnData order; use the identifier mapping to
    # transfer the metadata-first mask without relying on row order.
    id_col = _choose_column(metadata.columns, ("cell_id", "cell", "cellid", "barcode", "cellbarcode", "obs_name"))
    assert id_col is not None
    permitted_ids = set(metadata.loc[keep_meta, id_col].astype(str))
    aligned_ids = aligned[id_col].astype(str)
    keep = aligned_ids.isin(permitted_ids).to_numpy()
    if int(keep.sum()) == 0:
        raise ValueError("metadata-first mask has no cells after AnnData alignment")
    source_layer = ""
    if "counts" in source.layers:
        raw = source.layers["counts"]
        var_names = source.var_names.astype(str).tolist()
        source_layer = "counts"
    elif "raw_count" in source.layers:
        raw = source.layers["raw_count"]
        var_names = source.var_names.astype(str).tolist()
        source_layer = "raw_count"
    elif source.raw is not None:
        raw = source.raw.X
        var_names = source.raw.var_names.astype(str).tolist()
        source_layer = ".raw.X"
    else:
        raw = source.X
        if bool(source.uns.get("X_is_raw_count", False)) is not True:
            raise ValueError("input AnnData has no counts/raw_count layer and X_is_raw_count is not true")
        var_names = source.var_names.astype(str).tolist()
        source_layer = "X"
    if raw.shape[0] != source.n_obs:
        raise ValueError("raw-count matrix and AnnData cell dimensions do not agree")
    keep_indices = np.flatnonzero(keep)
    raw = raw[keep_indices]
    if sparse.issparse(raw):
        raw = raw.tocsr().astype(np.float32)
        minimum = float(raw.min()) if raw.nnz else 0.0
    else:
        raw = np.asarray(raw, dtype=np.float32)
        minimum = float(np.min(raw))
    values = raw.data if sparse.issparse(raw) else raw
    if minimum < 0 or not np.isfinite(values).all():
        raise ValueError("raw-count matrix is not finite and nonnegative")
    if values.size and not np.allclose(values, np.rint(values), atol=1e-6):
        raise ValueError("raw-count matrix contains non-integer values")
    obs = aligned.iloc[keep_indices].copy()
    state_col = _choose_column(
        obs.columns,
        ("celltype_extended_atlas", "celltype_PijuanSala2019", "celltype", "cell_type", "cluster", "state"),
    )
    if state_col is None:
        raise ValueError("metadata has no auditable cell state/celltype column")
    obs["state"] = obs[state_col].astype(str).str.strip()
    if obs["state"].eq("").any():
        raise ValueError("metadata cell state/celltype contains empty values")
    var_names, gene_mapping = _resolve_gene_symbols(
        var_names,
        gene_metadata_csv,
        alias_manifest_path=alias_manifest_path,
    )
    if raw.shape[1] != len(var_names):
        raise ValueError("raw-count matrix and gene metadata dimensions do not agree")
    exact = ad.AnnData(X=raw, obs=obs, var=pd.DataFrame(index=var_names))
    exact.uns["X_is_raw_count"] = True
    exact.uns["source_h5ad"] = str(input_h5ad)
    if getattr(source, "isbacked", False):
        source.file.close()
    output_dir.mkdir(parents=True, exist_ok=True)
    obs_output = obs.reset_index().rename(columns={"index": "cell_id"})
    write_tsv(
        output_dir / "metadata_cells_sanitized.tsv",
        obs_output.to_dict("records"),
        list(obs_output.columns),
    )
    counts_path = output_dir / "state_input_counts.mtx"
    mmwrite(counts_path, raw.T.tocoo() if sparse.issparse(raw) else sparse.coo_matrix(raw.T))
    write_tsv(
        output_dir / "state_input_genes.tsv",
        [{"gene_index": i, "gene": gene} for i, gene in enumerate(var_names)],
        ["gene_index", "gene"],
    )
    audit.update({
        "input_h5ad": str(input_h5ad),
        "input_h5ad_sha256": sha256_file(input_h5ad),
        "input_shape": input_shape,
        "sanitized_shape": list(exact.shape),
        "sanitized_counts_mtx_sha256": sha256_file(counts_path),
        "sanitized_counts_mtx_bytes": counts_path.stat().st_size,
        "state_column": state_col,
        "source_layer": source_layer,
        "gene_symbol_mapping": gene_mapping,
    })
    return exact, obs, audit


def build_snapshot_manifest(data_path: Path, source_name: str, dataset: str, repo: Path) -> Path:
    panel = panel_genes()
    panel_sha = sha256_file(PANEL_PATH)
    overlap: set[str] = set()
    rows = 0
    with data_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        expected = [
            "source", "target", "source_genesymbol", "target_genesymbol",
            "is_directed", "is_stimulation", "is_inhibition", "consensus_direction",
            "consensus_stimulation", "consensus_inhibition",
        ]
        if list(reader.fieldnames or []) != expected:
            raise ValueError(f"{data_path} schema mismatch")
        for row in reader:
            rows += 1
            for key in ("source_genesymbol", "target_genesymbol"):
                if row[key] in panel:
                    overlap.add(row[key])
    manifest = {
        "schema_version": "ve.external-knowledge-snapshot.v1",
        "source_name": source_name,
        "retrieved_at": "2026-08-31",
        "source_url": "https://omnipathdb.org/interactions",
        "source_query": {
            "datasets": dataset, "organisms": "10090", "genesymbols": "1",
            "format": "tsv", "license": "academic", "partners_source": "data/gene_panel/T3__gata4.genes.txt",
            "partners_count": len(panel), "partners_panel_sha256": panel_sha,
        },
        "license": "academic access via OmniPath API",
        "schema": {"format": "TSV", "columns": [
            "source", "target", "source_genesymbol", "target_genesymbol", "is_directed",
            "is_stimulation", "is_inhibition", "consensus_direction", "consensus_stimulation",
            "consensus_inhibition",
        ], "organism_taxon_id": 10090},
        "target_mapping": {
            "mapping_type": "official OmniPath mouse gene-symbol response",
            "source_column": "source_genesymbol", "target_column": "target_genesymbol",
            "panel_reference": "data/gene_panel/T3__gata4.genes.txt",
            "panel_gene_count": len(panel), "edge_symbols_overlapping_panel": len(overlap),
        },
        "directed_edges": rows,
        "data_path": data_path.name,
        "bytes": data_path.stat().st_size,
        "sha256": sha256_file(data_path),
        "scope": "mouse taxon 10090; full API snapshot retained locally; downstream response genes restricted to T3 panel",
        "scientific_status": "audited_external_knowledge_component; not context-specific effect truth",
    }
    path = data_path.parent / "snapshot_manifest.json"
    json_write(path, manifest)
    return path


def _matrix_for_genes(adata: ad.AnnData, genes: list[str]) -> tuple[sparse.csr_matrix, list[str]]:
    positions = {str(gene): i for i, gene in enumerate(adata.var_names.astype(str))}
    present = [gene for gene in genes if gene in positions]
    if not present:
        raise ValueError("none of the requested genes are present in exact-stage input")
    matrix = adata.X[:, [positions[gene] for gene in present]]
    return (matrix.tocsr() if sparse.issparse(matrix) else sparse.csr_matrix(matrix), present)


def _rank_scores(values: np.ndarray) -> np.ndarray:
    values = np.abs(np.asarray(values, dtype=float))
    order = np.argsort(-values, kind="mergesort")
    score = np.zeros(len(values), dtype=float)
    score[order] = (len(values) - np.arange(len(values))) / (len(values) + 1.0)
    return score


def _python_package_version(distribution: str) -> str:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return "NOT_INSTALLED"


def _locked_python_toolchain() -> dict[str, Any]:
    versions = {
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "CellOracle": _python_package_version("celloracle"),
        "genomepy": _python_package_version("genomepy"),
    }
    versions["lock_status"] = (
        "PASS"
        if versions["CellOracle"] == "0.22.0" and versions["genomepy"] == "0.16.4"
        else "BLOCKED_TOOLCHAIN"
    )
    return versions


def _load_locked_celloracle_base_grn(co: Any) -> tuple[Any, dict[str, str]]:
    """Load the pinned upstream base-GRN from the task-local cache."""
    if not CELLORACLE_GRN_FILE.is_file():
        raise FileNotFoundError(f"CellOracle base-GRN cache is missing: {CELLORACLE_GRN_FILE}")
    actual_sha = sha256_file(CELLORACLE_GRN_FILE)
    if actual_sha != CELLORACLE_GRN_SHA256:
        raise ValueError(
            f"CellOracle base-GRN hash mismatch: expected {CELLORACLE_GRN_SHA256}, got {actual_sha}"
        )
    loader = importlib.import_module("celloracle.data.load_promoter_base_GRN")
    previous_data_dir = loader.CELLORACLE_DATA_DIR
    loader.CELLORACLE_DATA_DIR = str(CELLORACLE_GRN_DIR.parent)
    try:
        base_grn = loader.load_mouse_promoter_base_GRN(
            version="mm10_gimmemotifsv5_fpr2", force_download=False
        )
    finally:
        loader.CELLORACLE_DATA_DIR = previous_data_dir
    return base_grn, {
        "path": str(CELLORACLE_GRN_FILE),
        "sha256": actual_sha,
        "source_url": "https://raw.githubusercontent.com/morris-lab/CellOracle/master/celloracle/data/promoter_base_GRN/mm10_TFinfo_dataframe_gimmemotifsv5_fpr2_threshold_10_20210630.parquet",
    }


def _celloracle_target_capabilities(base_grn: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """Distinguish a target row from a perturbable TF source column."""
    target_col = "gene_short_name"
    if target_col not in base_grn.columns:
        raise ValueError(f"CellOracle base GRN lacks required {target_col!r} column")
    rows = set(base_grn[target_col].astype(str))
    sources = {str(column) for column in base_grn.columns if str(column) != target_col}
    result: dict[str, dict[str, Any]] = {}
    for target in ("Gata4", "Gata6", "Ctnnb1"):
        row_present = target in rows
        source_present = target in sources
        if not row_present:
            reason = "target gene row absent from base GRN"
        elif not source_present:
            reason = "target is not a TF source column in the promoter base GRN"
        else:
            reason = "target is present as a perturbable TF source"
        result[target] = {
            "gene_row_present": row_present,
            "tf_source_column_present": source_present,
            "perturbable": row_present and source_present,
            "reason": reason,
        }
    return result


def _run_celloracle_target(
    oracle: Any,
    target: str,
    output_dir: Path,
    input_shape: list[int],
    base_grn_rows: int,
) -> dict[str, Any]:
    """Run one unchanged upstream simulation on a clean fitted Oracle object."""
    parent = output_dir / "celloracle"
    target_path = parent / f"{target}_votes.tsv"
    stability_path = parent / f"{target}_state_sampling.tsv"
    if target_path.exists() or stability_path.exists():
        raise FileExistsError(f"refusing to overwrite existing CellOracle target output: {target}")
    oracle.simulate_shift(
        perturb_condition={target: 0.0},
        GRN_unit="cluster",
        n_propagation=3,
        ignore_warning=True,
        clip_delta_X=True,
    )
    delta = oracle.adata.layers.get("delta_X")
    if delta is None:
        raise RuntimeError("CellOracle did not publish layers['delta_X']")
    delta = delta.toarray() if sparse.issparse(delta) else np.asarray(delta)
    names = oracle.adata.var_names.astype(str).tolist()
    positions = {gene: i for i, gene in enumerate(names)}
    panel = panel_genes()
    rows: list[dict[str, Any]] = []
    stability_rows: list[dict[str, Any]] = []
    state_response_rows: list[dict[str, Any]] = []
    state_coverage_rows: list[dict[str, Any]] = []
    sample_state_response_rows: list[dict[str, Any]] = []
    state_values = oracle.adata.obs["state"].astype(str).to_numpy()
    sample_values = (
        oracle.adata.obs["sample"].astype(str).to_numpy()
        if "sample" in oracle.adata.obs
        else np.full(len(state_values), "__SINGLE_INPUT_SAMPLE__", dtype=object)
    )
    cell_ids = np.asarray(oracle.adata.obs_names.astype(str))
    if len(np.unique(cell_ids)) != len(cell_ids):
        raise RuntimeError(f"CellOracle input has duplicate cell IDs for {target}")
    for state in sorted(np.unique(state_values)):
        mask = state_values == state
        indices = np.flatnonzero(mask)
        if len(indices) < 4:
            continue
        state_samples = sorted(set(sample_values[indices].astype(str)))
        state_coverage_rows.append({
            "target_gene": target,
            "state": state,
            "n_cells": len(indices),
            "n_samples": len(state_samples),
            "sample_ids": ";".join(state_samples),
            "cell_id_count": len(indices),
            "cell_id_unique": len(set(cell_ids[indices])) == len(indices),
            "cell_id_sha256": hashlib.sha256(
                "\n".join(cell_ids[indices].tolist()).encode("utf-8")
            ).hexdigest(),
        })
        midpoint = len(indices) // 2
        first, second = indices[:midpoint], indices[midpoint:]
        for response_gene in panel:
            if response_gene == target or response_gene not in positions:
                continue
            pos = positions[response_gene]
            effect = float(np.median(delta[indices, pos]))
            first_effect = float(np.median(delta[first, pos]))
            second_effect = float(np.median(delta[second, pos]))
            sign = 1 if effect > 0 else -1 if effect < 0 else 0
            first_sign = 1 if first_effect > 0 else -1 if first_effect < 0 else 0
            second_sign = 1 if second_effect > 0 else -1 if second_effect < 0 else 0
            rows.append({
                "target_gene": target, "condition_id": "", "stage": EXACT_STAGE,
                "state": state, "response_gene": response_gene, "sign": sign,
                "rank_score": 0.0, "confidence": "", "evidence_family": "WT_CELLORACLE_REAL",
                "directness_score": "", "lineage_gate": "", "provenance": "CellOracle:real_api",
                "conflict_flag": False, "effect": effect,
            })
            state_response_rows.append({
                "target_gene": target,
                "state": state,
                "response_gene": response_gene,
                "n_cells": len(indices),
                "n_samples": len(state_samples),
                "sample_ids": ";".join(state_samples),
                "effect": effect,
                "sign": sign,
            })
            stability_rows.append({
                "target_gene": target, "state": state, "response_gene": response_gene,
                "n_first": len(first), "n_second": len(second),
                "effect_first": first_effect, "effect_second": second_effect,
                "sign_first": first_sign, "sign_second": second_sign,
                "sign_agree": first_sign != 0 and first_sign == second_sign,
            })
        for sample in state_samples:
            sample_indices = indices[sample_values[indices].astype(str) == sample]
            if len(sample_indices) < 4:
                continue
            sample_effects = np.asarray(
                [float(np.median(delta[sample_indices, positions[g]])) for g in panel if g in positions],
                dtype=float,
            )
            finite = sample_effects[np.isfinite(sample_effects)]
            sample_state_response_rows.append({
                "target_gene": target,
                "state": state,
                "sample": sample,
                "n_cells": len(sample_indices),
                "response_gene_count": len(sample_effects),
                "finite_response_fraction": float(len(finite) / len(sample_effects)) if len(sample_effects) else 0.0,
                "nonzero_response_fraction": float(np.count_nonzero(finite) / len(finite)) if len(finite) else 0.0,
                "median_abs_effect": float(np.median(np.abs(finite))) if len(finite) else None,
                "cell_id_count": len(sample_indices),
                "cell_id_unique": len(set(cell_ids[sample_indices])) == len(sample_indices),
                "cell_id_sha256": hashlib.sha256(
                    "\n".join(cell_ids[sample_indices].tolist()).encode("utf-8")
                ).hexdigest(),
            })
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise RuntimeError(f"CellOracle produced no panel response rows for {target}")
    frame["rank_score"] = frame.groupby("state")["effect"].transform(
        lambda col: _rank_scores(col.to_numpy())
    )
    frame = frame.drop(columns=["effect"])
    _write_tsv_atomic(target_path, frame.to_dict("records"), list(REQUIRED_VOTE_FIELDS))
    _write_tsv_atomic(stability_path, stability_rows, list(stability_rows[0]))
    state_response_path = parent / f"{target}_state_response.tsv"
    _write_tsv_atomic(
        state_response_path,
        state_response_rows,
        ["target_gene", "state", "response_gene", "n_cells", "n_samples", "sample_ids", "effect", "sign"],
    )
    state_coverage_path = parent / f"{target}_state_coverage.tsv"
    _write_tsv_atomic(
        state_coverage_path,
        state_coverage_rows,
        ["target_gene", "state", "n_cells", "n_samples", "sample_ids", "cell_id_count", "cell_id_unique", "cell_id_sha256"],
    )
    sample_state_response_path = parent / f"{target}_sample_state_response.tsv"
    _write_tsv_atomic(
        sample_state_response_path,
        sample_state_response_rows,
        [
            "target_gene", "state", "sample", "n_cells", "response_gene_count",
            "finite_response_fraction", "nonzero_response_fraction", "median_abs_effect",
            "cell_id_count", "cell_id_unique", "cell_id_sha256",
        ],
    )
    return {
        "status": "PASS",
        "target": target,
        "input_shape": input_shape,
        "base_grn_rows": base_grn_rows,
        "output": str(target_path),
        "state_sampling_output": str(stability_path),
        "state_response_output": str(state_response_path),
        "state_coverage_output": str(state_coverage_path),
        "sample_state_response_output": str(sample_state_response_path),
        "nonzero_rows": int((frame["sign"].astype(int) != 0).sum()),
        "outputs_sha256": {
            "output": sha256_file(target_path),
            "state_sampling_output": sha256_file(stability_path),
            "state_response_output": sha256_file(state_response_path),
            "state_coverage_output": sha256_file(state_coverage_path),
            "sample_state_response_output": sha256_file(sample_state_response_path),
        },
    }


def _peak_rss_bytes() -> int:
    """Return Linux ru_maxrss in bytes for the target worker audit."""
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)


def _celloracle_target_worker(
    oracle: Any,
    target: str,
    output_dir: Path,
    input_shape: list[int],
    base_grn_rows: int,
    checkpoint_path: Path,
) -> None:
    """Child entrypoint; only a target result/checkpoint crosses the process boundary."""
    started_at = datetime.now(timezone.utc).isoformat()
    started_clock = time.monotonic()
    try:
        target_result = _run_celloracle_target(
            oracle, target, output_dir, input_shape, base_grn_rows
        )
        status = str(target_result.get("status", "NOT_RUN"))
        error = None
    except BaseException as exc:  # pragma: no cover - resource/environment-specific
        target_result = {
            "status": "BLOCKED_TOOLCHAIN",
            "target": target,
            "error": repr(exc),
        }
        status = "BLOCKED_TOOLCHAIN"
        error = traceback.format_exc(limit=20)
    payload = {
        "schema": "ve.t3.s1a-celloracle-target-checkpoint.v1",
        "task": "T3-S1A-STATE-JOIN",
        "target": target,
        "pid": os.getpid(),
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "wall_seconds": time.monotonic() - started_clock,
        "peak_rss_bytes": _peak_rss_bytes(),
        "status": status,
        "target_result": target_result,
    }
    if error:
        payload["traceback"] = error
    _write_json_atomic(checkpoint_path, payload)


def _run_celloracle_target_isolated(
    oracle: Any,
    target: str,
    output_dir: Path,
    input_shape: list[int],
    base_grn_rows: int,
    log: list[str],
) -> dict[str, Any]:
    """Run one target in a forked worker without changing the CellOracle call."""
    parent = output_dir / "celloracle"
    parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path = parent / f"{target}_checkpoint.json"
    runtime_path = parent / f"{target}_runtime.json"
    if checkpoint_path.exists() or runtime_path.exists():
        raise FileExistsError(f"refusing to overwrite existing target checkpoint: {target}")
    try:
        context = mp.get_context(CELLORACLE_TARGET_START_METHOD)
    except ValueError as exc:  # pragma: no cover - platform-specific
        return {"target": target, "status": "BLOCKED_TOOLCHAIN", "error": repr(exc)}
    started_at = datetime.now(timezone.utc).isoformat()
    started_clock = time.monotonic()
    process = context.Process(
        target=_celloracle_target_worker,
        args=(oracle, target, output_dir, input_shape, base_grn_rows, checkpoint_path),
        name=f"t3-s1a-celloracle-{target}",
    )
    process.start()
    peak_rss_bytes = 0
    timed_out = False
    deadline = started_clock + CELLORACLE_TARGET_TIMEOUT_MINUTES * 60
    while process.is_alive():
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            timed_out = True
            process.terminate()
            process.join(timeout=30)
            if process.is_alive():
                process.kill()
                process.join(timeout=30)
            break
        process.join(timeout=min(CELLORACLE_TARGET_CHECK_INTERVAL_SECONDS, remaining))
        if process.is_alive():
            try:
                import psutil
            except ImportError:
                psutil = None
            if psutil is not None:
                try:
                    peak_rss_bytes = max(
                        peak_rss_bytes, int(psutil.Process(process.pid).memory_info().rss)
                    )
                except (psutil.Error, OSError):
                    pass
    if process.pid:
        try:
            import psutil
        except ImportError:
            psutil = None
        if psutil is not None and not process.is_alive():
            try:
                peak_rss_bytes = max(
                    peak_rss_bytes, int(psutil.Process(process.pid).memory_info().rss)
                )
            except (psutil.Error, OSError):
                pass
    process.join(timeout=1)
    finished_at = datetime.now(timezone.utc).isoformat()
    runtime = {
        "start_method": CELLORACLE_TARGET_START_METHOD,
        "pid": process.pid,
        "started_at": started_at,
        "finished_at": finished_at,
        "wall_seconds": time.monotonic() - started_clock,
        "timeout_minutes": CELLORACLE_TARGET_TIMEOUT_MINUTES,
        "check_interval_seconds": CELLORACLE_TARGET_CHECK_INTERVAL_SECONDS,
        "timed_out": timed_out,
        "exitcode": process.exitcode,
        "peak_rss_bytes_parent_observed": peak_rss_bytes,
    }
    checkpoint: dict[str, Any] | None = None
    if checkpoint_path.is_file():
        try:
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            if checkpoint.get("schema") != "ve.t3.s1a-celloracle-target-checkpoint.v1":
                checkpoint = None
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            checkpoint = None
    if checkpoint:
        runtime["worker_wall_seconds"] = checkpoint.get("wall_seconds")
        runtime["worker_peak_rss_bytes"] = checkpoint.get("peak_rss_bytes")
        if isinstance(checkpoint.get("peak_rss_bytes"), (int, float)):
            peak_rss_bytes = max(peak_rss_bytes, int(checkpoint["peak_rss_bytes"]))
            runtime["peak_rss_bytes"] = peak_rss_bytes
    _write_json_atomic(runtime_path, runtime)
    if checkpoint and isinstance(checkpoint.get("target_result"), dict):
        target_result = dict(checkpoint["target_result"])
        target_result["checkpoint"] = str(checkpoint_path)
        target_result["runtime"] = runtime
        if checkpoint.get("status") == "PASS":
            log.append(
                f"CellOracle target {target} PASS in isolated worker; "
                f"wall_seconds={runtime['wall_seconds']:.1f}"
            )
            return target_result
        target_result.setdefault("status", "BLOCKED_TOOLCHAIN")
        target_result["runtime"] = runtime
        return target_result
    status = "BLOCKED_RUNTIME" if timed_out or process.exitcode != 0 else "BLOCKED_TOOLCHAIN"
    reason = (
        f"target worker exceeded {CELLORACLE_TARGET_TIMEOUT_MINUTES} minute bounded window"
        if timed_out
        else f"target worker exited without a checkpoint (exitcode={process.exitcode})"
    )
    log.append(f"CellOracle target {target} {status}: {reason}")
    return {
        "target": target,
        "status": status,
        "error": reason,
        "runtime": runtime,
    }


def run_celloracle(
    exact: ad.AnnData,
    output_dir: Path,
    log: list[str],
) -> dict[str, Any]:
    """Run exact CellOracle API with one clean, checkpointed worker per target."""
    result: dict[str, Any] = {
        "method": "CellOracle",
        "status": "NOT_RUN",
        "targets": {},
        "target_process_isolation": {
            "start_method": CELLORACLE_TARGET_START_METHOD,
            "timeout_minutes": CELLORACLE_TARGET_TIMEOUT_MINUTES,
            "check_interval_seconds": CELLORACLE_TARGET_CHECK_INTERVAL_SECONDS,
            "shared_grn_fit": True,
            "semantics_changed": False,
        },
    }
    runtime_config = output_dir / "deployment/runtime"
    runtime_config.mkdir(parents=True, exist_ok=True)
    for key, value in {
        "XDG_CONFIG_HOME": runtime_config / "config",
        "XDG_CACHE_HOME": runtime_config / "cache",
        "MPLCONFIGDIR": runtime_config / "mpl",
        "NUMBA_CACHE_DIR": runtime_config / "numba",
    }.items():
        Path(value).mkdir(parents=True, exist_ok=True)
        os.environ[key] = str(value)
    os.environ.setdefault("NUMBA_DISABLE_CACHING", "1")
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[key] = "1"
    try:
        import celloracle as co
    except Exception as exc:  # pragma: no cover - environment-specific
        result["status"] = "BLOCKED_TOOLCHAIN"
        result["error"] = repr(exc)
        return result
    result["tool_versions"] = _locked_python_toolchain()
    if result["tool_versions"]["lock_status"] != "PASS":
        result["status"] = "BLOCKED_TOOLCHAIN"
        result["error"] = "installed Python package versions do not match deployment lock"
        return result
    try:
        base_grn, base_grn_source = _load_locked_celloracle_base_grn(co)
        result["base_grn_cache"] = base_grn_source
        target_capabilities = _celloracle_target_capabilities(base_grn)
        target_values = set(base_grn["gene_short_name"].astype(str))
        parent = output_dir / "celloracle"
        parent.mkdir(parents=True, exist_ok=True)
        # Selection is made after exact-stage sanitization and is deterministic;
        # panel, target, lineage markers and variable genes are always retained.
        if sparse.issparse(exact.X):
            log_expr = exact.X.tocsr().astype(np.float32)
            log_expr.data = np.log1p(log_expr.data)
            mean = np.asarray(log_expr.mean(axis=0)).ravel()
            squared = log_expr.copy()
            squared.data **= 2
            variance = np.maximum(np.asarray(squared.mean(axis=0)).ravel() - mean ** 2, 0.0)
        else:
            log_expr = np.log1p(np.asarray(exact.X, dtype=np.float32))
            variance = np.var(log_expr, axis=0)
        must_keep = list(dict.fromkeys(panel_genes() + list(POSITIVE_MARKERS) + list(NEGATIVE_MARKERS) + ["Gata4", "Gata6", "Ctnnb1"]))
        order = np.argsort(-variance, kind="mergesort")
        exact_names = set(exact.var_names.astype(str))
        chosen = [gene for gene in must_keep if gene in exact_names]
        for index in order:
            gene = str(exact.var_names[index])
            if gene not in chosen:
                chosen.append(gene)
            if len(chosen) >= 2000:
                break
        counts, chosen = _matrix_for_genes(exact, chosen)
        obs_columns = ["state"]
        if "sample" in exact.obs.columns:
            obs_columns.append("sample")
        obs = exact.obs[obs_columns].copy()
        for column in obs_columns:
            obs[column] = obs[column].astype(str)
        method_adata = ad.AnnData(X=counts, obs=obs, var=pd.DataFrame(index=chosen))
        svd = TruncatedSVD(
            n_components=min(30, max(2, min(method_adata.shape) - 1)),
            random_state=SEED,
        )
        log_counts = counts.copy().astype(np.float32)
        log_counts.data = np.log1p(log_counts.data)
        method_adata.obsm["X_pca"] = svd.fit_transform(log_counts)
        applicable_targets = [
            target for target in ("Gata4", "Gata6", "Ctnnb1")
            if target_capabilities[target]["perturbable"]
        ]
        oracle = None
        shared_fit_error: Exception | None = None
        if applicable_targets:
            try:
                log.append("CellOracle shared Oracle import/PCA/KNN/GRN fit starting")
                oracle = co.Oracle()
                oracle.import_anndata_as_raw_count(
                    adata=method_adata,
                    cluster_column_name="state",
                    embedding_name="X_pca",
                )
                oracle.import_TF_data(TF_info_matrix=base_grn)
                oracle.perform_PCA(n_components=min(30, method_adata.shape[0] - 1, method_adata.shape[1] - 1))
                oracle.knn_imputation(k=min(30, max(2, method_adata.shape[0] - 1)), n_pca_dims=20, n_jobs=1)
                oracle.fit_GRN_for_simulation(
                    GRN_unit="cluster", alpha=10, use_cluster_specific_TFdict=False, verbose_level=0
                )
                log.append("CellOracle shared GRN fit completed")
            except Exception as exc:  # preserve exact shared method failure
                shared_fit_error = exc
        for target in ("Gata4", "Gata6", "Ctnnb1"):
            target_result: dict[str, Any] = {"status": "NOT_RUN", "target": target}
            capability = target_capabilities[target]
            if not capability["perturbable"]:
                target_result["status"] = "NOT_APPLICABLE_BASE_GRN_TARGET_ABSENT"
                if capability["gene_row_present"] and not capability["tf_source_column_present"]:
                    target_result["status"] = "NOT_APPLICABLE_BASE_GRN_REGULATOR_ABSENT"
                target_result["reason"] = capability["reason"]
            elif shared_fit_error is not None or oracle is None:
                target_result["status"] = "BLOCKED_TOOLCHAIN"
                target_result["error"] = repr(shared_fit_error or RuntimeError("CellOracle shared GRN is unavailable"))
            else:
                target_result = _run_celloracle_target_isolated(
                    oracle, target, output_dir, list(method_adata.shape), int(len(base_grn)), log
                )
            result["targets"][target] = target_result
        result["status"] = _aggregate_method_status(
            result["targets"].values(), allow_not_applicable=True
        )
        result["base_grn_targets"] = {target: target in target_values for target in ("Gata4", "Gata6", "Ctnnb1")}
        result["base_grn_target_capabilities"] = target_capabilities
        result["base_grn_source"] = "task-local CellOracle mm10_gimmemotifsv5_fpr2 cache"
        log.append("CellOracle real API execution completed for applicable targets")
    except Exception as exc:  # pragma: no cover - environment-specific
        result["status"] = "BLOCKED_TOOLCHAIN"
        result["error"] = repr(exc)
    return result


def run_sctenifold(
    exact: ad.AnnData,
    output_dir: Path,
    log: list[str],
) -> dict[str, Any]:
    """Run scTenifoldKnk; preserve its output as unsigned rank-only evidence."""
    parent = output_dir / "sctenifold"
    parent.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {"method": "scTenifoldNet/scTenifoldKnk", "status": "NOT_RUN", "targets": {}}
    genes = list(dict.fromkeys(panel_genes() + ["Gata4", "Gata6", "Ctnnb1"]))
    counts, genes = _matrix_for_genes(exact, genes)
    matrix_path = parent / "input_counts.mtx"
    mmwrite(matrix_path, counts.T.tocoo())
    gene_path = parent / "input_genes.tsv"
    write_tsv(gene_path, [{"gene_index": i, "gene": gene} for i, gene in enumerate(genes)], ["gene_index", "gene"])
    runner = ROOT / "scripts/run_sctenifold_knk.R"
    for target in ("Gata4", "Gata6", "Ctnnb1"):
        target_result: dict[str, Any] = {"status": "NOT_RUN", "target": target}
        if target not in genes:
            target_result["status"] = "NOT_APPLICABLE_INPUT_GENE_ABSENT"
            result["targets"][target] = target_result
            continue
        raw_out = parent / f"{target}_diffRegulation.tsv"
        version_out = parent / f"{target}_diffRegulation.tsv.versions.tsv"
        env = os.environ.copy()
        task_rlib = output_dir / "deployment/Rlib"
        active_rlib = task_rlib if task_rlib.is_dir() else NEW_RLIB
        env["R_LIBS_USER"] = f"{active_rlib}:{OLD_RLIB}:{USER_RLIB}"
        env["LD_LIBRARY_PATH"] = "/opt/anaconda3/lib:" + env.get("LD_LIBRARY_PATH", "")
        env["OMP_NUM_THREADS"] = "1"
        env["OPENBLAS_NUM_THREADS"] = "1"
        command = [
            "Rscript", str(runner), str(matrix_path), str(gene_path), target, str(raw_out), str(SEED),
        ]
        completed = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True)
        target_result["command"] = command
        target_result["stdout_tail"] = completed.stdout[-2000:]
        target_result["stderr_tail"] = completed.stderr[-4000:]
        if completed.returncode != 0 or not raw_out.is_file() or not version_out.is_file():
            target_result["status"] = "BLOCKED_TOOLCHAIN"
            target_result["returncode"] = completed.returncode
            result["targets"][target] = target_result
            continue
        try:
            version_table = pd.read_csv(version_out, sep="\t", dtype=str)
            runtime_versions = dict(zip(version_table["package"], version_table["version"]))
            expected_versions = {
                "R": "4.5.1",
                "Matrix": "1.7.3",
                "scTenifoldNet": "1.4",
                "scTenifoldKnk": "1.1",
            }
            if any(runtime_versions.get(key) != value for key, value in expected_versions.items()):
                raise RuntimeError(
                    f"R package/runtime versions do not match deployment lock: {runtime_versions}"
                )
            table = pd.read_csv(raw_out, sep="\t")
            gene_col = next((col for col in ("gene", "Gene", "gene_name") if col in table.columns), None)
            if gene_col is None:
                gene_col = table.columns[0]
            score_col = next((col for col in ("distance", "Z", "FC", "p.adj", "p.value") if col in table.columns), None)
            if score_col is None:
                raise ValueError("diffRegulation has no documented rank/distance field")
            table[gene_col] = table[gene_col].astype(str)
            table = table[table[gene_col].isin(panel_genes())].copy()
            values = pd.to_numeric(table[score_col], errors="coerce").fillna(0.0).to_numpy(float)
            score = _rank_scores(values)
            rows = []
            for (_, row), rank_score in zip(table.iterrows(), score):
                rows.append({
                    "target_gene": target, "condition_id": "", "stage": EXACT_STAGE,
                    "state": "__GLOBAL__", "response_gene": str(row[gene_col]), "sign": 0,
                    "rank_score": float(rank_score), "confidence": "", "evidence_family": "WT_NETWORK_RANK_ONLY",
                    "dosage_fraction": 0.5 if target == "Gata6" else 0.0,
                    "directness_score": "", "lineage_gate": "", "provenance": "scTenifoldKnk:real_api:unsigned_diffRegulation",
                    "conflict_flag": False,
                })
            vote_path = parent / f"{target}_rank_votes.tsv"
            write_tsv(vote_path, rows, list(REQUIRED_VOTE_FIELDS))
            if not rows:
                target_result["status"] = "BLOCKED_NO_PANEL_EVIDENCE"
                target_result["error"] = "diffRegulation had no response genes in the T3 panel"
                result["targets"][target] = target_result
                continue
            target_result.update({
                "status": "PASS_UNSIGNED_RANK_ONLY",
                "raw_output": str(raw_out), "rank_vote_output": str(vote_path),
                "version_output": str(version_out), "tool_versions": runtime_versions,
                "rows_panel": len(rows), "score_field": score_col,
            })
        except Exception as exc:
            target_result["status"] = "BLOCKED_TOOLCHAIN"
            target_result["error"] = repr(exc)
        result["targets"][target] = target_result
    result["status"] = _aggregate_method_status(
        result["targets"].values(), allow_not_applicable=True
    )
    result["input_shape"] = list(counts.shape)
    result["input_counts_sha256"] = sha256_file(matrix_path)
    result["note"] = "scTenifold output is unsigned rank evidence; no sign is inferred from distance, Z, FC, p.value or p.adj"
    log.append("scTenifold real API execution attempted for all applicable targets")
    return result


def _load_network_snapshots(repo: Path) -> tuple[Any, Any, dict[str, Any]]:
    sys.path.insert(0, str(repo / "docs/batch3/interfaces"))
    from virtual_embryo_tools.directed_knowledge import load_audited_snapshot, snapshot_summary
    collectri_manifest = COLLECTRI_DIR / "snapshot_manifest.json"
    omnipath_manifest = OMNIPATH_DIR / "snapshot_manifest.json"
    if not collectri_manifest.exists():
        collectri_manifest = build_snapshot_manifest(COLLECTRI_DIR / "collectri_mouse_full.tsv", "CollecTRI", "collectri", repo)
    if not omnipath_manifest.exists():
        omnipath_manifest = build_snapshot_manifest(OMNIPATH_DIR / "omnipath_mouse_full.tsv", "OmniPath", "omnipath", repo)
    collectri = load_audited_snapshot(collectri_manifest, repo_root=repo, expected_source_name="CollecTRI", expected_dataset="collectri", expected_taxon_id=10090)
    omnipath = load_audited_snapshot(omnipath_manifest, repo_root=repo, expected_source_name="OmniPath", expected_dataset="omnipath", expected_taxon_id=10090)
    return collectri, omnipath, {"CollecTRI": snapshot_summary(collectri), "OmniPath": snapshot_summary(omnipath)}


def _standardize(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    center = np.median(values, axis=0)
    scale = np.median(np.abs(values - center), axis=0) * 1.4826
    scale[scale < 1e-8] = 1.0
    return np.clip((values - center) / scale, -6, 6)


def build_state_join(
    exact: ad.AnnData,
    obs: pd.DataFrame,
    collectri: Any,
    omnipath: Any,
    output_dir: Path,
) -> tuple[Path, dict[str, Any]]:
    panel = panel_genes()
    parent = ad.read_h5ad(PARENT_PATH)
    parent_values = parent.layers["log1p"] if "log1p" in parent.layers else parent.X
    parent_values = parent_values.toarray() if sparse.issparse(parent_values) else np.asarray(parent_values)
    parent_panel = parent.var_names.astype(str).tolist()
    parent_pos = {gene: i for i, gene in enumerate(parent_panel)}
    external_names = exact.var_names.astype(str).tolist()
    external_all_pos = {gene: i for i, gene in enumerate(external_names)}
    path_rows = []
    edge_rows = []
    from virtual_embryo_tools.directed_knowledge import build_directed_paths, build_tf_edge_evidence
    for target in ("Gata4", "Gata6"):
        edge_rows.extend(build_tf_edge_evidence(collectri, target_gene=target))
    path_rows.extend(build_directed_paths(omnipath, source_gene="Ctnnb1", max_hops=3, max_paths=5000))
    response_path_genes = sorted({str(row["response_gene"]) for row in path_rows if int(row.get("ko_minus_wt_sign", 0)) != 0})
    join_genes = list(dict.fromkeys(
        panel + list(POSITIVE_MARKERS) + list(NEGATIVE_MARKERS)
        + [target for details in CONDITIONS.values() for target in details["targets"]]
        + response_path_genes
    ))
    join_indices = [external_all_pos[gene] for gene in join_genes if gene in external_all_pos]
    join_genes = [gene for gene in join_genes if gene in external_all_pos]
    if not join_genes:
        raise ValueError("exact-stage input has no genes required for state join")
    missing_panel = sorted(set(panel) - set(external_all_pos))
    if missing_panel:
        raise ValueError(f"exact-stage input is missing T3 panel genes: {missing_panel[:10]}")
    join_matrix = exact.X[:, join_indices]
    join_matrix = join_matrix.toarray() if sparse.issparse(join_matrix) else np.asarray(join_matrix)
    external_log = np.log1p(join_matrix.astype(np.float32, copy=False))
    external_pos = {gene: i for i, gene in enumerate(join_genes)}
    ext_states = obs["state"].astype(str).to_numpy()
    ext_state_names = sorted(np.unique(ext_states))
    panel_positions = [external_pos[g] for g in panel if g in external_pos]
    ext_centroids = {
        state: external_log[ext_states == state][:, panel_positions].mean(axis=0)
        for state in ext_state_names
    }
    parent_panel_positions = [parent_pos[g] for g in panel if g in parent_pos and g in external_pos]
    external_panel_positions = [external_pos[g] for g in panel if g in parent_pos and g in external_pos]
    def corr(a: np.ndarray, b: np.ndarray) -> float:
        a = a - a.mean(); b = b - b.mean()
        den = float(np.linalg.norm(a) * np.linalg.norm(b))
        return float(np.dot(a, b) / den) if den > 1e-12 else -1.0
    # Marker program is calculated on exact-stage WT data, then summarized per
    # matched state.  It does not use a hardcoded external cell-type whitelist.
    positive = [external_pos[g] for g in POSITIVE_MARKERS if g in external_pos]
    negative = [external_pos[g] for g in NEGATIVE_MARKERS if g in external_pos]
    if not positive or not negative:
        raise ValueError("exact-stage input lacks a complete lineage marker program")
    z = _standardize(external_log)
    probabilities = 1.0 / (1.0 + np.exp(-(z[:, positive].mean(axis=1) - z[:, negative].mean(axis=1))))
    state_probability = {state: float(np.median(probabilities[ext_states == state])) for state in ext_state_names}
    state_n = {state: int((ext_states == state).sum()) for state in ext_state_names}
    mappings: dict[str, dict[str, Any]] = {}
    for state_index, state in enumerate(sorted(parent.obs["celltype"].astype(str).unique())):
        if state in ext_centroids:
            matched, similarity = state, 1.0
        else:
            pcentroid = parent_values[parent.obs["celltype"].astype(str).to_numpy() == state][:, parent_panel_positions].mean(axis=0)
            choices = [(corr(pcentroid, ext_centroids[candidate]), candidate) for candidate in ext_state_names]
            similarity, matched = max(choices, key=lambda item: (item[0], item[1]))
        mappings[state] = {
            "matched_external_state": matched,
            "match_similarity": float(similarity),
            "external_n": state_n[matched],
            "p_mesp1_lineage": state_probability[matched],
            "state_join_status": (
                "PASS"
                if matched and np.isfinite(similarity) and state_n[matched] >= 4
                else "HOLD"
            ),
        }
    state_gate_rows: list[dict[str, Any]] = []
    for condition, details in CONDITIONS.items():
        for state, mapping in sorted(mappings.items()):
            matched = mapping["matched_external_state"]
            mask = ext_states == matched
            expr_values = []
            for target in details["targets"]:
                if target in external_pos:
                    expr_values.append(float(external_log[mask, external_pos[target]].mean()))
            target_expression = float(np.mean(expr_values)) if expr_values else ""
            if condition.startswith("BETA"):
                activity_genes = [g for g in response_path_genes if g in external_pos]
                pathway_activity = float(external_log[mask][:, [external_pos[g] for g in activity_genes]].mean()) if activity_genes else ""
                activity_status = "NOT_VALIDATED_WT_EXPRESSION_MODULE_PROXY"
            else:
                pathway_activity = ""
                activity_status = "NOT_VALIDATED_TARGET_EXPRESSION_ONLY"
            state_join_status = mapping["state_join_status"]
            state_gate_rows.append({
                "condition_id": condition, "stage": EXACT_STAGE, "state": state,
                "lineage_gate": mapping["p_mesp1_lineage"], "p_mesp1_lineage": mapping["p_mesp1_lineage"],
                "gate_pass": bool(mapping["p_mesp1_lineage"] >= 0.5),
                "state_join_status": state_join_status,
                "state_sample_n": mapping["external_n"],
                # The current inputs are WT expression plus a source-level
                # WT attestation.  They do not contain a validated
                # perturbation/state-activity measurement, so this gate must
                # remain false and be consumed by the prior committee.
                "activity_gate_pass": False,
                "target_gene": ";".join(details["targets"]), "target_expression": target_expression,
                "tf_activity": target_expression if not condition.startswith("BETA") else "",
                "pathway_activity": pathway_activity, "activity_evidence_status": activity_status,
                "matched_external_state": matched, "match_similarity": mapping["match_similarity"],
                "external_n": mapping["external_n"],
                "provenance": "ExtendedMouseAtlas exact E8.75 WT raw counts; marker program and centroid state join",
            })
    state_gate_path = output_dir / "intermediates/state_gate.tsv"
    write_tsv(state_gate_path, state_gate_rows, list(STATE_GATE_FIELDS))
    activity_rows = [row for row in state_gate_rows]
    write_tsv(output_dir / "intermediates/state_activity.tsv", activity_rows, list(STATE_GATE_FIELDS))
    return state_gate_path, {
        "state_count": len(mappings), "external_state_count": len(ext_state_names),
        "state_mappings": mappings, "edge_rows": edge_rows, "path_rows": path_rows,
        "response_path_genes": response_path_genes, "state_gate_rows": state_gate_rows,
    }


def _method_vote_rows(
    method_path: Path,
    target: str,
    condition: str,
    state_names: list[str],
    state_mapping: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    rows = read_tsv(method_path) if method_path.exists() else []
    output = []
    for row in rows:
        base = dict(row)
        base["target_gene"] = target
        base["condition_id"] = condition
        base["stage"] = EXACT_STAGE
        base["dosage_fraction"] = 0.5 if target == "Gata6" else 0.0
        raw_state = str(base.get("state", "")).strip()
        if not raw_state or raw_state == "__GLOBAL__":
            mapped_states = state_names
        elif state_mapping is None:
            mapped_states = [raw_state]
        else:
            # CellOracle state labels belong to the exact-stage external input.
            # Project them through the recorded parent -> matched-external map;
            # never treat an unmatched external label as a parent state.
            mapped_states = [
                parent_state
                for parent_state in state_names
                if str(state_mapping.get(parent_state, {}).get("matched_external_state", "")) == raw_state
            ]
        for state in mapped_states:
            output.append({**base, "state": state})
    return output


def _edge_vote_rows(edge_rows: list[Mapping[str, Any]], target: str, condition: str, state_names: list[str]) -> list[dict[str, Any]]:
    output = []
    for edge in edge_rows:
        if edge["target_gene"] != target:
            continue
        for state in state_names:
            output.append({
                "target_gene": target, "condition_id": condition, "stage": EXACT_STAGE,
                "state": state, "response_gene": edge["response_gene"],
                "sign": int(edge["ko_minus_wt_sign"]), "rank_score": 0.8 if int(edge["ko_minus_wt_sign"]) else 0.0,
                "confidence": "", "evidence_family": "CURATED_TF_TARGET",
                "dosage_fraction": 0.5 if target == "Gata6" else 0.0,
                "directness_score": edge["directness_score"], "lineage_gate": "",
                "provenance": edge["provenance"], "conflict_flag": bool(edge["conflict_flag"]),
            })
    return output


def _path_vote_rows(path_rows: list[Mapping[str, Any]], state_names: list[str], condition: str, max_hops: int) -> list[dict[str, Any]]:
    output = []
    bounded = [row for row in path_rows if int(row["hops"]) <= max_hops]
    for path in bounded:
        for state in state_names:
            output.append({
                "target_gene": "Ctnnb1", "condition_id": condition, "stage": EXACT_STAGE,
                "state": state, "response_gene": path["response_gene"],
                "sign": int(path["ko_minus_wt_sign"]), "rank_score": 1.0 / max(1, int(path["hops"])),
                "confidence": "", "evidence_family": "DIRECTED_SIGNALING",
                "dosage_fraction": 0.0,
                "directness_score": "", "lineage_gate": "",
                "provenance": path["provenance"], "conflict_flag": bool(path["conflict_flag"]),
            })
    return output


def _route_slug(route_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", route_id).strip("_").lower()


def _state_sampling_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"status": "NOT_RUN", "rows": 0, "agreement_fraction": None}
    rows = read_tsv(path)
    valid = [row for row in rows if row.get("sign_first") not in ("0", "") and row.get("sign_second") not in ("0", "")]
    agree = [row for row in valid if row.get("sign_agree", "").lower() == "true"]
    fraction = len(agree) / len(valid) if valid else None
    return {"status": "PASS" if fraction is not None and fraction >= 0.8 else "HOLD", "rows": len(rows), "valid_rows": len(valid), "agreement_fraction": fraction}


def _build_state_response_support(
    method_results: Mapping[str, Any],
    output_dir: Path,
    state_join: Mapping[str, Any],
) -> dict[str, Any]:
    """Audit modelled state response without relabeling it as biology."""
    state_mapping = state_join.get("state_mappings", {})
    required_external_states = sorted({
        str(mapping.get("matched_external_state", ""))
        for mapping in state_mapping.values()
        if str(mapping.get("matched_external_state", "")).strip()
    })
    target_reports: dict[str, Any] = {}
    for target in ("Gata4", "Gata6", "Ctnnb1"):
        target_result = (
            method_results.get("CellOracle", {})
            .get("targets", {})
            .get(target, {})
        )
        status = str(target_result.get("status", "NOT_RUN"))
        if status.startswith("NOT_APPLICABLE"):
            target_reports[target] = {
                "status": status,
                "claim": "NOT_APPLICABLE_CURRENT_CELLORACLE_GRN",
                "biological_activity_status": "NOT_VALIDATED",
                "reason": target_result.get("reason", status),
            }
            continue
        response_path = Path(str(target_result.get("state_response_output", "")))
        coverage_path = Path(str(target_result.get("state_coverage_output", "")))
        sample_path = Path(str(target_result.get("sample_state_response_output", "")))
        sampling_path = Path(str(target_result.get("state_sampling_output", "")))
        required_paths = (response_path, coverage_path, sample_path, sampling_path)
        if status != "PASS" or any(not path.is_file() for path in required_paths):
            target_reports[target] = {
                "status": "NOT_RUN_OR_INCOMPLETE",
                "method_status": status,
                "claim": "NO_STATE_RESPONSE_SUPPORT",
                "biological_activity_status": "NOT_VALIDATED",
            }
            continue
        response_rows = read_tsv(response_path)
        coverage_rows = read_tsv(coverage_path)
        sample_rows = read_tsv(sample_path)
        sampling_rows = read_tsv(sampling_path)
        response_states = sorted({str(row.get("state", "")) for row in response_rows})
        coverage_by_state = {str(row.get("state", "")): row for row in coverage_rows}
        response_by_state: dict[str, list[dict[str, str]]] = {}
        for row in response_rows:
            response_by_state.setdefault(str(row.get("state", "")), []).append(row)
        sampling_by_state: dict[str, list[dict[str, str]]] = {}
        for row in sampling_rows:
            sampling_by_state.setdefault(str(row.get("state", "")), []).append(row)
        per_state: dict[str, Any] = {}
        failures: list[str] = []
        for state in required_external_states:
            coverage = coverage_by_state.get(state)
            state_response = response_by_state.get(state, [])
            valid_effects = []
            for row in state_response:
                try:
                    value = float(row.get("effect", "nan"))
                except (TypeError, ValueError):
                    value = float("nan")
                if np.isfinite(value):
                    valid_effects.append(value)
            sampled = sampling_by_state.get(state, [])
            valid_sampled = [
                row for row in sampled
                if row.get("sign_first") not in (None, "", "0")
                and row.get("sign_second") not in (None, "", "0")
            ]
            agreeing = [row for row in valid_sampled if str(row.get("sign_agree", "")).lower() == "true"]
            agreement = len(agreeing) / len(valid_sampled) if valid_sampled else None
            state_ok = bool(
                coverage
                and str(coverage.get("cell_id_unique", "")).lower() == "true"
                and int(coverage.get("n_cells", "0")) >= 4
                and state_response
                and len(valid_effects) == len(state_response)
                and agreement is not None
                and agreement >= 0.8
            )
            if not state_ok:
                failures.append(state)
            per_state[state] = {
                "status": "PASS" if state_ok else "HOLD",
                "n_cells": int(coverage.get("n_cells", "0")) if coverage else 0,
                "n_samples": int(coverage.get("n_samples", "0")) if coverage else 0,
                "response_rows": len(state_response),
                "finite_effect_fraction": len(valid_effects) / len(state_response) if state_response else 0.0,
                "within_state_sign_agreement": agreement,
            }
        sample_state_counts = {
            state: sum(1 for row in sample_rows if str(row.get("state", "")) == state)
            for state in required_external_states
        }
        target_reports[target] = {
            "status": "PASS_STATE_RESPONSE_SUPPORT" if not failures else "HOLD_STATE_RESPONSE_SUPPORT",
            "claim": "MODELLED_STATE_RESPONSE_ONLY",
            "biological_activity_status": "NOT_VALIDATED",
            "required_external_states": required_external_states,
            "response_states": response_states,
            "unmapped_external_states": sorted(set(response_states) - set(required_external_states)),
            "per_state": per_state,
            "sample_state_rows": len(sample_rows),
            "sample_state_rows_by_required_state": sample_state_counts,
            "states_with_multiple_samples": sum(
                1 for state in required_external_states if int(coverage_by_state.get(state, {}).get("n_samples", "0")) >= 2
            ),
            "failures": failures,
            "limitations": [
                "CellOracle full-matrix shift response is a modelled response, not biological activity validation",
                "within-state first/second cell split is technical/descriptive stability, not an independent biological replicate",
            ],
        }
    applicable = [
        report for report in target_reports.values()
        if str(report.get("status", "")).startswith(("PASS_STATE_RESPONSE", "HOLD_STATE_RESPONSE"))
    ]
    return {
        "schema": "ve.t3.s1a-state-response-support.v1",
        "status": "PASS_STATE_RESPONSE_SUPPORT" if any(
            report.get("status") == "PASS_STATE_RESPONSE_SUPPORT" for report in applicable
        ) else "NOT_IDENTIFIABLE",
        "claim": "MODELLED_STATE_RESPONSE_ONLY",
        "biological_activity_status": "NOT_VALIDATED",
        "targets": target_reports,
        "notes": "This artifact audits exact-input CellOracle state response and coverage; it never sets activity_gate_pass or proves in vivo activity.",
    }


def _gate_result(status: str) -> str:
    """Map implementation statuses to the finite gate-report vocabulary."""
    if status == "PASS" or status.startswith("PASS"):
        return "PASS"
    if status == "NOT_APPLICABLE" or status.startswith("NOT_APPLICABLE"):
        return "NOT_APPLICABLE"
    if status in {"BLOCKED", "BLOCKED_TOOLCHAIN", "NOT_RUN"} or status.startswith("BLOCKED"):
        return "BLOCKED"
    return "FAIL"


def _aggregate_method_status(
    target_results: Iterable[Mapping[str, Any]],
    *,
    allow_not_applicable: bool = True,
) -> str:
    """Summarize target statuses without hiding a partial tool failure."""
    statuses = [str(result.get("status", "NOT_RUN")) for result in target_results]
    if not statuses:
        return "NOT_RUN"
    passed = [status for status in statuses if status.startswith("PASS")]
    allowed_na = [
        status for status in statuses
        if allow_not_applicable and status.startswith("NOT_APPLICABLE")
    ]
    hard = [status for status in statuses if status not in passed and status not in allowed_na]
    if hard and passed:
        return "PARTIAL"
    if hard:
        return "BLOCKED_TOOLCHAIN"
    return "PASS" if passed else "NOT_APPLICABLE"


def _target_status(method_status: Mapping[str, Any], method: str, target: str) -> str:
    result = method_status.get(method, {}).get("targets", {}).get(target)
    if not isinstance(result, Mapping):
        return "NOT_RUN"
    return str(result.get("status", "NOT_RUN"))


def _local_output_evidence(value: Any, output_dir: Path) -> dict[str, Any] | None:
    if not value:
        return None
    path = Path(str(value))
    if not path.is_file():
        return None
    try:
        relative = path.resolve().relative_to(output_dir.resolve()).as_posix()
    except ValueError:
        relative = str(path)
    return {"path": relative, "sha256": sha256_file(path)}


def _route_method_summary(
    method_results: Mapping[str, Any],
    targets: Iterable[str],
    output_dir: Path,
) -> dict[str, Any]:
    target_set = set(targets)
    summary: dict[str, Any] = {}
    for method, result in method_results.items():
        method_targets = result.get("targets", {}) if isinstance(result, Mapping) else {}
        selected_targets = sorted(target_set)
        summary[method] = {
            "status": result.get("status", "NOT_RUN") if isinstance(result, Mapping) else "NOT_RUN",
            "targets": {
                target: {
                    "status": method_targets.get(target, {}).get("status", "NOT_RUN"),
                    "reason": method_targets.get(target, {}).get(
                        "error", method_targets.get(target, {}).get("status", "NOT_RUN")
                    ),
                    "outputs": [
                        evidence
                        for key in (
                            "output", "raw_output", "rank_vote_output", "state_sampling_output",
                            "state_response_output", "state_coverage_output",
                            "sample_state_response_output", "version_output",
                        )
                        for evidence in [_local_output_evidence(method_targets.get(target, {}).get(key), output_dir)]
                        if evidence is not None
                    ],
                }
                for target in selected_targets
            },
        }
    return summary


def _state_join_assessment(
    state_join: Mapping[str, Any] | None,
    condition: str,
) -> dict[str, Any]:
    """Assess the state/activity evidence that the committee actually uses."""
    rows = [
        row for row in (state_join or {}).get("state_gate_rows", [])
        if row.get("condition_id") == condition
    ]
    if not rows:
        return {
            "status": "BLOCKED",
            "mapping_status": "BLOCKED",
            "activity_status": "NOT_RUN",
            "rows": 0,
            "blockers": ["STATE_JOIN_ROWS_MISSING"],
        }
    mapping_failures = []
    activity_failures = []
    for row in rows:
        try:
            sample_n = int(row.get("state_sample_n", row.get("external_n", 0)))
            similarity = float(row.get("match_similarity", "nan"))
        except (TypeError, ValueError):
            sample_n, similarity = 0, float("nan")
        if (
            row.get("state_join_status") != "PASS"
            or not str(row.get("matched_external_state", "")).strip()
            or sample_n < 4
            or not np.isfinite(similarity)
        ):
            mapping_failures.append(str(row.get("state", "")))
        if (
            row.get("activity_gate_pass") is not True
            or row.get("activity_evidence_status") != "VALIDATED_STATE_ACTIVITY"
        ):
            activity_failures.append(
                f"{row.get('state', '')}:{row.get('activity_evidence_status', 'NOT_RUN')}"
            )
    mapping_status = "PASS" if not mapping_failures else "BLOCKED"
    activity_status = "PASS" if not activity_failures else "NOT_VALIDATED"
    blockers = []
    if mapping_failures:
        blockers.append("STATE_MAPPING_INVALID")
    if activity_failures:
        blockers.append("STATE_ACTIVITY_NOT_VALIDATED")
    return {
        "status": "PASS" if mapping_status == "PASS" and activity_status == "PASS" else "HOLD" if mapping_status == "PASS" else "BLOCKED",
        "mapping_status": mapping_status,
        "activity_status": activity_status,
        "rows": len(rows),
        "mapping_failures": sorted(set(mapping_failures)),
        "activity_failures": sorted(set(activity_failures)),
        "blockers": blockers,
    }


def _verify_preexisting_deployment(output_dir: Path) -> None:
    """Permit only the known pre-deployment tree in a fresh output atom."""
    manifest_path = output_dir / "deployment/DEPLOYMENT_MANIFEST.json"
    if not manifest_path.is_file():
        raise FileExistsError(
            "output atom contains deployment but its deployment manifest is missing"
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FileExistsError(f"cannot verify pre-existing deployment manifest: {exc}") from exc
    if (
        manifest.get("schema") != "ve.t3.s1a-deployment.v1"
        or manifest.get("task") != "T3-S1A-STATE-JOIN"
        or manifest.get("status") != "READY_FOR_EXACT_INPUT_RUN"
    ):
        raise FileExistsError("pre-existing deployment manifest is not the locked T3-S1A deployment")
    python = manifest.get("python", {})
    r = manifest.get("r", {})
    if python.get("CellOracle") != "0.22.0" or python.get("genomepy") != "0.16.4":
        raise FileExistsError("pre-existing Python deployment does not match the lock")
    if r.get("scTenifoldNet") != "1.4" or r.get("scTenifoldKnk") != "1.1":
        raise FileExistsError("pre-existing R deployment does not match the lock")


def _repo_relative(path: Path, repo: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"provenance path is outside repository: {path}") from exc


def _source_artifact_records(
    files: Mapping[str, Path],
    repo: Path,
) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    hashes: dict[str, str] = {}
    artifacts: dict[str, dict[str, str]] = {}
    for name, path in sorted(files.items()):
        if not path.is_file():
            raise FileNotFoundError(f"source artifact is missing: {path}")
        digest = sha256_file(path)
        relative = _repo_relative(path, repo)
        hashes[name] = digest
        artifacts[name] = {"path": relative, "sha256": digest}
    return hashes, artifacts


def _is_transient_runtime_artifact(path: Path) -> bool:
    """Exclude files that a runtime may remove immediately after completion."""
    name = path.name
    return (
        name.endswith(("-shm", "-wal"))
        or ".tmp-" in name
        or name.endswith((".tmp", ".part"))
    )


def _write_artifact_manifest(
    output_dir: Path,
    manifest_name: str = "artifact_manifest.json",
) -> Path:
    entries = []
    for path in sorted(output_dir.rglob("*")):
        if (
            not path.is_file()
            or path.name in {"artifact_manifest.json", manifest_name, "MANIFEST.json"}
            or _is_transient_runtime_artifact(path)
        ):
            continue
        entries.append({
            "path": path.relative_to(output_dir).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    manifest_path = output_dir / "metrics" / manifest_name
    json_write(manifest_path, {
        "schema": "ve.t3.s1a-artifact-manifest.v1",
        "task": "T3-S1A-STATE-JOIN",
        "files": entries,
        "note": "Pre-gate immutable artifact manifest; the gate report is intentionally not self-referenced.",
    })
    return manifest_path


def _hash_relative_paths(output_dir: Path, paths: Iterable[str]) -> dict[str, str]:
    hashes = {}
    for relative in paths:
        path = (output_dir / relative).resolve()
        if output_dir.resolve() not in path.parents or not path.is_file():
            raise FileNotFoundError(f"route evidence is missing: {relative}")
        hashes[relative] = sha256_file(path)
    return hashes


def _selected_gene_stability(
    targets: Iterable[str],
    method_status: Mapping[str, Any],
    stability: Mapping[str, Any],
) -> dict[str, Any]:
    per_target: dict[str, Any] = {}
    failures: list[str] = []
    applicable_targets: list[str] = []
    not_applicable_targets: list[str] = []
    for target in targets:
        oracle_status = _target_status(method_status, "CellOracle", target)
        sample = stability.get(target, {})
        sample_status = str(sample.get("status", "NOT_RUN"))
        if oracle_status.startswith("NOT_APPLICABLE"):
            status = oracle_status
            not_applicable_targets.append(target)
        elif oracle_status == "PASS" and sample_status == "PASS":
            status = "PASS"
            applicable_targets.append(target)
        else:
            status = f"{sample_status}_CELLORACLE_{oracle_status}"
            applicable_targets.append(target)
        per_target[target] = {**sample, "status": status, "celloracle_status": oracle_status}
        if status != "PASS" and not status.startswith("NOT_APPLICABLE"):
            failures.append(f"{target}:{status}")
    if not applicable_targets and not_applicable_targets:
        failures.append("NO_APPLICABLE_CELLORACLE_TARGET")
    return {
        "status": "PASS" if not failures else "NOT_IDENTIFIABLE",
        "per_target": per_target,
        "failures": failures,
        "applicable_targets": applicable_targets,
        "not_applicable_targets": not_applicable_targets,
    }


def _evidence_family_stability(selected: list[Any], targets: Iterable[str]) -> dict[str, Any]:
    """Do not claim leave-one-family-out stability without per-family signs."""
    per_target: dict[str, Any] = {}
    failures: list[str] = []
    for target in targets:
        records = [record for record in selected if record.target_gene == target]
        families = sorted({family for record in records for family in record.source_families})
        if not records:
            status = "NOT_RUN_NO_SELECTED_RECORDS"
        elif any(len(record.source_families) < 2 for record in records):
            status = "NOT_IDENTIFIABLE_SINGLE_FAMILY_RECORD"
        else:
            # The committee stores the merged sign and family names, not the
            # sign contributed by each family.  Leave-one-out direction is
            # therefore not identifiable from this artifact.
            status = "NOT_IDENTIFIABLE_PER_FAMILY_SIGN_NOT_RETAINED"
        per_target[target] = {"status": status, "families": families, "records": len(records)}
        if status != "PASS":
            failures.append(f"{target}:{status}")
    return {"status": "PASS" if not failures else "NOT_IDENTIFIABLE", "per_target": per_target, "failures": failures}


def _assess_route(
    route_id: str,
    records: list[Any],
    method_status: dict[str, Any],
    stability: dict[str, Any],
    state_join: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    condition, lane = route_id.split("::", 1)
    targets = CONDITIONS[condition]["targets"]
    blockers: list[str] = []
    limitations: list[str] = []
    hard_blocked = False
    route_records = [record for record in records if record.condition_id == condition]
    selected = [record for record in route_records if record.sign != 0]
    state_assessment = _state_join_assessment(state_join, condition)
    if state_assessment["mapping_status"] != "PASS":
        blockers.append("STATE_MAPPING_INVALID")
        hard_blocked = True
    if state_assessment["activity_status"] != "PASS":
        blockers.append("STATE_ACTIVITY_NOT_VALIDATED")
    if not selected:
        blockers.append("NO_SELECTED_SIGNED_RECORDS")
    for target in targets:
        sct_status = _target_status(method_status, "scTenifoldNet/scTenifoldKnk", target)
        if sct_status != "PASS_UNSIGNED_RANK_ONLY":
            blockers.append(f"{target}:scTenifold:{sct_status}")
            hard_blocked = True
        if condition.startswith("GATA") and target == "Gata4":
            oracle_status = _target_status(method_status, "CellOracle", target)
            if oracle_status != "PASS":
                blockers.append(f"{target}:CellOracle:{oracle_status}")
                hard_blocked = True
        elif condition.startswith("GATA") and target == "Gata6":
            oracle_status = _target_status(method_status, "CellOracle", target)
            if oracle_status.startswith("NOT_APPLICABLE"):
                limitations.append("Gata6:CellOracle base GRN target absent; L2 relies on curated signed edge")
            elif oracle_status != "PASS":
                blockers.append(f"{target}:CellOracle:{oracle_status}")
                hard_blocked = True
        target_selected = [record for record in selected if record.target_gene == target]
        if lane == "L1_STRICT_AGREEMENT":
            if not target_selected:
                blockers.append(f"{target}:NO_STRICT_SIGN")
            elif any(len(record.source_families) < 2 for record in target_selected):
                blockers.append(f"{target}:INSUFFICIENT_INDEPENDENT_FAMILIES")
        else:
            if not target_selected:
                blockers.append(f"{target}:NO_CONDITION_AWARE_SIGN")
        if any(record.conflict_flag for record in target_selected):
            blockers.append(f"{target}:CONFLICT")
    gene_stability = _selected_gene_stability(targets, method_status, stability)
    if gene_stability["status"] != "PASS":
        blockers.append("SELECTED_GENE_STABILITY_NOT_IDENTIFIABLE")
    family_stability = _evidence_family_stability(selected, targets)
    if family_stability["status"] != "PASS":
        blockers.append("EVIDENCE_FAMILY_STABILITY_NOT_IDENTIFIABLE")
    if condition.startswith("GATA"):
        direct = [record for record in selected if record.target_gene == "Gata4" and record.directness_score is not None and record.directness_score > 0]
        if lane == "L1_STRICT_AGREEMENT" and not direct:
            blockers.append("Gata4:DIRECTNESS_REQUIRED")
        # CellOracle base-GRN absence is recorded above as a limitation, never
        # converted into a proxy result.
    else:
        path_families = {family for record in selected for family in record.source_families}
        if "DIRECTED_SIGNALING" not in path_families:
            blockers.append("Ctnnb1:DIRECTED_SIGNALING_PATH_REQUIRED")
        if lane == "L1_STRICT_AGREEMENT" and len(path_families) < 2:
            blockers.append("Ctnnb1:INSUFFICIENT_INDEPENDENT_SIGN_FAMILIES")
        limitations.append("scTenifold rank evidence is unsigned and does not count as a sign family")
    status = "BLOCKED" if hard_blocked else "PASS" if not blockers else "HOLD"
    candidate_generation = bool(
        status == "PASS"
        and state_assessment["status"] == "PASS"
        and gene_stability["status"] == "PASS"
        and family_stability["status"] == "PASS"
    )
    return {
        "route_id": route_id, "status": status,
        "candidate_generation": candidate_generation,
        "blocks_submission": False, "blockers": sorted(set(blockers)),
        "limitations": limitations, "selected_records": len(selected),
        "route_records": len(route_records),
        "evidence_family_leave_one_out": family_stability["status"],
        "state_join_gate": state_assessment,
        "selected_gene_stability": gene_stability,
        "evidence_family_stability": family_stability,
        "stability": stability,
    }


def combine_routes(
    output_dir: Path,
    state_join: dict[str, Any],
    method_results: dict[str, Any],
) -> tuple[list[Any], dict[str, Any]]:
    from virtual_embryo_tools.perturb_prior_committee import combine_prior_votes
    intermediate = output_dir / "intermediates"
    state_names = sorted(state_join["state_mappings"])
    state_mapping = state_join["state_mappings"]
    external_to_parent: dict[str, list[str]] = {}
    for parent_state, mapping in state_mapping.items():
        external_state = str(mapping.get("matched_external_state", "")).strip()
        if external_state:
            external_to_parent.setdefault(external_state, []).append(str(parent_state))
    state_mapping_audit = {
        "parent_state_count": len(state_names),
        "matched_external_state_count": len(external_to_parent),
        "ambiguous_external_states": {
            external: sorted(parents)
            for external, parents in sorted(external_to_parent.items())
            if len(parents) > 1
        },
        "projection": "external_method_state_to_recorded_parent_state_mapping",
        "unmatched_external_method_states_excluded": True,
    }
    source_rows: list[dict[str, Any]] = []
    route_records: dict[str, list[Any]] = {}
    route_reports: dict[str, Any] = {}
    for route_id in ROUTES:
        condition, lane = route_id.split("::", 1)
        votes: list[dict[str, Any]] = []
        if condition.startswith("GATA"):
            for target in CONDITIONS[condition]["targets"]:
                votes.extend(_edge_vote_rows(state_join["edge_rows"], target, condition, state_names))
                celloracle = method_results["CellOracle"].get("targets", {}).get(target, {})
                if celloracle.get("status") == "PASS":
                    votes.extend(_method_vote_rows(
                        Path(celloracle["output"]), target, condition, state_names,
                        state_mapping=state_mapping,
                    ))
                sct = method_results["scTenifoldNet/scTenifoldKnk"].get("targets", {}).get(target, {})
                if sct.get("status", "").startswith("PASS"):
                    votes.extend(_method_vote_rows(Path(sct["rank_vote_output"]), target, condition, state_names))
        else:
            votes.extend(_path_vote_rows(state_join["path_rows"], state_names, condition, 2 if "L1" in lane else 3))
            sct = method_results["scTenifoldNet/scTenifoldKnk"].get("targets", {}).get("Ctnnb1", {})
            if sct.get("status", "").startswith("PASS"):
                votes.extend(_method_vote_rows(Path(sct["rank_vote_output"]), "Ctnnb1", condition, state_names))
        vote_path = intermediate / f"votes_{_route_slug(route_id)}.tsv"
        for row in votes:
            row["route_id"] = route_id
        fields = ["route_id", *REQUIRED_VOTE_FIELDS]
        write_tsv(vote_path, votes, fields)
        source_rows.extend(votes)
        prior_path = intermediate / f"prior_{_route_slug(route_id)}.json"
        evidence_path = intermediate / f"evidence_{_route_slug(route_id)}.tsv"
        records = combine_prior_votes(
            vote_tables=[vote_path], state_gate_path=intermediate / "state_gate.tsv", lane=lane,
            output_json=prior_path, evidence_tsv=evidence_path,
            config={
                "min_independent_families": 2 if "L1" in lane else 1,
                "max_nonzero_fraction": 0.10 if "L1" in lane else 0.25,
                "panel_size": 500,
                "dosage_fractions": {"Gata4": 0.0, "Gata6": 0.5, "Ctnnb1": 0.0},
                "require_state_activity": True,
                "directness_required_targets": ["Gata4"] if condition.startswith("GATA") and "L1" in lane else [],
                "directness_threshold": 0.0,
                "signaling_path_required_targets": ["Ctnnb1"] if condition.startswith("BETA") and "L1" in lane else [],
            },
        )
        route_records[route_id] = records
        route_reports[route_id] = {"prior": str(prior_path), "evidence": str(evidence_path), "records": records, "vote_path": str(vote_path)}
    source_path = intermediate / "source_votes.tsv"
    write_tsv(source_path, source_rows, ["route_id", *REQUIRED_VOTE_FIELDS])
    return source_rows, {
        "route_records": route_records,
        "route_reports": route_reports,
        "source_path": source_path,
        "state_mapping_audit": state_mapping_audit,
    }


def run_task(
    repo: Path,
    input_h5ad: Path,
    metadata_csv: Path,
    archive: Path,
    output_dir: Path,
) -> dict[str, Any]:
    repo = repo.resolve(); output_dir = output_dir.resolve()
    if output_dir.exists():
        existing_results = [path for path in output_dir.iterdir() if path.name != "deployment"]
        if existing_results:
            raise FileExistsError(f"refusing to overwrite existing result files: {existing_results[:5]}")
        if (output_dir / "deployment").exists():
            _verify_preexisting_deployment(output_dir)
    expected_archive = ARCHIVE_DEFAULT.resolve()
    expected_input = SOURCE_H5AD_DEFAULT.resolve()
    expected_metadata = METADATA_DEFAULT.resolve()
    if archive.resolve() != expected_archive or input_h5ad.resolve() != expected_input or metadata_csv.resolve() != expected_metadata:
        raise ValueError(
            "T3-S1A requires the official archive-extracted input paths; "
            "custom H5AD/metadata/archive inputs are not admitted"
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    log: list[str] = [f"started={datetime.now(timezone.utc).isoformat()}", f"seed={SEED}", f"archive={archive}"]
    if not archive.is_file():
        raise FileNotFoundError(archive)
    expected_md5_path = archive.parent / "official_md5.txt"
    official_md5 = verify_official_md5_manifest(expected_md5_path, archive)
    actual_md5 = md5_file(archive)
    if actual_md5 != EXPECTED_MD5:
        raise ValueError(f"ExtendedMouseAtlas MD5 mismatch: expected {EXPECTED_MD5}, got {actual_md5}")
    wt_attestation = verify_source_wt_attestation(archive.parent / "publication.html")
    extracted = extract_outer_metadata(
        archive,
        archive.parent,
        include_source_h5ad=True,
    )
    if not input_h5ad.is_file():
        raise FileNotFoundError(input_h5ad)
    exact, obs, data_audit = load_exact_stage_input(
        input_h5ad,
        metadata_csv,
        output_dir / "data",
        source_wt_attested=True,
        wt_evidence=f"{wt_attestation['path']}:E8.5-E9.5 embryo collection for the extended atlas",
        gene_metadata_csv=archive.parent / "metadata_genes.csv",
        alias_manifest_path=PANEL_ALIAS_MANIFEST,
    )
    data_audit.update({"archive_bytes": archive.stat().st_size, "archive_md5": actual_md5, "archive_sha256": sha256_file(archive), "archive_expected_md5_file": str(expected_md5_path), "official_md5_manifest": official_md5, "outer_members": extracted, "wt_attestation_source": wt_attestation})
    json_write(output_dir / "metrics/data_audit.json", data_audit)
    collectri, omnipath, snapshot_summaries = _load_network_snapshots(repo)
    state_gate_path, state_join = build_state_join(exact, obs, collectri, omnipath, output_dir)
    method_results = {
        "CellOracle": run_celloracle(exact, output_dir, log),
        "scTenifoldNet/scTenifoldKnk": run_sctenifold(exact, output_dir, log),
    }
    json_write(output_dir / "metrics/tool_execution.json", method_results)
    state_response_support = _build_state_response_support(method_results, output_dir, state_join)
    json_write(output_dir / "metrics/state_response_support.json", state_response_support)
    source_rows, combined = combine_routes(output_dir, state_join, method_results)
    stability = {
        target: _state_sampling_status(output_dir / f"celloracle/{target}_state_sampling.tsv")
        for target in ("Gata4", "Gata6", "Ctnnb1")
    }
    json_write(output_dir / "metrics/stability.json", stability)
    source_files = {
        "ExtendedMouseAtlas_archive": archive,
        "ExtendedMouseAtlas_input_h5ad": input_h5ad,
        "ExtendedMouseAtlas_metadata_cells": metadata_csv,
        "ExtendedMouseAtlas_metadata_genes": archive.parent / "metadata_genes.csv",
        "ExtendedMouseAtlas_official_md5": expected_md5_path,
        "official_WT_attestation": archive.parent / "publication.html",
        "T3_panel_alias_manifest": PANEL_ALIAS_MANIFEST,
        "T3_panel_alias_source_Bex3": ROOT / "infra/external_data/quarantine/T3-S1A-STATE-JOIN/gene_alias_sources/MGI_1338016_Bex3.html",
        "T3_panel_alias_source_Ccn5": ROOT / "infra/external_data/quarantine/T3-S1A-STATE-JOIN/gene_alias_sources/MMRRC_43087_Ccn5.html",
        "T3_panel_alias_source_Cemip2": ROOT / "infra/external_data/quarantine/T3-S1A-STATE-JOIN/gene_alias_sources/MGI_1890373_Cemip2.html",
        "T3_panel_alias_source_Cnmd": ROOT / "infra/external_data/quarantine/T3-S1A-STATE-JOIN/gene_alias_sources/MGI_1341171_Cnmd.html",
        "T3_panel_alias_source_Selenop": ROOT / "infra/external_data/quarantine/T3-S1A-STATE-JOIN/gene_alias_sources/MGI_894288_Selenop.html",
        "sanitized_state_input_counts": output_dir / "data/state_input_counts.mtx",
        "sanitized_state_input_genes": output_dir / "data/state_input_genes.tsv",
        "sanitized_state_metadata": output_dir / "data/metadata_cells_sanitized.tsv",
        "OmniPath_snapshot": OMNIPATH_DIR / "omnipath_mouse_full.tsv",
        "CollecTRI_snapshot": COLLECTRI_DIR / "collectri_mouse_full.tsv",
        "parent_E8.75_h5ad": PARENT_PATH,
        "T3_panel": PANEL_PATH,
        "CellOracle_mm10_base_GRN": CELLORACLE_GRN_FILE,
        "CellOracle_mm10_base_GRN_manifest": CELLORACLE_GRN_DIR.parent / "snapshot_manifest.json",
    }
    source_hashes, source_artifacts = _source_artifact_records(source_files, repo)
    route_admission = {}
    for route_id, records in combined["route_records"].items():
        route_admission[route_id] = _assess_route(
            route_id, records, method_results, stability, state_join
        )
        route_admission[route_id]["state_mapping_audit"] = combined["state_mapping_audit"]
        route_admission[route_id]["state_response_support"] = state_response_support
        condition = route_id.split("::", 1)[0]
        route_targets = CONDITIONS[condition]["targets"]
        prior_path = Path(combined["route_reports"][route_id]["prior"])
        evidence_path = Path(combined["route_reports"][route_id]["evidence"])
        route_admission[route_id]["prior_path"] = prior_path.relative_to(output_dir).as_posix()
        route_admission[route_id]["evidence_path"] = evidence_path.relative_to(output_dir).as_posix()
        route_admission[route_id]["evidence_paths"] = [
            route_admission[route_id]["prior_path"],
            route_admission[route_id]["evidence_path"],
            Path(combined["route_reports"][route_id]["vote_path"]).relative_to(output_dir).as_posix(),
            "intermediates/state_gate.tsv",
            "intermediates/state_activity.tsv",
            "metrics/data_audit.json",
            "metrics/tool_execution.json",
            "metrics/stability.json",
            "metrics/state_response_support.json",
        ]
        route_admission[route_id]["source_hashes"] = source_hashes
        route_admission[route_id]["source_artifacts"] = source_artifacts
        route_admission[route_id]["method_status"] = _route_method_summary(
            method_results, route_targets, output_dir
        )
    artifact_manifest_path = _write_artifact_manifest(output_dir)
    artifact_manifest_relative = artifact_manifest_path.relative_to(output_dir).as_posix()
    artifact_manifest_sha256 = sha256_file(artifact_manifest_path)
    for route in route_admission.values():
        route["prior_sha256"] = sha256_file(output_dir / route["prior_path"])
        route["evidence_sha256"] = sha256_file(output_dir / route["evidence_path"])
        route["artifact_manifest_path"] = artifact_manifest_relative
        route["artifact_manifest_sha256"] = artifact_manifest_sha256
        route["evidence_hashes"] = _hash_relative_paths(output_dir, route["evidence_paths"])
    passed = [route for route in route_admission.values() if route["status"] == "PASS"]
    blocked = [route for route in route_admission.values() if route["status"] == "BLOCKED"]
    if len(passed) == len(ROUTES):
        global_status, outcome = "PASS", "PRIOR_GATE_PASS"
    elif passed:
        global_status, outcome = "HOLD", "PARTIAL_ROUTE_PASS"
    elif blocked:
        global_status, outcome = "BLOCKED", "BLOCKED"
    else:
        global_status, outcome = "HOLD", "HOLD_AS_COMPONENT"
    route_criterion_result = (
        "PASS" if len(passed) == len(ROUTES)
        else "BLOCKED" if blocked and not passed
        else "FAIL"
    )
    state_criterion_result = (
        "PASS"
        if all(route["state_join_gate"]["status"] == "PASS" for route in route_admission.values())
        else "BLOCKED"
        if any(route["state_join_gate"]["status"] == "BLOCKED" for route in route_admission.values())
        else "FAIL"
    )
    gate_report = {
        "schema": "gate_report.v2", "task_id": "T3-S1A-STATE-JOIN", "gate_id": "route_specific_prior_gate_v2",
        "status": global_status, "outcome": outcome,
        "blockers": sorted({blocker for route in route_admission.values() for blocker in route["blockers"]}),
        "blocks_submission": False, "candidate_generation": False, "server_submission": False,
        "routes": list(route_admission.values()),
        "state_mapping_audit": combined["state_mapping_audit"],
        "criteria": [
            {"name": "exact_E8.75_WT_raw_counts", "result": "PASS", "evidence": "metrics/data_audit.json"},
            {"name": "state_join_and_activity", "result": state_criterion_result, "evidence": "intermediates/state_gate.tsv"},
            {"name": "CellOracle_real_api", "result": _gate_result(method_results["CellOracle"]["status"]), "evidence": "metrics/tool_execution.json"},
            {"name": "scTenifold_real_api", "result": _gate_result(method_results["scTenifoldNet/scTenifoldKnk"]["status"]), "evidence": "metrics/tool_execution.json"},
            {"name": "route_specific_admission", "result": route_criterion_result, "evidence": "metrics/gate_report.v2.json"},
        ],
        "evidence_paths": [
            "intermediates/source_votes.tsv", "intermediates/state_gate.tsv",
            "metrics/data_audit.json", "metrics/tool_execution.json",
            "metrics/stability.json", "metrics/state_response_support.json",
        ],
        "state_response_support": state_response_support,
        "notes": "Prior/gate evidence only; no H5AD, scorer, server submission, or scientific causal validation. blocks_submission: false.",
        "source_snapshots": snapshot_summaries,
    }
    json_write(output_dir / "metrics/gate_report.v2.json", gate_report)
    versions = {
        "CellOracle": method_results["CellOracle"],
        "scTenifoldNet_scTenifoldKnk": method_results["scTenifoldNet/scTenifoldKnk"],
        "python_environment": str(ROOT / ".venvs/ve-t3-prior/bin/python"),
        "R_LIBS_USER": f"{output_dir / 'deployment/Rlib' if (output_dir / 'deployment/Rlib').is_dir() else NEW_RLIB}:{OLD_RLIB}:{USER_RLIB}", "seed": SEED,
    }
    json_write(output_dir / "TOOL_VERSIONS.json", versions)
    write_tsv(output_dir / "DATA_SOURCES_USED.tsv", [
        {"source": "ExtendedMouseAtlas", "role": "exact E8.75 WT raw-count state/activity input", "status": "PASS", "path": str(archive), "sha256": sha256_file(archive), "license": "CC BY 4.0 publication / official supplemental archive"},
        {"source": "OmniPath", "role": "full mouse directed signaling snapshot", "status": "AUDITED_PASS", "path": str(OMNIPATH_DIR / "omnipath_mouse_full.tsv"), "sha256": sha256_file(OMNIPATH_DIR / "omnipath_mouse_full.tsv"), "license": "academic API access"},
        {"source": "CollecTRI", "role": "full mouse signed TF-target snapshot", "status": "AUDITED_PASS", "path": str(COLLECTRI_DIR / "collectri_mouse_full.tsv"), "sha256": sha256_file(COLLECTRI_DIR / "collectri_mouse_full.tsv"), "license": "academic OmniPath access"},
    ], ["source", "role", "status", "path", "sha256", "license"])
    (output_dir / "METHOD_DISCLOSURE.md").write_text(
        "# T3-S1A method disclosure\n\n"
        "CellOracle is executed through the installed upstream API on exact-stage WT raw counts and its bundled mm10 promoter base GRN. CellOracle state-response/coverage files are modelled response evidence only and do not validate in vivo activity. scTenifoldKnk is executed through R; scTenifoldNet is its network engine. scTenifold diffRegulation is retained as unsigned rank evidence only. Curated edges/pathways provide provenance and any explicit sign; occupancy provides directness only. This bundle cannot be used as a candidate or leaderboard result.\n",
        encoding="utf-8",
    )
    (output_dir / "config_resolved.yaml").write_text(
        "task: T3-S1A-STATE-JOIN\nseed: 20260830\nexact_stage: E8.75\nnetwork_used: true\nexternal_downloads_used: true\ncelloracle_target_process_isolation: fork\ncelloracle_target_checkpoint: true\nruntime_observation_window_minutes_per_target: 60\nruntime_check_interval_seconds: 60\ncelloracle_external_state_projection: recorded_parent_state_mapping\ncelloracle_state_response_support: true\nstate_response_claim: modelled_state_response_only\ncandidate_generation: false\nserver_submission: false\nconfidence_policy: nullable_uncalibrated_external_evidence\nstop_after: route_gate_written\n",
        encoding="utf-8",
    )
    completion = {
        "task": "T3-S1A-STATE-JOIN", "status": outcome, "global_status": global_status,
        "routes": {route_id: {key: value for key, value in route.items() if key != "stability"} for route_id, route in route_admission.items()},
        "candidate_generation": False, "server_submission": False, "blocks_submission": False,
        "core_computation_status": {"CellOracle": method_results["CellOracle"]["status"], "scTenifoldNet_scTenifoldKnk": method_results["scTenifoldNet/scTenifoldKnk"]["status"]},
        "limitations": ["scientific validation is NOT_RUN", "no H5AD/candidate/local scorer/server score", "unsigned scTenifold output cannot provide sign"],
    }
    json_write(output_dir / "COMPLETION_REPORT.json", completion)
    (output_dir / "COMPLETION_REPORT.md").write_text(
        "# T3-S1A completion report\n\n"
        f"- Global outcome: `{outcome}` (`{global_status}`)\n"
        "- Candidate generation: `false`\n"
        "- Server submission: `false`\n"
        "- Scientific validation: `NOT_RUN`\n"
        "- Submission blocking: `false`\n\n"
        + "\n".join(
            f"- `{route_id}`: `{route['status']}`; blockers={route['blockers']}"
            for route_id, route in route_admission.items()
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "RESULT.md").write_text(
        f"# T3-S1A result\n\nGlobal gate: `{outcome}` (`{global_status}`).\n\n"
        + "\n".join(f"- `{route_id}`: `{route['status']}`; blockers={route['blockers']}" for route_id, route in route_admission.items())
        + "\n\nNo H5AD, candidate, scorer, server submission, or leaderboard claim was produced. `blocks_submission: false`.\n",
        encoding="utf-8",
    )
    log.extend([f"global_outcome={outcome}", "candidate_generation=false", "server_submission=false"])
    (output_dir / "run.log").write_text("\n".join(log) + "\n", encoding="utf-8")
    manifest_files = []
    for path in sorted(output_dir.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.json" and not _is_transient_runtime_artifact(path):
            manifest_files.append({"path": str(path.relative_to(output_dir)), "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    json_write(output_dir / "MANIFEST.json", {"schema": "ve.t3.s1a-state-join-manifest.v1", "task": "T3-S1A-STATE-JOIN", "files": manifest_files, "created_at": datetime.now(timezone.utc).isoformat(), "candidate_generation": False, "server_submission": False, "blocks_submission": False})
    return {"outcome": outcome, "status": global_status, "routes": route_admission, "output_dir": str(output_dir)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--input-h5ad", type=Path, default=SOURCE_H5AD_DEFAULT)
    parser.add_argument("--metadata-csv", type=Path, default=METADATA_DEFAULT)
    parser.add_argument("--archive", type=Path, default=ARCHIVE_DEFAULT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--extract-metadata-only", action="store_true")
    args = parser.parse_args(argv)
    if args.extract_metadata_only:
        print(json.dumps(extract_outer_metadata(args.archive, args.archive.parent), ensure_ascii=False, indent=2))
        return 0
    result = run_task(args.repo, args.input_h5ad, args.metadata_csv, args.archive, args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
