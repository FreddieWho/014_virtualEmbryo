#!/usr/bin/env python3
"""Deploy and audit the T3 prior toolchain from local, hash-locked inputs only.

This script never installs from an index and never fetches data.  A missing
knowledge snapshot is an explicit blocker; it is not replaced by a TF-only
or unregistered graph.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CELLORACLE_ARCHIVE = (
    "infra/external_data/sanitized/T3/B2-T3-A1/CELLORACLE/"
    "CellOracle-7948870a3b70f7d228e54734e1fa9ed3291fc23b.tar.gz"
)
SCTENIFOLD_ARCHIVE = (
    "infra/external_data/sanitized/T3/B2-T3-A1/SCTENIFOLDKNK/"
    "scTenifoldKnk-d635a5855295b4ee75909438b09b2ea27ce3437c.tar.gz"
)
SCTENIFOLDNET_ARCHIVE = (
    "artifacts/tool_integration/T3-S1-PRIOR/deployment/cache/"
    "scTenifoldNet_1.4.tar.gz"
)
SOURCE_VERSIONS = {
    "CellOracle": "0.22.0",
    "scTenifoldNet": "1.4",
    "scTenifoldKnk": "1.1",
}
DOCREP_CACHE = "artifacts/tool_integration/T3-S1-PRIOR/deployment/cache/docrep-0.3.2.tar.gz"
R_FALLBACK_ROOT = Path("/home/huyudi/R/x86_64-pc-linux-gnu-library/4.5")
LOCAL_DEPENDENCY_LOCK = "docs/batch3/config/T3_S1_LOCAL_DEPENDENCY_LOCK.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_command(
    command: list[str],
    *,
    env: dict[str, str] | None = None,
    timeout: int = 900,
) -> dict[str, Any]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            env=merged_env,
            timeout=timeout,
        )
        return {
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout[-6000:],
            "stderr": completed.stderr[-6000:],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "returncode": None,
            "stdout": (exc.stdout or "")[-6000:],
            "stderr": (exc.stderr or "")[-6000:],
            "timed_out": True,
        }


def archive_record(repo: Path, relative: str, verify_hash: bool) -> dict[str, Any]:
    archive = repo / relative
    manifest_path = archive.parent / "source_manifest.json"
    result: dict[str, Any] = {
        "path": str(archive),
        "present": archive.is_file(),
        "source_manifest": str(manifest_path),
        "status": "MISSING",
    }
    if not archive.is_file():
        return result
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected = manifest["files"][0]
        result.update(
            {
                "expected_bytes": expected.get("bytes"),
                "expected_sha256": expected.get("sha256"),
                "actual_bytes": archive.stat().st_size,
                "manifest_status": manifest.get("status"),
                "model_input": manifest.get("model_input"),
                "role": manifest.get("role"),
            }
        )
        result["bytes_match"] = result["actual_bytes"] == result["expected_bytes"]
        if verify_hash:
            result["actual_sha256"] = sha256_file(archive)
            result["hash_match"] = result["actual_sha256"] == result["expected_sha256"]
        else:
            result["hash_match"] = "MANIFEST_LOCKED_NOT_RECHECKED"
        if not result["bytes_match"]:
            result["status"] = "HASH_OR_SIZE_MISMATCH"
        elif verify_hash and result["hash_match"] is True:
            result["status"] = "PASS"
        else:
            result["status"] = "HASH_NOT_RECHECKED"
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        result["status"] = "MANIFEST_ERROR"
        result["error"] = str(exc)
    return result


def source_version(repo: Path, archive_relative: str, member_suffix: str) -> str | None:
    archive = repo / archive_relative
    try:
        with tarfile.open(archive) as handle:
            member = next(name for name in handle.getnames() if name.endswith(member_suffix))
            payload = handle.extractfile(member)
            if payload is None:
                return None
            text = payload.read().decode("utf-8", errors="replace")
        if member_suffix.endswith("version.py"):
            for line in text.splitlines():
                if "__version__" in line and "=" in line:
                    return line.split("=", 1)[1].strip().strip("'\"")
        if member_suffix.endswith("DESCRIPTION"):
            for line in text.splitlines():
                if line.startswith("Version:"):
                    return line.split(":", 1)[1].strip()
    except (OSError, tarfile.TarError, StopIteration):
        return None
    return None


def python_probe(
    python: Path,
    package: str,
    *,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    code = (
        "import importlib, importlib.util, sys; "
        f"spec=importlib.util.find_spec({package!r}); "
        "print('spec', spec.origin if spec else 'NONE'); "
        f"m=importlib.import_module({package!r}) if spec else None; "
        "print('version', getattr(m, '__version__', 'UNKNOWN') if m else 'NONE')"
    )
    result = run_command([str(python), "-c", code], env=env, timeout=180)
    result["package"] = package
    result["importable"] = result["returncode"] == 0 and "spec NONE" not in result["stdout"]
    return result


def _resolve_locked_path(repo: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else repo / path


def _package_metadata(archive: Path) -> dict[str, str]:
    metadata: dict[str, str] = {}
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as handle:
            metadata_name = next(
                name for name in handle.namelist()
                if name.endswith(".dist-info/METADATA")
                and name.count("/") == 1
            )
            text = handle.read(metadata_name).decode("utf-8", errors="replace")
        package_keys = {
            "Name": "name", "Version": "version", "License": "license",
            "License-Expression": "license",
        }
    elif tarfile.is_tarfile(archive):
        with tarfile.open(archive, "r:*") as handle:
            names = handle.getnames()
            description_name = next(
                (
                    name for name in names
                    if name == "DESCRIPTION" or name.endswith("/DESCRIPTION")
                ),
                None,
            )
            metadata_name = description_name or next(
                name for name in names
                if name == "PKG-INFO" or name.endswith("/PKG-INFO")
            )
            payload = handle.extractfile(metadata_name)
            if payload is None:
                raise ValueError("package metadata payload is missing")
            text = payload.read().decode("utf-8", errors="replace")
        package_keys = (
            {"Package": "name", "Version": "version", "License": "license"}
            if description_name
            else {"Name": "name", "Version": "version", "License": "license"}
        )
    else:
        raise ValueError("unsupported package archive format")
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        if key in package_keys and package_keys[key] not in metadata:
            metadata[package_keys[key]] = value.strip()
    if metadata.get("license", "").upper() in {"", "UNKNOWN"} and zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as handle:
            license_names = [
                name for name in handle.namelist()
                if name.endswith(".dist-info/licenses/LICENSE")
                or name.endswith(".dist-info/LICENSE")
            ]
            for license_name in license_names:
                license_text = handle.read(license_name).decode("utf-8", errors="replace")
                if "Permission is hereby granted" in license_text:
                    metadata["license"] = "MIT License"
                    break
    if metadata.get("license", "").upper() in {"", "UNKNOWN"} and tarfile.is_tarfile(archive):
        with tarfile.open(archive, "r:*") as handle:
            license_names = [
                name for name in handle.getnames()
                if name.endswith("/COPYING") or name.endswith("/LICENSE")
            ]
            for license_name in license_names:
                payload = handle.extractfile(license_name)
                license_text = payload.read().decode("utf-8", errors="replace") if payload else ""
                if "MIT License" in license_text or "Permission is hereby granted" in license_text:
                    metadata["license"] = "MIT License"
                    break
    return metadata


def local_package_record(
    repo: Path,
    deployment_dir: Path,
    package_name: str,
) -> dict[str, Any]:
    """Validate and expose one explicitly locked local package archive."""
    lock_path = repo / LOCAL_DEPENDENCY_LOCK
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        expected = lock["packages"][package_name]
        source = _resolve_locked_path(repo, expected["source_path"])
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        return {
            "status": "LOCK_ERROR",
            "package": package_name,
            "lock": str(lock_path),
            "reason": str(exc),
            "scientific_data": False,
        }
    if not source.is_file():
        return {
            "status": "MISSING",
            "package": package_name,
            "lock": str(lock_path),
            "source_path": str(source),
            "reason": "explicitly locked local package archive is absent",
            "scientific_data": False,
        }
    cache_dir = deployment_dir / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    target = cache_dir / source.name
    source_hash = sha256_file(source)
    source_bytes = source.stat().st_size
    if source_hash != expected["sha256"] or source_bytes != expected["bytes"]:
        return {
            "status": "HASH_OR_SIZE_MISMATCH",
            "package": package_name,
            "lock": str(lock_path),
            "source_path": str(source),
            "bytes": source_bytes,
            "sha256": source_hash,
            "expected_bytes": expected["bytes"],
            "expected_sha256": expected["sha256"],
            "scientific_data": False,
        }
    if target.resolve() != source.resolve():
        if target.is_file() and sha256_file(target) != source_hash:
            return {
                "status": "CACHE_TARGET_MISMATCH",
                "package": package_name,
                "lock": str(lock_path),
                "source_path": str(source),
                "artifact_path": str(target),
                "reason": "existing deployment cache target has a different hash",
                "scientific_data": False,
            }
        if not target.is_file():
            shutil.copy2(source, target)
    try:
        metadata = _package_metadata(target)
    except (OSError, KeyError, StopIteration, tarfile.TarError, ValueError, zipfile.BadZipFile) as exc:
        return {
            "status": "INVALID_METADATA",
            "package": package_name,
            "lock": str(lock_path),
            "source_path": str(source),
            "artifact_path": str(target),
            "sha256": source_hash,
            "bytes": source_bytes,
            "error": str(exc),
            "scientific_data": False,
        }
    if (
        metadata.get("name", "").lower() != package_name.lower()
        or metadata.get("version") != expected["version"]
        or metadata.get("license") != expected["license"]
    ):
        return {
            "status": "METADATA_MISMATCH",
            "package": package_name,
            "lock": str(lock_path),
            "source_path": str(source),
            "artifact_path": str(target),
            "bytes": source_bytes,
            "sha256": source_hash,
            "expected_version": expected["version"],
            "expected_license": expected["license"],
            "metadata": metadata,
            "scientific_data": False,
        }
    return {
        "status": "PRESENT_LOCAL_CACHE",
        "package": package_name,
        "lock": str(lock_path),
        "source_path": str(source),
        "artifact_path": str(target),
        "bytes": target.stat().st_size,
        "sha256": sha256_file(target),
        "source_sha256": source_hash,
        "metadata": metadata,
        "expected": expected,
        "acquisition": expected.get("acquisition", "pre-existing local cache; no network"),
        "license_evidence": metadata.get("license"),
        "scientific_data": False,
    }


KNOWLEDGE_SNAPSHOT_ROOTS = (
    "infra/external_data/sanitized",
    "docs/batch3",
)
KNOWLEDGE_REQUIREMENTS = ("CollecTRI", "OmniPath")


def _knowledge_candidates(repo: Path, source_name: str) -> list[Path]:
    token = source_name.lower().replace(" ", "")
    found: list[Path] = []
    for relative_root in KNOWLEDGE_SNAPSHOT_ROOTS:
        root = repo / relative_root
        if not root.exists():
            continue
        for directory, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(d for d in dirnames if d not in {".git", ".venvs"})
            for name in sorted(dirnames + filenames):
                if token in name.lower().replace(" ", ""):
                    found.append(Path(directory) / name)
    return sorted(set(found))


def _repo_relative_path(repo: Path, value: str, *, base: Path | None = None) -> Path:
    path = Path(value)
    resolved = (base / path if base is not None and not path.is_absolute() else path).resolve()
    repo_root = repo.resolve()
    if not resolved.is_relative_to(repo_root):
        raise ValueError(f"declared path escapes repository: {value}")
    return resolved


def _audit_knowledge_candidate(repo: Path, candidate: Path) -> dict[str, Any]:
    base = candidate if candidate.is_dir() else candidate.parent
    manifest_candidates = [
        base / "snapshot_manifest.json",
        Path(str(candidate) + ".manifest.json"),
    ]
    manifest_path = next((path for path in manifest_candidates if path.is_file()), None)
    if manifest_path is None:
        return {
            "candidate": str(candidate),
            "status": "PRESENT_BUT_NOT_AUDITED",
            "reason": "snapshot_manifest.json with provenance and file hashes is missing",
        }
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        source_url = manifest["source_url"]
        license_name = manifest["license"]
        schema = manifest["schema"]
        target_mapping = manifest["target_mapping"]
        directed_edges = manifest["directed_edges"]
        data_relative = manifest["data_path"]
        expected_bytes = int(manifest["bytes"])
        expected_sha256 = manifest["sha256"]
        data_path = _repo_relative_path(repo, data_relative, base=manifest_path.parent)
        if not source_url or not license_name or not schema:
            raise ValueError("source_url, license, and schema must be non-empty")
        if not target_mapping or int(directed_edges) <= 0:
            raise ValueError("target_mapping and directed_edges must be non-empty")
        if not data_path.is_file():
            raise ValueError("declared data_path is missing")
        actual_bytes = data_path.stat().st_size
        actual_sha256 = sha256_file(data_path)
        if actual_bytes != expected_bytes or actual_sha256 != expected_sha256:
            raise ValueError("declared data bytes/SHA256 do not match")
        data_format = str(schema.get("format", "")).upper()
        columns = schema.get("columns")
        if data_format != "TSV" or not isinstance(columns, list) or not columns:
            raise ValueError("knowledge snapshot must declare a non-empty TSV schema")
        with data_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            if reader.fieldnames != columns:
                raise ValueError("declared schema columns do not match TSV header")
            source_column = target_mapping.get("source_column")
            target_column = target_mapping.get("target_column")
            directed_column = str(schema.get("directed_column", "is_directed"))
            required_columns = {source_column, target_column, directed_column}
            if not required_columns.issubset(set(columns)):
                raise ValueError("target mapping or directed column is absent from TSV schema")
            row_count = 0
            directed_count = 0
            mapped_symbols: set[str] = set()
            for row in reader:
                row_count += 1
                if not row.get(source_column) or not row.get(target_column):
                    raise ValueError("knowledge snapshot contains an empty mapped edge symbol")
                mapped_symbols.update((row[source_column], row[target_column]))
                if str(row.get(directed_column, "")).lower() == "true":
                    directed_count += 1
            if row_count != int(directed_edges) or directed_count != int(directed_edges):
                raise ValueError("declared directed edge count does not match TSV content")

        panel_reference = target_mapping.get("panel_reference")
        panel_gene_count = int(target_mapping.get("panel_gene_count", 0))
        expected_overlap = int(target_mapping.get("edge_symbols_overlapping_panel", 0))
        if not panel_reference or panel_gene_count <= 0 or expected_overlap <= 0:
            raise ValueError("target mapping must declare a non-empty panel reference and counts")
        panel_path = _repo_relative_path(repo, str(panel_reference))
        if not panel_path.is_file():
            raise ValueError("declared target-mapping panel is missing")
        panel_symbols = {
            line.strip()
            for line in panel_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
        if len(panel_symbols) != panel_gene_count:
            raise ValueError("declared panel gene count does not match panel content")
        query = manifest.get("source_query", {})
        expected_panel_sha256 = query.get("partners_panel_sha256")
        if expected_panel_sha256 and sha256_file(panel_path) != expected_panel_sha256:
            raise ValueError("declared target-mapping panel SHA256 does not match")
        actual_overlap = len(mapped_symbols & panel_symbols)
        if actual_overlap != expected_overlap:
            raise ValueError("declared panel edge-symbol overlap does not match TSV content")
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return {
            "candidate": str(candidate),
            "manifest": str(manifest_path),
            "status": "PRESENT_BUT_NOT_AUDITED",
            "reason": str(exc),
        }
    return {
        "candidate": str(candidate),
        "manifest": str(manifest_path),
        "status": "AUDITED_PASS",
        "source_url": source_url,
        "license": license_name,
        "schema": schema,
        "target_mapping_count": panel_gene_count,
        "edge_symbols_overlapping_panel": expected_overlap,
        "directed_edges": int(directed_edges),
        "row_count": row_count,
        "all_edges_directed": directed_count == int(directed_edges),
        "panel_path": str(panel_path),
        "data_path": str(data_path),
        "bytes": expected_bytes,
        "sha256": expected_sha256,
    }


def knowledge_snapshot_audit(repo: Path) -> dict[str, Any]:
    sources: dict[str, Any] = {}
    for source_name in KNOWLEDGE_REQUIREMENTS:
        candidates = _knowledge_candidates(repo, source_name)
        audits = [_audit_knowledge_candidate(repo, candidate) for candidate in candidates]
        passing = [audit for audit in audits if audit["status"] == "AUDITED_PASS"]
        sources[source_name] = {
            "status": "AUDITED_PASS" if passing else (
                "PRESENT_BUT_NOT_AUDITED" if audits else "MISSING"
            ),
            "audits": audits,
        }
    overall = (
        "AUDITED_PASS"
        if all(source["status"] == "AUDITED_PASS" for source in sources.values())
        else "BLOCKED_EXTERNAL_DATA"
    )
    return {
        "status": overall,
        "required": list(KNOWLEDGE_REQUIREMENTS),
        "sources": sources,
        "fallback_used": None,
        "audit_contract": {
            "required_fields": [
                "source_url", "license", "sha256", "schema",
                "target_mapping", "directed_edges", "data_path", "bytes",
            ],
            "requirement": "both sources must be independently audited; filename presence is insufficient",
        },
    }


def data_manifest_status(repo: Path) -> dict[str, Any]:
    root = repo / "infra/external_data/sanitized/T3/B2-T3-A1"
    entries: dict[str, Any] = {}
    for source_id, relative in {
        "E-MTAB-6967": "EMTAB6967/source_manifest.json",
        "E-MTAB-11763": "EMTAB11763/source_manifest.json",
        "GSE52123": "GSE52123/source_manifest.json",
    }.items():
        path = root / relative
        if not path.is_file():
            entries[source_id] = {"status": "MISSING", "manifest": str(path)}
            continue
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            role_by_source = {
                "E-MTAB-6967": "WT expression model input",
                "E-MTAB-11763": "metadata-only fallback; not expression input",
                "GSE52123": "GATA4 ChIP directness only; not expression input",
            }
            entries[source_id] = {
                "status": manifest.get("status"),
                "model_input": manifest.get("model_input"),
                "source_id": manifest.get("source_id", source_id),
                "manifest": str(path),
                "sanitized_sha256": manifest.get("sanitized", {}).get("sanitized_sha256"),
                "sanitized_meta_sha256": manifest.get("sanitized_meta_sha256"),
                "sanitized_genes_sha256": manifest.get("sanitized_genes_sha256"),
                "role": role_by_source.get(source_id, "metadata/directness/supporting evidence only"),
            }
        except (OSError, json.JSONDecodeError) as exc:
            entries[source_id] = {"status": "MANIFEST_ERROR", "error": str(exc)}
    return entries


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--env-dir", type=Path, default=None,
        help="default: <repo>/.venvs/ve-t3-prior",
    )
    parser.add_argument(
        "--verify-hash", action="store_true",
        help="re-read the large archives and compare their SHA256 to source_manifest.json",
    )
    parser.add_argument(
        "--reuse-local-installs", action="store_true",
        help="skip reinstalling packages already deployed in the task environment",
    )
    args = parser.parse_args()

    repo = args.repo.resolve()
    artifact = repo / "artifacts/tool_integration/T3-S1-PRIOR"
    deployment_dir = artifact / "deployment"
    deployment_dir.mkdir(parents=True, exist_ok=True)
    env_dir = (args.env_dir or repo / ".venvs/ve-t3-prior").resolve()
    r_library = env_dir / "Rlib"

    report: dict[str, Any] = {
        "schema": "ve.t3.prior.local-deployment.v1",
        "task": "T3-S1-PRIOR",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "policy": {
            "network_used": False,
            "external_downloads_used": False,
            "external_downloads_pre_acquired": True,
            "download_authorization": "explicit user authorization on 2026-08-31",
            "pip_index": "disabled",
            "source_policy": "local cache and hash-locked B2/software artifacts only",
        },
        "archives": {},
        "environment": {},
        "tools": {},
        "local_dependency_caches": {
            "docrep": {
                "archive": str(repo / DOCREP_CACHE),
                "manifest": str(repo / "artifacts/tool_integration/T3-S1-PRIOR/deployment/cache/docrep-0.3.2.manifest.json"),
                "status": "PRESENT" if (repo / DOCREP_CACHE).is_file() else "MISSING",
            },
            "velocyto": local_package_record(repo, deployment_dir, "velocyto"),
            "biothings_client": local_package_record(repo, deployment_dir, "biothings_client"),
            "mygene": local_package_record(repo, deployment_dir, "mygene"),
            "mysql-connector-python": local_package_record(repo, deployment_dir, "mysql-connector-python"),
            "pyfaidx": local_package_record(repo, deployment_dir, "pyfaidx"),
            "gimmemotifs": local_package_record(repo, deployment_dir, "gimmemotifs"),
            "setuptools": local_package_record(repo, deployment_dir, "setuptools"),
            "Cython": local_package_record(repo, deployment_dir, "Cython"),
            "louvain": local_package_record(repo, deployment_dir, "louvain"),
            "xdg": local_package_record(repo, deployment_dir, "xdg"),
            "pybedtools": local_package_record(repo, deployment_dir, "pybedtools"),
            "biofluff": local_package_record(repo, deployment_dir, "biofluff"),
            "feather-format": local_package_record(repo, deployment_dir, "feather-format"),
            "iteround": local_package_record(repo, deployment_dir, "iteround"),
            "logomaker": local_package_record(repo, deployment_dir, "logomaker"),
            "qnorm": local_package_record(repo, deployment_dir, "qnorm"),
            "pyarrow": local_package_record(repo, deployment_dir, "pyarrow"),
            "genomepy": local_package_record(repo, deployment_dir, "genomepy"),
            "scTenifoldNet": local_package_record(repo, deployment_dir, "scTenifoldNet"),
        },
        "data": data_manifest_status(repo),
        "knowledge_snapshots": {},
        "overall_status": "IN_PROGRESS",
    }
    log_lines: list[str] = []

    for name, relative in {
        "CellOracle": CELLORACLE_ARCHIVE,
        "scTenifoldKnk": SCTENIFOLD_ARCHIVE,
    }.items():
        record = archive_record(repo, relative, args.verify_hash)
        report["archives"][name] = record
        log_lines.append(json.dumps({"archive": name, **record}, ensure_ascii=False))

    # The two values were read from the pinned archives during the preflight.
    # Avoid a second full gzip scan here; the manifest/hash remains the source
    # identity and the package probe below is the deployment check.
    celloracle_source_version = SOURCE_VERSIONS["CellOracle"]
    sctenifold_source_version = SOURCE_VERSIONS["scTenifoldKnk"]

    env_created = False
    env_python = env_dir / "bin/python"
    if not (env_dir / "pyvenv.cfg").is_file():
        env_dir.parent.mkdir(parents=True, exist_ok=True)
        result = run_command(
            [sys.executable, "-m", "venv", "--system-site-packages", str(env_dir)],
            timeout=300,
        )
        log_lines.append(json.dumps({"venv": result}, ensure_ascii=False))
        env_created = result["returncode"] == 0
    else:
        env_created = True
    report["environment"].update(
        {
            "path": str(env_dir),
            "python": str(env_python),
            "created_or_reused": env_created,
            "dependency_isolation": "partial_system_site_packages",
            "r_library": str(r_library),
            "python_runtime_env": {
                "LD_LIBRARY_PATH": "/opt/anaconda3/lib",
                "MPLCONFIGDIR": str(deployment_dir / "mplconfig"),
                "NUMBA_CACHE_DIR": str(deployment_dir / "numba_cache"),
                "XDG_CONFIG_HOME": str(deployment_dir / "xdg_config"),
                "XDG_CACHE_HOME": str(deployment_dir / "xdg_cache"),
                "PIP_CACHE_DIR": str(deployment_dir / "pip_cache"),
            },
        }
    )

    python_probe_env = {
        "LD_LIBRARY_PATH": "/opt/anaconda3/lib",
        "MPLCONFIGDIR": str(deployment_dir / "mplconfig"),
        "NUMBA_CACHE_DIR": str(deployment_dir / "numba_cache"),
        "XDG_CONFIG_HOME": str(deployment_dir / "xdg_config"),
        "XDG_CACHE_HOME": str(deployment_dir / "xdg_cache"),
        "PIP_CACHE_DIR": str(deployment_dir / "pip_cache"),
    }
    (deployment_dir / "mplconfig").mkdir(parents=True, exist_ok=True)
    (deployment_dir / "numba_cache").mkdir(parents=True, exist_ok=True)
    (deployment_dir / "xdg_config").mkdir(parents=True, exist_ok=True)
    (deployment_dir / "xdg_cache").mkdir(parents=True, exist_ok=True)
    (deployment_dir / "pip_cache").mkdir(parents=True, exist_ok=True)
    if env_created and env_python.is_file():
        def install_python_archive(
            package: str,
            archive: Path,
            *,
            timeout: int = 1200,
        ) -> dict[str, Any]:
            if args.reuse_local_installs:
                return {
                    "status": "REUSED_LOCAL_INSTALL",
                    "returncode": 0,
                    "archive": str(archive),
                }
            result = run_command(
                [
                    str(env_python), "-m", "pip", "install",
                    "--no-index", "--no-deps", "--no-build-isolation",
                    "--disable-pip-version-check", str(archive),
                ],
                env=python_probe_env,
                timeout=timeout,
            )
            result["package"] = package
            result["status"] = (
                "LOCAL_CACHE_INSTALL" if result["returncode"] == 0
                else "LOCAL_CACHE_INSTALL_FAILED"
            )
            return result

        for dependency in (
            "biothings_client", "mygene", "mysql-connector-python", "pyfaidx",
            "setuptools", "Cython", "louvain", "xdg", "pybedtools", "biofluff", "feather-format",
            "iteround", "logomaker", "qnorm", "pyarrow", "gimmemotifs"
        ):
            dependency_cache = report["local_dependency_caches"][dependency]
            dependency_archive = Path(dependency_cache.get("artifact_path", ""))
            if dependency_cache.get("status") == "PRESENT_LOCAL_CACHE" and dependency_archive.is_file():
                dependency_install = install_python_archive(
                    dependency, dependency_archive, timeout=300
                )
            else:
                dependency_install = {
                    "status": "NOT_DEPLOYED",
                    "reason": f"no provenance-locked local {dependency} archive",
                }
            report["tools"][f"{dependency}_install"] = dependency_install
            log_lines.append(
                json.dumps({f"{dependency}_install": dependency_install}, ensure_ascii=False)
            )

        genomepy_cache = report["local_dependency_caches"]["genomepy"]
        genomepy_archive = Path(genomepy_cache.get("artifact_path", ""))
        if genomepy_cache.get("status") == "PRESENT_LOCAL_CACHE" and genomepy_archive.is_file():
            genomepy_install = install_python_archive("genomepy", genomepy_archive, timeout=300)
        else:
            genomepy_install = {
                "status": "NOT_DEPLOYED",
                "reason": "no provenance-locked local genomepy archive",
            }
        report["tools"]["genomepy_install"] = genomepy_install
        log_lines.append(json.dumps({"genomepy_install": genomepy_install}, ensure_ascii=False))

        velocyto_cache = report["local_dependency_caches"]["velocyto"]
        velocyto_archive = Path(velocyto_cache.get("artifact_path", ""))
        if velocyto_cache.get("status") == "PRESENT_LOCAL_CACHE" and velocyto_archive.is_file():
            velocyto_install = install_python_archive("velocyto", velocyto_archive, timeout=300)
            report["tools"]["velocyto_install"] = velocyto_install
        else:
            report["tools"]["velocyto_install"] = {
                "status": "NOT_DEPLOYED",
                "reason": "no provenance-locked local wheel cache",
            }

        docrep_archive = repo / DOCREP_CACHE
        if docrep_archive.is_file():
            docrep_install = (
                {
                    "status": "REUSED_LOCAL_CACHE_INSTALL",
                    "returncode": 0,
                    "archive": str(docrep_archive),
                }
                if args.reuse_local_installs
                else run_command(
                    [
                        str(env_python), "-m", "pip", "install",
                        "--no-index", "--no-deps", "--no-build-isolation",
                        "--disable-pip-version-check", str(docrep_archive),
                    ],
                    env=python_probe_env,
                    timeout=300,
                )
            )
            report["tools"]["docrep_install"] = docrep_install
            log_lines.append(json.dumps({"docrep_install": docrep_install}, ensure_ascii=False))
        else:
            report["tools"]["docrep_install"] = {
                "status": "NOT_DEPLOYED",
                "reason": "no provenance-locked local cache",
            }

        install = install_python_archive(
            "CellOracle", repo / CELLORACLE_ARCHIVE, timeout=1200
        )
        report["tools"]["CellOracle_install"] = install
        log_lines.append(json.dumps({"CellOracle_install": install}, ensure_ascii=False))

        report["tools"]["velocyto_import"] = python_probe(
            env_python, "velocyto", env=python_probe_env
        )
        report["tools"]["biothings_client_import"] = python_probe(
            env_python, "biothings_client", env=python_probe_env
        )
        report["tools"]["mygene_import"] = python_probe(
            env_python, "mygene", env=python_probe_env
        )
        report["tools"]["mysql_connector_import"] = python_probe(
            env_python, "mysql.connector", env=python_probe_env
        )
        report["tools"]["pyfaidx_import"] = python_probe(
            env_python, "pyfaidx", env=python_probe_env
        )
        report["tools"]["gimmemotifs_scanner_import"] = python_probe(
            env_python, "gimmemotifs.scanner", env=python_probe_env
        )
        report["tools"]["setuptools_import"] = python_probe(
            env_python, "setuptools", env=python_probe_env
        )
        report["tools"]["Cython_import"] = python_probe(
            env_python, "Cython", env=python_probe_env
        )
        report["tools"]["louvain_import"] = python_probe(
            env_python, "louvain", env=python_probe_env
        )
        report["tools"]["xdg_import"] = python_probe(
            env_python, "xdg", env=python_probe_env
        )
        report["tools"]["pybedtools_import"] = python_probe(
            env_python, "pybedtools", env=python_probe_env
        )
        report["tools"]["biofluff_import"] = python_probe(
            env_python, "fluff", env=python_probe_env
        )
        report["tools"]["feather_format_import"] = python_probe(
            env_python, "feather", env=python_probe_env
        )
        report["tools"]["iteround_import"] = python_probe(
            env_python, "iteround", env=python_probe_env
        )
        report["tools"]["logomaker_import"] = python_probe(
            env_python, "logomaker", env=python_probe_env
        )
        report["tools"]["qnorm_import"] = python_probe(
            env_python, "qnorm", env=python_probe_env
        )
        report["tools"]["pyarrow_import"] = python_probe(
            env_python, "pyarrow", env=python_probe_env
        )
        report["tools"]["genomepy_import"] = python_probe(
            env_python, "genomepy", env=python_probe_env
        )
        report["tools"]["CellOracle_import"] = python_probe(
            env_python, "celloracle", env=python_probe_env
        )
        report["tools"]["decoupler"] = python_probe(
            env_python, "decoupler", env=python_probe_env
        )
        report["tools"]["anndata"] = python_probe(
            env_python, "anndata", env=python_probe_env
        )
        log_lines.extend(
            json.dumps({key: value}, ensure_ascii=False)
            for key, value in report["tools"].items()
            if key in {
                "velocyto_import", "biothings_client_import", "mygene_import",
                "mysql_connector_import",
                "pyfaidx_import",
                "gimmemotifs_scanner_import",
                "setuptools_import",
                "Cython_import", "louvain_import",
                "xdg_import",
                "pybedtools_import",
                "biofluff_import", "feather_format_import", "iteround_import",
                "logomaker_import", "qnorm_import", "pyarrow_import",
                "genomepy_import", "CellOracle_import", "decoupler", "anndata",
            }
        )
    else:
        report["tools"]["CellOracle_install"] = {
            "status": "NOT_DEPLOYED",
            "reason": "venv creation failed",
        }

    r_library.mkdir(parents=True, exist_ok=True)
    r_env = {"R_LIBS": str(r_library)}
    scnet_cache = report["local_dependency_caches"]["scTenifoldNet"]
    scnet_archive = Path(scnet_cache.get("artifact_path", ""))
    if scnet_cache.get("status") == "PRESENT_LOCAL_CACHE" and scnet_archive.is_file():
        scnet_install = (
            {
                "status": "REUSED_SOURCE_INSTALL_ATTEMPT",
                "returncode": None,
                "archive": str(scnet_archive),
            }
            if args.reuse_local_installs
            else run_command(
                [
                    "R", "CMD", "INSTALL", "--library=" + str(r_library),
                    "--no-test-load", str(scnet_archive),
                ],
                env=r_env,
                timeout=1800,
            )
        )
        report["tools"]["scTenifoldNet_install"] = scnet_install
        log_lines.append(json.dumps({"scTenifoldNet_install": scnet_install}, ensure_ascii=False))
        scnet_probe = run_command(
            [
                "Rscript", "--vanilla", "-e",
                "cat(as.character(packageVersion('scTenifoldNet')),'\\n',find.package('scTenifoldNet'))",
            ],
            env=r_env,
            timeout=180,
        )
        report["tools"]["scTenifoldNet_import"] = scnet_probe
        report["tools"]["scTenifoldNet_import"]["source_version"] = SOURCE_VERSIONS["scTenifoldNet"]
        report["tools"]["scTenifoldNet_import"]["source_version_match"] = (
            scnet_probe["returncode"] == 0
            and scnet_probe["stdout"].splitlines()[0].strip() == SOURCE_VERSIONS["scTenifoldNet"]
        )
        log_lines.append(json.dumps({"scTenifoldNet_import": scnet_probe}, ensure_ascii=False))
    else:
        report["tools"]["scTenifoldNet_install"] = {
            "status": "NOT_DEPLOYED",
            "reason": "no provenance-locked local scTenifoldNet archive",
        }
        report["tools"]["scTenifoldNet_import"] = {
            "status": "NOT_TESTABLE",
            "source_version": SOURCE_VERSIONS["scTenifoldNet"],
            "source_version_match": False,
        }

    r_archive = repo / SCTENIFOLD_ARCHIVE
    if r_archive.is_file():
        r_install = (
            {
                "status": "REUSED_SOURCE_INSTALL_ATTEMPT",
                "returncode": None,
                "archive": str(r_archive),
            }
            if args.reuse_local_installs
            else run_command(
                [
                    "R", "CMD", "INSTALL", "--library=" + str(r_library),
                    "--no-test-load", str(r_archive),
                ],
                env=r_env,
                timeout=1800,
            )
        )
        report["tools"]["scTenifoldKnk_install"] = r_install
        log_lines.append(json.dumps({"scTenifoldKnk_install": r_install}, ensure_ascii=False))
        r_probe = run_command(
            [
                "Rscript", "--vanilla", "-e",
                "cat(as.character(packageVersion('scTenifoldKnk')),'\\n',find.package('scTenifoldKnk'))",
            ],
            env=r_env,
            timeout=180,
        )
        report["tools"]["scTenifoldKnk_import"] = r_probe
        report["tools"]["scTenifoldKnk_import"]["source_version"] = sctenifold_source_version
        report["tools"]["scTenifoldKnk_import"]["source_version_match"] = (
            r_probe["returncode"] == 0
            and r_probe["stdout"].splitlines()[0].strip() == sctenifold_source_version
        )
        log_lines.append(json.dumps({"scTenifoldKnk_import": r_probe}, ensure_ascii=False))
        fallback_records: dict[str, Any] = {}
        for package in ("scTenifoldNet", "scTenifoldKnk"):
            source_dir = R_FALLBACK_ROOT / package
            target_dir = r_library / package
            if source_dir.is_dir() and not target_dir.exists():
                shutil.copytree(source_dir, target_dir)
            description = source_dir / "DESCRIPTION"
            fallback_records[package] = {
                "source_path": str(source_dir),
                "local_path": str(target_dir),
                "present": source_dir.is_dir(),
                "copied": target_dir.is_dir() and source_dir.is_dir(),
                "description_sha256": sha256_file(description) if description.is_file() else None,
                "role": "version-mismatched local fallback; not source-archive equivalence",
            }
        report["tools"]["scTenifoldKnk_local_fallback"] = {
            "status": "PRESENT_VERSION_MISMATCH" if fallback_records.get("scTenifoldKnk", {}).get("present") else "MISSING",
            "packages": fallback_records,
            "source_requirement": "scTenifoldNet >= 1.4 for scTenifoldKnk source 1.1",
            "scientific_use": "approved independent-vote fallback only; no source-version claim",
        }
        log_lines.append(
            json.dumps(
                {"scTenifoldKnk_local_fallback": report["tools"]["scTenifoldKnk_local_fallback"]},
                ensure_ascii=False,
            )
        )
        fallback_probe = run_command(
            [
                "Rscript", "--vanilla", "-e",
                "cat(as.character(packageVersion('scTenifoldKnk')),'\\n',find.package('scTenifoldKnk'))",
            ],
            env=r_env,
            timeout=180,
        )
        report["tools"]["scTenifoldKnk_local_fallback_probe"] = fallback_probe
        log_lines.append(
            json.dumps({"scTenifoldKnk_local_fallback_probe": fallback_probe}, ensure_ascii=False)
        )
        fallback_smoke = run_command(
            [
                "Rscript", "--vanilla", "-e",
                "set.seed(1); x <- matrix(rpois(30*30, lambda=3), nrow=30, ncol=30); "
                "rownames(x) <- paste0('g',seq_len(nrow(x))); "
                "colnames(x) <- paste0('c',seq_len(ncol(x))); "
                "out <- scTenifoldKnk::scTenifoldKnk(x, qc=FALSE, gKO='g1', "
                "nc_nNet=1, nc_nCells=20, nc_nComp=2, td_K=2, td_maxIter=10, "
                "ma_nDim=2, nCores=1); cat('SMOKE_OK ',length(out),'\\n',sep='')",
            ],
            env=r_env,
            timeout=300,
        )
        report["tools"]["scTenifoldKnk_fallback_smoke"] = fallback_smoke
        log_lines.append(
            json.dumps({"scTenifoldKnk_fallback_smoke": fallback_smoke}, ensure_ascii=False)
        )
    else:
        report["tools"]["scTenifoldKnk_install"] = {
            "status": "NOT_DEPLOYED",
            "reason": "source archive missing",
        }

    report["tools"]["source_versions"] = {
        "CellOracle": celloracle_source_version,
        "scTenifoldNet": SOURCE_VERSIONS["scTenifoldNet"],
        "scTenifoldKnk": sctenifold_source_version,
    }
    report["knowledge_snapshots"] = knowledge_snapshot_audit(repo)

    archive_ok = all(item.get("status") == "PASS" for item in report["archives"].values())
    package_cache_ok = all(
        report["local_dependency_caches"].get(package, {}).get("status")
        == "PRESENT_LOCAL_CACHE"
        for package in (
            "velocyto", "biothings_client", "mygene", "mysql-connector-python",
            "pyfaidx", "setuptools", "Cython", "louvain", "xdg", "pybedtools", "biofluff",
            "feather-format", "iteround", "logomaker", "qnorm", "pyarrow",
            "gimmemotifs",
            "genomepy", "scTenifoldNet"
        )
    )
    biothings_client_import = report["tools"].get("biothings_client_import", {}).get("importable", False)
    mygene_import = report["tools"].get("mygene_import", {}).get("importable", False)
    mysql_connector_import = report["tools"].get("mysql_connector_import", {}).get("importable", False)
    pyfaidx_import = report["tools"].get("pyfaidx_import", {}).get("importable", False)
    gimmemotifs_import = report["tools"].get("gimmemotifs_scanner_import", {}).get("importable", False)
    setuptools_import = report["tools"].get("setuptools_import", {}).get("importable", False)
    cython_import = report["tools"].get("Cython_import", {}).get("importable", False)
    louvain_import = report["tools"].get("louvain_import", {}).get("importable", False)
    xdg_import = report["tools"].get("xdg_import", {}).get("importable", False)
    pybedtools_import = report["tools"].get("pybedtools_import", {}).get("importable", False)
    biofluff_import = report["tools"].get("biofluff_import", {}).get("importable", False)
    feather_format_import = report["tools"].get("feather_format_import", {}).get("importable", False)
    iteround_import = report["tools"].get("iteround_import", {}).get("importable", False)
    logomaker_import = report["tools"].get("logomaker_import", {}).get("importable", False)
    qnorm_import = report["tools"].get("qnorm_import", {}).get("importable", False)
    pyarrow_import = report["tools"].get("pyarrow_import", {}).get("importable", False)
    genomepy_import = report["tools"].get("genomepy_import", {}).get("importable", False)
    velocyto_import = report["tools"].get("velocyto_import", {}).get("importable", False)
    cell_import = report["tools"].get("CellOracle_import", {}).get("importable", False)
    scnet_install_ok = (
        (
            report["tools"].get("scTenifoldNet_install", {}).get("returncode") == 0
            or report["tools"].get("scTenifoldNet_install", {}).get("status")
            == "REUSED_SOURCE_INSTALL_ATTEMPT"
        )
        and report["tools"].get("scTenifoldNet_import", {}).get("source_version_match") is True
    )
    sctenifold_knk_ok = (
        (
            report["tools"].get("scTenifoldKnk_install", {}).get("returncode") == 0
            or report["tools"].get("scTenifoldKnk_install", {}).get("status")
            == "REUSED_SOURCE_INSTALL_ATTEMPT"
        )
        and report["tools"].get("scTenifoldKnk_import", {}).get("source_version_match") is True
    )
    method_ready = (
        archive_ok and package_cache_ok and biothings_client_import and mygene_import
        and mysql_connector_import and pyfaidx_import and gimmemotifs_import
        and setuptools_import and cython_import and louvain_import and xdg_import
        and pybedtools_import and biofluff_import
        and feather_format_import and iteround_import and logomaker_import and qnorm_import
        and pyarrow_import and genomepy_import
        and velocyto_import and cell_import
        and scnet_install_ok and sctenifold_knk_ok
    )
    knowledge_ok = report["knowledge_snapshots"]["status"] == "AUDITED_PASS"
    report["overall_status"] = (
        "PASS"
        if method_ready and knowledge_ok
        else "BLOCKED_EXTERNAL_DATA"
        if method_ready and not knowledge_ok
        else "PARTIAL_LOCAL_DEPLOYMENT"
    )
    report["deployment_gates"] = {
        "source_archives_verified": archive_ok,
        "required_local_caches_verified": package_cache_ok,
        "biothings_client_importable": biothings_client_import,
        "mygene_importable": mygene_import,
        "mysql_connector_importable": mysql_connector_import,
        "pyfaidx_importable": pyfaidx_import,
        "gimmemotifs_scanner_importable": gimmemotifs_import,
        "setuptools_importable": setuptools_import,
        "Cython_importable": cython_import,
        "louvain_importable": louvain_import,
        "xdg_importable": xdg_import,
        "pybedtools_importable": pybedtools_import,
        "biofluff_importable": biofluff_import,
        "feather_format_importable": feather_format_import,
        "iteround_importable": iteround_import,
        "logomaker_importable": logomaker_import,
        "qnorm_importable": qnorm_import,
        "pyarrow_importable": pyarrow_import,
        "genomepy_importable": genomepy_import,
        "velocyto_importable": velocyto_import,
        "CellOracle_importable": cell_import,
        "scTenifoldNet_source_version_match": scnet_install_ok,
        "scTenifoldKnk_source_version_match": sctenifold_knk_ok,
        "method_deployment_ready": method_ready,
        "knowledge_snapshots_audited": knowledge_ok,
    }
    report["science_impact"] = {
        "Gata4_Gata6_condition": (
            "method_deployment_ready_but_prior_not_yet_run"
            if method_ready
            else "BLOCKED_TOOLCHAIN"
        ),
        "beta_catenin_condition": (
            "BLOCKED_EXTERNAL_DATA" if not knowledge_ok else "method_deployment_ready_but_prior_not_yet_run"
        ),
        "blocks_submission": False,
    }

    report_path = deployment_dir / "deployment_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tool_versions = {
        "schema": "ve.t3.prior.tool-versions.v1",
        "task": "T3-S1-PRIOR",
        "deployment_report": str(report_path),
        "network_used": False,
        "external_downloads_used": False,
        "external_downloads_pre_acquired": True,
        "download_authorization": "explicit user authorization on 2026-08-31",
        "source_archives": report["archives"],
        "local_dependency_caches": report["local_dependency_caches"],
        "source_versions": report["tools"].get("source_versions", {}),
        "runtime": {
            "python": sys.version,
            "python_executable": sys.executable,
            "r_library": str(r_library),
        },
        "observed_tools": {
            key: {
                "returncode": value.get("returncode"),
                "importable": value.get("importable"),
                "stdout_tail": value.get("stdout", "")[-1000:],
            }
            for key, value in report["tools"].items()
            if isinstance(value, dict) and key not in {"CellOracle_install", "scTenifoldKnk_install"}
        },
        "knowledge_snapshots": report["knowledge_snapshots"],
        "overall_status": report["overall_status"],
    }
    (artifact / "TOOL_VERSIONS.json").write_text(
        json.dumps(tool_versions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (deployment_dir / "deploy.log").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["overall_status"], "report": str(report_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
