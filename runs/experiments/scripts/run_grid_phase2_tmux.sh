#!/usr/bin/env bash
# Start phase-2 grid in a detached tmux session (reattach anytime).
# Usage:
#   bash runs/experiments/scripts/run_grid_phase2_tmux.sh          # start (stops old session first)
#   bash runs/experiments/scripts/run_grid_phase2_tmux.sh stop     # kill grid + tmux session
#   tmux attach -t metamatch-grid                        # watch live output
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SESSION="metamatch-grid"
LOG="$ROOT/runs/experiments/grid_phase2_tmux.log"

stop_all() {
  echo "Stopping MetaMatch grid / pipeline processes..."
  pkill -f "tools/run_metamatch_grid.py" 2>/dev/null || true
  pkill -f "Run-MetaMatchPipeline.ps1" 2>/dev/null || true
  sleep 2
  if tmux has-session -t "$SESSION" 2>/dev/null; then
    tmux kill-session -t "$SESSION"
    echo "Killed tmux session: $SESSION"
  fi
}

if [[ "${1:-}" == "stop" ]]; then
  stop_all
  exit 0
fi

if [[ "${1:-}" == "stop-after-current" ]]; then
  touch "$ROOT/runs/experiments/GRID_STOP_AFTER_CURRENT"
  echo "Stop after current experiment: $ROOT/runs/experiments/GRID_STOP_AFTER_CURRENT"
  echo "Grid process must be running; it will exit before the next experiment."
  exit 0
fi

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux not found. Install: brew install tmux"
  exit 1
fi

stop_all

echo "Starting grid in tmux session: $SESSION"
echo "Log file: $LOG"
echo ""
echo "  Watch live:  tmux attach -t $SESSION"
echo "  Detach:      Ctrl+B then D"
echo "  Or tail log: tail -f $LOG"
echo ""

tmux new-session -d -s "$SESSION" -c "$ROOT" \
  "python3 tools/run_metamatch_grid.py 2>&1 | tee -a '$LOG'; echo ''; echo '=== GRID FINISHED $(date -u -Iseconds) ==='; echo 'Press Enter to close pane...'; read"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "Grid is running in tmux."
else
  echo "Failed to create tmux session."
  exit 1
fi
