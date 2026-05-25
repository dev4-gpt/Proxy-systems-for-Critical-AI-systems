#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SESSION="metamatch-targeted"
SCRIPT="$ROOT/runs/experiments/run_targeted_pair.sh"

if [[ "${1:-}" == "stop" ]]; then
  pkill -f "run_targeted_pair.sh" 2>/dev/null || true
  pkill -f "Run-MetaMatchPipeline.ps1" 2>/dev/null || true
  tmux kill-session -t "$SESSION" 2>/dev/null || true
  echo "Stopped."
  exit 0
fi

command -v tmux >/dev/null || { echo "brew install tmux"; exit 1; }
tmux kill-session -t "$SESSION" 2>/dev/null || true
tmux new-session -d -s "$SESSION" -c "$ROOT" "bash '$SCRIPT'; echo DONE; read"
echo "Started in tmux session: $SESSION"
echo "  tmux attach -t $SESSION"
echo "  tail -f runs/experiments/targeted_pair_*.log"
