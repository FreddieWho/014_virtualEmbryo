from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from virtual_embryo_tools.route_gate import (
    EXPECTED_ROUTE_IDS,
    RouteGateError,
    load_route_gate,
)

ROUTES = sorted(EXPECTED_ROUTE_IDS)


def _slug(route_id: str) -> str:
    return route_id.lower().replace("::", "_").replace("-", "_")


def _prior_payload(route_id: str) -> dict[str, object]:
    condition, lane = route_id.split("::", 1)
    return {
        "schema_version": "ve.t3.signed-prior.v2",
        "condition_ids": [condition],
        "lane": lane,
        "sign_definition": "KO_MINUS_MATCHED_WT",
        "records": [],
        "metadata": {},
    }


def _method_summary(targets: set[str], output_path: str, output_hash: str, target_status: str) -> dict[str, object]:
    return {
        "status": "PASS",
        "targets": {
            target: {
                "status": target_status,
                "reason": "fixture",
                "outputs": [{"path": output_path, "sha256": output_hash}],
            }
            for target in targets
        },
    }


def _artifact_manifest(tmp_path: Path, paths: list[str]) -> tuple[str, str]:
    entries = []
    for relative in paths:
        path = tmp_path / relative
        entries.append({
            "path": relative,
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    manifest_path = tmp_path / "metrics/artifact_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({
        "schema": "ve.t3.s1a-artifact-manifest.v1",
        "task": "T3-S1A-STATE-JOIN",
        "files": entries,
    }), encoding="utf-8")
    return "metrics/artifact_manifest.json", hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def route_entry(
    tmp_path: Path,
    *,
    route_id: str,
    prior_path: str,
    evidence_path: str,
    status: str = "PASS",
    candidate_generation: bool = True,
) -> dict[str, object]:
    prior = tmp_path / prior_path
    evidence = tmp_path / evidence_path
    prior_hash = hashlib.sha256(prior.read_bytes()).hexdigest()
    evidence_hash = hashlib.sha256(evidence.read_bytes()).hexdigest()
    condition = route_id.split("::", 1)[0]
    targets = {"Gata4", "Gata6"} if condition.startswith("GATA") else {"Ctnnb1"}
    method_status = {
        "CellOracle": _method_summary(targets, prior_path, prior_hash, "PASS"),
        "scTenifoldNet/scTenifoldKnk": _method_summary(targets, prior_path, prior_hash, "PASS_UNSIGNED_RANK_ONLY"),
    }
    return {
        "route_id": route_id,
        "status": status,
        "candidate_generation": candidate_generation,
        "blockers": [] if status == "PASS" else ["fixture blocker"],
        "blocks_submission": False,
        "evidence_paths": [prior_path, evidence_path],
        "evidence_hashes": {prior_path: prior_hash, evidence_path: evidence_hash},
        "prior_path": prior_path,
        "prior_sha256": prior_hash,
        "evidence_path": evidence_path,
        "evidence_sha256": evidence_hash,
        "artifact_manifest_path": "metrics/artifact_manifest.json",
        "artifact_manifest_sha256": "",
        "source_hashes": {"fixture": prior_hash},
        "source_artifacts": {"fixture": {"path": prior_path, "sha256": prior_hash}},
        "state_join_gate": {"status": "PASS"},
        "selected_gene_stability": {"status": "PASS"},
        "evidence_family_stability": {"status": "PASS"},
        "method_status": method_status,
    }


def report(tmp_path: Path, **updates: object) -> dict[str, object]:
    routes = []
    paths: list[str] = []
    for route_id in ROUTES:
        slug = _slug(route_id)
        prior_path = f"intermediates/{slug}_prior.json"
        evidence_path = f"intermediates/{slug}_evidence.tsv"
        prior = tmp_path / prior_path
        prior.parent.mkdir(parents=True, exist_ok=True)
        prior.write_text(json.dumps(_prior_payload(route_id)), encoding="utf-8")
        evidence = tmp_path / evidence_path
        evidence.write_text("fixture\n", encoding="utf-8")
        paths.extend([prior_path, evidence_path])
    manifest_path, manifest_hash = _artifact_manifest(tmp_path, paths)
    for route_id in ROUTES:
        slug = _slug(route_id)
        route = route_entry(
            tmp_path,
            route_id=route_id,
            prior_path=f"intermediates/{slug}_prior.json",
            evidence_path=f"intermediates/{slug}_evidence.tsv",
        )
        route["artifact_manifest_path"] = manifest_path
        route["artifact_manifest_sha256"] = manifest_hash
        routes.append(route)
    value: dict[str, object] = {
        "schema": "gate_report.v2",
        "task_id": "T3-S1A-STATE-JOIN",
        "gate_id": "route_specific_prior_gate_v2",
        "status": "PASS",
        "outcome": "PRIOR_GATE_PASS",
        "blockers": [],
        "blocks_submission": False,
        "candidate_generation": False,
        "server_submission": False,
        "criteria": [{"name": "route_specific_admission", "result": "PASS"}],
        "routes": routes,
    }
    value.update(updates)
    return value


def write_report(tmp_path: Path, value: dict[str, object]) -> Path:
    path = tmp_path / "metrics/gate_report.v2.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_missing_report_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(RouteGateError, match="does not exist"):
        load_route_gate(tmp_path / "missing.json", route_id=ROUTES[0])


def test_missing_route_fails_closed(tmp_path: Path) -> None:
    value = report(tmp_path, routes=[report(tmp_path)["routes"][0]])
    with pytest.raises(RouteGateError, match="exactly"):
        load_route_gate(write_report(tmp_path, value), route_id=ROUTES[0])


def test_missing_top_level_contract_fails_closed(tmp_path: Path) -> None:
    value = report(tmp_path)
    value.pop("status")
    with pytest.raises(RouteGateError, match="status"):
        load_route_gate(write_report(tmp_path, value), route_id=ROUTES[0])
    value = report(tmp_path)
    value.pop("criteria")
    with pytest.raises(RouteGateError, match="criteria"):
        load_route_gate(write_report(tmp_path, value), route_id=ROUTES[0])
    value = report(tmp_path, criteria=[{"name": "tool", "result": "BLOCKED"}])
    with pytest.raises(RouteGateError, match="failed or blocked"):
        load_route_gate(write_report(tmp_path, value), route_id=ROUTES[0])


def test_hold_route_is_not_activatable(tmp_path: Path) -> None:
    value = report(tmp_path, status="HOLD", outcome="PARTIAL_ROUTE_PASS")
    value["routes"][0]["status"] = "HOLD"
    value["routes"][0]["candidate_generation"] = False
    value["routes"][0]["blockers"] = ["fixture blocker"]
    with pytest.raises(RouteGateError, match="status must be PASS"):
        load_route_gate(write_report(tmp_path, value), route_id=ROUTES[0])


def test_conflicting_duplicate_route_and_illegal_schema_fail_closed(tmp_path: Path) -> None:
    value = report(tmp_path)
    value["routes"][1]["route_id"] = value["routes"][0]["route_id"]
    with pytest.raises(RouteGateError, match="exactly"):
        load_route_gate(write_report(tmp_path, value), route_id=ROUTES[0])
    with pytest.raises(RouteGateError, match="schema"):
        load_route_gate(write_report(tmp_path, report(tmp_path, schema="gate_report.v1")), route_id=ROUTES[0])


def test_modified_evidence_is_rejected(tmp_path: Path) -> None:
    value = report(tmp_path)
    (tmp_path / value["routes"][0]["evidence_path"]).write_text("modified\n", encoding="utf-8")
    with pytest.raises(RouteGateError, match="evidence hash"):
        load_route_gate(write_report(tmp_path, value), route_id=ROUTES[0])


def test_partial_global_outcome_with_passing_route_is_accepted(tmp_path: Path) -> None:
    value = report(tmp_path, status="HOLD", outcome="PARTIAL_ROUTE_PASS", blockers=["another route is blocked"])
    for route in value["routes"][1:]:
        route["status"] = "HOLD"
        route["candidate_generation"] = False
        route["blockers"] = ["fixture blocker"]
    result = load_route_gate(write_report(tmp_path, value), route_id=ROUTES[0])
    assert result["report"]["outcome"] == "PARTIAL_ROUTE_PASS"


def test_blocked_global_outcome_is_auditable_but_not_activatable(tmp_path: Path) -> None:
    value = report(tmp_path, status="BLOCKED", outcome="BLOCKED")
    for route in value["routes"]:
        route["status"] = "BLOCKED"
        route["candidate_generation"] = False
        route["blockers"] = ["toolchain blocker"]
    audited = load_route_gate(write_report(tmp_path, value))
    assert audited["report"]["outcome"] == "BLOCKED"
    assert len(audited["routes"]) == 4
    with pytest.raises(RouteGateError, match="status must be PASS"):
        load_route_gate(write_report(tmp_path, value), route_id=ROUTES[0])


def test_route_mapping_key_cannot_be_overridden(tmp_path: Path) -> None:
    value = report(tmp_path)
    entries = {route["route_id"]: route for route in value["routes"]}
    entries[ROUTES[0]]["route_id"] = "other"
    value["routes"] = entries
    with pytest.raises(RouteGateError, match="disagrees"):
        load_route_gate(write_report(tmp_path, value), route_id=ROUTES[0])


def test_route_report_schema_accepts_contract_fixture(tmp_path: Path) -> None:
    schema_path = Path(__file__).resolve().parents[2] / "schemas/route_gate_report.v2.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert not list(Draft202012Validator(schema).iter_errors(report(tmp_path)))
