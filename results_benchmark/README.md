# results_benchmark layout

Organized benchmark outputs for the **two-stage CAIS proxy-discovery** validation pass:

1. **Stage 1 — MetaMatch retrieval** (`queryv2` winner, frozen in `runs/experiments/`) — 0 magnets, 20/0/0 Good/OK/Weak.
2. **Stage 2 — REDUX 4** — four methods via `proxytool_redux/_extracted/redux4_core.py`; labeled eval + proxy bridges live here.

**Canonical bundle:** [`../CANONICAL_RESULTS/`](../CANONICAL_RESULTS/) — frozen headline artifacts (G1–G9). **Start here**, then [`RESULTS_REVIEW.md`](RESULTS_REVIEW.md) (navigator).

**Master doc:** [`WORK_REVIEW.md`](WORK_REVIEW.md) — phases A–I, tags, repro. **Deep audit:** [`MASTER_EVALUATION.md`](MASTER_EVALUATION.md). **Repo inventory:** [`REPO_AUDIT.md`](REPO_AUDIT.md).

## How to read this folder

Use [`RESULTS_REVIEW.md`](RESULTS_REVIEW.md) for the five-minute review path (file order + headline numbers). Do not duplicate that flow here — this table is for **doc roles** only.

| Document | Role |
|----------|------|
| [`RESULTS_REVIEW.md`](RESULTS_REVIEW.md) | **Navigator** — which output to open, in order |
| [`WORK_REVIEW.md`](WORK_REVIEW.md) | **Master** — what ran, phases A–I, repro commands |
| [`PAPER_PACKAGE.md`](PAPER_PACKAGE.md) | Gate checklist G1–G8 (+ G9 informational) |
| [`VALIDATION_MEMO.md`](VALIDATION_MEMO.md) | Stats prose, reviewer concerns |
| [`REPO_AUDIT.md`](REPO_AUDIT.md) | What matters vs archived junk |
| [`MASTER_EVALUATION.md`](MASTER_EVALUATION.md) | Deep independent audit |
| [`CAIS_REVIEW_REFERENCE.md`](CAIS_REVIEW_REFERENCE.md) | Pre-consolidation baseline + post-consolidation deltas |
| [`REMOVABLE_HISTORY.md`](REMOVABLE_HISTORY.md) | Cleanup inventory (Tier A/B done) |
| [`README.md`](README.md) | This directory map |
| Spot checks + case study | [`queryv2_spot_check.md`](queryv2_spot_check.md), [`anchorsv2_spot_check.md`](anchorsv2_spot_check.md), [`testing_case_study_airflow.md`](testing_case_study_airflow.md) |

## MetaMatch phase-2 (queryv2 + anchorsv2)

| Path | Role |
|------|------|
| `queryv2_spot_check.md` | Read-only retrieval notes for winner archive |
| `queryv2_redux/` | REDUX anchor→top-5 proxy scores (20 anchors); `rollup_summary.csv`, `run_manifest.json` |
| `anchorsv2_spot_check.md` | Anchor-list sensitivity run (24 anchors, 4 additions) |
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

## Narrative docs

See **How to read this folder** above for doc roles. Full review path: [`RESULTS_REVIEW.md`](RESULTS_REVIEW.md).
