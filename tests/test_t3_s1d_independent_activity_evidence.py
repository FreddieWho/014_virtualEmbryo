from __future__ import annotations

import pandas as pd

from scripts.t3_s1d_independent_activity_evidence import _effect_rows


def test_effect_rows_audit_replicate_direction_and_panel_summary():
    frame = pd.DataFrame(
        {
            "gene": ["Gata6", "Nkx2-5", "Other"],
            "WT1": [10.0, 20.0, 5.0],
            "WT2": [12.0, 18.0, 5.0],
            "MUT1": [5.0, 10.0, 6.0],
            "MUT2": [6.0, 11.0, 7.0],
        }
    )
    rows, summary = _effect_rows(
        frame,
        symbol_column="gene",
        study="TEST",
        target="Gata6",
        perturbation="KO",
        control_columns=["WT1", "WT2"],
        perturb_columns=["MUT1", "MUT2"],
        panel=["Gata6", "Nkx2-5", "Missing"],
    )
    assert len(rows) == 2
    assert summary["panel_present_count"] == 2
    assert summary["target_replicate_direction_consistent_n"] == 2
    assert summary["target_log2fc_perturb_minus_control"] < 0
    assert all(row["activity_eligible_for_E875"] is False for row in rows)
