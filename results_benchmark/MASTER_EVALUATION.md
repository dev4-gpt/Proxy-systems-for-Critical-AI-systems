# MASTER EVALUATION — CAIS / MetaMatch / REDUX

**Repository:** `mdk5293/Proxy-systems-for-Critical-AI-systems` (local working copy)
**Repo root:** `/Users/aryamandev/Library/Mobile Documents/com~apple~CloudDocs/Research Assistant`
**Evaluation date:** 2026-06-18
**Author of this review:** independent end-to-end audit (every number below was re-derived from the files cited; see [Cross-verification index](#13-cross-verification-index-claim--source))
**Scope:** all research work to date — MetaMatch retrieval, the REDUX 4 similarity engine, the labeled ground-truth validation pass, supporting statistics, repo hygiene, and prioritized next steps.

---

## 0. Resolution status (2026-06-18 remediation pass)

The discrepancies, gaps, and reproducibility issues this document originally flagged have now been worked through. Summary (details in [§14](#14-discrepancies-found-docs-vs-data) and [§12](#12-reproducibility-status)):

| # | Issue | Status | What changed |
|---|-------|--------|--------------|
| 1 | Dual "lenient" metadata F1 (0.93 vs 1.00) | **RESOLVED** | `tools/run_labeled_benchmark.py` patched to exclude `target_uncertain` from P/R/F1 (matching `labeled_strict_metrics.py` and the documented cohort rule). Summaries were regenerated and independently re-derived offline (stdlib-only, no pandas/network) via `tools/recompute_labeled_metrics_stdlib.py` — byte-identical output. `labeled_summary.csv` ≡ `labeled_lenient_summary.csv`. **Consistent lenient metadata F1 = 1.00.** All docs re-cite this value. |
| 2 | `related_mariadb_mysql` `score_error` "No module named 'proxytool_redux'" | **RESOLVED** (root cause) / live-refresh reproducible | Root cause = missing `PYTHONPATH=.` (the package imports fine from the repo root; it is not a true scoring failure). The on-disk `labeled_scored.json` no longer carries `score_error` and `score_source = live_redux` with verified values (metadata 54.36, code_centric 44.15, dynamic 7.5, cross_language 42.21); all other 9 pairs byte-identical. To independently re-verify in a normal (non-sandbox) shell: `export GITHUB_TOKEN="$(gh auth token)" && PYTHONPATH=. timeout 900 python3 tools/score_labeled_benchmark_redux.py --benchmark configs/labeled_benchmark_pairs.json --output results_benchmark/labeled_scored.json --live --max-commits 150`. |
| 3 | Unauthenticated stat runs (403s) | **RESOLVED (authenticated re-run captured) — needs paper decision** | The authenticated projected-pair re-run was executed on 2026-06-19 (`export GITHUB_TOKEN="$(gh auth token)" && PYTHONPATH=. python3 scripts/projected_pair_pipeline.py --mode full --workers 1,2`, run outside the sandbox on the real network). Output saved to **`projected_pairs/full_summary_authenticated.json`** (telemetry `authenticated=true`, 49×200 / 5×403, api_non_200_ratio 0.093). The original unauthenticated **`projected_pairs/full_summary.json`** is **preserved unchanged** as the frozen, cited reference. **The authenticated numbers differ materially and flip the decision** (Spearman −0.21→**+0.777**, Pearson −0.35→**+0.776**, `go` false→**true**), driven by both authentication *and* a rubric/allocation change (the committed rubric now emits **n=25**: target_uncertain 10→5 + known_related 5, vs the frozen n=30). Because this overturns the headline "methods don't agree" negative finding, it is **flagged for the author's decision** before propagating into `PAPER_PACKAGE.md` / `VALIDATION_MEMO.md`. See [§9](#9-component-6--statistics-discrimination--cross-method-spearman). |
| 4 | REDUX core gitignored + untracked | **RESOLVED** | `proxytool_redux/{_extracted/redux4_core.py,_extracted/__init__.py,benchmark.py,benchmark_metrics.py,bootstrap.py}`, `scripts/extract_redux4_core.py`, `scripts/run_repro_benchmark.py`, and `REDUX_REPRO.md` are now git-tracked. `.gitignore` reconciled (`projected_pairs/` un-ignored; only the 7 MB exploratory notebook stays out). Committed (not pushed). |
| 5 | anchorsv2 not an independent rerun | **DEFERRED (re-attempted authenticated 2026-06-19, exceeded budget)** | Re-attempted outside the sandbox on the real network with authentication: `export GITHUB_TOKEN="$(gh auth token)" && PYTHONPATH=. timeout 1500 bash tools/run_anchorsv2_redux.sh full` (after clearing `results_benchmark/anchorsv2_redux/` so reused slugs are re-scored, not skipped). The run's **`--fit-global` step (per-repo feature extraction incl. commit embeddings for ~140 unique anchor+proxy URLs) alone exceeded the 25-min budget** and was killed by `timeout` before writing any per-anchor CSV. **No partial/corrupted output was produced** (the output dir was empty at kill time); the existing valid bootstrap outputs were **restored byte-for-byte from backup** and remain git-clean. The retrieval-side stability number was still re-verified: `tools/anchorsv2_overlap.py` re-derives `anchorsv2_overlap.csv` **byte-identical** (mean top-5 Jaccard 0.9567, 17/20 at 1.0). The REDUX metadata-mean rollup remains the bootstrap. See [§7](#7-component-4--queryv2--anchorsv2-redux-bridges). |

**Reproducibility note:** `gh auth status` reports a keyring warning, but `gh auth token` returns a working token (verified 2026-06-19 HTTP 200, core limit 5000/5000, ~4999 remaining). All network re-runs in the 2026-06-19 pass used `export GITHUB_TOKEN="$(gh auth token)"` and ran outside the sandbox (the in-sandbox allowlist blocks the GitHub REST API).

### 0.1 — 2026-06-19 authenticated re-run pass (network outside sandbox)

The two network-bound DEFERRED items were re-attempted with a verified GitHub token on the real network:

1. **Token/API reachability — OK.** `curl /rate_limit` returned HTTP 200; authenticated core limit **5000**, ~4999 remaining; search limit 30/min.
2. **Projected-pair authenticated re-run — DONE, captured to a new file, flagged.** Completed in ~87 s. New `projected_pairs/full_summary_authenticated.json`: n=25, **Spearman ρ=+0.7772 (p=4.87e-6)**, **Pearson r=+0.7757 (p=5.24e-6)**, paired-t 1.488 (p=0.150), TOST equivalent=false, **decision `go`=true**, telemetry `authenticated=true` (49×200 / 5×403). Frozen unauthenticated `full_summary.json` (n=30, ρ=−0.2107, `go`=false) **preserved unchanged**. The flip is consequential (see [§9](#9-component-6--statistics-discrimination--cross-method-spearman)) and is **flagged for the author's decision**; downstream paper docs were **not** edited to the new value.
3. **Independent anchorsv2 REDUX rerun — still DEFERRED.** The `--fit-global` feature-extraction step alone exceeded the 25-min budget; killed by `timeout` with **no partial output**, existing bootstrap outputs restored byte-identical. Retrieval-side overlap (Jaccard 0.9567, 17/20) re-verified byte-identical offline.
4. **Labeled MariaDB/MySQL `--live` confirmation — CONFIRMED.** Re-ran `tools/score_labeled_benchmark_redux.py --live --max-commits 150` (to a temp file for safe diffing): **10/10 pairs scored, zero `score_error`**, MariaDB↔MySQL byte-identical (metadata 54.36, code_centric 44.15, dynamic 7.5, cross_language 42.21, `score_source=live_redux`), all other 9 pairs unchanged. On-disk `labeled_scored.json` left untouched (already correct).

---

## 1. Executive summary

This repository implements and validates a **two-stage proxy-discovery system for Critical AI Systems (CAIS)**. Stage one — **MetaMatch** — is a GitHub retrieval/ranking pipeline (PowerShell + Python grid search) that, given an "anchor" repository, returns a curated set of candidate "proxy" repositories with good retrieval hygiene. Stage two — **REDUX 4** — is a multi-signal repository-similarity engine (commit-metadata, code-clone, dynamic-behavior, and cross-language methods) that scores how similar two repositories actually are. The validation pass glues the two stages to a small **labeled ground-truth cohort** (real mirrors, forks, and hard negatives) and reports honest statistics for paper decision gates.

**State of the work (verified):**

- **MetaMatch retrieval is complete and frozen.** The Phase-2 grid winner `penalty300_min700_cap22_queryv2` achieves **0 top-5 magnets** and **20/0/0** Good/OK/Weak across 20 anchors — verified in `runs/experiments/documentation/WINNER.md` and `EXPERIMENT_LOG.md`.
- **Labeled ground truth separates cleanly.** On the strict `known_match`-only cohort, metadata / code_centric / cross_language all reach **F1 = 1.0**; dynamic is weaker at **F1 = 0.80** — verified in `labeled/labeled_strict_summary.csv`.
- **REDUX similarity bridges retrieval to similarity.** queryv2 produced **100** anchor→proxy metadata scores (20 anchors × top-5); anchorsv2 produced **116** scores (24 anchors) — verified in the rollup CSVs and run manifests.
- **Anchor-list perturbation is stable.** Mean top-5 Jaccard = **0.957** on 20 shared slugs, **17/20** identical — verified in `archives/metamatch_sensitivity/anchorsv2_overlap.csv`.
- **Honest weaknesses are documented, not hidden.** Cross-method Spearman ρ = **−0.21** (p = 0.26) on the frozen unauthenticated n=30 run **fails** the project's own 0.30 rubric; the methods are complementary views, not redundant confirmations. **Caveat (2026-06-19):** an authenticated re-run under the *current* rubric (n=25) yields ρ = **+0.78** (`go`=true) — this flips the finding and is captured in `projected_pairs/full_summary_authenticated.json`, but because the change confounds authentication with a rubric/allocation change it is **flagged for the author's decision** and has **not** been propagated into the paper docs (see [§0.1](#01--2026-06-19-authenticated-re-run-pass-network-outside-sandbox) and [§9](#9-component-6--statistics-discrimination--cross-method-spearman)).

**The original most important caveat (now resolved):** the REDUX scoring engine that produces nearly every headline number (`proxytool_redux/_extracted/redux4_core.py`, `benchmark.py`, `benchmark_metrics.py`, `bootstrap.py`) was **git-ignored and not tracked**, so a fresh `git clone` could not re-run scoring. **As of the 2026-06-18 remediation pass these files are committed** (see [§0](#0-resolution-status-2026-06-18-remediation-pass) and [§12](#12-reproducibility-status)), and the one labeled pair that carried `"score_error": "No module named 'proxytool_redux'"` was re-scored authenticated with the error cleared.

**Bottom line:** the results are internally consistent and the documented numbers match the data. The work is paper-ready for the *retrieval + labeled-separation + multi-view-similarity* story, **provided** the paper (a) reports the honest Spearman, (b) discloses that anchorsv2 is partly bootstrapped from queryv2 (full independent rerun is DEFERRED — command in §7), and (c) notes the REDUX core is now tracked so reviewers can reproduce. The two doc-vs-data discrepancies originally found in §14 are now RESOLVED.

---

## 2. Repository map (key directories and their roles)


| Path                                                  | Role                                                                                            | Tracked in git?                                                            |
| ----------------------------------------------------- | ----------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `proxytool_redux/`                                    | REDUX 4 similarity engine (scoring core + benchmark runners)                                    | **Yes** — core now tracked; only the 7 MB exploratory notebook excluded     |
| `proxytool_redux/_extracted/redux4_core.py`           | 180 KB extracted scoring library (metrics, normalizers, 4 methods)                              | **Yes** (tracked as of 2026-06-18)                                         |
| `proxytool_redux/benchmark.py`                        | `run_all_benchmarks()` orchestrator (Test 2/3 + 30-pair)                                        | **Yes**                                                                    |
| `proxytool_redux/benchmark_metrics.py`                | P/R/F1/separation metrics imported by labeled tools                                             | **Yes**                                                                    |
| `runs/experiments/`                                   | Frozen MetaMatch grid archive (24 experiment folders + docs)                                    | Yes (snapshots)                                                            |
| `runs/experiments/penalty300_min700_cap22_queryv2/`   | **MetaMatch winner** — 20 anchors, frozen `30_Matches.csv` per anchor                           | Yes                                                                        |
| `runs/experiments/penalty300_min700_cap22_anchorsv2/` | Anchor-list sensitivity archive (24 anchors, 4 swaps)                                           | Yes                                                                        |
| `runs/experiments/documentation/`                     | `WINNER.md`, `PHASE2_NOTES.md`, `CAP_ANALYSIS.md`, `EXPERIMENT_LOG.md`, `GRID_PHASE2_STATUS.md` | Yes                                                                        |
| `runs/2026-05-0{1,2,3}-`*                             | Live batch run outputs (airflow + domain×language batches)                                      | No (gitignored live outputs)                                               |
| `results_benchmark/`                                  | **Validation package** — labeled eval, REDUX bridges, stats, narrative                          | Mostly yes                                                                 |
| `results_benchmark/labeled/`                          | Strict/lenient/threshold metric summaries                                                       | Yes                                                                        |
| `results_benchmark/queryv2_redux/`                    | 20 anchor CSVs + `rollup_summary.csv` + `run_manifest.json`                                     | Yes                                                                        |
| `results_benchmark/anchorsv2_redux/`                  | 24 anchor CSVs + rollup + manifest                                                              | Yes                                                                        |
| `results_benchmark/archives/`                         | Historical sweep CSVs (7 subfolders) with root symlinks                                         | Yes                                                                        |
| `results_benchmark/projected_pairs/`                  | Cross-method Spearman/Pearson summary (n=30)                                                    | **Yes** (tracked despite being in `.gitignore`)                            |
| `configs/`                                            | Benchmark seed manifest, rubric, grid variants                                                  | Yes (some variants historical)                                             |
| `scripts/`                                            | REDUX extraction + projected-pair pipeline + repro harness                                      | Partial (5 of 7 tracked)                                                   |
| `tools/`                                              | MetaMatch grid management (10) + validation bridges (8)                                         | Yes                                                                        |
| `proxytool_REDUX_*.ipynb` (root)                      | 7 notebook iterations; REDUX 4 is the live one                                                  | Yes (but large)                                                            |


---

## 3. The pipeline, end-to-end

```
                         ANCHOR REPO (e.g. apache/airflow)
                                    │
        ┌───────────────────────────────────────────────────────┐
        │ STAGE 1 — MetaMatch retrieval  (PowerShell + tools/*.py)│
        │  Get-AnchorCandidates → Get-AnchorMatches → grid sweep  │
        │  penalty / min-score / per-owner caps + query overrides │
        │  selection by Good/OK/Weak + "magnet" hygiene scoring   │
        └───────────────────────────────────────────────────────┘
                                    │  winner = penalty300_min700_cap22_queryv2
                                    │  (frozen under runs/experiments/)
                                    ▼
                 Top-N candidate "proxy" repos per anchor
                 (runs/experiments/.../manual-ml-py/<anchor>/30_Matches.csv)
                                    │
        ┌───────────────────────────────────────────────────────┐
        │ STAGE 2 — REDUX 4 similarity  (proxytool_redux/, gitig.)│
        │  per-repo features: cadence, churn, sentiment, semantic,│
        │  contributors, co-change, temporal, embeddings, language│
        │  → MinMax/Winsor/ZScore normalize → CAIS-weighted blend │
        │  4 methods: metadata · code_centric · dynamic · x-lang  │
        └───────────────────────────────────────────────────────┘
            │                                   │
            │ bridge A: score retrieved proxies │ bridge B: score labeled pairs
            ▼                                   ▼
  queryv2_redux/ (100) + anchorsv2_redux/(116)   labeled_scored.json (10 pairs)
  rollup_summary.csv                              │
            │                                     ▼  (ADDED LAYER)
            │                          tools/run_labeled_benchmark.py
            │                          tools/labeled_strict_metrics.py
            │                                     ▼
            │                          labeled/ strict + lenient + threshold
            ▼                                     ▼
        ┌───────────────────────────────────────────────────────┐
        │ STAGE 3 — Statistics & decision gates                   │
        │  discrimination (similar 94.4% vs dissimilar 4.7%)      │
        │  cross-method Spearman ρ=−0.21 (projected_pairs/)       │
        │  anchorsv2 Jaccard 0.96  →  PAPER_PACKAGE.md G1–G8       │
        └───────────────────────────────────────────────────────┘
```

**Provenance legend** (from `WORK_REVIEW.md` tag legend):

- **[Reproducible]** = ground-truth + repro layer (seed manifest, `run_manifest`, `verify_repo_access`, labeled scorers, `benchmark_metrics`).
- **[Anchor/Query]** = the author's MetaMatch retrieval + queryv2/anchorsv2 REDUX bridges.
- **[Pre-existing]** = prior REDUX benchmarks + WINNER arc that predate this validation pass.
- **[Analysis]** = synthesis memos with no new scoring command.

In plain terms: **MetaMatch retrieval and the REDUX engine form the base**; the **labeled cohort, `verify_repo_access`, `write_run_manifest`, and `run_labeled_benchmark` are the supplied layer**; the discrimination tables and projected-pair Spearman are **pre-existing REDUX outputs** reused read-only.

---

## 4. Component 1 — MetaMatch retrieval & queryv2 selection

**Purpose:** Given anchor repos, retrieve and rank candidate GitHub proxies, then tune hyperparameters (cross-anchor frequency penalty, minimum score, per-owner caps, query overrides) to maximize retrieval hygiene — minimizing "magnets" (repos that dominate many anchors' results) while keeping the qualified pool ("Good").

**Inputs:** anchor list (`recommended_anchors_top.csv`), query overrides (`metamatch_anchor_query_overrides.json`), winner hyperparameters (`metamatch_hyperparams.json`: penalty 300, min 700, cap 2/2).

**Outputs (exact paths):**

- Frozen winner: `runs/experiments/penalty300_min700_cap22_queryv2/manual-ml-py/<anchor>/30_Matches.csv`
- Scorecard: `runs/experiments/documentation/WINNER.md`
- Grid log: `runs/experiments/documentation/EXPERIMENT_LOG.md`, `experiment_comparison_summary.csv`

**Key results (verified against `WINNER.md` + `EXPERIMENT_LOG.md`):**


| Experiment                            | Penalty | Top-5 magnets | Weak  | Good   | OK    | Role                  |
| ------------------------------------- | ------- | ------------- | ----- | ------ | ----- | --------------------- |
| `penalty30_min700_cap21`              | 30      | 30            | 8     | 10     | 2     | Loose baseline        |
| `penalty100_min700_cap21`             | 100     | 18            | 2     | 14     | 4     | Prior baseline        |
| `penalty300_min700_cap22`             | 300     | 5             | 0     | 20     | 0     | Hyperparam step       |
| `**penalty300_min700_cap22_queryv2`** | **300** | **0**         | **0** | **20** | **0** | **Winner**            |
| `penalty300_min700_cap22_anchorsv2`   | 300     | 0             | 0     | 24     | 0     | Sensitivity (4 swaps) |


The monotone trend (magnets 30 → 18 → 5 → 0 as penalty rises) is internally consistent across all 24 grid folders in the scorecard. `CAP_ANALYSIS.md` confirms per-owner caps did **not** move Good/OK/Weak at penalty=110 (only a 1-repo Streamlit difference), justifying the fixed cap 2/2.

**Honest assessment:** The retrieval win is real and well-documented, but "0 magnets, 20/0/0" measures **GitHub retrieval hygiene, not test-scenario adequacy** — the docs are careful to say this repeatedly (`queryv2_spot_check.md`, `PAPER_PACKAGE.md` limitations). The win is also partly a product of query overrides hand-tuned per anchor (`metamatch_anchor_query_overrides.json`), which is a mild overfitting risk: the winner is selected on the same 20 anchors used to tune the queries. anchorsv2 (below) is the intended mitigation.

---

## 5. Component 2 — anchorsv2 sensitivity

**Purpose:** Test whether the retrieval result is robust to changing the anchor set. anchorsv2 swaps four anchors vs the original list (per `PHASE2_NOTES.md`): NLP-progress→scikit-learn, ML-From-Scratch→mlflow, recommenders→treeverse/dvc, pytorch-lightning→pytorch/vision.

**Inputs:** `recommended_anchors_top_v2.csv`; same penalty/min/cap/query settings as queryv2.

**Outputs:** `runs/experiments/penalty300_min700_cap22_anchorsv2/`; overlap table `results_benchmark/archives/metamatch_sensitivity/anchorsv2_overlap.csv` (root symlink `anchorsv2_overlap.csv`).

**Key results (re-computed from `anchorsv2_overlap.csv`, 20 rows):**


| Metric                          | Value                                                                       | Verification                    |
| ------------------------------- | --------------------------------------------------------------------------- | ------------------------------- |
| Shared folder slugs compared    | 20                                                                          | row count                       |
| Mean top-5 Jaccard              | **0.9567**                                                                  | computed mean of `jaccard_topk` |
| Slugs identical (Jaccard = 1.0) | **17 / 20**                                                                 | count                           |
| Drift slugs                     | `explosion/spaCy` 0.667, `huggingface/datasets` 0.667, `jina-ai/serve` 0.80 | the only rows < 1.0             |


All three documented drift cases match the data exactly. Retrieval hygiene on the new anchors holds (24/0/0 Good/OK/Weak; 0 magnets — `anchorsv2_spot_check.md`).

**Honest assessment:** Stability is genuinely high. Two caveats worth stating in the paper: (1) the comparison is only over the **20 shared slugs**; the 4 swapped anchors are intentionally different and are *not* part of the Jaccard number, so "robustness" is demonstrated for the unchanged anchors, not the swapped ones; (2) the docs correctly forbid reading "24 Good vs 20 Good" as a head-to-head win (different denominators).

---

## 6. Component 3 — REDUX 4 scoring engine (`proxytool_redux`)

**Purpose:** Quantify *actual* repository similarity along four orthogonal "methods," so that retrieval neighbors and labeled pairs can be scored on a 0–100 scale.

**Architecture (from `proxytool_redux/_extracted/redux4_core.py`, `benchmark.py`, `scoring.py`):**

- **Per-repo feature extraction** from git/commit history and GitHub API: cadence, churn, sentiment (VADER/lexicon backends), commit-semantic embeddings, contributor structure, co-change, temporal rhythm, language mix, plus repo-signal metrics (release cadence, branching, issues, doc quality, CI signals).
- **Normalization:** `MinMaxNormalizer`, `MinMaxNormalizerWinsor`, `ZScoreNormalizer`, with a **global min-max fit shared across benchmark tables** (`fit_global_minmax_for_all_benchmark_tables`) so scores are comparable across pairs.
- **Four methods:**
  - `metadata` — `family_cosine` over the metric family, blended with CAIS weights (`CAIS_WEIGHTS_REDUX3_BLEND = 0.7·strict + 0.3·mimic`), over commit windows `[50, 150]` weighted `{50:0.65, 150:0.35}`, coverage penalty λ = 0.20.
  - `code_centric` — `code_clone_similarity` / `deep_code_similarity` (tree/readme/language-aware).
  - `dynamic` — `dynamic_behavior_similarity`.
  - `cross_language` — language-mix similarity.
- **Reporting modes:** `contrastive` (sigmoid of score minus median of domain hard-negatives, temperature 6.0 — see `scoring.contrastive_adjust`) for benchmarks; `rank_pct` for retrieval.

**Benchmark entry point:** `run_all_benchmarks()` in `benchmark.py` produces `three_test_argument_table.csv` (Test 2 functional-similar + Test 3 dissimilar), `custom_30_pairs_canonical.csv`, and `metadata_discrimination_canonical.csv`. The REPRO notebook variant is `proxytool_REDUX_4_REPRO.ipynb` (5 cells; documented in `REDUX_REPRO.md`).

**Honest assessment:** This is the technical heart of the project and is well-engineered (clean separation of metrics, normalizers, reporting modes; a small pure-numeric `scoring.py` that is the only fully git-tracked piece). **It was the largest reproducibility liability** — the 180 KB core, the benchmark runner, and `benchmark_metrics.py` were untracked — but these are now committed (see §0 and §12). The `metadata` method also carries the most weight in every downstream claim, while `dynamic` is consistently the weakest signal (F1 0.667–0.80, lenient–strict) — the paper should avoid implying the four methods are equally trustworthy.

---

## 7. Component 4 — queryv2 + anchorsv2 REDUX bridges

**Purpose:** Apply REDUX `metadata` scoring to the *retrieved* proxies, turning "did retrieval find clean neighbors?" into "are those neighbors actually similar?"

**Tool:** `tools/score_metamatch_proxies_redux.py` (queryv2) and `tools/run_anchorsv2_redux.sh` (anchorsv2). Both read frozen archives — **no MetaMatch re-run**.

**Outputs & verified counts:**


| Bridge    | Anchors | Pair scores | Manifest                                                   | Verification                               |
| --------- | ------- | ----------- | ---------------------------------------------------------- | ------------------------------------------ |
| queryv2   | 20      | **100**     | `queryv2_redux/run_manifest.json` (`n_pair_scores: 100`)   | rollup sums to 20×5 = 100                  |
| anchorsv2 | 24      | **116**     | `anchorsv2_redux/run_manifest.json` (`rollup_anchors: 24`) | rollup sums to 116 (22×5 + jina 4 + dvc 2) |


Representative queryv2 thin-anchor metadata means (`queryv2_redux/rollup_summary.csv`): jina-ai/serve **96.35**, ray-project/ray **92.31**, apache/airflow **95.36**, OpenBB **93.77** — all match `WORK_REVIEW.md` / `PAPER_PACKAGE.md`.

**Important nuance — anchorsv2 is partly bootstrapped (verified in `anchorsv2_redux/run_manifest.json`):** `n_pair_scores` for the run is **17**, with `anchors_scored_this_run = [mlflow/mlflow, pytorch/vision, scikit-learn/scikit-learn, treeverse/dvc]`. The remaining 20 shared slugs are **copied from `queryv2_redux/`** (17 identical) or **rescored** (3: apache/airflow, jina-ai/serve, ray-project/ray). I confirmed the copy by spot-checking identical means (e.g. EasyOCR 95.09, Lightning 94.35 appear in both rollups) and confirmed the 3 rescores differ (airflow 95.36→96.36, ray 92.31→90.38). So the "116 anchorsv2 scores" is **17 freshly-scored + 3 rescored + 96 reused** — not 116 independent computations. The docs disclose this ("17 shared slugs bootstrapped"), but the paper must state it plainly.

**Status (DEFERRED — re-attempted authenticated 2026-06-19, exceeded budget):** a full independent anchorsv2 rerun was attempted again on 2026-06-19 with a verified token on the real network (outside the sandbox), after clearing `results_benchmark/anchorsv2_redux/` so reused slugs would be re-scored rather than skipped:

```bash
export GITHUB_TOKEN="$(gh auth token)"
PYTHONPATH=. timeout 1500 bash tools/run_anchorsv2_redux.sh full
```

The token authenticated fine (core 4985/5000 at start) and the REDUX core loaded, but the `--fit-global` step — which extracts per-repo features (commit fetch + sentence-transformer commit embeddings on CPU) for **all ~140 unique anchor+proxy URLs** *before* any pair is scored — alone ran past the 25-minute budget. `timeout` killed it at 1500 s having written **zero** per-anchor CSVs, so there was **no partial/corrupted output**; the existing valid bootstrap outputs under `results_benchmark/anchorsv2_redux/` were **restored byte-for-byte from backup** (verified git-clean, rollup byte-identical). The REDUX metadata-mean rollup therefore remains the **17-fresh + 3-rescored + 96-reused bootstrap** described above — *not* an independent 24-anchor recompute.

What *was* re-verified on 2026-06-19: the retrieval-side stability number is computed offline from the frozen MetaMatch archives (no REDUX, no network) and `tools/anchorsv2_overlap.py` re-derives `anchorsv2_overlap.csv` **byte-identical** — mean top-5 Jaccard **0.9567**, **17/20** at 1.0, drift `explosion/spaCy` 0.667, `huggingface/datasets` 0.667, `jina-ai/serve` 0.80. So the anchor-stability claim is independently re-confirmed; only the REDUX similarity-mean rollup remains a bootstrap.

To finish the independent REDUX replication a future run needs either a longer time budget (the global feature-extraction fit on ~140 repos dominates) or a pre-warmed `.proxytool_cache/` so the fit is I/O-cheap.

**Honest assessment:** The bridge is the right idea and the numbers are reproducible from the archives. The weaknesses are real: (1) thin anchor pools — several anchors have very few qualified proxies (jina pool 3, dvc 2), so a 5-deep top-k is padded; (2) `metadata_only` scoring means the bridges report only one of four methods; (3) the bootstrap above means anchorsv2 is a *consistency check*, not an independent replication.

---

## 8. Component 5 — Labeled ground-truth evaluation (added layer)

**Purpose:** Replace the script-discovered `30_Pairs.json` "plausible" cohort with an **evidence-backed** 10-pair cohort and measure whether REDUX methods separate real matches from non-matches.

**Inputs:** `configs/labeled_benchmark_pairs.json` (seed, empty scores by design) → `results_benchmark/labeled_scored.json` (10 pairs scored). Cohort composition (verified in `labeled_scored.json`):


| Label              | Count | Examples                                                                      |
| ------------------ | ----- | ----------------------------------------------------------------------------- |
| `known_match`      | 5     | v8, blender, LibreOffice/core, libapps, freetype (official/read-only mirrors) |
| `known_related`    | 2     | MariaDB↔MySQL, LibreOffice↔OpenOffice (documented lineage)                    |
| `known_non_match`  | 2     | tensorflow↔django, vscode↔xgboost (hard negatives)                            |
| `target_uncertain` | 1     | MONAI↔tensorflow (realism only — *should be excluded from P/R/F1*)            |


**Outputs:** `labeled/labeled_strict_summary.csv`, `labeled/labeled_summary.csv`, `labeled/labeled_lenient_summary.csv`, per-pair `labeled/labeled_pair_table.csv`, threshold sweeps `labeled/threshold45/`, `labeled/threshold55/`.

**Key results — STRICT (`known_match` only, threshold 50), verified in `labeled_strict_summary.csv`:**


| Method         | Precision | Recall | F1       | Accuracy | Pos mean | Neg mean | Gap   |
| -------------- | --------- | ------ | -------- | -------- | -------- | -------- | ----- |
| metadata       | 1.00      | 1.00   | **1.00** | 1.00     | 94.4     | 6.25     | 88.16 |
| code_centric   | 1.00      | 1.00   | **1.00** | 1.00     | 100.0    | 14.67    | 85.33 |
| cross_language | 1.00      | 1.00   | **1.00** | 1.00     | 100.0    | 21.84    | 78.16 |
| dynamic        | 0.80      | 0.80   | **0.80** | 0.71     | 78.5     | 50.0     | 28.5  |


**Key results — LENIENT (threshold 50, `target_uncertain` excluded from P/R/F1), verified in `labeled_summary.csv` (now identical to `labeled_lenient_summary.csv`):**


| Method         | Precision | Recall | F1        | Accuracy | TP/FP/TN/FN |
| -------------- | --------- | ------ | --------- | -------- | ----------- |
| metadata       | 1.00      | 1.00   | **1.00**  | 1.00     | 7/0/2/0     |
| cross_language | 1.00      | 0.857  | **0.923** | 0.889    | 6/0/2/1     |
| code_centric   | 1.00      | 0.714  | **0.833** | 0.778    | 5/0/2/2     |
| dynamic        | 0.80      | 0.571  | **0.667** | 0.556    | 4/1/1/3     |


**(RESOLVED — was D1.)** Both lenient files now exclude the realism-only `target_uncertain` pair per the documented cohort rule, so `labeled_summary.csv` and `labeled_lenient_summary.csv` agree exactly. The single consistent **lenient metadata F1 = 1.00**. The earlier 0.93 figure came from silently counting `target_uncertain`'s metadata 58.33 as a false positive, which contradicted the stated exclusion rule; `tools/run_labeled_benchmark.py` was fixed to drop `target_uncertain` from the metric cohort.

**Honest assessment:** Strict separation is excellent and the right headline. The cohort is small (5/2/2/1 = 10 pairs), so a single mis-score swings F1 by ~0.1; the paper should report this as a *proof-of-concept separation*, not a population estimate. dynamic is genuinely weak and should be framed as a secondary signal.

---

## 9. Component 6 — Statistics (discrimination + cross-method Spearman)

**Discrimination (verified in `archives/metadata_diagnostics/metadata_discrimination_canonical.csv`):**


| Metric                     | Value      |
| -------------------------- | ---------- |
| Similar mean metadata %    | **94.444** |
| Dissimilar mean metadata % | **4.748**  |
| Gap                        | **89.697** |
| Pairwise AUC-like          | **1.0**    |
| FPR-like / TPR-like @ 50   | 0.0 / 1.0  |


Metadata cleanly separates similar from dissimilar cohorts (Test 2 functional-similar + 30-pair vs Test 3 dissimilar). Matches the documented ~94.4% vs ~4.7%.

**Cross-method agreement (verified in `projected_pairs/full_summary.json`, n=30):**


| Stat             | Value                    | Rubric (`configs/projected_pair_rubric.json` min 0.30) |
| ---------------- | ------------------------ | ------------------------------------------------------ |
| Spearman ρ       | **−0.2107** (p = 0.2636) | **FAILS**                                              |
| Pearson r        | −0.3507 (p = 0.0575)     | Fails                                                  |
| Paired t         | −0.114 (p = 0.910)       | n/a                                                    |
| TOST equivalence | equivalent = **true**    | passes equivalence band ±0.1                           |
| Decision `go`    | **false**                | agreement gates fail                                   |


**Authenticated re-run (2026-06-19) — captured separately, decision needs author sign-off.** The deferred authenticated regeneration was executed on the real network and saved to a **new** file so the frozen reference above is not destroyed:

```bash
export GITHUB_TOKEN="$(gh auth token)"
PYTHONPATH=. python3 scripts/projected_pair_pipeline.py --mode full --workers 1,2   # outside the sandbox
```

| Stat | Frozen `full_summary.json` (unauth, n=30) | Authenticated `full_summary_authenticated.json` (n=25) |
| ---- | ----------------------------------------- | ------------------------------------------------------ |
| Spearman ρ | −0.2107 (p=0.264) **FAILS** | **+0.7772 (p=4.87e-6) PASSES** |
| Pearson r | −0.3507 (p=0.057) Fails | **+0.7757 (p=5.24e-6) Passes** |
| Paired t | −0.114 (p=0.910) | 1.488 (p=0.150) |
| TOST equivalent | true | false |
| Decision `go` | **false** | **true** |
| Telemetry authenticated | false (30/79 = 38% HTTP 403) | **true** (5/54 = 9% HTTP 403; api_non_200_ratio 0.093) |
| n / allocation | 30 (uncertain 10) | 25 (uncertain 5 + known_related 5 in rubric; pipeline emits 25 rows) |

**Two confounded causes** drive the flip, so the comparison is *not* like-for-like: (a) **authentication** removes the 403 starvation that previously returned empty/garbage uncertain-pair search results; and (b) the committed `configs/projected_pair_rubric.json` `thirty_pair_allocation` has since changed (`target_uncertain` 10→5, `known_related` 5 added), so the documented command now yields **n=25**, not the frozen n=30. The Spearman is dominated by the 20 static control pairs (metadata vs cross-language), so reducing/cleaning the noisy uncertain pairs pushes ρ strongly positive. The comparator is also heterogeneous (cross-language for controls, 1/search-rank for uncertain rows), which limits how much weight this single ρ should carry either way.

**⚠ Author decision required:** the authenticated run **overturns the project's headline "methods don't agree (ρ negative)" finding**. This is too consequential to silently propagate, so `PAPER_PACKAGE.md`, `VALIDATION_MEMO.md`, `WORK_REVIEW.md`, etc. were **left citing the frozen ρ=−0.21**. Decide whether to (i) adopt the authenticated n=25 result as canonical (promote `full_summary_authenticated.json` → `full_summary.json` and rewrite the multi-view-agreement narrative to "methods agree, go=true"), or (ii) re-run with the original n=30 allocation for an apples-to-apples authenticated comparison before changing any paper claim. The labeled cohort, by contrast, was already authenticated (see §0).

---

## 10. Component 7 — Testing / CAIS case study

**File:** `results_benchmark/testing_case_study_airflow.md`. Bridges `apache/airflow` retrieval → REDUX similarity → CAIS test-scenario dimensions.

**Verified against `queryv2_redux/apache-airflow.csv`:** the case study cites feast-dev/feast 96.4, dagster-io/dagster 96.3, around-dataengineering 93.6; the CSV shows **96.36 / 96.27 / 93.64** — accurate. The top-3 by MetaMatch rank (feast, dagster, around-dataengineering) match the frozen `30_Matches.csv` ordering.

**Honest assessment:** This is a *single-anchor qualitative bridge*, explicitly labeled as "the minimum bridge from similarity → test-relevant outcomes." It is sufficient to answer the reviewer concern in principle but is not a quantitative testing-outcome evaluation. It does not replace domain safety cases, which the doc states.

---

## 11. Consolidated results tables (every headline number, with source)

### 11.1 Retrieval


| Claim                         | Value     | Source file                                |
| ----------------------------- | --------- | ------------------------------------------ |
| queryv2 top-5 magnets         | 0         | `runs/experiments/documentation/WINNER.md` |
| queryv2 Good/OK/Weak          | 20/0/0    | `WINNER.md`, `EXPERIMENT_LOG.md`           |
| anchorsv2 Good/OK/Weak        | 24/0/0    | `anchorsv2_spot_check.md`, `WINNER.md`     |
| Magnet trend (penalty 30→300) | 30→18→5→0 | `EXPERIMENT_LOG.md`                        |


### 11.2 Labeled ground truth (threshold 50)


| Method         | Strict F1 | Lenient F1 (`labeled_summary.csv`, `target_uncertain` excluded) | Source                                                              |
| -------------- | --------- | --------------------------------------------------------------- | ------------------------------------------------------------------- |
| metadata       | 1.00      | 1.00                                                            | `labeled/labeled_strict_summary.csv`, `labeled/labeled_summary.csv` |
| code_centric   | 1.00      | 0.833                                                           | same                                                                |
| cross_language | 1.00      | 0.923                                                           | same                                                                |
| dynamic        | 0.80      | 0.667                                                           | same                                                                |


### 11.3 REDUX bridges


| Claim                           | Value                  | Source                                                  |
| ------------------------------- | ---------------------- | ------------------------------------------------------- |
| queryv2 pair scores             | 100 (20×5)             | `queryv2_redux/rollup_summary.csv`, `run_manifest.json` |
| anchorsv2 pair scores           | 116 (24 anchors)       | `anchorsv2_redux/rollup_summary.csv`                    |
| anchorsv2 scored fresh this run | 17 (4 swapped anchors) | `anchorsv2_redux/run_manifest.json`                     |
| airflow metadata mean           | 95.36                  | `queryv2_redux/rollup_summary.csv`                      |


### 11.4 Stability & statistics


| Claim                          | Value                        | Source                                                                |
| ------------------------------ | ---------------------------- | --------------------------------------------------------------------- |
| anchorsv2 mean top-5 Jaccard   | 0.9567                       | `archives/metamatch_sensitivity/anchorsv2_overlap.csv`                |
| Identical slugs                | 17/20                        | same                                                                  |
| Similar vs dissimilar metadata | 94.444 vs 4.748 (gap 89.697) | `archives/metadata_diagnostics/metadata_discrimination_canonical.csv` |
| Cross-method Spearman ρ        | −0.2107 (p=0.264)            | `projected_pairs/full_summary.json`                                   |
| Pearson r                      | −0.3507 (p=0.057)            | same                                                                  |


---

## 12. Reproducibility status

**Reviewable from a fresh clone (no scoring needed):** all committed output artifacts — `labeled_scored.json`, everything under `labeled/`, both REDUX rollups + per-anchor CSVs, `anchorsv2_overlap.csv` and its archive target, the discrimination CSV, `run_manifest.json`, and (notably) `**projected_pairs/full_summary.json` is tracked despite being listed in `.gitignore`** — so the Spearman stats survive a clone.

**Now reproducible from a fresh clone (RESOLVED — verified via `git ls-files`, 2026-06-18):**


| Needed to re-score                          | Tracked? | Notes                                                       |
| ------------------------------------------- | -------- | ----------------------------------------------------------- |
| `proxytool_redux/_extracted/redux4_core.py` | **Yes**  | 180 KB scoring engine now committed                         |
| `proxytool_redux/_extracted/__init__.py`    | **Yes**  | package marker                                              |
| `proxytool_redux/benchmark.py`              | **Yes**  | benchmark runner                                            |
| `proxytool_redux/benchmark_metrics.py`      | **Yes**  | labeled scorers import this                                 |
| `proxytool_redux/bootstrap.py`              | **Yes**  | feature globals / core loader                               |
| `proxytool_redux/__init__.py`, `scoring.py` | Yes      | (already tracked)                                           |
| `scripts/extract_redux4_core.py`            | **Yes**  | regenerates `redux4_core.py` deterministically              |
| `scripts/run_repro_benchmark.py`            | **Yes**  | runs `run_all_benchmarks()`                                 |
| `REDUX_REPRO.md`                            | **Yes**  | reproduction runbook                                        |
| `proxytool_redux/proxytool.ipynb` (7 MB)    | No       | intentionally excluded (large); not needed to re-score      |


A fresh clone can now re-score with `PYTHONPATH=. python3 tools/score_labeled_benchmark_redux.py --live` (requires `GITHUB_TOKEN` for live pairs). The blanket `proxytool_redux/`, `scripts/`, `REDUX_REPRO.md`, and `results_benchmark/projected_pairs/` entries in `.gitignore` were reconciled so the gitignore matches what is actually tracked.

**Original symptom now cleared (re-confirmed 2026-06-19):** `labeled_scored.json` → `related_mariadb_mysql` previously carried `"score_error": "No module named 'proxytool_redux'"` (a missing `PYTHONPATH=.`, not a true scoring failure). It was re-scored authenticated (`export GITHUB_TOKEN="$(gh auth token)"`); the error key is gone and verified live values are metadata 54.36, code_centric 44.15, dynamic 7.5, cross_language 42.21 (`score_source = live_redux`). All other 9 pairs are byte-identical to the prior file. **Re-verified 2026-06-19** by re-running `PYTHONPATH=. python3 tools/score_labeled_benchmark_redux.py --benchmark configs/labeled_benchmark_pairs.json --live --max-commits 150` on the real network (to a temp file for safe diffing): **10/10 pairs scored, no `score_error`, all values byte-identical** to the on-disk file, so `labeled_scored.json` was left untouched.

**Repro fingerprints (`run_manifest.json`):** `benchmark_manifest_sha256 = c85d9d2011dfa748463a73e257391e5364cfb9dc53ceb8f2dff1e53ad569ae0e`; `hyperparams_sha256 = e5c736c70c35fccf94098b5f26b33ae96ae435b4a018fb6e386e46134b8066f4`. The manifest snapshot itself still records `github_token_present: false`/`gh_authenticated: false` (it was not regenerated, to preserve the cited fingerprints); note that `gh auth status` reports a keyring warning even though `gh auth token` yields a working token (verified core limit 5000/5000). Steps needing GitHub commit fetches should export `GITHUB_TOKEN="$(gh auth token)"` first.

---

## 13. Cross-verification index (claim → source)


| #   | Claim                                              | Verified in                                                           | Status                |
| --- | -------------------------------------------------- | --------------------------------------------------------------------- | --------------------- |
| 1   | Strict metadata/code/x-lang F1 = 1.0; dynamic 0.80 | `labeled/labeled_strict_summary.csv`                                  | ✅ exact               |
| 2   | Lenient metadata 1.00 / dynamic 0.667 (`target_uncertain` excluded) | `labeled/labeled_summary.csv` ≡ `labeled_lenient_summary.csv`        | ✅ exact (D1 resolved) |
| 3   | queryv2 = 100 pair scores, 20 anchors              | `queryv2_redux/rollup_summary.csv`, `run_manifest.json`               | ✅ exact               |
| 4   | anchorsv2 = 116 pair scores, 24 anchors            | `anchorsv2_redux/rollup_summary.csv`                                  | ✅ exact               |
| 5   | anchorsv2 mean Jaccard ~0.96, 17/20 at 1.0         | `archives/metamatch_sensitivity/anchorsv2_overlap.csv`                | ✅ 0.9567              |
| 6   | Drift: spaCy & datasets 0.67, jina 0.80            | same                                                                  | ✅ exact               |
| 7   | Discrimination 94.4% vs 4.7%                       | `archives/metadata_diagnostics/metadata_discrimination_canonical.csv` | ✅ 94.444 / 4.748      |
| 8   | Spearman ρ ≈ −0.21 (p≈0.26)                        | `projected_pairs/full_summary.json`                                   | ✅ −0.2107 / 0.264     |
| 9   | queryv2 winner 0 magnets, 20/0/0                   | `runs/experiments/documentation/WINNER.md`                            | ✅ exact               |
| 10  | airflow proxies feast/dagster ~96                  | `queryv2_redux/apache-airflow.csv`                                    | ✅ 96.36 / 96.27       |
| 11  | Cohort = 5/2/2/1 labeled pairs                     | `labeled_scored.json`                                                 | ✅ exact               |
| 12  | Run manifest SHA256 fingerprints                   | `run_manifest.json`                                                   | ✅ exact               |
| 13  | anchorsv2 17 fresh + bootstrap                     | `anchorsv2_redux/run_manifest.json`                                   | ✅ `n_pair_scores:17`  |
| 14  | REDUX core now tracked                             | `git ls-files proxytool_redux/` → 7 files (core + runners)            | ✅ resolved            |
| 15  | "Lenient" metadata F1 now single value (1.00)      | `labeled_summary.csv` ≡ `labeled_lenient_summary.csv`                 | ✅ resolved (D1)       |
| 16  | MariaDB/MySQL `score_error` cleared (live rescore) | `labeled_scored.json` (no `score_error`; `score_source=live_redux`)   | ✅ resolved (D2); re-confirmed 2026-06-19 (10/10, byte-identical) |
| 17  | Authenticated projected-pair re-run captured        | `projected_pairs/full_summary_authenticated.json` (`authenticated:true`) | ✅ ρ=+0.7772 / p=4.87e-6 (n=25; flips decision — author sign-off) |
| 18  | Frozen unauth projected-pair reference preserved    | `projected_pairs/full_summary.json` (`authenticated:false`)           | ✅ unchanged ρ=−0.2107 |
| 19  | anchorsv2 retrieval Jaccard re-derived offline      | `archives/metamatch_sensitivity/anchorsv2_overlap.csv`               | ✅ byte-identical 0.9567 / 17-of-20 (2026-06-19) |


---

## 14. Discrepancies found (docs vs data)

**D1 — Two conflicting "lenient" metadata F1 values (0.93 vs 1.00). — RESOLVED.**
The cause (confirmed by reading `proxytool_redux/benchmark_metrics.py::compute_pair_classification_metrics`): the old `run_labeled_benchmark.py` output (`labeled_summary.csv`) treated the `target_uncertain` MONAI↔tensorflow pair as a de-facto negative — its metadata score 58.33 ≥ 50 became a **false positive** (TP/FP/TN/FN = 7/1/2/0), dragging precision to 0.875 and F1 to 0.933 — while `labeled_strict_metrics.py` (`labeled_lenient_summary.csv`) correctly **excluded** `target_uncertain` (7/0/2/0 → F1 = 1.00). **Fix applied:** `tools/run_labeled_benchmark.py` now drops `target_uncertain` from the metric cohort (constant `EXCLUDE_FROM_METRICS`), matching the documented rule and `labeled_strict_metrics.py`. After regeneration, `labeled_summary.csv` and `labeled_lenient_summary.csv` are identical and the single consistent **lenient metadata F1 = 1.00** (code_centric 0.833, cross_language 0.923, dynamic 0.667). All threshold sweeps (`threshold45/`, `threshold55/`) were regenerated too, and every doc (`VALIDATION_MEMO.md`, `PAPER_PACKAGE.md`, `WORK_REVIEW.md`, `RESULTS_REVIEW.md`, this file) now cites 1.00.

**D2 — A labeled pair carried a scoring error yet showed scores. — RESOLVED.**
`labeled_scored.json` → `related_mariadb_mysql` previously had `"score_source": "live_redux"` **and** `"score_error": "No module named 'proxytool_redux'"`. Root cause: the live fill was run without `PYTHONPATH=.`, so the (then-untracked, but present-on-disk) package could not be imported. **Fix applied:** with the REDUX core now tracked and `PYTHONPATH=.` set, the pair was re-scored live and authenticated (`export GITHUB_TOKEN="$(gh auth token)"`). The `score_error` key is gone; verified values are metadata 54.36, code_centric 44.15 (was 44.02), dynamic 7.5, cross_language 42.21 — confirming the earlier values were essentially correct but now verified by a successful live REDUX run. The other 9 pairs are byte-identical, so no valid data was disturbed.

**Minor note (not a discrepancy):** the `rollup_summary.csv` files set `thin_pool = False` for the four anchors the spot-check memos call "thin" (jina/ray/airflow/OpenBB in queryv2). The narrative "thin anchor" language refers to small *final-30 unique pools* from the retrieval scorecard, not the rollup's `thin_pool` flag (which only trips when top-k < 5, e.g. anchorsv2 jina n=4, dvc n=2). The terms are consistent once you know this, but the paper should define "thin" once.

---

## 15. Repo hygiene assessment & cleanup recommendations

The repo is large (4,670 git-tracked files) and carries substantial historical sprawl. Using `REPO_AUDIT.md` plus direct inspection:

**Actively used (the minimal paper package — ~22 paths + 8 tools):**

- Configs: `configs/labeled_benchmark_pairs.json`, `configs/projected_pair_rubric.json`, `metamatch_hyperparams.json`
- Frozen archives: `runs/experiments/penalty300_min700_cap22_queryv2/`, `…_anchorsv2/`
- Outputs: `labeled_scored.json`, `labeled/labeled_summary.csv`, `labeled/labeled_strict_summary.csv`, `run_manifest.json`, `repo_access_validation.csv`, `queryv2_redux/rollup_summary.csv` (+ `run_manifest.json`), `anchorsv2_redux/rollup_summary.csv`, `anchorsv2_overlap.csv`, `metadata_discrimination_canonical.csv`, `three_test_argument_table.csv`, `projected_pairs/full_summary.json`
- Narrative: `WORK_REVIEW.md`, `VALIDATION_MEMO.md`, `PAPER_PACKAGE.md`, `runs/experiments/documentation/WINNER.md`, `testing_case_study_airflow.md`
- Tools (8): `write_run_manifest.py`, `verify_repo_access.py`, `score_labeled_benchmark_redux.py`, `run_labeled_benchmark.py`, `labeled_strict_metrics.py`, `score_metamatch_proxies_redux.py`, `anchorsv2_overlap.py`, `run_anchorsv2_redux.sh`

**Historical / archive-only (keep, but mark as not-for-repro):**

- 20 grid-history experiment folders under `runs/experiments/penalty{30,55,75,100,110,150,175,200,250,275}_`* (winner already selected)
- `results_benchmark/archives/redux4_sweep/` (~40 coverage/temperature CSVs), `archives/custom_30_pairs/`
- `results_benchmark/_before_repro_run/` (3 CSVs duplicating `archives/` targets)
- 6 of 7 root REDUX notebooks (`proxytool*.ipynb` ≈ 5 MB each; only REDUX 4 is live)
- `Run-MetaMatchPipeline_old.ps1`, `configs/30_Pairs_*.json`, `configs/*_old.json`, `tmp_rubric_low_volume.json`
- `runs/2026-05-0{1,2,3}-*` live batch outputs (gitignored)

**Gitignored but cited (RESOLVED 2026-06-18):**

- `proxytool_redux/` — REDUX core now tracked (`redux4_core.py`, `_extracted/__init__.py`, `benchmark.py`, `benchmark_metrics.py`, `bootstrap.py`, plus pre-existing `__init__.py`/`scoring.py`); only the 7 MB `proxytool.ipynb` stays ignored.
- `scripts/` — `extract_redux4_core.py` and `run_repro_benchmark.py` now tracked (7 of 7 source files); `results_plots/`, `analysis/` remain local-only by design.
- `results_benchmark/projected_pairs/` — removed from `.gitignore`; the 6 tracked files now match the gitignore (no more contradiction).

**Concrete cleanup recommendations (DO NOT delete now — recommendations only):**


| Priority | Action                                                                                                                                                                                                                                                 | Why                                                             |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------- |
| 1 ✅DONE | **`proxytool_redux/` tracking story fixed** — core committed (`redux4_core.py`, `benchmark*.py`, `bootstrap.py`, `_extracted/__init__.py`) plus `scripts/extract_redux4_core.py` for deterministic regeneration                                          | Reviewers can now reproduce; D2 fixed                           |
| 2 ✅DONE | Reconciled `.gitignore` with reality for `projected_pairs/` and `scripts/` (un-ignored; now match what is tracked)                                                                                                                                     | Silent drift removed                                            |
| 3 ✅DONE | Resolved discrepancy D1 (single "lenient" definition, `target_uncertain` excluded) and regenerated the affected tables                                                                                                                                 | One consistent lenient F1 (1.00)                                |
| 4        | Move 6 stale root notebooks (~30 MB) to an `archive/notebooks/` folder or Git LFS                                                                                                                                                                      | Repo bloat; only REDUX 4 is live                                |
| 5        | Remove `results_benchmark/_before_repro_run/` after confirming it duplicates `archives/`                                                                                                                                                               | Pure duplicate snapshot                                         |
| 6        | Add a one-line "archive-only, do not re-run" banner to the 20 grid-history folders                                                                                                                                                                     | Prevents accidental re-runs (G8 = no retune)                    |
| 7 ✅DONE | Re-scored `related_mariadb_mysql` with REDUX present + token (authenticated live run)                                                                                                                                                                  | `score_error` artifact removed                                  |


---

## 16. Gaps, weaknesses, and risks (honest)

1. **~~Gitignored REDUX core (highest risk).~~ RESOLVED.** The scoring engine (`redux4_core.py`, `benchmark.py`, `benchmark_metrics.py`, `bootstrap.py`) is now git-tracked; a clean clone can re-score with `PYTHONPATH=.`. The D2 failure is fixed.
2. **Cross-method Spearman — frozen unauth ρ=−0.21 fails the rubric; authenticated re-run flips it to +0.78 (decision pending).** The frozen unauthenticated n=30 run gives ρ=−0.21 (fails 0.30); the 2026-06-19 authenticated n=25 re-run gives ρ=+0.78 (`go`=true). The two are confounded by authentication *and* a rubric allocation change (n 30→25), so they are not apples-to-apples. **This needs the author's decision** (see §9) before the paper's "complementary, non-corroborating methods" framing is kept or reversed.
3. **anchorsv2 is partly bootstrapped (full REDUX rerun still DEFERRED).** Only 17 of 24 anchors were freshly scored; 96 of 116 REDUX "scores" are reused from queryv2. The 2026-06-19 authenticated re-attempt exceeded the 25-min budget at the global feature-extraction fit and was killed with no partial output (bootstrap restored byte-identical). The retrieval-side Jaccard (0.9567, 17/20) *was* re-verified offline. The REDUX similarity rollup remains a consistency check, not independent replication; command + caveats in §7.
4. **Tiny labeled cohort.** 10 pairs (5/2/2/1). Strict F1 = 1.0 is a clean *separation demonstration*, not a population-level accuracy estimate; one mis-score moves F1 ~0.1.
5. **Thin anchor pools.** Several anchors have <5 qualified proxies; top-5 is padded, weakening per-anchor REDUX means (jina, ray, dvc).
6. **Unauthenticated stat runs (now addressed; outcome pending decision).** The labeled cohort was re-scored authenticated, and on 2026-06-19 the projected-pair pipeline was also re-run authenticated → `projected_pairs/full_summary_authenticated.json` (telemetry `authenticated=true`). The frozen unauthenticated `full_summary.json` and `run_manifest.json` are preserved. The authenticated result materially changes the Spearman conclusion (§9) and awaits author sign-off before being promoted to canonical.
7. **Retrieval tuning overfit risk.** queryv2 query overrides were tuned per-anchor on the same 20 anchors used for selection; anchorsv2 mitigates but does not eliminate this.
8. **Doc sprawl.** 23 markdown files with overlapping gate tables invite drift (D1 is exactly this). `WORK_REVIEW.md` is the SoT but the others duplicate metrics.
9. **dynamic method is weak.** F1 0.667 (lenient) / 0.80 (strict); it should be framed as secondary, not co-equal.
10. **Bridges report metadata only.** `--metadata-only` means the retrieval→similarity story rests on one of four methods.

---

## 17. What to do next (prioritized)

**P0 — Make it reproducible (blocks publication credibility):**

1. **DONE.** REDUX core committed (`redux4_core.py`, `benchmark.py`, `benchmark_metrics.py`, `bootstrap.py` + `scripts/extract_redux4_core.py`, `run_repro_benchmark.py`, `REDUX_REPRO.md`). A fresh clone runs `PYTHONPATH=. python3 tools/labeled_strict_metrics.py` without `ModuleNotFoundError`.
2. **DONE (authenticated) — projected-pair decision pending.** Labeled scoring re-run authenticated; `related_mariadb_mysql` `score_error` cleared and re-confirmed 2026-06-19. The projected-pair pipeline was regenerated authenticated 2026-06-19 → `projected_pairs/full_summary_authenticated.json` (frozen `full_summary.json` preserved); the result flips the decision and awaits author sign-off (§9). `run_manifest.json` left as the frozen fingerprint snapshot.

**P1 — Fix the two discrepancies (blocks paper accuracy):**
3. **DONE.** D1 resolved by excluding `target_uncertain` per the stated rule → lenient metadata F1 = 1.0; `labeled_summary.csv` ≡ `labeled_lenient_summary.csv`; all docs re-cite consistently.
4. **DONE.** D2 resolved — MariaDB/MySQL re-scored live + authenticated, `score_error` removed.

**P2 — Strengthen the claims you already make:**
5. **STILL DEFERRED (re-attempted 2026-06-19).** The **full independent** anchorsv2 REDUX rerun (`export GITHUB_TOKEN="$(gh auth token)" && PYTHONPATH=. timeout 1500 bash tools/run_anchorsv2_redux.sh full`, dir cleared first) was re-attempted authenticated on the real network but the global feature-extraction fit on ~140 repos exceeded the 25-min budget and was killed with no partial output; the bootstrap was restored byte-identical. Needs a longer budget or a pre-warmed `.proxytool_cache/`. The retrieval-side Jaccard was re-verified offline (0.9567, 17/20).
6. Expand the labeled cohort from 10 → ~20–30 evidence-backed pairs (more mirrors + more hard negatives) to make F1 a meaningful estimate rather than a separation demo.
7. Score the REDUX bridges on **all four methods**, not metadata-only, so retrieval→similarity is reported multi-view (matching the "complementary methods" framing).

**P3 — Hygiene & paper packaging:**
8. Reconcile `.gitignore` with what is actually tracked (`projected_pairs/`, `scripts/`); add "archive-only" banners to the 20 grid folders; relocate the 6 stale notebooks.
9. Ship the **minimal paper package** (~22 paths + 8 tools) as the reviewer bundle and point everyone to `WORK_REVIEW.md` + this `MASTER_EVALUATION.md` as the two entry documents.
10. In the paper, lead with strict separation + retrieval hygiene + anchor stability; report Spearman as an explicit multi-view (non-redundancy) finding rather than burying it.

---

## 18. Related documents


| Document                                   | Role                                         |
| ------------------------------------------ | -------------------------------------------- |
| `results_benchmark/WORK_REVIEW.md`         | Master phase table A–G, tags, repro commands |
| `results_benchmark/VALIDATION_MEMO.md`     | Reviewer-response statistics backbone        |
| `results_benchmark/PAPER_PACKAGE.md`       | Decision gates G1–G8 + limitations           |
| `results_benchmark/REPO_AUDIT.md`          | Used-vs-sprawl inventory                     |
| `results_benchmark/RESULTS_REVIEW.md`      | Output-file navigator                        |
| `runs/experiments/documentation/WINNER.md` | MetaMatch scorecard                          |
| `REDUX_REPRO.md`                           | REDUX 4 reproduction runbook (now tracked)   |


*This document was produced by reading and re-deriving every cited number from the files listed. Where a value could not be independently confirmed (e.g. the MariaDB/MySQL scores behind a `score_error`), it is flagged as unverified rather than asserted.*