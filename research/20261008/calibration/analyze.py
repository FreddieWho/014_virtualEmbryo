#!/usr/bin/env python3
"""Portable entry point: regenerate frozen T2/T3 audit calculations."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'config.json')
    parser.add_argument('--evidence-dir', type=Path)
    parser.add_argument('--output-dir', type=Path, help='Output parent, containing t2/ and t3/')
    parser.add_argument('--task', choices=['all', 't2', 't3'], default='all')
    parser.add_argument('--bootstrap-resamples', type=int)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    out = (args.output_dir or args.config.resolve().parent / config['output_dir']).resolve()
    for task in (['t2', 't3'] if args.task == 'all' else [args.task]):
        command = [sys.executable, str(ROOT / task / 'analyze.py'), '--config', str(args.config.resolve()), '--output-dir', str(out / task)]
        if args.evidence_dir is not None:
            command += ['--evidence-dir', str(args.evidence_dir.resolve())]
        if args.bootstrap_resamples is not None:
            command += ['--bootstrap-resamples', str(args.bootstrap_resamples)]
        subprocess.run(command, check=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
