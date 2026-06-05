# results_benchmark layout

Organized benchmark outputs for the CAIS / MetaMatch paper package.

**Start here:** [`WORK_REVIEW.md`](WORK_REVIEW.md) — master validation document (phases, tags, repro, cross-verification). UTF-8 cleanup log: [`ENCODING_FIXES.md`](ENCODING_FIXES.md).

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
| `labeled_scored.json` | 10-pair REDUX scores |
| `labeled/` | Threshold 50/45/55 summaries + claim checks |
| `run_manifest.json` | Repro SHA256 + GitHub auth snapshot |

## Historical / auxiliary CSVs (`archives/`)

Loose root-level sweep and ablation CSVs were moved under `archives/` with symlinks at former paths where tools/docs still reference them:

| Subfolder | Contents |
|-----------|----------|
| `redux4_sweep/` | Coverage/temperature grid sweep outputs |
| `known_mirror/` | Mirror benchmark candidate rows and summaries |
| `custom_30_pairs/` | 30-pair scoring variants |
| `continuous_scores/` | Mirror vs non-mirror continuous score tables |
| `metadata_diagnostics/` | Discrimination / permissiveness diagnostics |
| `legacy_tables/` | table1–3, three_test_argument_table |
| `metamatch_sensitivity/` | anchorsv2_overlap.csv |

## Narrative docs (`[Analysis]`)

- `WORK_REVIEW.md` — **master** phase table, tag legend, repro commands
- `VALIDATION_MEMO.md` — reviewer response backbone
- `PAPER_PACKAGE.md` — gate checklist G1–G8
- `testing_case_study_airflow.md` — queryv2 case study
- `ENCODING_FIXES.md` — display-text UTF-8 fixes (2026-06-05)
