#!/usr/bin/env bash
# Two targeted full-batch runs: penalty150 min700 cap22, penalty200 min600 cap22
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
COMPARE="penalty100_min700_cap21,penalty55_min700_cap21,penalty30_min700_cap21"
PIPELINE="pwsh -NoProfile -File ./Run-MetaMatchPipeline.ps1"
LOG="$ROOT/runs/experiments/targeted_pair_$(date -u +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG") 2>&1

run_exp() {
  local id="$1"
  shift
  echo ""
  echo "========== $id $(date -u -Iseconds) =========="
  $PIPELINE \
    -ArchiveAsExperiment "$id" \
    -CompareWith "$COMPARE" \
    "$@"
  echo "========== finished $id $(date -u -Iseconds) =========="
}

echo "Log: $LOG"
run_exp penalty150_min700_cap22 \
  -CrossAnchorFreqPenaltyWeight:150 -MinimumScore:700 -MaxPerOwner:2 -MaxPerOwnerPerSubdomain:2

run_exp penalty200_min600_cap22 \
  -CrossAnchorFreqPenaltyWeight:200 -MinimumScore:600 -MaxPerOwner:2 -MaxPerOwnerPerSubdomain:2

python3 tools/run_metamatch_grid.py --finalize-only
echo "=== Targeted pair complete $(date -u -Iseconds) ==="
