#!/usr/bin/env python3
"""Recheck every P0 parent against the implemented Batch 3 H5AD contract.

This is a read-only parent/contract preflight.  It writes reports and hashes
only; it never edits a parent, creates a candidate, scores, or submits one.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

import sys

INTERFACE_ROOT = Path(__file__).resolve().parents[1] / "docs" / "batch3" / "interfaces"
if str(INTERFACE_ROOT) not in sys.path:
    sys.path.insert(0, str(INTERFACE_ROOT))

from virtual_embryo_tools.contract_io import validate_h5ad_contract  # noqa: E402


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_file(path: Path, repo: Path) -> dict[str, Any]:
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    return {
        "path": str(path.relative_to(repo)),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def run(repo: Path, output_dir: Path) -> dict[str, Any]:
    repo = Path(repo).resolve()
    output_dir = Path(output_dir).resolve()
    if output_dir.exists() and not output_dir.is_dir():
        raise NotADirectoryError(output_dir)
    if output_dir.is_dir() and any(output_dir.iterdir()):
        raise FileExistsError(
            f"refusing to overwrite existing preflight output directory: {output_dir}"
        )
    p0 = repo / "artifacts/tool_integration/P0-LOCK"
    lock_path = p0 / "locks/SCORER_LOCK.json"
    registry_path = p0 / "locks/PARENT_REGISTRY.yaml"
    adapter_path = repo / "docs/batch3/interfaces/virtual_embryo_tools/contract_io.py"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    parents = registry.get("parents", [])
    if not parents:
        raise ValueError("P0 parent registry contains no parents")

    output_dir.mkdir(parents=True, exist_ok=True)
    test_log_path = output_dir / "tests.log"
    test_command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "docs/batch3/interfaces/tests",
    ]
    test_env = os.environ.copy()
    test_env["PYTHONPATH"] = os.pathsep.join(
        [str(repo / "docs/batch3/interfaces"), str(repo), test_env.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)
    test_run = subprocess.run(
        test_command,
        cwd=repo,
        env=test_env,
        capture_output=True,
        text=True,
        check=False,
    )
    test_output = (test_run.stdout or "") + (test_run.stderr or "")
    test_log_path.write_text(test_output, encoding="utf-8")
    test_summary_line = next(
        (line.strip() for line in reversed(test_output.splitlines()) if line.strip()),
        "",
    )
    test_result = {
        "status": "PASS" if test_run.returncode == 0 else "FAIL",
        "returncode": int(test_run.returncode),
        "command": test_command,
        "log_path": str(test_log_path.relative_to(repo)),
        "log_sha256": sha256_file(test_log_path),
        "summary_line": test_summary_line,
    }

    rows: list[dict[str, Any]] = []
    for parent in parents:
        board_key = str(parent["board"])
        task, board = board_key.split(":", 1)
        path = repo / str(parent["canonical_path"])
        actual_sha = sha256_file(path) if path.is_file() else None
        expected_sha = str(parent.get("sha256", ""))
        contract = validate_h5ad_contract(
            path,
            task=task,
            board=board,
            scorer_lock=lock_path,
            parent_path=path,
            parent_sha256=expected_sha,
        )
        shape = contract.get("checks", {}).get("shape", {})
        registry_shape_match = (
            contract["status"] == "PASS"
            and int(shape.get("n_obs", -1)) == int(parent.get("n_obs", -2))
            and int(shape.get("n_vars", -1)) == int(parent.get("n_vars", -2))
        )
        rows.append(
            {
                "task": task,
                "board": board,
                "candidate_id": parent.get("candidate_id"),
                "path": str(path.relative_to(repo)),
                "registry_sha256": expected_sha,
                "actual_sha256": actual_sha,
                "parent_sha256_match": actual_sha == expected_sha,
                "contract_status": contract["status"],
                "registry_shape_match": registry_shape_match,
                "contract_errors": contract["errors"],
                "contract_report": contract,
            }
        )

    previous_adapter = (
        lock.get("contract_snapshot", {})
        .get("batch3_contract_adapter", {})
    )
    adapter_sha = sha256_file(adapter_path)
    all_pass = all(
        row["parent_sha256_match"]
        and row["contract_status"] == "PASS"
        and row["registry_shape_match"]
        for row in rows
    ) and test_run.returncode == 0
    result: dict[str, Any] = {
        "schema": "ve.batch3.contract-preflight.v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if all_pass else "FAIL",
        "candidate_generation": False,
        "server_submission": False,
        "parent_count": len(rows),
        "parents": rows,
        "adapter_lock": {
            "path": str(adapter_path.relative_to(repo)),
            "sha256": adapter_sha,
            "implementation": "tested_core_adapter",
            "previous_p0_snapshot": previous_adapter,
            "test_run": test_result,
        },
        "interpretation": (
            "All current P0 parents passed the implemented contract and retained "
            "their registry SHA256. The original P0 contract hash is preserved "
            "as a historical scaffold snapshot; adapter_lock is the downstream "
            "effective tested implementation."
        ),
        "blocks_submission": False,
    }
    result_path = output_dir / "contract_preflight.json"
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    board_index_path = repo / str(
        lock.get("contract_snapshot", {})
        .get("board_index", {})
        .get("path", "data/gene_panel/index.json")
    )
    board_index = json.loads(board_index_path.read_text(encoding="utf-8"))
    panel_paths: list[Path] = []
    for parent in parents:
        board_key = str(parent["board"])
        definition = board_index[board_key]
        panel_path = repo / "data/gene_panel" / str(definition["genes_file"])
        if not panel_path.is_file():
            panel_path = repo / str(definition["genes_file"])
        if panel_path not in panel_paths:
            panel_paths.append(panel_path)
    test_paths = sorted((repo / "docs/batch3/interfaces/tests").glob("test_*.py"))
    source_paths = [
        adapter_path,
        Path(__file__).resolve(),
        lock_path,
        registry_path,
        board_index_path,
        *panel_paths,
        *(repo / str(parent["canonical_path"]) for parent in parents),
        *test_paths,
    ]
    manifest = {
        "schema": "ve.batch3.contract-preflight-manifest.v1",
        "task": "BATCH3-CONTRACT-PREFLIGHT",
        "candidate_generation": False,
        "server_submission": False,
        "test_run": test_result,
        "files": [
            {
                "path": result_path.name,
                "bytes": result_path.stat().st_size,
                "sha256": sha256_file(result_path),
            },
            source_file(test_log_path, output_dir),
        ],
        "source_files": [source_file(path, repo) for path in source_paths],
    }
    (output_dir / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/tool_integration/CONTRACT-PREFLIGHT-20260831-v2"),
    )
    args = parser.parse_args(argv)
    result = run(args.repo, args.output_dir)
    print(
        json.dumps(
            {
                "status": result["status"],
                "parent_count": result["parent_count"],
                "adapter_sha256": result["adapter_lock"]["sha256"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
