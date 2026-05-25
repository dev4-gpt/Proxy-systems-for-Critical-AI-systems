#!/usr/bin/env bash
# Phase-2 grid: penalty 110-200 x min 700/750/800 x caps 11/12/21/22 (60 runs).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
LOG="$ROOT/runs/experiments/grid_phase2_$(date -u +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG") 2>&1
echo "=== Grid phase 2 started $(date -u -Iseconds) ==="
echo "Log: $LOG"
python3 tools/run_metamatch_grid.py
echo "=== Grid phase 2 finished $(date -u -Iseconds) ==="
