# Canonical results — full validation arc (G1–G8)

Frozen headline artifacts for the CAIS / MetaMatch / REDUX validation pass. Symlinks point at live files under `results_benchmark/` (single source of truth).

**Master document:** [`results_benchmark/WORK_REVIEW.md`](../results_benchmark/WORK_REVIEW.md)

## Files

| File | Proves | Headline |
|------|--------|----------|
| [`gates.json`](gates.json) | Decision gates G1–G8 | All pass; G8 = no retune |
| [`labeled_strict_summary.csv`](labeled_strict_summary.csv) | G1 ground-truth separation | Strict metadata/code/x-lang F1 = 1.0 |
| [`labeled_summary.csv`](labeled_summary.csv) | G2 lenient cohort | Lenient metadata F1 = 1.00 |
| [`labeled_scored.json`](labeled_scored.json) | 10-pair scored cohort | Per-pair REDUX scores |
| [`retrieval_winner.json`](retrieval_winner.json) | G5 MetaMatch winner | 0 magnets, 20/0/0 Good/OK/Weak |
| [`queryv2_redux_rollup.csv`](queryv2_redux_rollup.csv) | G6 retrieval → similarity | 20 anchors × top-5 metadata |
| [`anchorsv2_overlap.csv`](anchorsv2_overlap.csv) | G7 anchor-list stability | Mean top-5 Jaccard 0.96 |
| [`cross_method_auth_n30.json`](cross_method_auth_n30.json) | G4 cross-method agreement | Spearman ρ = +0.69 (auth n=30) |
| [`metadata_discrimination.csv`](metadata_discrimination.csv) | Method positioning | Similar 94.4% vs dissimilar 4.7% |
| [`manifest.json`](manifest.json) | Repro fingerprint | SHA256 of bundle + git commit |

## Five-minute review path

1. [`gates.json`](gates.json)
2. [`labeled_strict_summary.csv`](labeled_strict_summary.csv) + [`labeled_summary.csv`](labeled_summary.csv)
3. [`retrieval_winner.json`](retrieval_winner.json)
4. [`queryv2_redux_rollup.csv`](queryv2_redux_rollup.csv)
5. [`cross_method_auth_n30.json`](cross_method_auth_n30.json)

## Reproduce validation pass

```bash
cd "$(git rev-parse --show-toplevel)"
export GITHUB_TOKEN="$(gh auth token)"
export PYTHONPATH=.

python3 tools/write_run_manifest.py
python3 tools/verify_repo_access.py --benchmark configs/labeled_benchmark_pairs.json --skip-clone
PYTHONPATH=. python3 tools/score_labeled_benchmark_redux.py
PYTHONPATH=. python3 tools/run_labeled_benchmark.py \
  --benchmark results_benchmark/labeled_scored.json \
  --threshold 50 --output-dir results_benchmark/labeled
PYTHONPATH=. python3 tools/labeled_strict_metrics.py
PYTHONPATH=. python3 tools/score_metamatch_proxies_redux.py \
  --top-k 5 --max-commits 50 --fit-global --metadata-only \
  --output-dir results_benchmark/queryv2_redux
PYTHONPATH=. python3 tools/anchorsv2_overlap.py
bash tools/run_anchorsv2_redux.sh all
```

See [`REDUX_REPRO.md`](../REDUX_REPRO.md) for REDUX setup.

## Related

- [`results_benchmark/RESULTS_REVIEW.md`](../results_benchmark/RESULTS_REVIEW.md) — output navigator
- [`results_benchmark/REMOVABLE_HISTORY.md`](../results_benchmark/REMOVABLE_HISTORY.md) — cleanup inventory
