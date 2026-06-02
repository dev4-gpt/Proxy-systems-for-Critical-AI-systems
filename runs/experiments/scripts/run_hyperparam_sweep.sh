#!/usr/bin/env bash
# Run all five hyperparameter sweep experiments sequentially (~45-60 min each).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
LOG="$ROOT/runs/experiments/sweep_$(date -u +%Y%m%d_%H%M%S).log"
COMPARE_BASELINE="penalty55_min700_cap21,penalty30_min700_cap21"
PIPELINE="pwsh -NoProfile -File ./Run-MetaMatchPipeline.ps1"

exec > >(tee -a "$LOG") 2>&1
echo "=== MetaMatch hyperparameter sweep started $(date -u -Iseconds) ==="
echo "Log: $LOG"

run_one() {
  local id="$1"
  local preset="$2"
  echo ""
  echo "========== $id (preset=$preset) $(date -u -Iseconds) =========="
  $PIPELINE \
    -ExperimentPreset "$preset" \
    -ResumePartial \
    -ArchiveAsExperiment "$id" \
    -CompareWith "$COMPARE_BASELINE"
  echo "========== finished $id $(date -u -Iseconds) =========="
}

run_one penalty75_min700_cap21 penalty75
run_one penalty100_min700_cap21 penalty100
run_one penalty55_min750_cap21 min750
run_one penalty55_min700_cap11 cap11
run_one penalty55_min700_cap21_nofallback nofallback

echo ""
echo "=== Final comparison (all experiments) ==="
python3 tools/compare_experiments.py --experiments \
  penalty30_min700_cap21 \
  penalty55_min700_cap21 \
  penalty75_min700_cap21 \
  penalty100_min700_cap21 \
  penalty55_min750_cap21 \
  penalty55_min700_cap11 \
  penalty55_min700_cap21_nofallback

python3 tools/pick_experiment_winner.py
python3 tools/update_experiment_log.py
python3 tools/apply_experiment_winner.py

echo "=== Sweep complete $(date -u -Iseconds) ==="
