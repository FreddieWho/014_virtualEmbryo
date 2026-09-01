from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from collections import defaultdict
from typing import Iterable, Mapping, Any
from .types import SignedPriorRecord


def _bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "pass"}


def _float(value: Any, default: float | None = None) -> float | None:
    if value in (None, ""):
        return default
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("numeric vote fields must be finite")
    return number


def _tokens(value: Any) -> tuple[str, ...]:
    if value in (None, ""):
        return ()
    if isinstance(value, (list, tuple, set)):
        values = value
    else:
        values = str(value).replace(",", ";").split(";")
    return tuple(sorted({str(item).strip() for item in values if str(item).strip()}))


def _gate_lookup(path: Path) -> dict[tuple[str, str, str], tuple[float, bool, bool, str]]:
    lookup: dict[tuple[str, str, str], tuple[float, bool, bool, str]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("state gate table has no header")
        required = {"state", "gate_pass"}
        missing = required.difference(reader.fieldnames)
        if missing:
            raise ValueError(f"state gate table missing fields: {sorted(missing)}")
        probability_fields = {"lineage_gate", "p_mesp1_lineage"}.intersection(reader.fieldnames)
        if not probability_fields:
            raise ValueError(
                "state gate table must include lineage_gate or p_mesp1_lineage"
            )
        for row in reader:
            condition = str(row.get("condition_id", ""))
            stage = str(row.get("stage", ""))
            state = str(row["state"])
            present_probabilities: list[float] = []
            for field in ("lineage_gate", "p_mesp1_lineage"):
                if field in probability_fields and row.get(field, "") not in (None, ""):
                    parsed_probability = _float(row.get(field))
                    if parsed_probability is not None:
                        present_probabilities.append(parsed_probability)
            if len(present_probabilities) > 1 and not math.isclose(
                present_probabilities[0], present_probabilities[1], rel_tol=0.0, abs_tol=1e-12
            ):
                raise ValueError("lineage_gate and p_mesp1_lineage disagree")
            probability = present_probabilities[0] if present_probabilities else None
            if probability is None:
                # Missing probability is not a valid positive gate.  Keep the
                # lookup explicit and fail closed instead of trusting a stale
                # gate_pass token.
                probability = 0.0
            if not 0.0 <= probability <= 1.0:
                raise ValueError("state gate probability must be in [0, 1]")
            passed = _bool(row.get("gate_pass")) if row.get("gate_pass") not in (None, "") else False
            if passed and probability <= 0.0:
                raise ValueError("gate_pass=true is inconsistent with missing/zero lineage probability")
            activity_pass = (
                _bool(row.get("activity_gate_pass"))
                if row.get("activity_gate_pass") not in (None, "")
                else False
            )
            activity_status = str(row.get("activity_evidence_status", "NOT_RUN")).strip() or "NOT_RUN"
            state_join_status = str(row.get("state_join_status", "PASS")).strip() or "PASS"
            activity_pass = activity_pass and state_join_status == "PASS"
            if state_join_status != "PASS" and activity_status == "PASS":
                activity_status = f"STATE_JOIN_{state_join_status}"
            key = (condition, stage, state)
            if key in lookup:
                previous_probability, previous_pass, previous_activity, previous_activity_status = lookup[key]
                lookup[key] = (
                    min(previous_probability, probability),
                    previous_pass and passed,
                    previous_activity and activity_pass,
                    previous_activity_status if previous_activity_status != "PASS" else activity_status,
                )
            else:
                lookup[key] = (probability, passed, activity_pass, activity_status)
    return lookup


def _lookup_gate(
    lookup: Mapping[tuple[str, str, str], tuple[float, bool, bool, str]],
    condition: str,
    stage: str,
    state: str,
) -> tuple[float, bool, bool, str]:
    for key in (
        (condition, stage, state),
        (condition, "", state),
        ("", stage, state),
        ("", "", state),
    ):
        if key in lookup:
            return lookup[key]
    return 0.0, False, False, "NOT_RUN"


def _record_json(record: SignedPriorRecord) -> dict[str, Any]:
    return {
        "target_gene": record.target_gene,
        "condition_id": record.condition_id,
        "stage": record.stage,
        "state": record.state,
        "response_gene": record.response_gene,
        "sign": record.sign,
        "rank_score": record.rank_score,
        "confidence": record.confidence,
        "lineage_gate": record.lineage_gate,
        "dosage_fraction": record.dosage_fraction,
        "source_families": list(record.source_families),
        "directness_score": record.directness_score,
        "conflict_flag": record.conflict_flag,
        "provenance": list(record.provenance),
    }


def combine_prior_votes(
    *,
    vote_tables: Iterable[Path],
    state_gate_path: Path,
    lane: str,
    output_json: Path,
    evidence_tsv: Path,
    config: Mapping[str, Any],
) -> list[SignedPriorRecord]:
    """Combine independent evidence families into an auditable signed prior."""
    lane = str(lane)
    min_families = int(
        config.get("min_independent_families", 2 if "STRICT" in lane else 1)
    )
    if min_families < 1:
        raise ValueError("min_independent_families must be positive")
    max_fraction = float(
        config.get("max_nonzero_fraction", 0.10 if "STRICT" in lane else 0.25)
    )
    if not 0.0 < max_fraction <= 1.0:
        raise ValueError("max_nonzero_fraction must be in (0, 1]")
    panel_size_config = config.get("panel_size")
    panel_size = int(panel_size_config) if panel_size_config is not None else None
    dosage_fractions = dict(config.get("dosage_fractions", {}))
    directness_required_default = bool(config.get("directness_required", False))
    directness_required_targets = set(config.get("directness_required_targets", []))
    directness_threshold = float(config.get("directness_threshold", 0.0))
    signaling_required_default = bool(config.get("signaling_path_required", False))
    signaling_required_targets = set(config.get("signaling_path_required_targets", []))
    signaling_families = set(
        config.get(
            "signaling_families",
            ["DIRECTED_SIGNALING", "SIGNALING_PATH", "CURATED_SIGNALING"],
        )
    )
    require_state_activity = bool(config.get("require_state_activity", False))
    gates = _gate_lookup(state_gate_path)
    groups: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for vote_table in vote_tables:
        with Path(vote_table).open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            if reader.fieldnames is None:
                raise ValueError(f"vote table has no header: {vote_table}")
            required = {
                "target_gene", "condition_id", "stage", "state", "response_gene",
                "sign", "rank_score", "confidence", "evidence_family",
            }
            missing = required.difference(reader.fieldnames)
            if missing:
                raise ValueError(f"vote table missing fields: {sorted(missing)}")
            for raw in reader:
                parsed = dict(raw)
                parsed["sign"] = int(raw["sign"])
                if parsed["sign"] not in (-1, 0, 1):
                    raise ValueError("vote sign must be -1, 0, or 1")
                parsed["rank_score"] = _float(raw["rank_score"], 0.0)
                parsed["confidence"] = _float(raw["confidence"], None)
                if not 0.0 <= parsed["rank_score"] <= 1.0:
                    raise ValueError("vote rank_score must be in [0, 1]")
                if parsed["confidence"] is not None and not 0.0 <= parsed["confidence"] <= 1.0:
                    raise ValueError("vote confidence must be None or in [0, 1]")
                parsed["directness_score"] = _float(raw.get("directness_score"))
                parsed["dosage_fraction"] = _float(raw.get("dosage_fraction"))
                if (
                    parsed["dosage_fraction"] is not None
                    and not 0.0 <= parsed["dosage_fraction"] <= 1.0
                ):
                    raise ValueError("vote dosage_fraction must be in [0, 1]")
                parsed["conflict_flag"] = _bool(raw.get("conflict_flag", False))
                parsed["evidence_family"] = str(raw["evidence_family"]).strip()
                if not parsed["evidence_family"]:
                    raise ValueError("evidence_family must not be empty")
                key = (
                    str(raw["target_gene"]), str(raw["condition_id"]), str(raw["stage"]),
                    str(raw["state"]), str(raw["response_gene"]),
                )
                groups[key].append(parsed)

    decisions: list[dict[str, Any]] = []
    for key, rows in sorted(groups.items()):
        target, condition, stage, state, response_gene = key
        lineage_gate, gate_pass, activity_gate_pass, activity_status = _lookup_gate(
            gates, condition, stage, state
        )
        nonzero_rows = [row for row in rows if row["sign"] != 0]
        family_signs: dict[str, set[int]] = defaultdict(set)
        for row in nonzero_rows:
            family_signs[row["evidence_family"]].add(row["sign"])
        all_signs = {sign for signs in family_signs.values() for sign in signs}
        conflict = bool({-1, 1}.intersection(all_signs)) and {-1, 1}.issubset(all_signs)
        conflict = conflict or any(row["conflict_flag"] for row in rows)
        source_families = tuple(sorted({row["evidence_family"] for row in rows}))
        sign_families = tuple(sorted(family_signs))
        directness_values = [
            row["directness_score"] for row in rows if row["directness_score"] is not None
        ]
        directness_score = max(directness_values) if directness_values else None
        dosage_values = {
            row["dosage_fraction"] for row in rows if row["dosage_fraction"] is not None
        }
        dosage_incomplete = bool(dosage_values) and sum(
            row["dosage_fraction"] is not None for row in rows
        ) != len(rows)
        expected_dosage = dosage_fractions.get(target)
        dosage_mismatch = (
            expected_dosage is not None
            and any(
                row["dosage_fraction"] is None
                or not math.isclose(float(row["dosage_fraction"]), float(expected_dosage), rel_tol=0.0, abs_tol=1e-12)
                for row in rows
            )
        )
        dosage_conflict = len(dosage_values) > 1 or dosage_incomplete or dosage_mismatch
        dosage_fraction = (
            float(expected_dosage)
            if expected_dosage is not None and not dosage_conflict
            else next(iter(dosage_values))
            if len(dosage_values) == 1 and not dosage_incomplete
            else None
        )
        path_present = any(
            row["evidence_family"] in signaling_families and row["sign"] != 0
            for row in rows
        )
        rank_values = [row["rank_score"] for row in nonzero_rows or rows]
        confidence_values = [
            row["confidence"]
            for row in (nonzero_rows or rows)
            if row["confidence"] is not None
        ]
        rank_score = sum(rank_values) / len(rank_values)
        confidence = (
            sum(confidence_values) / len(confidence_values)
            if confidence_values
            else None
        )
        provenance = tuple(
            sorted({token for row in rows for token in _tokens(row.get("provenance"))})
        )
        decision_sign = 0
        reason = "NO_SIGN_VOTE"
        blocked_families = {
            row["evidence_family"]
            for row in rows
            if row["evidence_family"] in {"BLOCKED_EXTERNAL_DATA", "BLOCKED_TOOLCHAIN"}
        }
        directness_required = directness_required_default or target in directness_required_targets
        signaling_required = signaling_required_default or target in signaling_required_targets
        if blocked_families:
            reason = "BLOCKED_EXTERNAL_DATA" if "BLOCKED_EXTERNAL_DATA" in blocked_families else "BLOCKED_TOOLCHAIN"
        elif not gate_pass:
            reason = "LINEAGE_GATE_FAIL"
        elif require_state_activity and not activity_gate_pass:
            reason = "STATE_ACTIVITY_GATE_FAIL"
        elif conflict:
            reason = "CONFLICT"
        elif dosage_conflict:
            reason = "DOSAGE_CONFLICT"
        elif len(sign_families) < min_families:
            reason = "INSUFFICIENT_INDEPENDENT_FAMILIES"
        elif directness_required and (
            directness_score is None or directness_score < directness_threshold
        ):
            reason = "DIRECTNESS_REQUIRED"
        elif signaling_required and not path_present:
            reason = "SIGNALING_PATH_REQUIRED"
        elif not nonzero_rows:
            reason = "NO_SIGN_VOTE"
        else:
            decision_sign = next(iter(all_signs))
            reason = "ELIGIBLE_PENDING_CAP"
        decisions.append(
            {
                "key": key,
                "target": target,
                "condition": condition,
                "stage": stage,
                "state": state,
                "response_gene": response_gene,
                "lineage_gate": lineage_gate,
                "activity_gate_pass": activity_gate_pass,
                "activity_evidence_status": activity_status,
                "dosage_fraction": dosage_fraction,
                "sign": decision_sign,
                "rank_score": rank_score,
                "confidence": confidence,
                "source_families": source_families,
                "sign_families": sign_families,
                "directness_score": directness_score,
                "conflict": conflict,
                "provenance": provenance,
                "reason": reason,
                "vote_signs": ";".join(str(row["sign"]) for row in rows),
                "vote_families": ";".join(row["evidence_family"] for row in rows),
            }
        )

    grouped_decisions: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for decision in decisions:
        grouped_decisions[
            (decision["target"], decision["condition"], decision["stage"], decision["state"])
        ].append(decision)
    for group_key, group in grouped_decisions.items():
        eligible = [item for item in group if item["sign"] != 0]
        effective_panel_size = panel_size or len(group)
        cap = max(1, int(math.floor(effective_panel_size * max_fraction)))
        eligible.sort(
            key=lambda item: (
                -item["rank_score"],
                -(item["confidence"] if item["confidence"] is not None else -1.0),
                item["response_gene"],
            )
        )
        selected = {id(item) for item in eligible[:cap]}
        for item in eligible:
            if id(item) not in selected:
                item["sign"] = 0
                item["reason"] = "CAP_EXCLUDED"
            else:
                item["reason"] = "SELECTED"

    records: list[SignedPriorRecord] = []
    for item in sorted(decisions, key=lambda value: value["key"]):
        record = SignedPriorRecord(
            target_gene=item["target"],
            condition_id=item["condition"],
            stage=item["stage"],
            state=item["state"],
            response_gene=item["response_gene"],
            sign=item["sign"],
            rank_score=item["rank_score"],
            confidence=item["confidence"],
            lineage_gate=item["lineage_gate"],
            dosage_fraction=item["dosage_fraction"],
            source_families=item["source_families"],
            directness_score=item["directness_score"],
            conflict_flag=item["conflict"],
            provenance=item["provenance"],
        )
        record.validate()
        records.append(record)

    output_json.parent.mkdir(parents=True, exist_ok=True)
    evidence_tsv.parent.mkdir(parents=True, exist_ok=True)
    conditions = sorted({record.condition_id for record in records})
    payload = {
        "schema_version": "ve.t3.signed-prior.v2",
        "condition_ids": conditions,
        "lane": lane,
        "sign_definition": "KO_MINUS_MATCHED_WT",
        "records": [_record_json(record) for record in records],
        "metadata": {
            "min_independent_families": min_families,
            "max_nonzero_fraction": max_fraction,
            "panel_size": panel_size,
            "nonzero_records": sum(record.sign != 0 for record in records),
            "record_count": len(records),
            "dosage_fractions": dosage_fractions,
            "require_state_activity": require_state_activity,
        },
    }
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    evidence_fields = [
        "target_gene", "condition_id", "stage", "state", "response_gene",
        "vote_signs", "vote_families", "sign", "rank_score", "confidence",
        "lineage_gate", "source_families", "directness_score", "conflict_flag",
        "dosage_fraction", "activity_gate_pass", "activity_evidence_status",
        "provenance", "decision_reason",
    ]
    with evidence_tsv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=evidence_fields, delimiter="\t")
        writer.writeheader()
        for item in sorted(decisions, key=lambda value: value["key"]):
            writer.writerow(
                {
                    "target_gene": item["target"],
                    "condition_id": item["condition"],
                    "stage": item["stage"],
                    "state": item["state"],
                    "response_gene": item["response_gene"],
                    "vote_signs": item["vote_signs"],
                    "vote_families": item["vote_families"],
                    "sign": item["sign"],
                    "rank_score": item["rank_score"],
                    "confidence": item["confidence"],
                    "lineage_gate": item["lineage_gate"],
                    "source_families": ";".join(item["source_families"]),
                    "directness_score": "" if item["directness_score"] is None else item["directness_score"],
                    "conflict_flag": item["conflict"],
                    "dosage_fraction": "" if item["dosage_fraction"] is None else item["dosage_fraction"],
                    "activity_gate_pass": item["activity_gate_pass"],
                    "activity_evidence_status": item["activity_evidence_status"],
                    "provenance": ";".join(item["provenance"]),
                    "decision_reason": item["reason"],
                }
            )
    return records
