#!/usr/bin/env bash
# Full source-only build, independent checks, and all matched released-stage controls.
set -euo pipefail
HERE=$(cd -- "$(dirname -- "$0")" && pwd)
DATA=${1:?Pass official released-stage data directory}
OUT=${2:?Pass a fresh output directory}
PY=${PYTHON:-/workspace/shared/t2venv/bin/python}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 LOKY_MAX_CPU_COUNT=1
mkdir -p "$OUT/reports"
"$PY" "$HERE/test_operator.py"
"$PY" "$HERE/build.py" --data "$DATA" --out "$OUT/final" --split final
"$PY" "$HERE/verify.py" --data "$DATA" --artifacts "$OUT/final"
"$PY" "$HERE/build.py" --data "$DATA" --out "$OUT/dev" --split dev
"$PY" "$HERE/verify.py" --data "$DATA" --artifacts "$OUT/dev"
for seed in 0 1 2; do
  "$PY" "$HERE/evaluate.py" --data "$DATA" --artifacts "$OUT/dev" --out "$OUT/reports/eval_seed${seed}.json" --seed "$seed"
done
