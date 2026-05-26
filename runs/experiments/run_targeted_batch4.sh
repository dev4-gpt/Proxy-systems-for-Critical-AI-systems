#!/usr/bin/env bash
# Batch 4: penalty 275/300 @ min700 + penalty250 @ min650 (cap 2/2 fixed)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
COMPARE="penalty250_min700_cap22,penalty200_min700_cap22"
PIPELINE="pwsh -NoProfile -File ./Run-MetaMatchPipeline.ps1"
LOG="$ROOT/runs/experiments/targeted_batch4_$(date -u +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG") 2>&1

run_exp() {
  local id="$1"
  shift
  echo ""
  echo "========== $id $(date -u -Iseconds) =========="
  $PIPELINE -ArchiveAsExperiment "$id" -CompareWith "$COMPARE" "$@"
  echo "========== finished $id $(date -u -Iseconds) =========="
}

echo "Log: $LOG"
echo "Champion baseline: penalty250_min700_cap22"

run_exp penalty275_min700_cap22 \
  -CrossAnchorFreqPenaltyWeight:275 -MinimumScore:700 -MaxPerOwner:2 -MaxPerOwnerPerSubdomain:2

run_exp penalty300_min700_cap22 \
  -CrossAnchorFreqPenaltyWeight:300 -MinimumScore:700 -MaxPerOwner:2 -MaxPerOwnerPerSubdomain:2

run_exp penalty250_min650_cap22 \
  -CrossAnchorFreqPenaltyWeight:250 -MinimumScore:650 -MaxPerOwner:2 -MaxPerOwnerPerSubdomain:2

python3 tools/run_metamatch_grid.py --finalize-only
python3 tools/pick_experiment_winner.py
python3 tools/apply_experiment_winner.py
echo "=== Batch 4 complete $(date -u -Iseconds) ==="
