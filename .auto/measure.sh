#!/bin/bash
# Measure one T2 heart-extrap candidate with the frozen R1 proxy spec.
# Usage: ./.auto/measure.sh [candidate.h5ad]
# Default: .auto/candidate.h5ad if present, else locked baseline parent.
# Outputs: METRIC name=value lines (primary: de_score) + human diag to stderr.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
CAND="${1:-}"
if [[ -z "$CAND" ]]; then
  if [[ -f "$REPO/.auto/candidate.h5ad" ]]; then CAND="$REPO/.auto/candidate.h5ad";
  else CAND="$REPO/submissions/scored/baseline-001/T2_heart_val_extrap/submission.h5ad"; fi
fi
TARGET="$REPO/artifacts/g0/G1-T2-R1-EXTRAP-GATE-20260916-v1/intermediates/proxy_target_e95_cardiac.h5ad"
REF="$REPO/artifacts/g0/G1-T2-R1-EXTRAP-GATE-20260916-v1/intermediates/proxy_ref_e875_cardiac.h5ad"
# fast pre-checks (<1s): file exists + h5ad readable header
if [[ ! -f "$CAND" ]]; then echo "missing candidate: $CAND" >&2; exit 2; fi
if [[ ! -f "$TARGET" || ! -f "$REF" ]]; then echo "missing proxy files" >&2; exit 2; fi
TMP="$(mktemp /tmp/extrap_measure_XXXXXX.json)"
trap 'rm -f "$TMP"' EXIT
T0=$(date +%s)
if ! env LD_LIBRARY_PATH=/opt/anaconda3/lib PYTHONPATH="$REPO/third_party/veckit" \
  python "$REPO/third_party/veckit/score_h5ad.py" --task T2 --setting heart \
  --input "$CAND" --target "$TARGET" --reference "$REF" --seed 20260916 --out "$TMP" \
  > /tmp/extrap_measure_stdout.log 2> /tmp/extrap_measure_stderr.log; then
  echo "SCORER_CRASH candidate=$CAND" >&2
  tail -20 /tmp/extrap_measure_stderr.log >&2 || true
  exit 3
fi
T1=$(date +%s); WALL=$((T1 - T0))
python3 - "$TMP" "$WALL" <<'EOF'
import json, sys
tmp, wall = sys.argv[1], float(sys.argv[2])
m = json.load(open(tmp))["metrics"]
def g(k):
    v = m.get(k)
    try: return float(v)
    except (TypeError, ValueError): return None
prim = g("de_score")
secondaries = ["de_direction","neighborhood_mmd","morans_I_agreement","variogram","mmd_u",
  "energy_distance","pseudobulk_pearson","variance_ratio","occupancy_dice","d2_shape",
  "sliced_wasserstein","scale_log_ratio","count_log_ratio","library_size_ratio","pb_rel_err"]
print(f"METRIC de_score={prim}")
for k in secondaries:
    v = g(k)
    if v is not None: print(f"METRIC {k}={v}")
print(f"METRIC wall_s={wall}")
EOF
echo "scored $CAND wall=${WALL}s (see METRIC lines above)" >&2
