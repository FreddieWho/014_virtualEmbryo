#!/usr/bin/env python3
"""Package an atom's immutable candidate submissions for manual upload.

The archive renames files only inside the ZIP. Canonical submission files and
their paths are never changed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VERSION_RE = re.compile(r"^(v\d{4})(?:_|$)")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _version_from_submission(path: Path) -> str:
    match = VERSION_RE.match(path.parent.name)
    if not match:
        raise ValueError(f"cannot derive vNNNN version from submission directory: {path}")
    return match.group(1)


def _board_label(task: str, board: str) -> str:
    prefix = f"{task}_"
    return board[len(prefix) :] if board.startswith(prefix) else board


def _relative(project_root: Path, path: Path) -> str:
    return path.resolve().relative_to(project_root.resolve()).as_posix()


def package_manual_upload(
    *,
    atom_root: Path,
    output_dir: Path,
    package_date: str,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    project_root = Path(project_root).resolve()
    atom_root = Path(atom_root).resolve()
    output_dir = Path(output_dir).resolve()
    freeze_path = atom_root / "FINAL_SET_MANIFEST.json"
    if not freeze_path.exists():
        raise FileNotFoundError(freeze_path)
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    items = freeze.get("candidates")
    if not isinstance(items, list) or not items:
        raise ValueError("final set has no candidates")

    atom_id = str(freeze.get("atom_id") or atom_root.name)
    prepared: list[dict[str, object]] = []
    candidate_ids: set[str] = set()
    member_names: set[str] = set()
    tasks: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("final set contains a non-object candidate")
        lane = str(item.get("lane_id", ""))
        board = str(item.get("board", ""))
        manifest_path = atom_root / "final" / lane / board / "MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        candidate_id = str(manifest.get("candidate_id", ""))
        task = str(manifest.get("task", ""))
        submission_rel = manifest.get("submission_file")
        if not candidate_id or candidate_id in candidate_ids:
            raise ValueError(f"duplicate or missing candidate_id: {candidate_id!r}")
        if manifest.get("lane_id") != lane or manifest.get("board") != board:
            raise ValueError(f"{manifest_path}: freeze/manifest lane or board mismatch")
        if not task or not isinstance(submission_rel, str):
            raise ValueError(f"{manifest_path}: missing task or submission_file")
        submission = (project_root / submission_rel).resolve()
        if project_root not in submission.parents or not submission.exists():
            raise FileNotFoundError(submission)
        actual_sha = _sha256(submission)
        if manifest.get("sha256") != actual_sha or item.get("sha256") != actual_sha:
            raise ValueError(f"{manifest_path}: submission SHA256 mismatch")
        version = _version_from_submission(submission)
        filename = f"{atom_id}__{task}__{_board_label(task, board)}__{lane}__{version}.h5ad"
        if filename in member_names:
            raise ValueError(f"duplicate archive member name: {filename}")
        candidate_ids.add(candidate_id)
        member_names.add(filename)
        tasks.add(task)
        prepared.append(
            {
                "package_filename": filename,
                "candidate_id": candidate_id,
                "task": task,
                "board": board,
                "lane": lane,
                "version": version,
                "canonical_submission": _relative(project_root, submission),
                "sha256": actual_sha,
                "n_cells": manifest.get("n_obs"),
                "n_genes": manifest.get("n_vars"),
                "server_status": manifest.get("score_status", "unknown"),
                "source": submission,
            }
        )
    if len(tasks) != 1:
        raise ValueError(f"one package must contain one task, got {sorted(tasks)}")

    task = next(iter(tasks))
    package_stem = f"{atom_id}__{task}__manual_upload__{package_date}"
    archive_path = output_dir / f"{package_stem}.zip"
    if archive_path.exists():
        raise FileExistsError(f"refusing to overwrite {archive_path}")
    archive_root = package_stem

    manifest_buffer = io.StringIO(newline="")
    fieldnames = [
        "package_filename",
        "candidate_id",
        "task",
        "board",
        "lane",
        "version",
        "canonical_submission",
        "sha256",
        "n_cells",
        "n_genes",
        "server_status",
    ]
    writer = csv.DictWriter(manifest_buffer, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for item in prepared:
        writer.writerow({key: item[key] for key in fieldnames})

    readme = (
        f"{atom_id} / {task} manual upload package\n"
        "========================================\n"
        "Upload each .h5ad separately. The filenames identify batch, task, board, lane and version.\n"
        "The H5AD bytes are copied from the canonical submission paths; canonical files were not renamed.\n"
        "Use UPLOAD_MANIFEST.tsv to map each filename to its candidate ID and SHA256.\n"
        "Server score and submission ID are intentionally not included; record them after upload.\n"
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    temporary = archive_path.with_name(f".{archive_path.name}.{os.getpid()}.tmp")
    try:
        with ZipFile(temporary, "w", compression=ZIP_DEFLATED, compresslevel=6) as archive:
            archive.writestr(f"{archive_root}/UPLOAD_MANIFEST.tsv", manifest_buffer.getvalue())
            archive.writestr(f"{archive_root}/UPLOAD_README.txt", readme)
            for item in prepared:
                archive.write(item["source"], arcname=f"{archive_root}/{item['package_filename']}")
        os.replace(temporary, archive_path)
    finally:
        if temporary.exists():
            temporary.unlink()

    return {
        "package": str(archive_path),
        "package_name": archive_path.name,
        "task": task,
        "atom_id": atom_id,
        "member_count": len(prepared),
        "members": [
            {key: item[key] for key in fieldnames}
            for item in prepared
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--atom-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "deliveries")
    parser.add_argument("--date", dest="package_date", required=True, help="YYYYMMDD")
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args()
    if not re.fullmatch(r"\d{8}", args.package_date):
        raise SystemExit("--date must be YYYYMMDD")
    result = package_manual_upload(
        atom_root=args.atom_root,
        output_dir=args.output_dir,
        package_date=args.package_date,
        project_root=args.project_root,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
