# CAIS / MetaMatch Validation — Work Review

**Repository:** `/Users/aryamandev/Library/Mobile Documents/com~apple~CloudDocs/Research Assistant`  
**Document:** `results_benchmark/WORK_REVIEW.md`  
**Last updated:** 2026-06-05

This document replaces a separate Word work-review table. Share the repository path and this file so reviewers can verify commands, outputs, and claims without a standalone doc.

---

## 1. Title & purpose

This validation pass integrates **professor-supplied ground-truth infrastructure** with **pre-existing MetaMatch Phase 2 results** (`penalty300_min700_cap22_queryv2` winner and `penalty300_min700_cap22_anchorsv2` sensitivity archive). It does **not** re-run the MetaMatch grid or re-archive queryv2. Instead, it **executes** the labeled-benchmark pipeline, **bridges** frozen retrieval outputs to REDUX proxy similarity, and **documents** honest statistics for paper gates.

The work addresses three reviewer concerns:

| # | Concern | Response in this pass |
|---|---------|------------------------|
| **1 — Ground truth** | `30_Pairs.json` plausible pairs are script-discovered realism, not verified labels | Evidence-backed cohort in `configs/labeled_benchmark_pairs.json` → scored in `results_benchmark/labeled_scored.json` → metrics in `results_benchmark/labeled/` |
| **2 — Testing / QA relevance** | Similarity must connect to test-relevant outcomes, not retrieval hygiene alone | queryv2 spot-check + REDUX proxy bridge (`queryv2_redux/`, `anchorsv2_redux/`) + airflow case study |
| **3 — Statistics & method positioning** | Cross-method agreement and discrimination must be reported honestly | `VALIDATION_MEMO.md` synthesizes labeled metrics, discrimination tables, and Spearman ρ ≈ −0.21 (fails rubric 0.30) |

---

## 2. What was NOT done

| Item | Why omitted |
|------|-------------|
| Re-archive / re-run `penalty300_min700_cap22_queryv2` | Frozen winner under `runs/experiments/`; read-only input to proxy REDUX and spot-check |
| New penalty-grid MetaMatch sweep | Phase 2 grid already complete; `PAPER_PACKAGE.md` gate G8 = **no retune** |
| Claim `30_Pairs.json` as ground truth | Plausible cohort only; use `labeled_scored.json` + explicit limitations |
| Equate magnets / Good-OK-Weak with test adequacy | Retrieval hygiene metrics only |
| Regenerate all historical REDUX CSVs | `metadata_discrimination_canonical.csv`, `three_test_argument_table.csv`, `projected_pairs/full_summary.json` reused in memo |
| Write `generated_at_utc` into config files | Timestamp lives only in `results_benchmark/run_manifest.json` (see §6) |

---

## 3. What was pre-existing

| Path | Role |
|------|------|
| `runs/experiments/penalty300_min700_cap22_queryv2/` | MetaMatch winner: 0 top-5 magnets, 20/0/0 Good/OK/Weak |
| `runs/experiments/penalty300_min700_cap22_anchorsv2/` | Anchor-list sensitivity (24 anchors, 4 swaps) |
| `runs/experiments/documentation/WINNER.md` | Experiment scorecard and recommended defaults |
| `runs/experiments/documentation/PHASE2_NOTES.md` | Phase 2 narrative and anchor swaps |
| `results_benchmark/metadata_discrimination_canonical.csv` | Similar vs dissimilar discrimination (symlink → `archives/`) |
| `results_benchmark/three_test_argument_table.csv` | REDUX cache for labeled scoring (symlink → `archives/`) |
| `results_benchmark/projected_pairs/full_summary.json` | Cross-method Spearman / Pearson on 30 projected pairs |
| `metamatch_hyperparams.json` | Winner hyperparams (penalty 300, min 700, cap 2/2) |

---

## 4. Professor vs Ours legend

Every command row in §5 carries a **source tag**:

| Tag | Meaning |
|-----|---------|
| **[Professor]** | Merged from professor bundle: seed manifest, benchmark metrics tools, rubric, pipeline helpers |
| **[Ours]** | Added in this validation pass: REDUX scoring bridges, strict/lenient split, overlap script, proxy REDUX |
| **[Pre-existing]** | Already in repo before this pass; read or reused, not created here |
| **[Docs]** | Narrative written from artifacts; no scoring command |

**Key distinction:** `score_labeled_benchmark_redux.py` is **[Ours]** — it fills `labeled_scored.json` from cached REDUX tables plus optional live REDUX. The professor provides the **empty seed** (`configs/labeled_benchmark_pairs.json`) and **`run_labeled_benchmark.py`**, which expects a scored file.

---

## 5. Main table — Phases A–G

All commands assume **repo root** as working directory.

**Auth note:** REDUX commit-fetch steps need GitHub API access. Set before Python REDUX commands:

```bash
export GITHUB_TOKEN="$(gh auth token)"
export PYTHONPATH=.
```

Smoke / manifest steps do not require a token but should be re-run after auth is fixed for an accurate snapshot.

| # | Phase | Command | Primary outputs | Result headline | Source |
|---|-------|---------|-----------------|-----------------|--------|
| **A** | Repro smoke | `python3 tools/write_run_manifest.py` | `results_benchmark/run_manifest.json` | SHA256 fingerprints of `configs/labeled_benchmark_pairs.json` + `metamatch_hyperparams.json`; `generated_at_utc` + GitHub env snapshot | **[Professor]** |
| **A** | Repo access | `python3 tools/verify_repo_access.py --benchmark configs/labeled_benchmark_pairs.json --skip-clone` | `results_benchmark/repo_access_validation.csv` | 18 unique repo URLs checked via `git ls-remote` (no clone) | **[Professor]** |
| **B** | Score labeled pairs | `PYTHONPATH=. python3 tools/score_labeled_benchmark_redux.py` | `results_benchmark/labeled_scored.json` | 10/10 pairs scored; most from cached `three_test_argument_table.csv` / mirror benchmark CSVs (`score_source` per pair) | **[Ours]** |
| **B** | Live REDUX gap-fill | `PYTHONPATH=. python3 tools/score_labeled_benchmark_redux.py --live` | updates `results_benchmark/labeled_scored.json` | Remaining pairs (e.g. MariaDB/MySQL) filled via live GitHub REDUX | **[Ours]** |
| **B** | Labeled metrics @50 | `PYTHONPATH=. python3 tools/run_labeled_benchmark.py --benchmark results_benchmark/labeled_scored.json --threshold 50 --output-dir results_benchmark/labeled` | `results_benchmark/labeled/labeled_pair_table.csv`, `labeled_summary.csv`, `labeled_summary.json`, `labeled_claim_checks.md` | Lenient cohort (`known_match` + `known_related` positive): metadata **F1 = 0.93**, accuracy 0.90 @ threshold **50** (percent scale) | **[Professor]** on **[Ours]** output |
| **B** | Threshold 45 / 55 | Same as above with `--threshold 45 --output-dir results_benchmark/labeled/threshold45` and `--threshold 55 --output-dir results_benchmark/labeled/threshold55` | `results_benchmark/labeled/threshold45/*`, `results_benchmark/labeled/threshold55/*` | Threshold sensitivity tables | **[Professor]** |
| **B** | Strict vs lenient | `PYTHONPATH=. python3 tools/labeled_strict_metrics.py --benchmark results_benchmark/labeled_scored.json --threshold 50 --output-dir results_benchmark/labeled` | `results_benchmark/labeled/labeled_strict_summary.csv`, `labeled_lenient_summary.csv` (+ `.json`) | **Strict** (`known_match` only): metadata/code_centric/cross_language **F1 = 1.0**; dynamic F1 = 0.80 | **[Ours]** |
| **C** | Stats memo | *(no command)* | `results_benchmark/VALIDATION_MEMO.md` | Discrimination ~94% vs ~5%; Spearman **ρ ≈ −0.21**; labeled + method positioning | **[Docs]** + **[Pre-existing]** |
| **D** | Spot-check retrieval | *(read-only inspection)* | `results_benchmark/queryv2_spot_check.md` | Confirms top-5 proxies for jina, ray, airflow, OpenBB in frozen `30_Matches.csv` archives | **[Docs]** + **[Pre-existing]** |
| **D** | Pilot proxy REDUX | `PYTHONPATH=. python3 tools/score_metamatch_proxies_redux.py --pilot-only --top-k 5 --max-commits 60 --fit-global` | `results_benchmark/queryv2_redux/*.csv` (4 thin anchors) | 20 pair scores (4×5); 4 methods in pilot | **[Ours]** |
| **D** | Full proxy REDUX | `PYTHONPATH=. python3 tools/score_metamatch_proxies_redux.py --top-k 5 --max-commits 50 --fit-global --metadata-only --output-dir results_benchmark/queryv2_redux` | `results_benchmark/queryv2_redux/*.csv` (20 files), `results_benchmark/queryv2_redux/rollup_summary.csv`, `results_benchmark/queryv2_redux/run_manifest.json` | **100** metadata pair scores (20×5); thin-anchor means: jina **96.4%**, ray **92.3%**, airflow **95.4%**, OpenBB **93.8%** | **[Ours]** |
| **E** | Testing case study | *(no command)* | `results_benchmark/testing_case_study_airflow.md` | Links `apache/airflow` top proxies + metadata REDUX to orchestration test dimensions | **[Docs]** |
| **F** | anchorsv2 overlap | `PYTHONPATH=. python3 tools/anchorsv2_overlap.py` | `results_benchmark/anchorsv2_overlap.csv` | **20** shared folder slugs; top-5 **Jaccard = 1.0** on all shared anchors (identical proxy sets) | **[Ours]** |
| **F** | anchorsv2 REDUX bridge | `bash tools/run_anchorsv2_redux.sh all` | `results_benchmark/anchorsv2_redux/` (24 anchor CSVs + `rollup_summary.csv` + `run_manifest.json`) | Same REDUX bridge for anchorsv2 sensitivity archive (appendix evidence) | **[Ours]** |
| **G** | Decision gates | *(no command)* | `results_benchmark/PAPER_PACKAGE.md` | Gates G1–G7 **PASS**; G8 **no MetaMatch retune** | **[Docs]** |

---

## 6. Inputs / configs table

| File | Role | `generated_at_utc`? | Source |
|------|------|---------------------|--------|
| `configs/labeled_benchmark_pairs.json` | **Seed manifest** — 10 pairs with labels, URLs, evidence; score fields empty (`""`) by design | **No** — static content; fingerprinted via SHA256 in run manifest | **[Professor]** |
| `results_benchmark/labeled_scored.json` | **Scored manifest** — same pairs with 0–100 method scores and `score_source` per pair | **No** — use `scoring_notes` and per-pair `score_source` | **[Ours]** output |
| `metamatch_hyperparams.json` | **Winner config** — penalty 300, min 700, cap 2/2, `winner_experiment_id` | **No** — static hyperparams file | **[Pre-existing]** / pinned by manifest |
| `results_benchmark/run_manifest.json` | **Run snapshot** — when repro was checked, GitHub auth state, SHA256 of seed + hyperparams | **Yes** — `generated_at_utc` lives **only here** | **[Professor]** tool output |

`write_run_manifest.py` **reads** the two config paths, hashes their bytes, and writes the manifest. It does **not** modify `labeled_benchmark_pairs.json` or `metamatch_hyperparams.json`.

**Current manifest fingerprints** (verify in `results_benchmark/run_manifest.json`):

- `benchmark_manifest_sha256`: `c85d9d2011dfa748463a73e257391e5364cfb9dc53ceb8f2dff1e53ad569ae0e`
- `hyperparams_sha256`: `e5c736c70c35fccf94098b5f26b33ae96ae435b4a018fb6e386e46134b8066f4`

---

## 7. Key results summary

### Labeled ground truth @ threshold 50 (0–100 scale)

**Strict** (`known_match` only — 5 positive, 2 negative) — `results_benchmark/labeled/labeled_strict_summary.csv`:

| Method | F1 | Accuracy | Pos/neg mean gap |
|--------|-----|----------|------------------|
| metadata | **1.00** | 1.00 | 88.2 |
| code_centric | **1.00** | 1.00 | 85.3 |
| cross_language | **1.00** | 1.00 | 78.2 |
| dynamic | 0.80 | 0.71 | 28.5 |

**Lenient** (`known_match` + `known_related` — 7 positive, 2 negative) — `results_benchmark/labeled/labeled_summary.json`:

| Method | F1 | Accuracy | Pos/neg mean gap |
|--------|-----|----------|------------------|
| metadata | **0.93** | 0.90 | 82.3 |
| cross_language | 0.86 | 0.80 | 63.5 |
| code_centric | 0.83 | 0.80 | 68.8 |
| dynamic | 0.62 | 0.50 | 9.3 |

`target_uncertain` (1 pair) is excluded from P/R/F1 claims.

### queryv2 REDUX proxy bridge

- **100** anchor→proxy metadata scores (20 anchors × top-5) — `results_benchmark/queryv2_redux/run_manifest.json` → `"n_pair_scores": 100`
- Thin-anchor metadata means (`results_benchmark/queryv2_redux/rollup_summary.csv`):

| Anchor | metadata_mean_topk |
|--------|-------------------|
| jina-ai/serve | 96.35% |
| ray-project/ray | 92.31% |
| apache/airflow | 95.36% |
| OpenBB-finance/OpenBB | 93.77% |

### anchorsv2 sensitivity

- Top-5 proxy **Jaccard = 1.0** on all **20** shared folder slugs — `results_benchmark/anchorsv2_overlap.csv`
- REDUX bridge for anchorsv2 archive — `results_benchmark/anchorsv2_redux/`

### MetaMatch retrieval winner (pre-existing, read-only)

- **0** top-5 magnets, **20/0/0** Good/OK/Weak — `runs/experiments/documentation/WINNER.md`

### Decision gates — `results_benchmark/PAPER_PACKAGE.md`

| Gate | Result |
|------|--------|
| G1 — Strict `known_match` separates @ 50 | **PASS** (metadata/code_centric/cross_language F1 = 1.0) |
| G2 — Lenient includes related pairs | **PASS** (metadata F1 = 0.93; dynamic weaker at 0.62) |
| G3 — Do not claim `30_Pairs` as ground truth | **PASS** |
| G4 — Spearman reported honestly | **PASS** (ρ ≈ −0.21; rubric 0.30 not met) |
| G5 — queryv2 retrieval winner frozen | **PASS** |
| G6 — queryv2 proxy REDUX bridge | **PASS** |
| G7 — anchorsv2 sensitivity | **PASS** (Jaccard 1.0) |
| G8 — MetaMatch retune required? | **NO** |

### Cross-method Spearman (honest)

From `results_benchmark/projected_pairs/full_summary.json` (n = 30 projected pairs):

| Stat | Value | vs rubric `minimum_spearman: 0.30` |
|------|-------|-------------------------------------|
| Spearman ρ | **−0.21** | **Fails** |
| p-value | 0.26 | Not significant |
| Pearson r | −0.35 (p ≈ 0.06) | Fails |

**Interpretation:** Methods measure complementary facets; do not claim strong rank correlation across methods.

---

## 8. Cross-verification paths

Open these files to verify each claim:

- **Labeled cohort scored:** `results_benchmark/labeled_scored.json` — each pair has method scores + `score_source`
- **Seed not overwritten:** `configs/labeled_benchmark_pairs.json` — score fields remain empty
- **Strict ground-truth metrics:** `results_benchmark/labeled/labeled_strict_summary.csv`
- **Lenient @ threshold 50:** `results_benchmark/labeled/labeled_summary.json`
- **Threshold sensitivity:** `results_benchmark/labeled/threshold45/`, `results_benchmark/labeled/threshold55/`
- **Repo reachability:** `results_benchmark/repo_access_validation.csv`
- **Repro fingerprints:** `results_benchmark/run_manifest.json`
- **Proxy bridge on queryv2:** `results_benchmark/queryv2_redux/run_manifest.json` → `n_pair_scores: 100`, `metadata_only: true`
- **Per-anchor proxy scores:** `results_benchmark/queryv2_redux/rollup_summary.csv` (20 rows)
- **Frozen retrieval source:** `runs/experiments/penalty300_min700_cap22_queryv2/manual-ml-py/<anchor>/30_Matches.csv`
- **Anchor-list robustness:** `results_benchmark/anchorsv2_overlap.csv` — `jaccard_topk` column
- **anchorsv2 REDUX bridge:** `results_benchmark/anchorsv2_redux/rollup_summary.csv`
- **Retrieval hygiene:** `results_benchmark/queryv2_spot_check.md`, `runs/experiments/documentation/WINNER.md`
- **Testing bridge:** `results_benchmark/testing_case_study_airflow.md`
- **Honest weak Spearman:** `results_benchmark/projected_pairs/full_summary.json`, `results_benchmark/VALIDATION_MEMO.md`
- **Discrimination:** `results_benchmark/metadata_discrimination_canonical.csv`
- **All gates:** `results_benchmark/PAPER_PACKAGE.md`
- **Full narrative:** `results_benchmark/VALIDATION_MEMO.md`

---

## 9. Repro commands

Copy-paste block from repo root. Requires `gh` logged in with `repo` scope (or classic PAT exported as `GITHUB_TOKEN`).

```bash
cd "/Users/aryamandev/Library/Mobile Documents/com~apple~CloudDocs/Research Assistant"

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

**Note:** Threshold is **50** on a 0–100 percent scale. Using script default `0.5` would be incorrect for this benchmark.

---

## 10. File inventory — validation pass artifacts

New or materially changed artifacts under `tools/`, `configs/`, and `results_benchmark/` from this validation pass.

### `tools/` (new / updated)

| Path | Status | Source |
|------|--------|--------|
| `tools/score_labeled_benchmark_redux.py` | Added | **[Ours]** |
| `tools/score_metamatch_proxies_redux.py` | Added | **[Ours]** |
| `tools/labeled_strict_metrics.py` | Added | **[Ours]** |
| `tools/anchorsv2_overlap.py` | Updated | **[Ours]** |
| `tools/run_anchorsv2_redux.sh` | **New (untracked)** | **[Ours]** |

Professor tools reused (not new): `tools/write_run_manifest.py`, `tools/verify_repo_access.py`, `tools/run_labeled_benchmark.py`.

### `configs/` (professor merge — typically already committed)

| Path | Role | Source |
|------|------|--------|
| `configs/labeled_benchmark_pairs.json` | Seed manifest (10 pairs, empty scores) | **[Professor]** |
| `configs/projected_pair_rubric.json` | Spearman rubric (`minimum_spearman: 0.30`) | **[Professor]** |

### `results_benchmark/` (new outputs from validation pass)

| Path | Role |
|------|------|
| `results_benchmark/labeled_scored.json` | Scored labeled cohort |
| `results_benchmark/labeled/` | Threshold 50 summaries + strict/lenient split |
| `results_benchmark/labeled/threshold45/` | Sensitivity @ 45 |
| `results_benchmark/labeled/threshold55/` | Sensitivity @ 55 |
| `results_benchmark/repo_access_validation.csv` | Git reachability check |
| `results_benchmark/run_manifest.json` | Repro snapshot (updated) |
| `results_benchmark/queryv2_redux/` | 20 anchor CSVs + rollup + manifest (100 pair scores) |
| `results_benchmark/queryv2_spot_check.md` | Retrieval spot-check memo |
| `results_benchmark/anchorsv2_redux/` | **New (untracked)** — anchorsv2 REDUX bridge (24 anchors) |
| `results_benchmark/anchorsv2_overlap.csv` | Jaccard overlap table (symlink → `archives/metamatch_sensitivity/`) |
| `results_benchmark/anchorsv2_spot_check.md` | **New (untracked)** — anchorsv2 retrieval notes |
| `results_benchmark/testing_case_study_airflow.md` | Testing / QA bridge case study |
| `results_benchmark/VALIDATION_MEMO.md` | Reviewer-response backbone (updated) |
| `results_benchmark/PAPER_PACKAGE.md` | Gate checklist (updated) |
| `results_benchmark/README.md` | **New (untracked)** — directory map |
| `results_benchmark/archives/` | **New (untracked)** — reorganized historical CSVs with root symlinks |

Historical CSVs moved under `results_benchmark/archives/` with symlinks at former root paths (`three_test_argument_table.csv`, `metadata_discrimination_canonical.csv`, etc.) so existing tool paths keep working.

---

## Closing note

This validation pass **executes** ground-truth tooling and **bridges** it to your frozen MetaMatch winner (`queryv2`) and anchorsv2 sensitivity archive. The retrieval win lives under `runs/experiments/` and was not re-archived. For paper claims: cite **strict** metrics for mirror ground truth, **lenient** metrics when including related pairs, **proxy REDUX** for similarity-on-retrieved-neighbors, and **honest Spearman** (ρ ≈ −0.21) for cross-method positioning. 