#!/usr/bin/env bash
# Batch 3: penalty/min grid at cap 2/2 (caps held fixed — see CAP_ANALYSIS.md)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
COMPARE="penalty100_min700_cap21,penalty150_min700_cap22,penalty30_min700_cap21,penalty55_min700_cap21"
PIPELINE="pwsh -NoProfile -File ./Run-MetaMatchPipeline.ps1"
LOG="$ROOT/runs/experiments/targeted_batch3_$(date -u +%Y%m%d_%H%M%S).log"
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
echo "All runs use MaxPerOwner=2, MaxPerOwnerPerSubdomain=2 (cap22)"

run_exp penalty150_min600_cap22 \
  -CrossAnchorFreqPenaltyWeight:150 -MinimumScore:600 -MaxPerOwner:2 -MaxPerOwnerPerSubdomain:2

run_exp penalty200_min700_cap22 \
  -CrossAnchorFreqPenaltyWeight:200 -MinimumScore:700 -MaxPerOwner:2 -MaxPerOwnerPerSubdomain:2

run_exp penalty175_min700_cap22 \
  -CrossAnchorFreqPenaltyWeight:175 -MinimumScore:700 -MaxPerOwner:2 -MaxPerOwnerPerSubdomain:2

run_exp penalty175_min600_cap22 \
  -CrossAnchorFreqPenaltyWeight:175 -MinimumScore:600 -MaxPerOwner:2 -MaxPerOwnerPerSubdomain:2

python3 tools/run_metamatch_grid.py --finalize-only
echo "=== Batch 3 complete $(date -u -Iseconds) ==="
