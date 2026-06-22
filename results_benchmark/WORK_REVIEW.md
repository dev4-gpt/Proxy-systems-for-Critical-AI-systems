# CAIS / MetaMatch Validation — Work Review

**Repository:** `mdk5293/Proxy-systems-for-Critical-AI-systems` (repo root = working directory for all commands below)  
**Master document:** `results_benchmark/WORK_REVIEW.md`

This file is the single source of truth for what was run, reused, tagged, and verified in the validation pass. Share the repository path and this document so reviewers can reproduce commands and cross-check claims without a separate Word table.

---

## Executive summary

This validation pass integrates **supplied ground-truth infrastructure** with **pre-existing MetaMatch Phase 2 results** (`penalty300_min700_cap22_queryv2` winner and `penalty300_min700_cap22_anchorsv2` sensitivity archive). It does **not** re-run the MetaMatch grid or re-archive queryv2. Instead, it **executes** the labeled-benchmark pipeline, **bridges** frozen retrieval outputs to REDUX proxy similarity, and **documents** honest statistics for paper gates.


| Goal                           | Outcome                                                                                                                                                                                           |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Evidence-backed labeled cohort | 10 pairs in `configs/labeled_benchmark_pairs.json` → scored in `labeled_scored.json` → metrics in `labeled/`                                                                                      |
| Retrieval → similarity bridge  | 100 metadata proxy scores in `queryv2_redux/`; anchorsv2 overlap + REDUX in `anchorsv2_redux/`                                                                                                    |
| Honest statistics              | Metadata discrimination ~94% vs ~5%; cross-method Spearman **ρ ≈ +0.69** (authenticated n=30, canonical, passes rubric 0.30; the earlier ρ ≈ −0.21 was an unauthenticated rate-limiting artifact) |
| Paper gates                    | G1–G8 **PASS** (G4 passes on authenticated data); G8 **no MetaMatch retune** (`PAPER_PACKAGE.md`)                                                                                                 |



| #                                       | Concern                                                                            | Response in this pass                                                                                                                                                                                                                          |
| --------------------------------------- | ---------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1 — Ground truth**                    | `30_Pairs.json` plausible pairs are script-discovered realism, not verified labels | Evidence-backed cohort in `configs/labeled_benchmark_pairs.json` -> scored in `results_benchmark/labeled_scored.json` -> metrics in `results_benchmark/labeled/`                                                                               |
| **2 — Testing / QA relevance**          | Similarity must connect to test-relevant outcomes, not retrieval hygiene alone     | queryv2 spot-check + REDUX proxy bridge (`queryv2_redux/`, `anchorsv2_redux/`) + airflow case study                                                                                                                                            |
| **3 — Statistics & method positioning** | Cross-method agreement and discrimination must be reported honestly                | `VALIDATION_MEMO.md` synthesizes labeled metrics, discrimination tables, and canonical authenticated Spearman ρ ≈ +0.69 (n=30, passes rubric 0.30); the earlier ρ ≈ −0.21 is documented as a superseded unauthenticated rate-limiting artifact |


**What was executed:** repro manifest, repo access check, labeled REDUX scoring, threshold/strict metrics, queryv2 + anchorsv2 proxy REDUX bridges, overlap analysis.

**What was reused (read-only):** frozen `runs/experiments/penalty300_min700_cap22_queryv2/`, historical REDUX CSVs (`three_test_argument_table.csv`, `metadata_discrimination_canonical.csv`), the projected-pair stats (canonical authenticated `projected_pairs/full_summary_authenticated_n30.json`; superseded unauthenticated `projected_pairs/full_summary.json` kept for transparency), WINNER arc docs.

---

## Tag legend

Every command row in the phase table carries a **source tag**. 


| Tag                | Meaning                                                      | Examples                                                                                                                                                                                                                                               |
| ------------------ | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **[Reproducible]** | Ground-truth and reproducibility layer                       | `configs/labeled_benchmark_pairs.json`, `write_run_manifest.py`, `verify_repo_access.py`, `run_labeled_benchmark.py`, `benchmark_metrics`, `score_labeled_benchmark_redux.py`, `labeled_strict_metrics.py`, `labeled_scored.json`, `run_manifest.json` |
| **[Anchor/Query]** | MetaMatch retrieval + queryv2 bridge on frozen experiments   | `metamatch_hyperparams.json`, `score_metamatch_proxies_redux.py`, `anchorsv2_overlap.py`, `run_anchorsv2_redux.sh`, `queryv2_redux/`, spot-check memos tied to frozen `30_Matches.csv` archives                                                        |
| **[Pre-existing]** | Prior REDUX paper benchmarks and WINNER arc before this pass | `runs/experiments/penalty300_min700_cap22_queryv2/`, `WINNER.md`, `metadata_discrimination_canonical.csv`, `three_test_argument_table.csv`                                                                                                             |
| **[Analysis]**     | Memos and docs synthesizing results (no scoring command)     | `VALIDATION_MEMO.md`, `PAPER_PACKAGE.md`, `testing_case_study_airflow.md`, `queryv2_spot_check.md`                                                                                                                                                     |


**Key distinction:** `score_labeled_benchmark_redux.py` is **[Reproducible]** — it fills `labeled_scored.json` from cached REDUX tables plus optional live REDUX. The seed manifest (`configs/labeled_benchmark_pairs.json`) ships with empty score fields; `run_labeled_benchmark.py` expects a scored file.

---

## What was NOT done


| Item                                                  | Why omitted                                                                            |
| ----------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Re-archive / re-run `penalty300_min700_cap22_queryv2` | Frozen winner under `runs/experiments/`; read-only input to proxy REDUX and spot-check |
| New penalty-grid MetaMatch sweep                      | Phase 2 grid complete; gate G8 = **no retune**                                         |
| Claim `30_Pairs.json` as ground truth                 | Plausible cohort only; use `labeled_scored.json` + explicit limitations                |
| Equate magnets / Good-OK-Weak with test adequacy      | Retrieval hygiene metrics only                                                         |
| Regenerate all historical REDUX CSVs                  | Canonical tables reused in memo and labeled scoring                                    |
| Write `generated_at_utc` into config files            | Timestamp lives only in `results_benchmark/run_manifest.json`                          |
| Modify frozen experiment scores/ranks                 | Cosmetic Description/Notes encoding fixes only where safe                              |


---

## What was pre-existing


| Path                                                                    | Role                                                                                           |
| ----------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `runs/experiments/penalty300_min700_cap22_queryv2/`                     | MetaMatch winner: 0 top-5 magnets, 20/0/0 Good/OK/Weak                                         |
| `runs/experiments/penalty300_min700_cap22_anchorsv2/`                   | Anchor-list sensitivity (24 anchors, 4 swaps)                                                  |
| `runs/experiments/documentation/WINNER.md`                              | Experiment scorecard and recommended defaults                                                  |
| `runs/experiments/documentation/PHASE2_NOTES.md`                        | Phase 2 narrative and anchor swaps                                                             |
| `results_benchmark/metadata_discrimination_canonical.csv`               | Similar vs dissimilar discrimination (symlink → `archives/`)                                   |
| `results_benchmark/three_test_argument_table.csv`                       | REDUX cache for labeled scoring (symlink → `archives/`)                                        |
| `results_benchmark/projected_pairs/full_summary_authenticated_n30.json` | **Canonical** cross-method Spearman / Pearson (authenticated, n=30): ρ=+0.69, go=true          |
| `results_benchmark/projected_pairs/full_summary.json`                   | Superseded **unauthenticated** cross-method run (ρ=−0.21, 38% 403) — retained for transparency |
| `metamatch_hyperparams.json`                                            | Winner hyperparams (penalty 300, min 700, cap 2/2)                                             |


---

## Phase table — A through G

All commands assume **repo root** as working directory.

**Auth note:** REDUX commit-fetch steps need GitHub API access:

```bash
export GITHUB_TOKEN="$(gh auth token)"
export PYTHONPATH=.
```

Smoke / manifest steps do not require a token but should be re-run after auth is fixed for an accurate snapshot.


| #     | Phase                  | Command                                                                                                                                                            | Primary outputs                                                                    | Result headline                                                                                                          | Source                              |
| ----- | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ----------------------------------- |
| **A** | Repro smoke            | `python3 tools/write_run_manifest.py`                                                                                                                              | `results_benchmark/run_manifest.json`                                              | SHA256 fingerprints of seed manifest + hyperparams; `generated_at_utc` + GitHub env snapshot                             | **[Reproducible]**                  |
| **A** | Repo access            | `python3 tools/verify_repo_access.py --benchmark configs/labeled_benchmark_pairs.json --skip-clone`                                                                | `results_benchmark/repo_access_validation.csv`                                     | 18 unique repo URLs checked via `git ls-remote` (no clone)                                                               | **[Reproducible]**                  |
| **B** | Score labeled pairs    | `PYTHONPATH=. python3 tools/score_labeled_benchmark_redux.py`                                                                                                      | `results_benchmark/labeled_scored.json`                                            | 10/10 pairs scored; most from cached REDUX tables (`score_source` per pair)                                              | **[Reproducible]**                  |
| **B** | Live REDUX gap-fill    | `PYTHONPATH=. python3 tools/score_labeled_benchmark_redux.py --live`                                                                                               | updates `labeled_scored.json`                                                      | Remaining pairs (e.g. MariaDB/MySQL) filled via live GitHub REDUX                                                        | **[Reproducible]**                  |
| **B** | Labeled metrics @50    | `PYTHONPATH=. python3 tools/run_labeled_benchmark.py --benchmark results_benchmark/labeled_scored.json --threshold 50 --output-dir results_benchmark/labeled`      | `labeled/labeled_pair_table.csv`, `labeled_summary.csv`, `labeled_claim_checks.md` | Lenient cohort (`target_uncertain` excluded): metadata **F1 = 1.00**, accuracy 1.00 @ threshold **50** (percent scale)   | **[Reproducible]**                  |
| **B** | Threshold 45 / 55      | Same with `--threshold 45/55` and output dirs `labeled/threshold45`, `labeled/threshold55`                                                                         | threshold sensitivity tables                                                       | Sensitivity @ 45 and 55                                                                                                  | **[Reproducible]**                  |
| **B** | Strict vs lenient      | `PYTHONPATH=. python3 tools/labeled_strict_metrics.py --benchmark results_benchmark/labeled_scored.json --threshold 50 --output-dir results_benchmark/labeled`     | `labeled_strict_summary.csv`, `labeled_lenient_summary.csv`                        | **Strict** (`known_match` only): metadata/code_centric/cross_language **F1 = 1.0**; dynamic F1 = 0.80                    | **[Reproducible]**                  |
| **C** | Stats memo             | *(no command)*                                                                                                                                                     | `results_benchmark/VALIDATION_MEMO.md`                                             | Discrimination ~94% vs ~5%; canonical authenticated Spearman **ρ ≈ +0.69** (n=30, go=true); labeled + method positioning | **[Analysis]** + **[Pre-existing]** |
| **D** | Spot-check retrieval   | *(read-only inspection)*                                                                                                                                           | `results_benchmark/queryv2_spot_check.md`                                          | Top-5 proxies for jina, ray, airflow, OpenBB in frozen `30_Matches.csv` archives                                         | **[Analysis]** + **[Pre-existing]** |
| **D** | Pilot proxy REDUX      | `PYTHONPATH=. python3 tools/score_metamatch_proxies_redux.py --pilot-only --top-k 5 --max-commits 60 --fit-global`                                                 | `queryv2_redux/*.csv` (4 thin anchors)                                             | 20 pair scores (4×5); 4 methods in pilot                                                                                 | **[Anchor/Query]**                  |
| **D** | Full proxy REDUX       | `PYTHONPATH=. python3 tools/score_metamatch_proxies_redux.py --top-k 5 --max-commits 50 --fit-global --metadata-only --output-dir results_benchmark/queryv2_redux` | 20 anchor CSVs, `rollup_summary.csv`, `run_manifest.json`                          | **100** metadata pair scores; thin-anchor means: jina **96.4%**, ray **92.3%**, airflow **95.4%**, OpenBB **93.8%**      | **[Anchor/Query]**                  |
| **E** | Testing case study     | *(no command)*                                                                                                                                                     | `results_benchmark/testing_case_study_airflow.md`                                  | Links `apache/airflow` top proxies + metadata REDUX to orchestration test dimensions                                     | **[Analysis]**                      |
| **F** | anchorsv2 overlap      | `PYTHONPATH=. python3 tools/anchorsv2_overlap.py`                                                                                                                  | `results_benchmark/anchorsv2_overlap.csv`                                          | **20** shared folder slugs; mean top-5 **Jaccard = 0.96** (17/20 at 1.0)                                                 | **[Anchor/Query]**                  |
| **F** | anchorsv2 REDUX bridge | `bash tools/run_anchorsv2_redux.sh all`                                                                                                                            | `results_benchmark/anchorsv2_redux/`                                               | Same REDUX bridge for anchorsv2 archive (24 anchors + rollup)                                                            | **[Anchor/Query]**                  |
| **G** | Decision gates         | *(no command)*                                                                                                                                                     | `results_benchmark/PAPER_PACKAGE.md`                                               | Gates G1–G8 **PASS** (G4 passes on authenticated data); G8 **no MetaMatch retune**                                       | **[Analysis]**                      |


---

## What was run vs reused


| Category            | Run in this pass                                                        | Reused read-only                                                                                                                                                    |
| ------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Ground truth        | `labeled_scored.json`, `labeled/` metrics, `repo_access_validation.csv` | Seed `labeled_benchmark_pairs.json` (content static)                                                                                                                |
| MetaMatch retrieval | —                                                                       | `penalty300_min700_cap22_queryv2/`, `penalty300_min700_cap22_anchorsv2/`                                                                                            |
| REDUX bridges       | `queryv2_redux/`, `anchorsv2_redux/`, overlap CSV                       | Cached rows in `three_test_argument_table.csv` for labeled scoring                                                                                                  |
| Statistics          | Strict/lenient summaries, threshold sweeps                              | `metadata_discrimination_canonical.csv`, `projected_pairs/full_summary_authenticated_n30.json` (canonical), `projected_pairs/full_summary.json` (superseded unauth) |
| Narrative           | Spot-check, case study, gate memo updates                               | `WINNER.md`, `PHASE2_NOTES.md`                                                                                                                                      |


---

## Inputs / configs


| File                                    | Role                                                      | `generated_at_utc`?                               | Source                                  |
| --------------------------------------- | --------------------------------------------------------- | ------------------------------------------------- | --------------------------------------- |
| `configs/labeled_benchmark_pairs.json`  | Seed manifest — 10 pairs, empty score fields by design    | **No** — fingerprinted via SHA256 in run manifest | **[Reproducible]**                      |
| `results_benchmark/labeled_scored.json` | Scored manifest — 0–100 method scores + `score_source`    | **No**                                            | **[Reproducible]**                      |
| `metamatch_hyperparams.json`            | Winner config — penalty 300, min 700, cap 2/2             | **No**                                            | **[Anchor/Query]** / pinned by manifest |
| `results_benchmark/run_manifest.json`   | Repro snapshot — auth state, SHA256 of seed + hyperparams | **Yes** — timestamp lives **only here**           | **[Reproducible]**                      |


`write_run_manifest.py` reads config paths, hashes bytes, writes the manifest. It does **not** modify seed or hyperparam files.

**Current manifest fingerprints** (verify in `run_manifest.json`):

- `benchmark_manifest_sha256`: `c85d9d2011dfa748463a73e257391e5364cfb9dc53ceb8f2dff1e53ad569ae0e`
- `hyperparams_sha256`: `e5c736c70c35fccf94098b5f26b33ae96ae435b4a018fb6e386e46134b8066f4`

---

## Key results summary

### Labeled ground truth @ threshold 50 (0–100 scale)

**Strict** (`known_match` only) — `labeled/labeled_strict_summary.csv`:


| Method         | F1       | Accuracy | Pos/neg mean gap |
| -------------- | -------- | -------- | ---------------- |
| metadata       | **1.00** | 1.00     | 88.2             |
| code_centric   | **1.00** | 1.00     | 85.3             |
| cross_language | **1.00** | 1.00     | 78.2             |
| dynamic        | 0.80     | 0.71     | 28.5             |


**Lenient** (`known_match` + `known_related`) — `results_benchmark/labeled/labeled_summary.json` (identical to `labeled/labeled_lenient_summary.json`):


| Method         | F1       | Accuracy | Pos/neg mean gap |
| -------------- | -------- | -------- | ---------------- |
| metadata       | **1.00** | 1.00     | 82.3             |
| cross_language | 0.92     | 0.89     | 63.5             |
| code_centric   | 0.83     | 0.78     | 68.8             |
| dynamic        | 0.67     | 0.56     | 9.3              |


`target_uncertain` (1 pair) excluded from P/R/F1 claims (both `labeled_summary` and `labeled_lenient_summary` now apply this exclusion consistently).

### queryv2 REDUX proxy bridge

- **100** anchor→proxy metadata scores — `queryv2_redux/run_manifest.json` → `n_pair_scores: 100`
- Thin-anchor metadata means (`queryv2_redux/rollup_summary.csv`): jina **96.35%**, ray **92.31%**, airflow **95.36%**, OpenBB **93.77%**

### anchorsv2 sensitivity

- Top-5 proxy overlap on **20** shared folder slugs — `anchorsv2_overlap.csv`: mean **Jaccard = 0.96**; **17/20** at 1.0; partial drift on `explosion/spaCy`, `huggingface/datasets` (0.67), `jina-ai/serve` (0.80)
- REDUX bridge — `anchorsv2_redux/` (**116** pair scores, 24 anchors)
- **Assembly note:** this is now a **full independent 24-anchor REDUX rerun** — all 24 anchors were freshly scored from the `penalty300_min700_cap22_anchorsv2` archive (`run_manifest.json`: `n_pair_scores: 116`, all 24 anchors in `anchors_scored_this_run`). It **replaces the earlier bootstrap** (17 fresh / 3 rescored / 96 reused from `queryv2_redux/`). Metadata-mean shifts vs the bootstrap are modest (overall mean 92.82 → 94.04); the largest are on the previously-reused/rescored anchors (`huggingface/transformers` +7.59, `ultralytics/yolov5` +4.36, `mlflow/mlflow` +4.00, `explosion/spaCy` +3.32). Reproduce: `bash tools/run_anchorsv2_redux.sh full`

### MetaMatch retrieval winner (pre-existing)

- **0** top-5 magnets, **20/0/0** Good/OK/Weak — `runs/experiments/documentation/WINNER.md`

### Decision gates — `PAPER_PACKAGE.md`


| Gate                                                   | Result                                                                                         |
| ------------------------------------------------------ | ---------------------------------------------------------------------------------------------- |
| G1 — Strict `known_match` separates @ 50               | **PASS**                                                                                       |
| G2 — Lenient includes related pairs                    | **PASS**                                                                                       |
| G3 — Do not claim `30_Pairs` as ground truth           | **PASS**                                                                                       |
| G4 — Cross-method agreement (authenticated, canonical) | **PASS** (authenticated n=30 ρ ≈ +0.69, go=true; prior ρ ≈ −0.21 was a rate-limiting artifact) |
| G5 — queryv2 retrieval winner frozen                   | **PASS**                                                                                       |
| G6 — queryv2 proxy REDUX bridge                        | **PASS**                                                                                       |
| G7 — anchorsv2 sensitivity                             | **PASS**                                                                                       |
| G8 — MetaMatch retune required?                        | **NO**                                                                                         |


### Cross-method Spearman (authenticated, canonical)

From the canonical authenticated run `projected_pairs/full_summary_authenticated_n30.json` (n = 30, original 10/10/10 allocation, `authenticated=true`): Spearman **ρ = +0.69** (p = 2.34e-5), Pearson r = **+0.66** (p = 6.25e-5), **go = true** — **passes** rubric `minimum_spearman: 0.30`. The authenticated n=25 current-rubric run (`full_summary_authenticated.json`) is consistent: ρ = **+0.78**, go = true.

**Honest methods note:** the earlier `projected_pairs/full_summary.json` reported ρ = **−0.21** (go=false); that was an artifact of **unauthenticated** GitHub rate-limiting (38% HTTP 403 starved the `target_uncertain` Search rows). Holding n=30 fixed and flipping only authentication moves ρ from −0.21 to +0.69 — authentication, not the rubric/n change, drives the flip. The unauthenticated file is retained unchanged for transparency.

---

## Cross-verification index


| Claim                                                   | Verify in                                                                               |
| ------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Labeled cohort scored                                   | `labeled_scored.json`                                                                   |
| Seed not overwritten                                    | `configs/labeled_benchmark_pairs.json` (empty score fields)                             |
| Strict / lenient metrics                                | `labeled/labeled_strict_summary.csv`, `labeled/labeled_summary.json`                    |
| Threshold sensitivity                                   | `labeled/threshold45/`, `labeled/threshold55/`                                          |
| Repo reachability                                       | `repo_access_validation.csv`                                                            |
| Repro fingerprints                                      | `run_manifest.json`                                                                     |
| Proxy bridge (queryv2)                                  | `queryv2_redux/run_manifest.json`, `queryv2_redux/rollup_summary.csv`                   |
| Frozen retrieval source                                 | `runs/experiments/penalty300_min700_cap22_queryv2/manual-ml-py/<anchor>/30_Matches.csv` |
| Anchor-list robustness                                  | `anchorsv2_overlap.csv`                                                                 |
| anchorsv2 REDUX                                         | `anchorsv2_redux/rollup_summary.csv`                                                    |
| Retrieval hygiene                                       | `queryv2_spot_check.md`, `WINNER.md`                                                    |
| Testing bridge                                          | `testing_case_study_airflow.md`                                                         |
| Canonical authenticated Spearman (ρ=+0.69, go=true)     | `projected_pairs/full_summary_authenticated_n30.json`, `VALIDATION_MEMO.md`             |
| Superseded unauthenticated Spearman (ρ=−0.21, artifact) | `projected_pairs/full_summary.json`                                                     |
| Discrimination                                          | `metadata_discrimination_canonical.csv`                                                 |
| All gates                                               | `PAPER_PACKAGE.md`                                                                      |


---

## Repro commands

```bash
cd "$(git rev-parse --show-toplevel)"

export GITHUB_TOKEN="$(gh auth token)"
export PYTHONPATH=.

# A — repro smoke + repo access
python3 tools/write_run_manifest.py --output results_benchmark/run_manifest.json
python3 tools/verify_repo_access.py --benchmark configs/labeled_benchmark_pairs.json --skip-clone

# B — labeled cohort
PYTHONPATH=. python3 tools/score_labeled_benchmark_redux.py
PYTHONPATH=. python3 tools/score_labeled_benchmark_redux.py --live   # gap-fill only if needed
PYTHONPATH=. python3 tools/run_labeled_benchmark.py \
  --benchmark results_benchmark/labeled_scored.json \
  --threshold 50 --output-dir results_benchmark/labeled
PYTHONPATH=. python3 tools/labeled_strict_metrics.py \
  --benchmark results_benchmark/labeled_scored.json \
  --threshold 50 --output-dir results_benchmark/labeled

# D — queryv2 proxy REDUX (reads frozen archive; does not re-run MetaMatch)
PYTHONPATH=. python3 tools/score_metamatch_proxies_redux.py \
  --top-k 5 --max-commits 50 --fit-global --metadata-only \
  --output-dir results_benchmark/queryv2_redux

# F — anchorsv2 overlap + REDUX bridge
PYTHONPATH=. python3 tools/anchorsv2_overlap.py
bash tools/run_anchorsv2_redux.sh all
```

**Note:** Threshold is **50** on a 0–100 percent scale. Script default `0.5` is incorrect for this benchmark.

---

## File inventory — validation pass

### `tools/` 


| Path                                     | Status  | Source             |
| ---------------------------------------- | ------- | ------------------ |
| `tools/score_labeled_benchmark_redux.py` | Added   | **[Reproducible]** |
| `tools/score_metamatch_proxies_redux.py` | Added   | **[Anchor/Query]** |
| `tools/labeled_strict_metrics.py`        | Added   | **[Reproducible]** |
| `tools/anchorsv2_overlap.py`             | Updated | **[Anchor/Query]** |
| `tools/run_anchorsv2_redux.sh`           | Added   | **[Anchor/Query]** |


Reused ground-truth tools: `write_run_manifest.py`, `verify_repo_access.py`, `run_labeled_benchmark.py`.

### `configs/`


| Path                                   | Role            | Source             |
| -------------------------------------- | --------------- | ------------------ |
| `configs/labeled_benchmark_pairs.json` | Seed manifest   | **[Reproducible]** |
| `configs/projected_pair_rubric.json`   | Spearman rubric | **[Reproducible]** |


### `results_benchmark/` (outputs)


| Path                                                  | Role                                                          |
| ----------------------------------------------------- | ------------------------------------------------------------- |
| `labeled_scored.json`                                 | Scored labeled cohort                                         |
| `labeled/`                                            | Threshold 50 + strict/lenient                                 |
| `labeled/threshold45/`, `labeled/threshold55/`        | Sensitivity                                                   |
| `repo_access_validation.csv`                          | Git reachability                                              |
| `run_manifest.json`                                   | Repro snapshot                                                |
| `queryv2_redux/`                                      | 20 anchor CSVs + rollup (100 pair scores)                     |
| `anchorsv2_redux/`                                    | anchorsv2 REDUX bridge (24 anchors)                           |
| `anchorsv2_overlap.csv`                               | Jaccard overlap (symlink → `archives/metamatch_sensitivity/`) |
| `queryv2_spot_check.md`, `anchorsv2_spot_check.md`    | Retrieval notes                                               |
| `testing_case_study_airflow.md`                       | Testing / QA bridge                                           |
| `VALIDATION_MEMO.md`, `PAPER_PACKAGE.md`, `README.md` | Analysis + directory map                                      |
| `WORK_REVIEW.md`                                      | This document                                                 |
| `archives/`                                           | Historical CSVs with root symlinks                            |


---

## Encoding and reproducibility notes

- Frozen experiment **scores, ranks, and functional columns** in `runs/experiments/**/30_Matches.csv` were **not** modified.
- Batch run artifacts under `runs/2026-05-*-batch/` received description fixes only (no score changes).

---

## Related documents


| Document                                   | Role                                                |
| ------------------------------------------ | --------------------------------------------------- |
| `VALIDATION_MEMO.md`                       | Reviewer-response statistics and method positioning |
| `PAPER_PACKAGE.md`                         | Gate checklist G1–G8                                |
| `results_benchmark/README.md`              | Directory layout and repro entry points             |
| `runs/experiments/documentation/WINNER.md` | MetaMatch winner scorecard                          |
| `REDUX_REPRO.md`                           | REDUX reproduction notes (repo root)                |


---

## Closing note

This validation pass **executes** ground-truth tooling and **bridges** it to the frozen MetaMatch winner (`queryv2`) and anchorsv2 sensitivity archive. The retrieval win lives under `runs/experiments/` and was not re-archived. For paper claims: cite **strict** metrics for mirror ground truth, **lenient** metrics when including related pairs, **proxy REDUX** for similarity-on-retrieved-neighbors, and the **canonical authenticated Spearman** (ρ ≈ +0.69 at n=30, go=true) for cross-method positioning — noting that the earlier ρ ≈ −0.21 was an unauthenticated GitHub rate-limiting artifact, retained for transparency.