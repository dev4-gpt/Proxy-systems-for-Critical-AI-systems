# Results review — where to look

A navigator for **output files and headline numbers** after the validation pass. This is not a second master document — for commands, tags, and repro see [WORK_REVIEW.md](WORK_REVIEW.md).

**Integration in one line:** frozen **queryv2** MetaMatch retrieval (our Phase 2 winner) + **labeled ground-truth** eval + **REDUX** proxy bridges, documented under `results_benchmark/`.

---

## Five-minute path (open in this order)

| #   | Open                                                                                                                                             | You get                                                                    |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------- |
| 1   | [PAPER_PACKAGE.md](PAPER_PACKAGE.md)                                                                                                             | Pass/fail gates G1–G8                                                      |
| 2   | [labeled/labeled_strict_summary.csv](labeled/labeled_strict_summary.csv) + [labeled/labeled_summary.csv](labeled/labeled_summary.csv)            | Ground-truth metrics (strict + lenient)                                    |
| 3   | [../runs/experiments/documentation/WINNER.md](../runs/experiments/documentation/WINNER.md)                                                       | MetaMatch retrieval winner (0 magnets, 20/0/0)                             |
| 4   | [queryv2_redux/rollup_summary.csv](queryv2_redux/rollup_summary.csv) + [anchorsv2_redux/rollup_summary.csv](anchorsv2_redux/rollup_summary.csv)  | REDUX similarity on retrieved proxies                                      |
| 5   | [projected_pairs/full_summary_authenticated_n30.json](projected_pairs/full_summary_authenticated_n30.json)                                       | Canonical cross-method Spearman (authenticated, n=30: ρ ≈ +0.69, go=true) |

For methodology and statistics in prose: [VALIDATION_MEMO.md](VALIDATION_MEMO.md). For which repo paths matter vs historical sprawl: [REPO_AUDIT.md](REPO_AUDIT.md).

---

## By research question

### 1. Ground truth — do methods separate real mirrors from non-matches?

| What                                    | Path                                                                                                                |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Cohort definition (10 pairs)            | [../configs/labeled_benchmark_pairs.json](../configs/labeled_benchmark_pairs.json)                                  |
| Per-pair REDUX scores                   | [labeled_scored.json](labeled_scored.json)                                                                          |
| **Strict** metrics (`known_match` only) | [labeled/labeled_strict_summary.csv](labeled/labeled_strict_summary.csv)                                            |
| **Lenient** metrics (+ related pairs)   | [labeled/labeled_summary.csv](labeled/labeled_summary.csv)                                                          |
| Per-pair table                          | [labeled/labeled_pair_table.csv](labeled/labeled_pair_table.csv)                                                    |
| Threshold 45 / 55 sensitivity           | [labeled/threshold45/](labeled/threshold45/), [labeled/threshold55/](labeled/threshold55/)                          |
| Repo access                             | [repo_access_validation.csv](repo_access_validation.csv)                                                            |

**Headlines @ threshold 50:** strict F1 = **1.0** (metadata, code_centric, cross_language); lenient metadata F1 = **1.00** (`target_uncertain` excluded from P/R/F1 per cohort rule); dynamic weaker (**0.67** lenient). Details: [WORK_REVIEW.md § Key results summary](WORK_REVIEW.md#key-results-summary).

---

### 2. Retrieval — did MetaMatch queryv2 win?

| What                      | Path                                                                                          |
| ------------------------- | --------------------------------------------------------------------------------------------- |
| Scorecard                 | [../runs/experiments/documentation/WINNER.md](../runs/experiments/documentation/WINNER.md)   |
| Frozen per-anchor matches | `runs/experiments/penalty300_min700_cap22_queryv2/manual-ml-py/<anchor>/30_Matches.csv`       |
| Spot-check notes          | [queryv2_spot_check.md](queryv2_spot_check.md)                                                |
| Winner hyperparams        | [../metamatch_hyperparams.json](../metamatch_hyperparams.json)                                |

**Headline:** **0** top-5 magnets, **20 / 0 / 0** Good / OK / Weak.

---

### 3. Similarity on queryv2 proxies — retrieval → REDUX bridge

| What                       | Path                                                                 |
| -------------------------- | -------------------------------------------------------------------- |
| **Summary (20 anchors)**   | [queryv2_redux/rollup_summary.csv](queryv2_redux/rollup_summary.csv) |
| Per-anchor CSVs (20 files) | [queryv2_redux/](queryv2_redux/)                                     |
| Run metadata               | [queryv2_redux/run_manifest.json](queryv2_redux/run_manifest.json)   |

**Headline:** **100** metadata pair scores (20 anchors × top-5). Thin-anchor means in rollup (e.g. jina 96.35%, ray 92.31%).

---

### 4. Anchor-list robustness — anchorsv2 vs queryv2

| What                             | Path                                                                                        |
| -------------------------------- | ------------------------------------------------------------------------------------------- |
| Top-5 overlap table              | [anchorsv2_overlap.csv](anchorsv2_overlap.csv) (→ `archives/metamatch_sensitivity/`)        |
| Spot-check (24 anchors, 4 swaps) | [anchorsv2_spot_check.md](anchorsv2_spot_check.md)                                          |
| **REDUX summary (24 anchors)**   | [anchorsv2_redux/rollup_summary.csv](anchorsv2_redux/rollup_summary.csv)                    |
| Per-anchor CSVs                  | [anchorsv2_redux/](anchorsv2_redux/)                                                        |
| Frozen retrieval archive         | `runs/experiments/penalty300_min700_cap22_anchorsv2/manual-ml-py/`                          |

**Headlines:** mean top-5 Jaccard **0.96** on 20 shared slugs (**17/20** at 1.0); **116** REDUX pair scores. The REDUX rollup is a **full independent 24-anchor rerun** (all 24 anchors freshly scored; replaces the earlier bootstrap; overall metadata mean 92.82 → 94.04) — see [PAPER_PACKAGE.md](PAPER_PACKAGE.md).

---

### 5. Method positioning — discrimination and cross-method agreement

| What                                                       | Path                                                                                                            |
| ---------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Similar vs dissimilar metadata                             | [metadata_discrimination_canonical.csv](metadata_discrimination_canonical.csv)                                  |
| Spearman / Pearson — **canonical authenticated** (n=30)    | [projected_pairs/full_summary_authenticated_n30.json](projected_pairs/full_summary_authenticated_n30.json)      |
| Spearman / Pearson — authenticated current rubric (n=25)   | [projected_pairs/full_summary_authenticated.json](projected_pairs/full_summary_authenticated.json)              |
| Spearman / Pearson — superseded **unauthenticated** (n=30) | [projected_pairs/full_summary.json](projected_pairs/full_summary.json)                                          |
| REDUX cache (Test 2+3, 30-pair)                            | [three_test_argument_table.csv](three_test_argument_table.csv)                                                  |
| Continuous scores                                          | [continuous_scores_summary.csv](continuous_scores_summary.csv)                                                  |

**Headlines:** similar mean ≈ **94.4%** vs dissimilar ≈ **4.7%**; canonical authenticated cross-method Spearman **ρ ≈ +0.69** (n=30, go=true — passes rubric 0.30; authenticated n=25 is consistent at ρ ≈ +0.78). The earlier ρ ≈ −0.21 (`full_summary.json`) was an **unauthenticated** GitHub rate-limiting artifact (38% HTTP 403), retained for transparency — see [VALIDATION_MEMO.md](VALIDATION_MEMO.md).

---

### 6. Testing / CAIS relevance (case study)

| What                                      | Path                                                               |
| ----------------------------------------- | ------------------------------------------------------------------ |
| Airflow anchor → proxies → test scenarios | [testing_case_study_airflow.md](testing_case_study_airflow.md)     |

Magnets / Good-OK-Weak are **retrieval hygiene only**, not test adequacy — see limitations in [PAPER_PACKAGE.md](PAPER_PACKAGE.md).

---

## Everything under `results_benchmark/` (folder map)

| Area              | Paths                                                                        |
| ----------------- | ---------------------------------------------------------------------------- |
| Gates & narrative | `PAPER_PACKAGE.md`, `VALIDATION_MEMO.md`, `WORK_REVIEW.md`, `REPO_AUDIT.md` |
| Labeled eval      | `labeled_scored.json`, `labeled/`                                            |
| queryv2 REDUX     | `queryv2_redux/`, `queryv2_spot_check.md`                                    |
| anchorsv2         | `anchorsv2_redux/`, `anchorsv2_spot_check.md`, `anchorsv2_overlap.csv`       |
| Repro snapshot    | `run_manifest.json`                                                          |
| Historical CSVs   | `archives/` (+ symlinks at former root paths)                                |

Full layout: [README.md](README.md).

---

## Review vs re-run

**Review only:** all paths above are in-repo; no re-scoring required to verify claims.

**Re-run from scratch:** commands in [WORK_REVIEW.md § Repro commands](WORK_REVIEW.md#repro-commands). Optional full REDUX setup: [../REDUX_REPRO.md](../REDUX_REPRO.md).
