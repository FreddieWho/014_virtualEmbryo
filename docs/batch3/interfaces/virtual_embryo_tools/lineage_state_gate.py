from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable, Mapping


def _as_rows(state_labels: Any) -> Iterable[tuple[str, Mapping[str, Any] | None]]:
    if isinstance(state_labels, Mapping):
        for state, value in state_labels.items():
            yield str(state), value if isinstance(value, Mapping) else {"lineage_gate": value}
        return
    for value in state_labels if state_labels is not None else ():
        if isinstance(value, Mapping):
            state = value.get("state", value.get("official_state", ""))
            yield str(state), value
        else:
            yield str(value), None


def _probability_for(
    wt_data: Any,
    state: str,
    row: Mapping[str, Any] | None,
    config: Mapping[str, Any],
) -> tuple[float | None, str]:
    for source in (row or {}, config.get("lineage_probabilities", {})):
        if isinstance(source, Mapping):
            for key in ("lineage_gate", "p_mesp1_lineage", "lineage_probability"):
                if key in source and source[key] not in (None, ""):
                    return float(source[key]), f"provided:{key}"
            if state in source and not isinstance(source[state], Mapping):
                return float(source[state]), "provided:state_mapping"
    if isinstance(wt_data, Mapping) and state in wt_data:
        value = wt_data[state]
        if not isinstance(value, Mapping) and value not in (None, ""):
            return float(value), "wt_data:state_mapping"
    return None, "missing_lineage_probability"


def build_lineage_state_gate(
    *,
    wt_data: Any,
    state_labels: Any,
    output_path: Path,
    config: Mapping[str, Any],
) -> Path:
    """Build Mesp1-lineage/state/activity gates with evidence columns."""
    threshold = float(config.get("lineage_threshold", 0.5))
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("lineage_threshold must be in [0, 1]")
    condition_id = str(config.get("condition_id", "unknown_condition"))
    stage = str(config.get("stage", "unknown_stage"))
    provenance_default = str(config.get("provenance", "lineage_probability_input"))
    rows: list[dict[str, Any]] = []
    for state, state_row in _as_rows(state_labels):
        if not state:
            raise ValueError("state labels must not be empty")
        probability, evidence = _probability_for(wt_data, state, state_row, config)
        if probability is None:
            probability = 0.0
            gate_pass = False
        else:
            if not 0.0 <= probability <= 1.0:
                raise ValueError("lineage probability must be in [0, 1]")
            gate_pass = probability >= threshold
        row_condition = str((state_row or {}).get("condition_id", condition_id))
        row_stage = str((state_row or {}).get("stage", stage))
        rows.append(
            {
                "condition_id": row_condition,
                "stage": row_stage,
                "state": state,
                "lineage_gate": probability,
                "p_mesp1_lineage": probability,
                "gate_pass": gate_pass,
                "provenance": str((state_row or {}).get("provenance", provenance_default)),
                "evidence": evidence,
            }
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "condition_id", "stage", "state", "lineage_gate", "p_mesp1_lineage",
        "gate_pass", "provenance", "evidence",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    return output_path
