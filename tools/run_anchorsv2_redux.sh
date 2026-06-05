#!/usr/bin/env bash
# Score anchor→proxy pairs from penalty300_min700_cap22_anchorsv2 (REDUX).
# Mirrors queryv2_redux workflow in tools/score_metamatch_proxies_redux.py.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=.

ARCHIVE="runs/experiments/penalty300_min700_cap22_anchorsv2"
OUT="results_benchmark/anchorsv2_redux"

run_pilot() {
  python3 tools/score_metamatch_proxies_redux.py \
    --archive "$ARCHIVE" \
    --output-dir "$OUT" \
    --pilot-only \
    --top-k 5 \
    --max-commits 60 \
    --fit-global
}

run_full() {
  python3 tools/score_metamatch_proxies_redux.py \
    --archive "$ARCHIVE" \
    --output-dir "$OUT" \
    --top-k 5 \
    --max-commits 50 \
    --fit-global \
    --metadata-only \
    --skip-existing
}

case "${1:-full}" in
  pilot) run_pilot ;;
  full)  run_full ;;
  all)   run_pilot; run_full ;;
  *)     echo "Usage: $0 [pilot|full|all]" >&2; exit 1 ;;
esac

python3 tools/write_run_manifest.py --output results_benchmark/run_manifest.json
