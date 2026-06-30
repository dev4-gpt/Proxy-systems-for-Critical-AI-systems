# Two-stage system for finding proxy test repositories for Critical AI Systems (CAIS)

> **Reference doc.** Source: [CAIS_REVIEW.docx](https://pennstateoffice365-my.sharepoint.com/:w:/g/personal/asd5520_psu_edu/IQDOj1wnLpNLSo6SHRMKwfcrAY7R55GhKp9A4FnfUFYLbfU?e=oopTyv) (pre-consolidation baseline). This markdown version is **updated post-consolidation** — v2 labeled cohort, `CANONICAL_RESULTS/`, G9 downstream, Tier A/B cleanup. Frozen headline bundle: `[CANONICAL_RESULTS/](CANONICAL_RESULTS/)`.

We built a two-stage CAIS proxy-discovery system.

MetaMatch (Stage 1) retrieves candidate test-proxy repositories from GitHub; our Phase 2 grid search found the optimal configuration (`queryv2`), achieving zero top-5 magnets and 20 / 0 / 0 in Good / OK / Weak retrieval hygiene across 20 anchors. REDUX 4 (Stage 2) scores repository similarity across four methods: metadata, code-centric, dynamic, and cross-language. We validated the end-to-end pipeline against labeled ground truth: the **primary cohort is now 24 pairs (v2)** with bootstrap confidence intervals; the original **10-pair cohort (v1)** remains frozen for comparison. Metadata discrimination separates similar (~94%) from dissimilar (5%) pairs with AUC-like 1.0; cross-method agreement is ρ = +0.69 in the authenticated run with n = 30. Anchor-list perturbation (`anchorsv2`) is stable with mean Jaccard 0.96 on 20 shared slugs. **Downstream usefulness (G9)** is quantified for all 24 anchors. Results are reproducible and collected in `results_benchmark/` with a frozen bundle in `CANONICAL_RESULTS/`.

The scoring engine core path is `proxytool_redux/_extracted/redux4_core.py`.

## Stage 1 — MetaMatch (retrieval)

Given an anchor repository such as `apache/airflow`, MetaMatch searches GitHub and ranks candidate proxy repositories using a penalty/scoring grid.

A full Phase 2 grid search was run across approximately 20 hyperparameter combinations. The frozen winner under `runs/experiments/` is:

`penalty300_min700_cap22_queryv2`

Key retrieval result:

- Top-5 magnets: 0
- Good / OK / Weak across 20 anchors: 20 / 0 / 0



## Stage 2 — REDUX 4 (similarity scoring)

Given any two repositories, `PROXYTOOL_REDUX_4` scores how similar they are across four methods:

- `metadata` — commit fingerprints
- `code_centric` — clone detection
- `dynamic` — behavioral similarity
- `cross_language` — cross-language similarity

The scoring engine lives in `proxytool_redux/_extracted/redux4_core.py`.

## The validation package (`results_benchmark/`)

This package connects the two stages to the evidence used for review and paper-writing.


| File                                                         | What it is                                                                                            | Best use                                   |
| ------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| `[CANONICAL_RESULTS/README.md](CANONICAL_RESULTS/README.md)` | Frozen headline artifacts (G1–G9), symlinks, SHA256 manifest                                          | **Start here** — one-page proof bundle     |
| `RESULTS_REVIEW.md`                                          | Navigator page with headline numbers and links to supporting files                                    | Finding the results quickly                |
| `PAPER_PACKAGE.md`                                           | Pass/fail on decision gates G1–G8 plus informational G9; paper-ready tables; limitations              | Checking whether the system passed         |
| `VALIDATION_MEMO.md`                                         | Statistical summary and method positioning in prose, mapped to three reviewer concerns                | Writing the methodology/statistics section |
| `WORK_REVIEW.md`                                             | Master review document with phase table (A–I), commands, source tags, repro, cross-verification index | Reproducing the work                       |
| `REPO_AUDIT.md`                                              | Inventory of paths and tools used in validation vs archived grid/sweep history                        | Checking what materially matters           |
| `MASTER_EVALUATION.md`                                       | Independent research-grade audit; re-derives numbers from raw files; hygiene record                   | Deep independent review                    |
| `README.md`                                                  | Directory map of `results_benchmark/`                                                                 | Navigation                                 |
| `anchorsv2_spot_check.md`                                    | Retrieval hygiene notes for the `anchorsv2` sensitivity run (24 anchors, **4 additions**)             | Supporting the anchorsv2 narrative         |
| `queryv2_spot_check.md`                                      | Retrieval hygiene notes for the `queryv2` winner (thin anchors, top-5 proxies)                        | Supporting the queryv2 narrative           |
| `testing_case_study_airflow.md`                              | Case study: Airflow anchor → REDUX proxy similarity → CAIS test-scenario mapping                      | Explaining how this connects to testing    |
| `downstream_validation/SUMMARY.md`                           | Triage, search effort, scenario coverage for all 24 anchors (G9)                                      | Quantified downstream usefulness           |
| `REMOVABLE_HISTORY.md`                                       | Cleanup inventory (Tier A/B executed; grid tarball location)                                          | What was pruned and why                    |




## Final results



### 1. MetaMatch retrieval winner


| Metric           | Value                                | Source                                     |
| ---------------- | ------------------------------------ | ------------------------------------------ |
| Winner config    | `penalty300, min700, cap22, queryv2` | `runs/experiments/documentation/WINNER.md` |
| Top-5 magnets    | 0                                    | same                                       |
| Good / OK / Weak | 20 / 0 / 0                           | same                                       |




### 2. Labeled ground-truth evaluation

**Primary — v2 (24 pairs; 22 in metric cohort excluding 2** `target_uncertain`**)**


| Cohort                                                        | Method           | F1    | Source                                  |
| ------------------------------------------------------------- | ---------------- | ----- | --------------------------------------- |
| Strict (`known_match` only)                                   | `metadata`       | 0.909 | `labeled_v2/labeled_strict_summary.csv` |
| Strict                                                        | `code_centric`   | 1.00  | same                                    |
| Strict                                                        | `cross_language` | 1.00  | same                                    |
| Strict                                                        | `dynamic`        | 0.842 | same                                    |
| Lenient (`known_match` + `known_related`; uncertain excluded) | `metadata`       | 0.941 | `labeled_v2/labeled_summary.csv`        |
| Lenient                                                       | `code_centric`   | 0.769 | same                                    |
| Lenient                                                       | `cross_language` | 0.933 | same                                    |
| Lenient                                                       | `dynamic`        | 0.692 | same                                    |


Bootstrap 95% CIs: `labeled_v2/bootstrap_ci.csv`. Lenient alias (same numbers): `labeled_v2/labeled_lenient_summary.csv`.

**Frozen comparison — v1 (10 pairs)**


| Cohort                                     | Method           | F1   | Source                               |
| ------------------------------------------ | ---------------- | ---- | ------------------------------------ |
| Strict (5 mirrors only)                    | `metadata`       | 1.00 | `labeled/labeled_strict_summary.csv` |
| Strict                                     | `code_centric`   | 1.00 | same                                 |
| Strict                                     | `cross_language` | 1.00 | same                                 |
| Strict                                     | `dynamic`        | 0.80 | same                                 |
| Lenient (+2 related; 1 uncertain excluded) | `metadata`       | 1.00 | `labeled/labeled_summary.csv`        |
| Lenient                                    | `code_centric`   | 0.83 | same                                 |
| Lenient                                    | `cross_language` | 0.92 | same                                 |
| Lenient                                    | `dynamic`        | 0.67 | same                                 |




### 3. REDUX proxy bridges


| Bridge                               | Anchors | Pair scores | Source                               |
| ------------------------------------ | ------- | ----------- | ------------------------------------ |
| `queryv2`                            | 20      | 100         | `queryv2_redux/rollup_summary.csv`   |
| `anchorsv2` (full independent rerun) | 24      | 116         | `anchorsv2_redux/rollup_summary.csv` |


The four anchorsv2-only **additions** (not in queryv2): `mlflow-mlflow`, `pytorch-vision`, `scikit-learn-scikit-learn`, `treeverse-dvc`.

Selected per-anchor metadata means for `queryv2`:

- `airflow`: 95.4%
- `gradio`: 97.9%
- `jina`: 96.4%
- `ray`: 92.3%



### 4. Anchor-list perturbation stability


| Metric               | Value                                | Source                  |
| -------------------- | ------------------------------------ | ----------------------- |
| Shared slugs         | 20                                   | `anchorsv2_overlap.csv` |
| Mean top-5 Jaccard   | 0.96                                 | same                    |
| Identical top-5 sets | 17 / 20                              | same                    |
| Partial drift        | spaCy 0.67, datasets 0.67, jina 0.80 | same                    |




### 5. Metadata discrimination


| Metric            | Value    | Source                                  |
| ----------------- | -------- | --------------------------------------- |
| Similar mean      | 94.4%    | `metadata_discrimination_canonical.csv` |
| Dissimilar mean   | 4.7%     | same                                    |
| Gap               | 89.7 pts | same                                    |
| Pairwise AUC-like | 1.0      | same                                    |




### 6. Cross-method agreement (canonical)


| Stat       | Value               | Source                                                |
| ---------- | ------------------- | ----------------------------------------------------- |
| Spearman ρ | +0.69 (p = 2.34e-5) | `projected_pairs/full_summary_authenticated_n30.json` |
| Pearson r  | +0.66 (p = 6.25e-5) | same                                                  |
| Decision   | `go = true`         | same                                                  |


**Note:** the original frozen run showed ρ = −0.21 and failed. This was a rate-limiting artifact: 38% of API calls returned HTTP 403. Holding the same n = 30 allocation and adding authentication moved ρ from −0.21 to +0.69. The unauthenticated file is retained in the repository for transparency (`projected_pairs/full_summary.json`, `ARCHIVE_ONLY.md`).

### 7. Downstream usefulness (G9, informational)


| Metric                  | Coverage                                             | Source                                        |
| ----------------------- | ---------------------------------------------------- | --------------------------------------------- |
| Proxy triage efficiency | 24 anchors (20 queryv2 + 4 additions)                | `downstream_validation/triage_metrics.csv`    |
| Candidate search effort | 24 anchors                                           | `downstream_validation/search_effort.csv`     |
| Scenario coverage       | 24 anchors (3 CAIS explicit + 21 metadata heuristic) | `downstream_validation/scenario_coverage.csv` |




## Gate summary


| Gate                                        | Result                                |
| ------------------------------------------- | ------------------------------------- |
| G1 — Strict `known_match` separates         | PASS (v2 strict metadata F1 = 0.909)  |
| G2 — Lenient includes related pairs         | PASS (v2 lenient metadata F1 = 0.941) |
| G3 — No false ground-truth claim            | PASS                                  |
| G4 — Cross-method agreement (authenticated) | PASS, ρ = +0.69                       |
| G5 — `queryv2` retrieval frozen             | PASS                                  |
| G6 — `queryv2` REDUX bridge                 | PASS                                  |
| G7 — `anchorsv2` sensitivity                | PASS                                  |
| G8 — No MetaMatch retune required           | NO                                    |
| G9 — Downstream usefulness                  | INFO (not pass/fail)                  |


---



## Consolidation delta (original CAIS_REVIEW → current repo)


| Topic              | Original doc                        | Current repo                                                             |
| ------------------ | ----------------------------------- | ------------------------------------------------------------------------ |
| Labeled cohort     | 10 pairs, strict metadata F1 = 1.00 | **24 pairs (v2 primary)**; v1 frozen                                     |
| Entry point        | `results_benchmark/` only           | `CANONICAL_RESULTS/` + `RESULTS_REVIEW.md`                               |
| Gates              | G1–G8                               | G1–G8 + **G9** (downstream)                                              |
| anchorsv2          | "4 swaps"                           | **4 additions**                                                          |
| Cleanup            | Not documented                      | Tier A/B done; grid in `archives/off_repo/metamatch_grid_history.tar.gz` |
| WORK_REVIEW phases | A–G                                 | **A–I**                                                                  |


For cleanup details see `[REMOVABLE_HISTORY.md](REMOVABLE_HISTORY.md)`. For repro commands see `[WORK_REVIEW.md](WORK_REVIEW.md)`.