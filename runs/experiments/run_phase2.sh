#!/usr/bin/env bash
# Query-tuned run on original 20 anchors, then alternate 20 (penalty 300 / min 700 / cap 2/2)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
COMPARE="penalty300_min700_cap22,penalty250_min700_cap22"
PIPELINE="pwsh -NoProfile -File ./Run-MetaMatchPipeline.ps1"
LOG="$ROOT/runs/experiments/phase2_$(date -u +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG") 2>&1

run_exp() {
  local id="$1"
  local anchors_csv="$2"
  shift 2
  echo ""
  echo "========== $id $(date -u -Iseconds) anchors=$anchors_csv =========="
  $PIPELINE -ArchiveAsExperiment "$id" -CompareWith "$COMPARE" \
    -AnchorsCsv "$anchors_csv" \
    -CrossAnchorFreqPenaltyWeight:300 -MinimumScore:700 \
    -MaxPerOwner:2 -MaxPerOwnerPerSubdomain:2 \
    "$@"
  echo "========== finished $id $(date -u -Iseconds) =========="
}

echo "Log: $LOG"
echo "Query overrides: metamatch_anchor_query_overrides.json (auto-loaded by Get-AnchorMatches.ps1)"
echo "Fallback caps: MaxUnqualifiedInTopFive=1, MaxUnqualifiedInFinal=12 (script defaults)"

run_exp penalty300_min700_cap22_queryv2 "./recommended_anchors_top.csv"

run_exp penalty300_min700_cap22_anchorsv2 "./recommended_anchors_top_v2.csv"

python3 tools/run_metamatch_grid.py --finalize-only
python3 tools/pick_experiment_winner.py
python3 tools/apply_experiment_winner.py
echo "=== Phase 2 batch complete $(date -u -Iseconds) ==="
