# results_benchmark layout

Organized benchmark outputs for the CAIS / MetaMatch paper package.

**Canonical bundle:** [`../CANONICAL_RESULTS/`](../CANONICAL_RESULTS/) — frozen headline artifacts (G1–G8).

**Start here:** [`WORK_REVIEW.md`](WORK_REVIEW.md) — master validation document (phases, tags, repro, cross-verification). **Where are the results?** → [`RESULTS_REVIEW.md`](RESULTS_REVIEW.md).

## MetaMatch phase-2 (queryv2 + anchorsv2)

| Path | Role |
|------|------|
| `queryv2_spot_check.md` | Read-only retrieval notes for winner archive |
| `queryv2_redux/` | REDUX anchor→top-5 proxy scores (20 anchors); `rollup_summary.csv`, `run_manifest.json` |
| `anchorsv2_spot_check.md` | Anchor-list sensitivity run (24 anchors, 4 swaps) |
| `anchorsv2_redux/` | Same REDUX bridge for `penalty300_min700_cap22_anchorsv2` |
| `anchorsv2_overlap.csv` → `archives/metamatch_sensitivity/` | Top-5 Jaccard vs queryv2 on shared slugs |

Reproduce REDUX:

```bash
# queryv2 (winner)
PYTHONPATH=. python3 tools/score_metamatch_proxies_redux.py --top-k 5 --max-commits 50 --fit-global --metadata-only --output-dir results_benchmark/queryv2_redux

# anchorsv2 (sensitivity)
bash tools/run_anchorsv2_redux.sh all   # pilot then full
```

## Labeled cohort (ground truth)

| Path | Role |
|------|------|
| `labeled_scored.json` | 10-pair REDUX scores (v1 frozen) |
| `labeled/` | Threshold 50/45/55 summaries + claim checks (v1) |
| `labeled_scored_v2.json` | 24-pair expanded cohort |
| `labeled_v2/` | v2 strict/lenient metrics + bootstrap CIs |
| `configs/labeled_benchmark_pairs_v2.json` | v2 seed manifest |
| `run_manifest.json` | Repro SHA256 + GitHub auth snapshot |

## Downstream validation

| Path | Role |
|------|------|
| `downstream_validation/SUMMARY.md` | Triage, search effort, scenario coverage |
| `downstream_validation/triage_metrics.csv` | Proxy triage efficiency |
| `downstream_validation/search_effort.csv` | Candidate search effort |
| `downstream_validation/scenario_coverage.csv` | Testing-relevance dimensions |

## Historical / auxiliary CSVs (`archives/`)

Loose root-level sweep and ablation CSVs live under `archives/` with symlinks at former paths where tools/docs still reference them. Grid history (`redux4_sweep/`, `custom_30_pairs/`, penalty-grid experiment folders) was tarball'd to `archives/off_repo/metamatch_grid_history.tar.gz` (gitignored); see `REMOVABLE_HISTORY.md`.

| Subfolder | Contents |
|-----------|----------|
| `known_mirror/` | Mirror benchmark candidate rows and summaries |
| `continuous_scores/` | Mirror vs non-mirror continuous score tables |
| `metadata_diagnostics/` | Discrimination / permissiveness diagnostics |
| `legacy_tables/` | table1–3, three_test_argument_table |
| `metamatch_sensitivity/` | anchorsv2_overlap.csv |

## Narrative docs (`[Analysis]`)

- `REMOVABLE_HISTORY.md` — cleanup inventory (Tier A–D)
- `RESULTS_REVIEW.md` — results navigator (paths + headline numbers)
- `WORK_REVIEW.md` — **master** phase table, tag legend, repro commands
- `VALIDATION_MEMO.md` — reviewer response backbone
- `PAPER_PACKAGE.md` — gate checklist G1–G8
- `testing_case_study_airflow.md` — queryv2 case study
