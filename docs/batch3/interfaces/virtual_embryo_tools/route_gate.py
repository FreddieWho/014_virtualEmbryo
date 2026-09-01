"""Fail-closed validation for the route-specific gate report."""

from __future__ import annotations

import json
import hashlib
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

EXPECTED_TASK_ID = "T3-S1A-STATE-JOIN"
EXPECTED_GATE_ID = "route_specific_prior_gate_v2"
EXPECTED_SCHEMA = "gate_report.v2"
ALLOWED_OUTCOMES = {
    "PRIOR_GATE_PASS",
    "PARTIAL_ROUTE_PASS",
    "HOLD_AS_COMPONENT",
    "BLOCKED",
}
REPORT_STATUSES = {"PASS", "HOLD", "BLOCKED"}
CRITERION_RESULTS = {"PASS", "FAIL", "NOT_APPLICABLE", "BLOCKED"}
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
EXPECTED_ROUTE_IDS = frozenset({
    "GATA4_GATA6_VALIDATION_E875::L1_STRICT_AGREEMENT",
    "GATA4_GATA6_VALIDATION_E875::L2_CONDITION_AWARE",
    "BETA_CATENIN_HIDDEN_E875::L1_STRICT_AGREEMENT",
    "BETA_CATENIN_HIDDEN_E875::L2_CONDITION_AWARE",
})
ROUTE_TARGETS = {
    "GATA4_GATA6_VALIDATION_E875": {"Gata4", "Gata6"},
    "BETA_CATENIN_HIDDEN_E875": {"Ctnnb1"},
}
REQUIRED_METHODS = {"CellOracle", "scTenifoldNet/scTenifoldKnk"}
METHOD_STATUS_RE = re.compile(r"^(?:PASS|NOT_APPLICABLE|BLOCKED|NOT_RUN|PARTIAL)(?:_[A-Z0-9]+)*$")


class RouteGateError(ValueError):
    """Raised when a route gate cannot be proven safe to consume."""


def _fail(message: str) -> None:
    raise RouteGateError(f"invalid route gate report: {message}")


@lru_cache(maxsize=None)
def _sha256_cached(path: str, size: int, mtime_ns: int) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _sha256_path(path: Path) -> str:
    resolved = path.resolve()
    stat = resolved.stat()
    return _sha256_cached(str(resolved), stat.st_size, stat.st_mtime_ns)


def _required_string(report: dict[str, Any], name: str) -> str:
    value = report.get(name)
    if not isinstance(value, str) or not value:
        _fail(f"{name} must be a non-empty string")
    return value


def _route_entries(report: dict[str, Any]) -> list[dict[str, Any]]:
    routes = report.get("routes")
    if isinstance(routes, list):
        entries = routes
    elif isinstance(routes, dict):
        entries = []
        for route_id, route in routes.items():
            if not isinstance(route, dict):
                _fail(f"route {route_id!r} must be an object")
            if "route_id" in route and route["route_id"] != route_id:
                _fail(f"route mapping key {route_id!r} disagrees with route_id")
            entries.append({**route, "route_id": route_id})
    else:
        _fail("routes must be an array or object")
    if not entries or any(not isinstance(route, dict) for route in entries):
        _fail("routes must contain route objects")
    return entries


def _validate_report_contract(report: dict[str, Any]) -> None:
    status = report.get("status")
    if status not in REPORT_STATUSES:
        _fail(f"status must be one of {sorted(REPORT_STATUSES)!r}")
    criteria = report.get("criteria")
    if not isinstance(criteria, list) or not criteria:
        _fail("criteria must be a non-empty array")
    for criterion in criteria:
        if not isinstance(criterion, dict):
            _fail("criteria must contain objects")
        if not isinstance(criterion.get("name"), str) or not criterion["name"]:
            _fail("each criterion needs a non-empty name")
        if criterion.get("result") not in CRITERION_RESULTS:
            _fail(f"criterion {criterion['name']!r} has an invalid result")
    expected_status = {
        "PRIOR_GATE_PASS": "PASS",
        "PARTIAL_ROUTE_PASS": "HOLD",
        "HOLD_AS_COMPONENT": "HOLD",
        "BLOCKED": "BLOCKED",
    }[report["outcome"]]
    if status != expected_status:
        _fail(f"outcome {report['outcome']!r} requires status {expected_status!r}")
    if report["outcome"] == "PRIOR_GATE_PASS" and any(
        criterion["result"] not in {"PASS", "NOT_APPLICABLE"}
        for criterion in criteria
    ):
        _fail("PRIOR_GATE_PASS cannot contain failed or blocked criteria")
    if report["outcome"] == "PARTIAL_ROUTE_PASS":
        routes = _route_entries(report)
        if not any(route.get("status") == "PASS" for route in routes):
            _fail("PARTIAL_ROUTE_PASS requires at least one PASS route")
        if all(route.get("status") == "PASS" for route in routes):
            _fail("PARTIAL_ROUTE_PASS requires at least one non-PASS route")
    if report["outcome"] == "HOLD_AS_COMPONENT":
        routes = _route_entries(report)
        if any(route.get("status") == "PASS" for route in routes):
            _fail("HOLD_AS_COMPONENT cannot contain a PASS route")
    if report["outcome"] == "BLOCKED":
        routes = _route_entries(report)
        if any(route.get("status") == "PASS" for route in routes):
            _fail("BLOCKED cannot contain a PASS route")
        if not any(route.get("status") == "BLOCKED" for route in routes):
            _fail("BLOCKED requires at least one BLOCKED route")
    if report.get("candidate_generation") is not False:
        _fail("top-level candidate_generation must be false")
    if report.get("server_submission") is not False:
        _fail("server_submission must be false")


def _validate_route_contract(route: dict[str, Any], artifact_root: Path) -> None:
    route_id = route.get("route_id")
    if not isinstance(route_id, str) or not route_id:
        _fail("each route needs a non-empty route_id")
    if route.get("status") not in {"PASS", "HOLD", "BLOCKED"}:
        _fail(f"route {route_id!r} has an invalid status")
    if route.get("blocks_submission") is not False:
        _fail(f"route {route_id!r} blocks_submission must be false")
    if not isinstance(route.get("evidence_paths"), list) or not route["evidence_paths"]:
        _fail(f"route {route_id!r} evidence_paths must be a non-empty array")
    evidence_hashes = route.get("evidence_hashes")
    if not isinstance(evidence_hashes, dict) or set(evidence_hashes) != set(route["evidence_paths"]):
        _fail(f"route {route_id!r} evidence_hashes must cover every evidence path")
    for evidence_path in route["evidence_paths"]:
        if not isinstance(evidence_path, str) or not evidence_path:
            _fail(f"route {route_id!r} has an unsafe evidence path")
        path = Path(evidence_path)
        if path.is_absolute() or ".." in path.parts:
            _fail(f"route {route_id!r} has an unsafe evidence path")
        resolved = (artifact_root / path).resolve()
        if artifact_root.resolve() not in resolved.parents or not resolved.is_file():
            _fail(f"route {route_id!r} evidence path does not exist in the artifact")
        expected_hash = evidence_hashes[evidence_path]
        if not isinstance(expected_hash, str) or not SHA256_RE.fullmatch(expected_hash):
            _fail(f"route {route_id!r} evidence hash is invalid for {evidence_path!r}")
        if _sha256_path(resolved).lower() != expected_hash.lower():
            _fail(f"route {route_id!r} evidence hash does not match {evidence_path!r}")
    for field in ("prior_path", "evidence_path", "artifact_manifest_path"):
        value = route.get(field)
        if not isinstance(value, str) or not value:
            _fail(f"route {route_id!r} is missing {field}")
        path = Path(value)
        if path.is_absolute() or ".." in path.parts:
            _fail(f"route {route_id!r} has an unsafe {field}")
        resolved = (artifact_root / path).resolve()
        if artifact_root.resolve() not in resolved.parents or not resolved.is_file():
            _fail(f"route {route_id!r} {field} does not exist in the artifact")
        hash_field = field.replace("_path", "_sha256")
        expected_hash = route.get(hash_field)
        if not isinstance(expected_hash, str) or not SHA256_RE.fullmatch(expected_hash):
            _fail(f"route {route_id!r} has an invalid {hash_field}")
        if _sha256_path(resolved).lower() != expected_hash.lower():
            _fail(f"route {route_id!r} {hash_field} does not match its file")
    if route["prior_path"] not in route["evidence_paths"] or route["evidence_path"] not in route["evidence_paths"]:
        _fail(f"route {route_id!r} prior/evidence paths must be route evidence")
    if (
        evidence_hashes.get(route["prior_path"]) != route["prior_sha256"]
        or evidence_hashes.get(route["evidence_path"]) != route["evidence_sha256"]
    ):
        _fail(f"route {route_id!r} prior/evidence hashes are not bound to evidence_hashes")
    _validate_prior_schema(artifact_root / route["prior_path"], artifact_root, route_id)
    _validate_artifact_manifest(artifact_root / route["artifact_manifest_path"], artifact_root, route["evidence_paths"])
    _validate_source_artifacts(route, artifact_root)
    source_hashes = route.get("source_hashes")
    if not isinstance(source_hashes, dict) or not source_hashes:
        _fail(f"route {route_id!r} source_hashes must be a non-empty object")
    if any(not isinstance(value, str) or not SHA256_RE.fullmatch(value) for value in source_hashes.values()):
        _fail(f"route {route_id!r} source_hashes must contain SHA256 strings")
    method_status = route.get("method_status")
    if not isinstance(method_status, dict) or set(method_status) != REQUIRED_METHODS:
        _fail(f"route {route_id!r} method_status must contain exactly {sorted(REQUIRED_METHODS)!r}")
    condition = route_id.split("::", 1)[0]
    required_targets = ROUTE_TARGETS.get(condition)
    if required_targets is None:
        _fail(f"route {route_id!r} has an unknown condition")
    for method, summary in method_status.items():
        if not isinstance(method, str) or not method or not isinstance(summary, dict):
            _fail(f"route {route_id!r} method_status is malformed")
        if not isinstance(summary.get("status"), str) or not METHOD_STATUS_RE.fullmatch(summary["status"]):
            _fail(f"route {route_id!r} method status is missing")
        if not isinstance(summary.get("targets"), dict) or set(summary["targets"]) != required_targets:
            _fail(f"route {route_id!r} method {method!r} has no target status")
        for target, target_summary in summary["targets"].items():
            if not isinstance(target, str) or not isinstance(target_summary, dict):
                _fail(f"route {route_id!r} method target status is malformed")
            if not isinstance(target_summary.get("status"), str) or not METHOD_STATUS_RE.fullmatch(target_summary["status"]):
                _fail(f"route {route_id!r} method target status is missing")
            outputs = target_summary.get("outputs")
            if not isinstance(outputs, list):
                _fail(f"route {route_id!r} method target outputs must be an array")
            for output in outputs:
                if not isinstance(output, dict) or not isinstance(output.get("path"), str):
                    _fail(f"route {route_id!r} method target output is malformed")
                output_path = Path(output["path"])
                if output_path.is_absolute() or ".." in output_path.parts:
                    _fail(f"route {route_id!r} method target output path is unsafe")
                resolved_output = (artifact_root / output_path).resolve()
                if artifact_root.resolve() not in resolved_output.parents or not resolved_output.is_file():
                    _fail(f"route {route_id!r} method target output is missing")
                if not isinstance(output.get("sha256"), str) or not SHA256_RE.fullmatch(output["sha256"]):
                    _fail(f"route {route_id!r} method target output hash is invalid")
                digest = _sha256_path(resolved_output)
                if digest.lower() != output["sha256"].lower():
                    _fail(f"route {route_id!r} method target output hash does not match file")
            if target_summary["status"].startswith("PASS") and not outputs:
                _fail(f"route {route_id!r} method target {target!r} has no output for PASS status")
            if target_summary["status"].startswith("NOT_APPLICABLE") and not target_summary.get("reason"):
                _fail(f"route {route_id!r} method target {target!r} needs a not-applicable reason")
    blockers = route.get("blockers")
    if not isinstance(blockers, list) or any(not isinstance(item, str) or not item for item in blockers):
        _fail(f"route {route_id!r} blockers must contain strings")
    if route["status"] == "PASS" and (blockers or route.get("candidate_generation") is not True):
        _fail(f"route {route_id!r} PASS status is inconsistent")
    if route["status"] != "PASS" and route.get("candidate_generation") is not False:
        _fail(f"route {route_id!r} non-PASS status must disable candidate_generation")
    for field in ("state_join_gate", "selected_gene_stability", "evidence_family_stability"):
        if not isinstance(route.get(field), dict) or route[field].get("status") not in {"PASS", "HOLD", "NOT_IDENTIFIABLE", "BLOCKED"}:
            _fail(f"route {route_id!r} is missing a valid {field}")
    if route["status"] == "PASS":
        if any(route[field].get("status") != "PASS" for field in ("state_join_gate", "selected_gene_stability", "evidence_family_stability")):
            _fail(f"route {route_id!r} PASS status requires validated state and stability gates")
        for target in required_targets:
            sct_status = route["method_status"]["scTenifoldNet/scTenifoldKnk"]["targets"][target]["status"]
            if sct_status != "PASS_UNSIGNED_RANK_ONLY":
                _fail(f"route {route_id!r} PASS status requires unsigned scTenifold rank evidence for {target}")


def _validate_prior_schema(prior_path: Path, artifact_root: Path, route_id: str) -> None:
    try:
        from jsonschema import Draft202012Validator
    except Exception as exc:  # pragma: no cover - deployment-specific
        _fail(f"cannot load prior schema validator: {exc}")
    repo_candidate = artifact_root.parents[2] / "docs/batch3/schemas/prior.schema.json"
    schema_path = repo_candidate if repo_candidate.is_file() else Path(__file__).resolve().parents[2] / "schemas/prior.schema.json"
    if not schema_path.is_file():
        _fail(f"prior schema is missing: {schema_path}")
    try:
        payload = json.loads(prior_path.read_text(encoding="utf-8"))
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        _fail(f"cannot read prior/schema: {exc}")
    errors = sorted(Draft202012Validator(schema).iter_errors(payload), key=lambda error: list(error.path))
    if errors:
        _fail(f"prior does not satisfy prior.schema.json: {errors[0].message}")
    condition, lane = route_id.split("::", 1)
    if payload.get("lane") != lane or condition not in payload.get("condition_ids", []):
        _fail(f"prior is not bound to route {route_id!r}")
    if any(
        record.get("condition_id") != condition
        for record in payload.get("records", [])
    ):
        _fail(f"prior records are not bound to route condition {condition!r}")


def _validate_artifact_manifest(manifest_path: Path, artifact_root: Path, evidence_paths: list[str]) -> None:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        _fail(f"cannot read artifact manifest: {exc}")
    if not isinstance(manifest, dict) or manifest.get("schema") != "ve.t3.s1a-artifact-manifest.v1":
        _fail("artifact manifest has an invalid schema")
    entries = manifest.get("files")
    if not isinstance(entries, list):
        _fail("artifact manifest files must be an array")
    by_path = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            _fail("artifact manifest entry is malformed")
        entry_path = Path(entry["path"])
        if entry_path.is_absolute() or ".." in entry_path.parts or entry_path in by_path:
            _fail("artifact manifest contains an unsafe/duplicate path")
        actual = (artifact_root / entry_path).resolve()
        if artifact_root.resolve() not in actual.parents or not actual.is_file():
            _fail(f"artifact manifest path is missing: {entry_path}")
        if not isinstance(entry.get("sha256"), str) or not SHA256_RE.fullmatch(entry["sha256"]):
            _fail(f"artifact manifest hash is invalid: {entry_path}")
        if entry.get("bytes") != actual.stat().st_size:
            _fail(f"artifact manifest byte count does not match: {entry_path}")
        if _sha256_path(actual).lower() != entry["sha256"].lower():
            _fail(f"artifact manifest hash does not match: {entry_path}")
        by_path[entry_path.as_posix()] = entry
    for evidence_path in evidence_paths:
        if evidence_path not in by_path:
            _fail(f"artifact manifest does not cover evidence path: {evidence_path}")


def _validate_source_artifacts(route: dict[str, Any], artifact_root: Path) -> None:
    source_artifacts = route.get("source_artifacts")
    source_hashes = route.get("source_hashes")
    if not isinstance(source_artifacts, dict) or not source_artifacts:
        _fail(f"route {route['route_id']!r} source_artifacts must be a non-empty object")
    if not isinstance(source_hashes, dict) or set(source_hashes) != set(source_artifacts):
        _fail(f"route {route['route_id']!r} source_hashes must match source_artifacts")
    repo_root = artifact_root.parents[2]
    for name, item in source_artifacts.items():
        if not isinstance(name, str) or not name or not isinstance(item, dict):
            _fail(f"route {route['route_id']!r} source artifact is malformed")
        source_path = item.get("path")
        source_hash = item.get("sha256")
        if not isinstance(source_path, str) or not source_path or not isinstance(source_hash, str):
            _fail(f"route {route['route_id']!r} source artifact {name!r} is incomplete")
        if not SHA256_RE.fullmatch(source_hash) or source_hashes[name] != source_hash:
            _fail(f"route {route['route_id']!r} source artifact {name!r} has inconsistent hash")
        relative = Path(source_path)
        if relative.is_absolute() or ".." in relative.parts:
            _fail(f"route {route['route_id']!r} source artifact {name!r} has an unsafe path")
        repo_actual = (repo_root / relative).resolve()
        artifact_actual = (artifact_root / relative).resolve()
        if repo_actual.is_file() and repo_root.resolve() in repo_actual.parents:
            actual = repo_actual
        elif artifact_actual.is_file() and artifact_root.resolve() in artifact_actual.parents:
            actual = artifact_actual
        else:
            _fail(f"route {route['route_id']!r} source artifact {name!r} is missing")
        if _sha256_path(actual).lower() != source_hash.lower():
            _fail(f"route {route['route_id']!r} source artifact {name!r} hash does not match")


def load_route_gate(
    report_path: str | Path,
    *,
    route_id: str | None = None,
    task_id: str = EXPECTED_TASK_ID,
    gate_id: str = EXPECTED_GATE_ID,
) -> dict[str, Any]:
    """Validate a report, optionally selecting one PASS route for activation.

    Without ``route_id`` this audits PASS/HOLD/BLOCKED reports.  With a route
    ID, the selected route must independently be PASS and candidate-eligible.
    """
    path = Path(report_path)
    if not path.is_file():
        _fail(f"report file does not exist: {path}")
    try:
        with path.open(encoding="utf-8") as handle:
            report = json.load(handle)
    except (OSError, UnicodeDecodeError) as exc:
        _fail(f"cannot read {path}: {exc}")
    except json.JSONDecodeError as exc:
        _fail(f"invalid JSON in {path}: {exc.msg} at line {exc.lineno}")
    if not isinstance(report, dict):
        _fail("top level must be an object")

    if report.get("schema") != EXPECTED_SCHEMA:
        _fail(f"schema must be {EXPECTED_SCHEMA!r}")
    if report.get("task_id") != task_id:
        _fail(f"task_id must be {task_id!r}")
    if report.get("gate_id") != gate_id:
        _fail(f"gate_id must be {gate_id!r}")
    outcome = report.get("outcome")
    if outcome not in ALLOWED_OUTCOMES:
        _fail(f"outcome must be one of {sorted(ALLOWED_OUTCOMES)!r}")
    _validate_report_contract(report)
    blockers = report.get("blockers")
    if blockers is not None:
        if not isinstance(blockers, list):
            _fail("blockers must be an array")
        if any(not isinstance(blocker, str) or not blocker for blocker in blockers):
            _fail("blockers must contain non-empty strings")
    if report.get("blocks_submission") is not False:
        _fail("blocks_submission must be false")

    routes = _route_entries(report)
    route_ids = [route.get("route_id") for route in routes]
    if (
        any(not isinstance(route_id, str) for route_id in route_ids)
        or set(route_ids) != EXPECTED_ROUTE_IDS
        or len(route_ids) != len(EXPECTED_ROUTE_IDS)
    ):
        _fail(
            "routes must contain exactly the four contracted route IDs: "
            f"{sorted(EXPECTED_ROUTE_IDS)!r}"
        )
    if outcome == "PRIOR_GATE_PASS" and any(route.get("status") != "PASS" for route in routes):
        _fail("PRIOR_GATE_PASS requires every route to be PASS")
    if outcome == "PARTIAL_ROUTE_PASS":
        if not any(route.get("status") == "PASS" for route in routes):
            _fail("PARTIAL_ROUTE_PASS requires at least one PASS route")
        if all(route.get("status") == "PASS" for route in routes):
            _fail("PARTIAL_ROUTE_PASS requires at least one non-PASS route")
    artifact_root = path.parent.parent
    for entry in routes:
        _validate_route_contract(entry, artifact_root)
    route_ids = [route["route_id"] for route in routes]
    if len(route_ids) != len(set(route_ids)):
        _fail("routes contain duplicated route_id values")
    if route_id is None:
        return {"report": report, "routes": routes}
    matches = [route for route in routes if route.get("route_id") == route_id]
    if not matches:
        _fail(f"route_id {route_id!r} is missing")
    if len(matches) != 1:
        _fail(f"route_id {route_id!r} is duplicated")
    route = matches[0]
    if route.get("status") != "PASS":
        _fail(f"route {route_id!r} status must be PASS")
    if route.get("candidate_generation") is not True:
        _fail(f"route {route_id!r} candidate_generation must be true")
    route_blockers = route.get("blockers")
    if not isinstance(route_blockers, list):
        _fail(f"route {route_id!r} blockers must be an array")
    if any(not isinstance(blocker, str) or not blocker for blocker in route_blockers):
        _fail(f"route {route_id!r} blockers must contain non-empty strings")
    return {"report": report, "route": route}


def validate_route_binding(binding: Mapping[str, Any], *, repo_root: str | Path) -> dict[str, Any]:
    """Revalidate the hash-bound handoff that an S1B entry point consumes."""
    root = Path(repo_root).resolve()
    required = (
        "route_id", "gate_report", "gate_report_sha256", "prior_path", "prior_sha256",
        "evidence_path", "evidence_sha256", "artifact_manifest_path", "artifact_manifest_sha256",
    )
    if any(not isinstance(binding.get(name), str) or not binding[name] for name in required):
        _fail("active route binding is incomplete")
    gate_path = (root / binding["gate_report"]).resolve()
    if root not in gate_path.parents or not gate_path.is_file():
        _fail("active route gate report is missing or outside the repository")
    if _sha256_path(gate_path).lower() != binding["gate_report_sha256"].lower():
        _fail("active route gate report hash does not match")
    validated = load_route_gate(gate_path, route_id=binding["route_id"])
    route = validated["route"]
    artifact_root = gate_path.parent.parent.resolve()
    for binding_path, route_path, hash_name in (
        ("prior_path", "prior_path", "prior_sha256"),
        ("evidence_path", "evidence_path", "evidence_sha256"),
        ("artifact_manifest_path", "artifact_manifest_path", "artifact_manifest_sha256"),
    ):
        resolved_binding = (root / binding[binding_path]).resolve()
        resolved_route = (artifact_root / route[route_path]).resolve()
        if resolved_binding != resolved_route or binding[hash_name] != route[hash_name]:
            _fail(f"active route binding does not match route {route_path}")
        if not resolved_binding.is_file() or _sha256_path(resolved_binding).lower() != binding[hash_name].lower():
            _fail(f"active route binding hash does not match {route_path}")
    return validated


validate_route_gate = load_route_gate
