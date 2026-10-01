#!/bin/bash
# Measure one T1 REPORT candidate with the frozen report-proxy spec.
# Usage: ./.auto/measure_t1.sh [candidate.h5ad]
# Default: .auto/t1_candidate.h5ad if present, else v0035 report prediction (baseline).
# Frozen: task=T1, seed=20260921, target=pseudo_target_e95_outer, reference=reference_e85_train.
# Outputs: METRIC name=value lines (primary: de_score, HIGHER better) + diag to stderr.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
CAND="${1:-}"
if [[ -z "$CAND" ]]; then
  if [[ -f "$REPO/.auto/t1_candidate.h5ad" ]]; then CAND="$REPO/.auto/t1_candidate.h5ad";
  else CAND="$REPO/artifacts/t1_three/T1-THREE-20260929-v1/r2joint/report_prediction.h5ad"; fi
fi
TARGET="$REPO/artifacts/g0/T1-NEXT-R1-QUANT-20260921-v1/intermediates/pseudo_target_e95_outer.h5ad"
REF="$REPO/artifacts/g0/T1-NEXT-R1-QUANT-20260921-v1/intermediates/reference_e85_train.h5ad"
if [[ ! -f "$CAND" ]]; then echo "missing candidate: $CAND" >&2; exit 2; fi
if [[ ! -f "$TARGET" || ! -f "$REF" ]]; then echo "missing proxy files" >&2; exit 2; fi
TMP="$(mktemp /tmp/t1_measure_XXXXXX.json)"
trap 'rm -f "$TMP"' EXIT
T0=$(date +%s)
if ! env LD_LIBRARY_PATH=/opt/anaconda3/lib PYTHONPATH="$REPO/third_party/veckit" \
  python "$REPO/third_party/veckit/score_h5ad.py" --task T1 \
  --input "$CAND" --target "$TARGET" --reference "$REF" --seed 20260921 --out "$TMP" \
  > /tmp/t1_measure_stdout.log 2> /tmp/t1_measure_stderr.log; then
  echo "SCORER_CRASH candidate=$CAND" >&2
  tail -20 /tmp/t1_measure_stderr.log >&2 || true
  exit 3
fi
T1=$(date +%s); WALL=$((T1 - T0))
python3 - "$TMP" "$WALL" <<'EOF'
import json, sys
tmp, wall = sys.argv[1], float(sys.argv[2])
d = json.load(open(tmp))
m = d["metrics"]
meta = d.get("meta", {})
def g(k):
    v = m.get(k)
    try: return float(v)
    except (TypeError, ValueError): return None
prim = g("de_score")
for k in ["de_score","de_direction","energy_distance","mmd_u","variogram",
          "pb_rel_err","library_size_ratio","variance_ratio","composition_JSD",
          "pseudobulk_pearson"]:
    v = g(k)
    if v is not None: print(f"METRIC {k}={v}")
print(f"METRIC wall_s={wall}")
print(f"METRIC pred_cells={meta.get('prediction_cells')} target_cells={meta.get('truth_cells')} genes={meta.get('genes')}")
EOF
echo "scored $CAND wall=${WALL}s (primary de_score HIGHER better; baseline v0035 report = 0.5926)" >&2
