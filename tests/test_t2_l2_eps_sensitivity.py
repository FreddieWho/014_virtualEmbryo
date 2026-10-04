"""Tests for the T2 LEADS L-002 two-value epsilon sensitivity runner.

Scope: cheap structural checks only. The sensitivity itself was executed once
and its numbers live in
``artifacts/tool_integration/T2-L002-FGW-EPS-SENSITIVITY-20260927-v1/``; these
tests guard the pre-declared design (exactly two epsilon values, no grid
search), the frozen-input reuse contract, and the fail-closed behaviour of the
reproduction control. They deliberately do not re-solve any FGW problem.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import t2_l2_eps_sensitivity as sens  # noqa: E402


def test_exactly_two_epsilon_values_including_the_frozen_baseline() -> None:
    assert sens.BASELINE_EPSILON == 0.005
    assert sens.ALTERNATIVE_EPSILON == 0.002
    # A grid search would have more than two values; the design is fixed.
    assert len({sens.BASELINE_EPSILON, sens.ALTERNATIVE_EPSILON}) == 2


def test_baseline_arm_is_flagged_as_such() -> None:
    assert sens.BASELINE_EPSILON != sens.ALTERNATIVE_EPSILON
    record = {"epsilon": sens.BASELINE_EPSILON}
    assert record["epsilon"] == sens.BASELINE_EPSILON


def test_frozen_inputs_exist_and_are_the_proxy_run() -> None:
    for holdout in sens.HOLDOUT_BY_NAME:
        problem = sens.PROXY_DIR / "intermediates" / holdout / "problem_fgw_full.npz"
        prepared = sens.PROXY_DIR / "intermediates" / holdout / "prepared.npz"
        assert problem.is_file(), problem
        assert prepared.is_file(), prepared


def test_random_envelope_is_reused_not_regenerated() -> None:
    envelope = sens.random_envelope("H1_embryo_leave_E7.25_out")
    assert envelope["n_draws"] == sens.RANDOM_DRAWS
    assert envelope["q05"] <= envelope["median"] <= envelope["max"]
    assert envelope["source"].endswith("metrics/random_baseline.tsv")


def test_reproduction_control_fails_closed_on_mismatched_numbers() -> None:
    baseline = {
        "soft": {"nfs_like": 0.5, "nbhd_pearson": 0.1, "fgw_objective": {"total": 0.2}},
        "dispersion": {"effective_sources": 10.0},
    }
    control = sens.reproduction_control("H1_embryo_leave_E7.25_out", baseline)
    assert control["checks"]["coupling_level_reproduced"] is False


def test_decision_rule_requires_all_questions_in_all_holdouts() -> None:
    results = []
    for holdout in ("A", "B"):
        for epsilon, eff, conflict, nfs, ratio in (
            (sens.BASELINE_EPSILON, 60.0, 0.70, 0.020, 0.15),
            (sens.ALTERNATIVE_EPSILON, 30.0, 0.40, 0.010, 0.07),
        ):
            results.append(
                {
                    "holdout": holdout,
                    "epsilon": epsilon,
                    "soft": {"nfs_like": nfs, "fgw_objective": {"total": 0.1}},
                    "hard": {"nfs_like": nfs, "fgw_objective": {"total": 0.1}},
                    "dispersion": {
                        "effective_sources": eff,
                        "conflict_rate": conflict,
                    },
                    "separation_vs_random": {
                        "soft_nfs_ratio_to_random_median": ratio,
                        "soft_nfs_below_random_q05": True,
                    },
                }
            )
    controls = [
        {"holdout": "A", "checks": {"coupling_level_reproduced": True}},
        {"holdout": "B", "checks": {"coupling_level_reproduced": True}},
    ]
    findings = sens.build_findings(results, controls)
    gate = findings["all_holdouts"]
    assert gate["reproduction_control_passed"] is True
    assert gate["Q1_dispersion_reduced_in_all"] is True
    assert gate["Q2_effect_stronger_in_all"] is True
    assert gate["Q3_separation_larger_in_all"] is True
    assert gate["escalation_criterion_met"] is True


def test_dispersion_without_effect_does_not_escalate() -> None:
    """The pre-declared rule must reject 'more concentrated but not stronger'."""
    results = []
    for holdout in ("A", "B"):
        for epsilon, eff, conflict, nfs, ratio in (
            (sens.BASELINE_EPSILON, 60.0, 0.70, 0.020, 0.15),
            (sens.ALTERNATIVE_EPSILON, 30.0, 0.40, 0.025, 0.19),
        ):
            results.append(
                {
                    "holdout": holdout,
                    "epsilon": epsilon,
                    "soft": {"nfs_like": nfs, "fgw_objective": {"total": 0.1}},
                    "hard": {"nfs_like": nfs, "fgw_objective": {"total": 0.1}},
                    "dispersion": {
                        "effective_sources": eff,
                        "conflict_rate": conflict,
                    },
                    "separation_vs_random": {
                        "soft_nfs_ratio_to_random_median": ratio,
                        "soft_nfs_below_random_q05": True,
                    },
                }
            )
    controls = [
        {"holdout": h, "checks": {"coupling_level_reproduced": True}} for h in ("A", "B")
    ]
    gate = sens.build_findings(results, controls)["all_holdouts"]
    assert gate["Q1_dispersion_reduced_in_all"] is True
    assert gate["Q2_effect_stronger_in_all"] is False
    assert gate["escalation_criterion_met"] is False


@pytest.mark.skipif(
    not (sens.DEFAULT_OUT / "metrics/sensitivity_results.json").is_file(),
    reason="L-002 run not present in this checkout",
)
def test_recorded_run_uses_exactly_two_epsilons() -> None:
    payload = json.loads(
        (sens.DEFAULT_OUT / "metrics/sensitivity_results.json").read_text(encoding="utf-8")
    )
    epsilons = {r["epsilon"] for r in payload["results"]}
    assert epsilons == {sens.BASELINE_EPSILON, sens.ALTERNATIVE_EPSILON}
    assert payload["design"]["epsilon_values"] == [
        sens.BASELINE_EPSILON,
        sens.ALTERNATIVE_EPSILON,
    ]
