"""Shared CLI/config handling for a read-only evidence audit."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent


def parse_args(task: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=f'Recompute {task.upper()} calibration audit from small frozen evidence; no models or scorers run.')
    parser.add_argument('--config', type=Path, default=PACKAGE_ROOT / 'config.json')
    parser.add_argument('--evidence-dir', type=Path, help='Override bundled evidence directory')
    parser.add_argument('--output-dir', type=Path, help='Write generated files here, without modifying frozen reports')
    parser.add_argument('--bootstrap-resamples', type=int)
    parser.add_argument('--bootstrap-seed', type=int)
    parser.add_argument('--evaluation-dir', type=Path, help='T2 only: override all 42 frozen score JSON receipts; does not rerun scoring')
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    base = args.config.resolve().parent
    args.evidence_dir = (args.evidence_dir or base / config['evidence_dir']).resolve()
    args.output_dir = (args.output_dir or base / config['output_dir'] / task).resolve()
    args.bootstrap_resamples = args.bootstrap_resamples if args.bootstrap_resamples is not None else config.get('bootstrap_resamples', 10000)
    args.bootstrap_seed = args.bootstrap_seed if args.bootstrap_seed is not None else config.get('bootstrap_seed', 20261008)
    if args.bootstrap_resamples < 1:
        parser.error('--bootstrap-resamples must be positive')
    if not args.evidence_dir.is_dir():
        parser.error(f'Evidence directory not found: {args.evidence_dir}')
    if args.output_dir == args.evidence_dir or args.evidence_dir in args.output_dir.parents:
        parser.error('Output must not overwrite evidence')
    return args


def logical_source(path: Path, evidence_dir: Path) -> str:
    """Stable evidence-relative IDs, independent of installation path."""
    path = Path(path).resolve()
    try:
        return 'evidence/' + path.relative_to(evidence_dir.resolve()).as_posix()
    except ValueError:
        # A CLI-specified external receipt directory is represented by filename;
        # its hashes, not the runtime machine path, identify the input bytes.
        return 'external_receipts/' + path.name


def excluded_source_receipt(path: Path, evidence_dir: Path):
    logical = logical_source(path, evidence_dir)
    receipt_path = evidence_dir.parent / 'provenance/EXCLUDED_SOURCE_RECEIPTS.json'
    if not receipt_path.is_file():
        return None
    for item in json.loads(receipt_path.read_text())['sources']:
        if item['omitted_package_path'] == logical:
            return item
    return None


def source_reference(path: Path, evidence_dir: Path) -> str:
    receipt = excluded_source_receipt(path, evidence_dir)
    return receipt['source_url'] if receipt else logical_source(path, evidence_dir)


def source_sha256(path: Path, evidence_dir: Path) -> str:
    """Hash bundled bytes, or return an explicitly identified original receipt.

    A receipt is provenance only: it does not assert absent text was reread or
    verified. Missing inputs without an allowlisted receipt still fail.
    """
    receipt = excluded_source_receipt(path, evidence_dir)
    if receipt:
        return receipt['original_sha256']
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
