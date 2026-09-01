#!/usr/bin/env python3
"""Audit small processed GEO perturbation files as independent evidence.

The files are used only for provenance and descriptive perturbation-response
checks.  They are not merged into the E8.75 challenge input and cannot open a
T3 candidate gate because their stage/tissue differs from the target task.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ATOM = "T3-S1D-INDEPENDENT-ACTIVITY-EVIDENCE-20260901-v1"
OUTPUT_DEFAULT = ROOT / "artifacts/tool_integration" / ATOM
SCRIPT_PATH = Path(__file__).resolve()
PANEL_PATH = ROOT / "data/gene_panel/T3__gata4.genes.txt"
DATA_ROOT = ROOT / "infra/external_data/quarantine/T3-S1D-INDEPENDENT-ACTIVITY-EVIDENCE"
SEED = 20260830


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


def _numeric_values(frame: pd.DataFrame, columns: list[str], row_index: Any) -> np.ndarray:
    values = pd.to_numeric(frame.loc[row_index, columns], errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("processed evidence contains non-finite target values")
    return values


def _effect_rows(
    frame: pd.DataFrame,
    *,
    symbol_column: str,
    study: str,
    target: str,
    perturbation: str,
    control_columns: list[str],
    perturb_columns: list[str],
    panel: list[str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if symbol_column not in frame.columns:
        raise ValueError(f"{study}: missing symbol column {symbol_column}")
    for column in control_columns + perturb_columns:
        if column not in frame.columns:
            raise ValueError(f"{study}: missing sample column {column}")
    indexed = frame.copy()
    indexed[symbol_column] = indexed[symbol_column].astype(str).str.strip()
    sample_columns = control_columns + perturb_columns
    for column in sample_columns:
        indexed[column] = pd.to_numeric(indexed[column], errors="coerce")
    if indexed[sample_columns].isna().any().any():
        raise ValueError(f"{study}: processed evidence contains non-numeric sample values")
    duplicate_rows = int(indexed[symbol_column].duplicated().sum())
    duplicate_symbols = int(indexed.loc[indexed[symbol_column].duplicated(), symbol_column].nunique())
    # Some GEO processed tables repeat identical probe/gene rows.  Collapse
    # them deterministically, record the operation, and never count a probe
    # duplicate as an additional biological replicate.
    indexed = indexed.groupby(symbol_column, sort=False, as_index=True)[sample_columns].mean()
    if target not in indexed.index:
        raise ValueError(f"{study}: target {target} is absent from processed matrix")

    control_target = _numeric_values(indexed, control_columns, target)
    perturb_target = _numeric_values(indexed, perturb_columns, target)
    control_mean = float(np.mean(control_target))
    perturb_mean = float(np.mean(perturb_target))
    target_log2fc = math.log2((perturb_mean + 1e-9) / (control_mean + 1e-9))
    target_replicate_signs = [int(np.sign(value - control_mean)) for value in perturb_target]
    target_expected_sign = -1
    target_consistent = sum(sign == target_expected_sign for sign in target_replicate_signs)

    rows: list[dict[str, Any]] = []
    panel_present = 0
    for gene in panel:
        if gene not in indexed.index:
            continue
        panel_present += 1
        control = _numeric_values(indexed, control_columns, gene)
        perturb = _numeric_values(indexed, perturb_columns, gene)
        control_mean_gene = float(np.mean(control))
        perturb_mean_gene = float(np.mean(perturb))
        log2fc = math.log2((perturb_mean_gene + 1e-9) / (control_mean_gene + 1e-9))
        rows.append(
            {
                "study": study,
                "target_gene": target,
                "response_gene": gene,
                "perturbation": perturbation,
                "control_n": len(control_columns),
                "perturbation_n": len(perturb_columns),
                "control_mean": control_mean_gene,
                "perturbation_mean": perturb_mean_gene,
                "log2fc_perturb_minus_control": log2fc,
                "direction": "DOWN" if log2fc < 0 else "UP" if log2fc > 0 else "ZERO",
                "activity_eligible_for_E875": False,
                "signed_family_eligible": False,
            }
        )
    summary = {
        "study": study,
        "target_gene": target,
        "response_gene_count": len(rows),
        "panel_present_count": panel_present,
        "control_columns": control_columns,
        "perturbation_columns": perturb_columns,
        "target_control_mean": control_mean,
        "target_perturbation_mean": perturb_mean,
        "target_log2fc_perturb_minus_control": target_log2fc,
        "target_expected_direction": "DOWN",
        "target_replicate_direction_signs": target_replicate_signs,
        "target_replicate_direction_consistent_n": target_consistent,
        "target_replicate_direction_consistent_fraction": target_consistent / len(target_replicate_signs),
        "panel_down_count": sum(row["direction"] == "DOWN" for row in rows),
        "panel_up_count": sum(row["direction"] == "UP" for row in rows),
        "panel_zero_count": sum(row["direction"] == "ZERO" for row in rows),
        "panel_median_abs_log2fc": float(np.median([abs(row["log2fc_perturb_minus_control"]) for row in rows])) if rows else None,
        "duplicate_symbol_rows_collapsed": duplicate_rows,
        "duplicate_symbol_count_collapsed": duplicate_symbols,
        "duplicate_aggregation": "mean_by_gene_symbol" if duplicate_rows else "none",
        "activity_eligible_for_E875": False,
        "signed_family_eligible": False,
    }
    return rows, summary


def _inventory() -> list[dict[str, Any]]:
    return [
        {
            "accession": "GSE156307",
            "target_gene": "Gata4",
            "organism": "Mus musculus",
            "stage": "E14.5",
            "tissue": "embryonic hindstomach epithelium",
            "perturbation": "Gata4 conditional knockout vs WT",
            "sample_design": "HS controls C2-C4; HS cKO M1-M5 in processed file; series also contains forestomach KI",
            "processed_file": "GSE156307/GSE156307_FPKM_G4cKO_G4cKI.xlsx",
            "source_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE156307",
            "download_url": "https://www.ncbi.nlm.nih.gov/geo/download/?acc=GSE156307&file=GSE156307_FPKM_G4cKO_G4cKI.xlsx&format=file",
            "metadata_status": "PASS",
            "task_compatibility": "NO_STAGE_TISSUE_MATCH",
            "evidence_grade": "B_CONTEXT_ONLY",
            "exclusion_reason": "E14.5 stomach is not the E8.75 target state; one external family only",
        },
        {
            "accession": "GSE255237",
            "target_gene": "Gata6",
            "organism": "Mus musculus",
            "stage": "E11.5",
            "tissue": "outflow tract",
            "perturbation": "Gata6STOP/+ vs WT",
            "sample_design": "series states three pools per genotype; processed file has 4 MUT and 3 WT columns",
            "processed_file": "GSE255237/GSE255237_NormCounts.txt.gz",
            "source_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE255237",
            "download_url": "https://www.ncbi.nlm.nih.gov/geo/download/?acc=GSE255237&file=GSE255237_NormCounts.txt.gz&format=file",
            "metadata_status": "DESIGN_COUNT_CONFLICT",
            "task_compatibility": "NO_STAGE_TISSUE_MATCH",
            "evidence_grade": "B_CONTEXT_ONLY",
            "exclusion_reason": "E11.5 OFT and heterozygous dosage do not match E8.75 target state; series design and sample columns conflict",
        },
        {
            "accession": "GSE67463",
            "target_gene": "Ctnnb1",
            "organism": "Mus musculus",
            "stage": "E14.5",
            "tissue": "XX/XY fetal gonad somatic cells",
            "perturbation": "Ctnnb1 knockout vs control",
            "sample_design": "series lists four control and four Ctnnb1KO replicates per sex, with Sox9 and double-KO branches",
            "processed_file": "NOT_DOWNLOADED_METADATA_ONLY",
            "source_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE67463",
            "download_url": "",
            "metadata_status": "PASS",
            "task_compatibility": "NO_STAGE_TISSUE_MATCH",
            "evidence_grade": "B_CONTEXT_ONLY",
            "exclusion_reason": "E14.5 gonad is not the E8.75 target state; processed file not downloaded in this atom",
        },
        {
            "accession": "GSE50859",
            "target_gene": "Ctnnb1",
            "organism": "Mus musculus",
            "stage": "E15.5-E17.5",
            "tissue": "footpad skin",
            "perturbation": "skin-specific beta-catenin knockout vs WT",
            "sample_design": "two samples per genotype at each of three stages",
            "processed_file": "NOT_DOWNLOADED_METADATA_ONLY",
            "source_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE50859",
            "download_url": "",
            "metadata_status": "PASS",
            "task_compatibility": "NO_STAGE_TISSUE_MATCH",
            "evidence_grade": "B_CONTEXT_ONLY",
            "exclusion_reason": "late skin stages are not the E8.75 target state; processed file not downloaded in this atom",
        },
        {
            "accession": "GSE70134",
            "target_gene": "Ctnnb1",
            "organism": "Mus musculus",
            "stage": "E11.5",
            "tissue": "dorso-medial pallium",
            "perturbation": "series labels control and mutant; target identity not confirmed in series metadata",
            "sample_design": "three litter-labelled controls and three mutants",
            "processed_file": "NOT_DOWNLOADED_METADATA_ONLY",
            "source_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE70134",
            "download_url": "",
            "metadata_status": "TARGET_IDENTITY_UNCONFIRMED",
            "task_compatibility": "NOT_IDENTIFIABLE",
            "evidence_grade": "C_METADATA_ONLY",
            "exclusion_reason": "series metadata does not establish that mutant is Ctnnb1 perturbation; processed file not downloaded",
        },
    ]


def _artifact_manifest(output_dir: Path) -> dict[str, Any]:
    files = []
    for path in sorted(output_dir.rglob("*")):
        if not path.is_file() or path.name == "artifact_manifest.stable.json":
            continue
        files.append({"path": path.relative_to(output_dir).as_posix(), "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    return {
        "schema": "ve.t3.s1d-independent-activity-artifact-manifest.v1",
        "task": "T3-S1D-INDEPENDENT-ACTIVITY-EVIDENCE",
        "atom": ATOM,
        "files": files,
    }


def run(*, output_dir: Path = OUTPUT_DEFAULT) -> dict[str, Any]:
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise FileExistsError(f"S1D output already exists: {output_dir}")
    output_dir.mkdir(parents=True)
    try:
        panel = panel_genes()
        g4_path = DATA_ROOT / "GSE156307/GSE156307_FPKM_G4cKO_G4cKI.xlsx"
        g6_path = DATA_ROOT / "GSE255237/GSE255237_NormCounts.txt.gz"
        for path in (g4_path, g6_path):
            if not path.is_file():
                raise FileNotFoundError(path)
        g4 = pd.read_excel(g4_path)
        g6 = pd.read_csv(g6_path, sep="\t")
        g4_rows, g4_summary = _effect_rows(
            g4,
            symbol_column="GENE_ID",
            study="GSE156307",
            target="Gata4",
            perturbation="Gata4 conditional knockout vs WT; E14.5 hindstomach",
            control_columns=["3_HS_C2", "16_HS_C3", "19_HS_C4"],
            perturb_columns=["6_HS_M1", "7_HS_M2", "20_HS_M3", "27_HS_M4", "29_HS_M5"],
            panel=panel,
        )
        g6_rows, g6_summary = _effect_rows(
            g6,
            symbol_column="Name",
            study="GSE255237",
            target="Gata6",
            perturbation="Gata6STOP/+ vs WT; E11.5 OFT",
            control_columns=["S2_WT3_EAX", "S3_WT4_EAX", "S4_WT5_EAX"],
            perturb_columns=["S5_MUT1_EAX", "S6_MUT3_EAX", "S7_MUT4_EAX", "S8_MUT5_EAX"],
            panel=panel,
        )
        inventory = _inventory()
        inventory_by_accession = {row["accession"]: row for row in inventory}
        inventory_by_accession["GSE156307"].update(
            {
                "downloaded_bytes": g4_path.stat().st_size,
                "downloaded_sha256": sha256_file(g4_path),
                "processed_shape": list(g4.shape),
                "sample_columns_audited": 14,
            }
        )
        inventory_by_accession["GSE255237"].update(
            {
                "downloaded_bytes": g6_path.stat().st_size,
                "downloaded_sha256": sha256_file(g6_path),
                "processed_shape": list(g6.shape),
                "sample_columns_audited": 7,
            }
        )
        output_data = output_dir / "data"
        metrics = output_dir / "metrics"
        write_tsv(
            output_data / "evidence_inventory.tsv",
            inventory,
            [
                "accession", "target_gene", "organism", "stage", "tissue", "perturbation", "sample_design",
                "processed_file", "source_url", "download_url", "metadata_status", "task_compatibility",
                "evidence_grade", "exclusion_reason", "downloaded_bytes", "downloaded_sha256",
                "processed_shape", "sample_columns_audited",
            ],
        )
        write_tsv(
            output_data / "panel_effect_summary.tsv",
            g4_rows + g6_rows,
            [
                "study", "target_gene", "response_gene", "perturbation", "control_n", "perturbation_n",
                "control_mean", "perturbation_mean", "log2fc_perturb_minus_control", "direction",
                "activity_eligible_for_E875", "signed_family_eligible",
            ],
        )
        write_json(
            metrics / "source_audit.json",
            {
                "schema": "ve.t3.s1d-source-audit.v1",
                "retrieved_at": "2026-09-01",
                "source_type": "NCBI GEO public series metadata plus two small processed files",
                "raw_data_downloaded": False,
                "new_external_data_downloaded": True,
                "files": {
                    "GSE156307": {"path": repo_relative(g4_path), "sha256": sha256_file(g4_path), "bytes": g4_path.stat().st_size, "shape": list(g4.shape)},
                    "GSE255237": {"path": repo_relative(g6_path), "sha256": sha256_file(g6_path), "bytes": g6_path.stat().st_size, "shape": list(g6.shape)},
                },
                "inventory": inventory,
                "panel_gene_count": len(panel),
            },
        )
        write_json(metrics / "processed_effects.json", {"GSE156307": g4_summary, "GSE255237": g6_summary})
        gate = {
            "schema": "ve.t3.s1d-independent-activity-gate.v1",
            "task": "T3-S1D-INDEPENDENT-ACTIVITY-EVIDENCE",
            "atom": ATOM,
            "status": "HOLD_INSUFFICIENT_MATCHED_ACTIVITY_EVIDENCE",
            "metadata_evidence": "PASS",
            "processed_activity_context": "PASS_FOR_TWO_OFF_TARGET_CONTEXTS",
            "target_task_matched_activity": "NOT_IDENTIFIABLE",
            "independent_signed_family_count_for_E875": 0,
            "candidate_generation": False,
            "server_submission": False,
            "blocks_submission": False,
            "reason": "Gata4/Gata6 processed perturbation effects are from E14.5 stomach or E11.5 OFT, not E8.75 target state; Ctnnb1 evidence remains metadata-only.",
            "scientific_statement": "These records support that target perturbations can produce expression responses in other contexts; they do not transfer a signed state-specific effect into T3 E8.75.",
        }
        write_json(metrics / "gate_report.json", gate)
        completion = {
            "schema": "ve.t3.s1d-completion.v1",
            "task": "T3-S1D-INDEPENDENT-ACTIVITY-EVIDENCE",
            "atom": ATOM,
            "status": gate["status"],
            "script": {"path": repo_relative(SCRIPT_PATH), "sha256": sha256_file(SCRIPT_PATH)},
            "processed_studies": ["GSE156307", "GSE255237"],
            "metadata_only_studies": ["GSE67463", "GSE50859", "GSE70134"],
            "candidate_generation": False,
            "server_submission": False,
            "blocks_submission": False,
        }
        write_json(metrics / "completion_report.json", completion)
        (output_dir / "RESULT.md").write_text(
            f"# {ATOM}\n\n"
            "Two small processed GEO perturbation files were audited. Both show "
            "descriptive target-response context, but neither matches the T3 E8.75 "
            "state/tissue; Ctnnb1 remains metadata-only. Candidate generation stays "
            "closed.\n",
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
