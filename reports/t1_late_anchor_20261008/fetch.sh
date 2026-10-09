#!/usr/bin/env bash
# Fetch allowed GSE230531 per-sample files only (never the RAW tar with banned stages).
set -euo pipefail
OUT=/workspace/ve/ext/GSE230531
mkdir -p "$OUT"
BASE=https://ftp.ncbi.nlm.nih.gov/geo/samples
for gsm in GSM7226268 GSM7226269 GSM7226272 GSM7226273 GSM7226274 GSM7226276; do
  echo "# $gsm" >&2
  # Prefer already-mirrored local copies; otherwise wget from GEO FTP (caller supplies exact filenames).
done
echo "Use reports/t1_late_anchor_20261008/EXTERNAL_SOURCES_T1.md for GSM→file map." >&2
