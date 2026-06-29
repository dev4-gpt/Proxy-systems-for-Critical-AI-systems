# Canonical results — full validation arc (G1–G9)

Frozen headline artifacts for the **two-stage CAIS proxy-discovery** validation pass:

1. **Stage 1 — MetaMatch** (`queryv2` winner): 0 magnets, 20/0/0 — frozen in `runs/experiments/`.
2. **Stage 2 — REDUX 4**: four methods via `proxytool_redux/_extracted/redux4_core.py`.
3. **Validation outputs** symlinked here from `results_benchmark/` (single source of truth).

**Start here**, then [`results_benchmark/RESULTS_REVIEW.md`](../results_benchmark/RESULTS_REVIEW.md) (navigator). **Master document:** [`results_benchmark/WORK_REVIEW.md`](../results_benchmark/WORK_REVIEW.md).

## Files

| File | Proves | Headline |
|------|--------|----------|
| [`gates.json`](gates.json) | Decision gates G1–G9 | G1–G8 pass; G9 informational |
| **v2 labeled cohort (primary)** | | |
| [`labeled_scored_v2.json`](labeled_scored_v2.json) | 24-pair scored cohort | Per-pair REDUX scores |
| [`labeled_v2/labeled_strict_summary.csv`](labeled_v2/labeled_strict_summary.csv) | G1 ground-truth separation | Strict (`known_match` only) metadata F1 = **0.909** (22-pair metric cohort) |
| [`labeled_v2/labeled_summary.csv`](labeled_v2/labeled_summary.csv) | G2 lenient cohort | Lenient (`known_match` + `known_related`) metadata F1 = **0.941** — canonical name |
| [`labeled_v2/labeled_lenient_summary.csv`](labeled_v2/labeled_lenient_summary.csv) | G2 lenient (symmetric alias) | Identical to `labeled_summary.csv`; written by `labeled_strict_metrics.py` for strict/lenient pairing |
| [`labeled_v2/bootstrap_ci.csv`](labeled_v2/bootstrap_ci.csv) | Bootstrap uncertainty | Strict metadata F1 mean 0.704 (95% CI 0.50–0.875) |
| **v1 labeled cohort (frozen 10-pair demo)** | | |
| [`labeled_strict_summary.csv`](labeled_strict_summary.csv) | v1 strict separation | Strict metadata F1 = 1.0 |
| [`labeled_summary.csv`](labeled_summary.csv) | v1 lenient cohort | Lenient metadata F1 = 1.00 |
| [`labeled_scored.json`](labeled_scored.json) | v1 10-pair cohort | Historical separation demo |
| **Retrieval + bridges** | | |
| [`retrieval_winner.json`](retrieval_winner.json) | G5 MetaMatch winner | 0 magnets, 20/0/0 Good/OK/Weak |
| [`queryv2_redux_rollup.csv`](queryv2_redux_rollup.csv) | G6 retrieval → similarity | 20 anchors × top-5 metadata |
| [`anchorsv2_overlap.csv`](anchorsv2_overlap.csv) | G7 anchor-list stability | Mean top-5 Jaccard 0.96 |
| [`cross_method_auth_n30.json`](cross_method_auth_n30.json) | G4 cross-method agreement | Spearman ρ = +0.69 (auth n=30) |
| [`metadata_discrimination.csv`](metadata_discrimination.csv) | Method positioning | Similar 94.4% vs dissimilar 4.7% |
| **Downstream (G9)** | | |
| [`downstream_validation/SUMMARY.md`](downstream_validation/SUMMARY.md) | G9 proxy triage story | 24 anchors (20 queryv2 + 4 additions); triage + search + scenario coverage |
| [`downstream_validation/triage_metrics.csv`](downstream_validation/triage_metrics.csv) | Triage efficiency | Per-anchor pool reduction |
| [`manifest.json`](manifest.json) | Repro fingerprint | SHA256 of bundle + git commit |

## Five-minute review path

1. [`gates.json`](gates.json)
2. [`labeled_v2/labeled_strict_summary.csv`](labeled_v2/labeled_strict_summary.csv) + [`labeled_v2/labeled_summary.csv`](labeled_v2/labeled_summary.csv)
3. [`retrieval_winner.json`](retrieval_winner.json)
4. [`queryv2_redux_rollup.csv`](queryv2_redux_rollup.csv)
5. [`cross_method_auth_n30.json`](cross_method_auth_n30.json)
6. (optional) [`downstream_validation/SUMMARY.md`](downstream_validation/SUMMARY.md)

## Reproduce validation pass

```bash
cd "$(git rev-parse --show-toplevel)"
export GITHUB_TOKEN="$(gh auth token)"
export PYTHONPATH=.

python3 tools/write_run_manifest.py
python3 tools/verify_repo_access.py --benchmark configs/labeled_benchmark_pairs.json --skip-clone

# v1 labeled cohort (10 pairs)
PYTHONPATH=. python3 tools/score_labeled_benchmark_redux.py
PYTHONPATH=. python3 tools/run_labeled_benchmark.py \
  --benchmark results_benchmark/labeled_scored.json \
  --threshold 50 --output-dir results_benchmark/labeled
PYTHONPATH=. python3 tools/labeled_strict_metrics.py

# v2 labeled cohort (24 pairs) — primary paper metrics
PYTHONPATH=. python3 tools/score_labeled_benchmark_redux.py \
  --benchmark configs/labeled_benchmark_pairs_v2.json \
  --output results_benchmark/labeled_scored_v2.json
PYTHONPATH=. python3 tools/run_labeled_benchmark.py \
  --benchmark results_benchmark/labeled_scored_v2.json \
  --threshold 50 --output-dir results_benchmark/labeled_v2
PYTHONPATH=. python3 tools/labeled_strict_metrics.py \
  --benchmark results_benchmark/labeled_scored_v2.json \
  --threshold 50 --output-dir results_benchmark/labeled_v2
PYTHONPATH=. python3 tools/labeled_bootstrap_ci.py

# MetaMatch bridges
PYTHONPATH=. python3 tools/score_metamatch_proxies_redux.py \
  --top-k 5 --max-commits 50 --fit-global --metadata-only \
  --output-dir results_benchmark/queryv2_redux
PYTHONPATH=. python3 tools/anchorsv2_overlap.py
bash tools/run_anchorsv2_redux.sh all

# G9 downstream metrics
PYTHONPATH=. python3 tools/compute_downstream_validation.py
```

See [`REDUX_REPRO.md`](../REDUX_REPRO.md) for REDUX setup.

## Related

- [`results_benchmark/RESULTS_REVIEW.md`](../results_benchmark/RESULTS_REVIEW.md) — output navigator
- [`results_benchmark/REMOVABLE_HISTORY.md`](../results_benchmark/REMOVABLE_HISTORY.md) — cleanup inventory (Tier A/B executed; grid history in `archives/off_repo/metamatch_grid_history.tar.gz`)
