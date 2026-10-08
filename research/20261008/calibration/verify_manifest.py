#!/usr/bin/env python3
"""Check every published file against the final SHA256 inventory (offline)."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
manifest = ROOT / 'provenance/FINAL_MANIFEST_SHA256.json'
records = json.loads(manifest.read_text())['files']
for record in records:
    path = ROOT / record['path']
    if not path.is_file():
        raise SystemExit(f'Missing: {record["path"]}')
    if path.stat().st_size != record['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
        raise SystemExit(f'Hash mismatch: {record["path"]}')
print(f'PASS: {len(records)} published files verified')
