# Repository Audit — CAIS / MetaMatch / REDUX

**Repository:** `mdk5293/Proxy-systems-for-Critical-AI-systems` (repo root)  
**Audit date:** 2026-06-05  
**Scope:** Read-only inventory of what the validation pass actually uses vs. historical sprawl.

---

## Executive summary

**You are not using everything in this repo.** The labeled validation pass (phases A–G) needs roughly **22 artifact paths** and **8 tools**. Everything else — MetaMatch penalty grid history (20 non-primary experiment folders), REDUX coverage/temperature sweeps (88 archived CSVs), seven REDUX notebook iterations, overlapping narrative docs, and duplicate pre-archive snapshots — is supporting material or dead weight for the current paper package.


| Finding                                                                                | Severity | Action                                                                            |
| -------------------------------------------------------------------------------------- | -------- | --------------------------------------------------------------------------------- |
| Validation is self-contained under `results_benchmark/` + 2 frozen experiment archives | Low      | Keep; cite `WORK_REVIEW.md` as master                                             |
| Four `results_benchmark/` docs repeat gates/metrics                                    | Medium   | Treat `WORK_REVIEW.md` as SoT; others are reviewer-facing slices                  |
| `_before_repro_run/` duplicates `archives/`                                            | Low      | Safe to ignore or merge later                                                     |
| Lenient labeled metrics computed twice                                                 | Low      | Both scripts intentional (strict vs lenient split)                                |
| `proxytool_redux/` REDUX core now tracked; `projected_pairs/` un-ignored (tracked)     | Resolved | Fresh clone can re-score (`PYTHONPATH=.`); see `REDUX_REPRO.md`                    |
| 20 grid-history experiment folders unused by validation                                | Low      | Archive reference only; do not re-run                                             |
| Root notebooks deleted; logic lives in `proxytool_redux/` (gitignored)                 | **High** | Document clone/setup in `REDUX_REPRO.md`                                          |


**Bottom line:** For paper submission and reviewer reproduction, ship the **minimal paper package** below. Use `WORK_REVIEW.md` as the single source of truth for commands, tags, and cross-verification.

---

## Documentation sprawl

There are **23 markdown files** across the repo. For validation, four overlap heavily:


| Document                               | Role                                                          | Overlap with others                       |
| -------------------------------------- | ------------------------------------------------------------- | ----------------------------------------- |
| `results_benchmark/WORK_REVIEW.md`     | **Master** — phase table A–G, tags, repro, cross-verification | —                                         |
| `results_benchmark/VALIDATION_MEMO.md` | Reviewer-response statistics backbone                         | Gates, labeled metrics, Spearman          |
| `results_benchmark/PAPER_PACKAGE.md`   | Gate checklist G1–G8                                          | Same gates as WORK_REVIEW closing section |
| `results_benchmark/README.md`          | Directory map + repro entry points                            | Subset of WORK_REVIEW                     |


Additional narrative (supporting, not redundant):

- `queryv2_spot_check.md`, `anchorsv2_spot_check.md`, `testing_case_study_airflow.md` — anchor-specific analysis
- `runs/experiments/documentation/WINNER.md`, `PHASE2_NOTES.md`, `CAP_ANALYSIS.md`, `EXPERIMENT_LOG.md` — MetaMatch grid history
- Root `README.md` (14 KB), `REDUX_REPRO.md`, `INSTRUCTIONS.md` (gitignored), `runs/README.md`

**Recommendation:** Point reviewers to `WORK_REVIEW.md` first. Keep `VALIDATION_MEMO.md` and `PAPER_PACKAGE.md` as paper-facing exports; do not maintain a fifth summary doc.

---

## Tools overlap

### Validation tools (8 — actively used)


| Tool                                     | Phase | Output                         |
| ---------------------------------------- | ----- | ------------------------------ |
| `tools/write_run_manifest.py`            | A     | `run_manifest.json`            |
| `tools/verify_repo_access.py`            | A     | `repo_access_validation.csv`   |
| `tools/score_labeled_benchmark_redux.py` | B     | `labeled_scored.json`          |
| `tools/run_labeled_benchmark.py`         | B     | `labeled/` threshold summaries |
| `tools/labeled_strict_metrics.py`        | B     | strict + lenient CSVs          |
| `tools/score_metamatch_proxies_redux.py` | D     | `queryv2_redux/`               |
| `tools/anchorsv2_overlap.py`             | F     | `anchorsv2_overlap.csv`        |
| `tools/run_anchorsv2_redux.sh`           | F     | `anchorsv2_redux/`             |


### MetaMatch grid tools (10 — historical; not needed for validation repro)


| Tool                            | Purpose                                  |
| ------------------------------- | ---------------------------------------- |
| `run_metamatch_grid.py`         | Penalty/min/cap grid sweeps              |
| `archive_experiment.py`         | Snapshot live runs → `runs/experiments/` |
| `compare_experiments.py`        | Cross-experiment CSV comparison          |
| `pick_experiment_winner.py`     | Scorecard winner selection               |
| `apply_experiment_winner.py`    | Patch PS1 defaults from winner           |
| `metamatch_experiment_score.py` | Good/OK/Weak scoring helpers             |
| `update_experiment_log.py`      | EXPERIMENT_LOG.md maintenance            |
| `evaluate_anchor_runs.py`       | Per-anchor magnet/hygiene eval           |
| `summarize_runs.py`             | `_summaries/` aggregation                |


**Overlap note:** `run_labeled_benchmark.py` and `labeled_strict_metrics.py` both compute lenient (`known_match` + `known_related`) metrics, and both now exclude `target_uncertain` from P/R/F1, so `labeled_summary.csv` and `labeled_lenient_summary.csv` are identical. `labeled_strict_metrics.py` adds the strict (`known_match`-only) cohort in the same pass. Not a bug; slightly redundant I/O.

Both labeled tools import `proxytool_redux.benchmark_metrics` (see gitignore gap below).

---

## Benchmark artifacts

### Active validation outputs (`results_benchmark/`)


| Path                          | Status           | Role                                           |
| ----------------------------- | ---------------- | ---------------------------------------------- |
| `labeled_scored.json`         | Active           | 10-pair REDUX scores                           |
| `labeled/`                    | Active           | Threshold 50/45/55 + strict/lenient            |
| `run_manifest.json`           | Active           | SHA256 + auth snapshot                         |
| `repo_access_validation.csv`  | Active           | Git reachability                               |
| `queryv2_redux/`              | Active           | 20 anchors × top-5 metadata REDUX (100 scores) |
| `anchorsv2_redux/`            | Active           | 24-anchor sensitivity REDUX bridge             |
| `anchorsv2_overlap.csv`       | Active (symlink) | Jaccard vs queryv2                             |
| Spot-check + case-study memos | Active           | Retrieval / testing bridge                     |


### Archived sweeps (`results_benchmark/archives/` — 88 files)


| Subfolder                | Contents                                | Used by validation?                               |
| ------------------------ | --------------------------------------- | ------------------------------------------------- |
| `legacy_tables/`         | `three_test_argument_table.csv`         | **Yes** — labeled scoring cache (symlink at root) |
| `metadata_diagnostics/`  | `metadata_discrimination_canonical.csv` | **Yes** — cited in VALIDATION_MEMO                |
| `metamatch_sensitivity/` | `anchorsv2_overlap.csv`                 | **Yes**                                           |
| `known_mirror/`          | Mirror benchmark rows                   | **Yes** — labeled scoring                         |
| `continuous_scores/`     | Mirror vs non-mirror tables             | Cited in VALIDATION_MEMO                          |
| `custom_30_pairs/`       | 30-pair scoring variants                | No — historical                                   |
| `redux4_sweep/`          | Coverage/temperature grid (~40 CSVs)    | No — REDUX tuning history                         |


### Duplicate snapshot

`results_benchmark/_before_repro_run/` holds **3 CSVs** that are identical in role to symlinks now under `archives/`:

- `three_test_argument_table.csv`
- `metadata_discrimination_canonical.csv`
- `custom_30_pairs_canonical.csv`

Safe to ignore; kept as pre-reorganization backup.

### Gitignored but cited


| Path                                 | In `.gitignore` | Cited by                                            |
| ------------------------------------ | --------------- | --------------------------------------------------- |
| `proxytool_redux/`                   | Yes             | All REDUX scoring tools, `run_labeled_benchmark.py` |
| `results_benchmark/projected_pairs/` | Yes             | Spearman ρ in VALIDATION_MEMO, G4                   |
| `scripts/`                           | Yes             | `projected_pair_pipeline.py`, REDUX extraction      |
| `results_plots/` (46 PNGs)           | Yes             | Not in validation pass                              |
| `analysis/`                          | Yes             | Publication comparison notes                        |


**Repro gap:** A fresh `git clone` gets validation CSVs/JSON but may lack REDUX core and projected-pair stats unless `proxytool_redux/` and `projected_pairs/` are restored per `REDUX_REPRO.md`.

---

## Notebook duplication

Root-level notebooks were removed (~117k lines in recent commit). REDUX logic now lives in `**proxytool_redux/`** (gitignored):


| Notebook                        | Approx. role               |
| ------------------------------- | -------------------------- |
| `proxytool.ipynb`               | Original                   |
| `proxytool_REDUX.ipynb`         | REDUX v1                   |
| `proxytool_REDUX_2.ipynb`       | REDUX v2                   |
| `proxytool_REDUX_3.ipynb`       | REDUX v3                   |
| `proxytool_REDUX_4.ipynb`       | REDUX v4 (current scoring) |
| `proxytool_REDUX_4_REPRO.ipynb` | Repro variant              |
| `proxytool_final.ipynb`         | Consolidated draft         |


Extracted Python lives in `proxytool_redux/_extracted/redux4_core.py` via `scripts/extract_redux4_core.py`. **Only REDUX 4 core is imported at runtime.** The other six notebooks are iteration history — not needed for validation repro if `_extracted/` is present.

`.gitignore` also excludes legacy root exports: `proxytool4.ipynb`, `changes.ipynb`, `proxytool copy.ipynb.txt`.

---

## Pipeline duplication

### PowerShell entry points (root)


| Script                             | Role                           | Status                              |
| ---------------------------------- | ------------------------------ | ----------------------------------- |
| `Get-AnchorMatches.ps1`            | Per-anchor MetaMatch retrieval | **Primary**                         |
| `Get-AnchorCandidates.ps1`         | Candidate discovery            | Active                              |
| `Run-MetaMatchPipeline.ps1`        | Batch pipeline orchestrator    | **Primary**                         |
| `Run-MetaMatchPipeline_old.ps1`    | Prior pipeline version         | **Duplicate** — historical          |
| `Run-AnchorPipelineBatch.ps1`      | Batch variant                  | Overlaps with Run-MetaMatchPipeline |
| `Run-RecommendedAnchorMatches.ps1` | Runs all anchors from CSV      | Overlaps with batch pipeline        |
| `Apply-MetaMatch2Updates.ps1`      | One-time migration script      | Historical                          |


Validation does **not** re-run any PowerShell pipeline. Frozen outputs under `runs/experiments/penalty300_min700_cap22_queryv2/` are read-only inputs.

### Python pipelines


| Location                             | Role                                           |
| ------------------------------------ | ---------------------------------------------- |
| `tools/run_metamatch_grid.py` + PS1  | MetaMatch hyperparam grid (Phase 2 — complete) |
| `scripts/projected_pair_pipeline.py` | 30-pair cross-method Spearman workflow         |
| `scripts/run_repro_benchmark.py`     | Earlier repro harness                          |
| `tools/score_*_redux.py`             | Validation-pass REDUX bridges                  |


---

## Config duplication


| File                                               | Role                                               | Needed for validation?           |
| -------------------------------------------------- | -------------------------------------------------- | -------------------------------- |
| `configs/labeled_benchmark_pairs.json`             | 10-pair seed manifest                              | **Yes**                          |
| `configs/projected_pair_rubric.json`               | Spearman rubric (min 0.30)                         | **Yes** (reference)              |
| `metamatch_hyperparams.json`                       | Winner hyperparams (penalty 300, min 700, cap 2/2) | **Yes**                          |
| `metamatch_anchor_query_overrides.json`            | Per-anchor query overrides                         | Used by frozen archives          |
| `configs/30_Pairs_merged.json`                     | Merged plausible pairs                             | No — realism cohort only         |
| `configs/30_Pairs_null.json`                       | Null variant                                       | No                               |
| `configs/30_Pairs_run1.json`, `30_Pairs_run2.json` | Run variants                                       | No                               |
| `configs/projected_pair_rubric_old.json`           | Prior rubric                                       | No                               |
| `configs/tmp_rubric_low_volume.json`               | Scratch rubric                                     | No                               |
| `30_Pairs.json` (root)                             | Plausible 30-pair cohort                           | **Do not claim as ground truth** |


---

## Experiment archives

**30 entries** under `runs/experiments/` (including docs/scripts/logs).

### Primary (validation uses these)


| Folder                               | Anchors | Role                                    |
| ------------------------------------ | ------- | --------------------------------------- |
| `penalty300_min700_cap22_queryv2/`   | 20      | **MetaMatch winner** — frozen retrieval |
| `penalty300_min700_cap22_anchorsv2/` | 24      | Anchor-list sensitivity (4 swaps)       |


### Reference (WINNER arc, not re-run)


| Folder                     | Notes                              |
| -------------------------- | ---------------------------------- |
| `penalty300_min700_cap22/` | Pre-queryv2 cap22 step (5 magnets) |
| `penalty30_min700_cap21/`  | Phase 2 baseline (30 magnets)      |


### Grid history only (20 folders — safe to ignore for paper)

`penalty55_`*, `penalty75_*`, `penalty100_*`, `penalty110_*`, `penalty150_*`, `penalty175_*`, `penalty200_*`, `penalty250_*`, `penalty275_*` — various penalty/min/cap combinations explored during Phase 2 grid. Documented in `runs/experiments/documentation/WINNER.md` and `anchor_comparison_by_experiment.csv`. **None are inputs to the validation pass.**

Live run outputs (`runs/manual-ml-py/`, `runs/_summaries/`, `runs/2026-05-*-batch/`) are gitignored and regenerated by pipeline runs.

---

## Scripts vs tools


| Directory                   | Tracked in git      | Purpose                                                                |
| --------------------------- | ------------------- | ---------------------------------------------------------------------- |
| `tools/` (18 files)         | **Yes**             | MetaMatch grid management + validation pass                            |
| `scripts/` (7 files)        | **No** (gitignored) | REDUX notebook extraction, projected-pair pipeline, repro harness      |
| `runs/experiments/scripts/` | **Yes**             | Experiment-specific helpers (see `runs/experiments/scripts/README.md`) |


**Convention drift:** Validation tooling landed in `tools/` (labeled ground-truth tooling + new bridges). REDUX development scripts stayed in gitignored `scripts/`. A newcomer should look at `tools/` for repro commands and `REDUX_REPRO.md` for REDUX setup.

---

## Minimal workflow

For reviewer reproduction of the validation pass (not re-running MetaMatch grid):

```bash
cd "$(git rev-parse --show-toplevel)"
export GITHUB_TOKEN="$(gh auth token)"
export PYTHONPATH=.

# A — repro smoke + repo access
python3 tools/write_run_manifest.py
python3 tools/verify_repo_access.py --benchmark configs/labeled_benchmark_pairs.json --skip-clone

# B — labeled cohort
PYTHONPATH=. python3 tools/score_labeled_benchmark_redux.py
PYTHONPATH=. python3 tools/run_labeled_benchmark.py \
  --benchmark results_benchmark/labeled_scored.json \
  --threshold 50 --output-dir results_benchmark/labeled
PYTHONPATH=. python3 tools/labeled_strict_metrics.py

# D — queryv2 proxy REDUX (reads frozen archive)
PYTHONPATH=. python3 tools/score_metamatch_proxies_redux.py \
  --top-k 5 --max-commits 50 --fit-global --metadata-only \
  --output-dir results_benchmark/queryv2_redux

# F — anchorsv2 overlap + REDUX bridge
PYTHONPATH=. python3 tools/anchorsv2_overlap.py
bash tools/run_anchorsv2_redux.sh all
```

**Prerequisite:** `proxytool_redux/` must be present locally (see `REDUX_REPRO.md`). Threshold is **50** on a 0–100 percent scale.

---

## Master table — what validation uses vs. what exists


| Category                            | Used by validation  | Exists in repo                                                     | Notes                                 |
| ----------------------------------- | ------------------- | ------------------------------------------------------------------ | ------------------------------------- |
| Experiment archives                 | 2 folders           | 23 folders                                                         | 20 are grid history                   |
| `results_benchmark/` active outputs | ~15 paths           | 28 top-level entries                                               | Includes symlinks + archives          |
| `results_benchmark/archives/`       | 4 subfolders        | 7 subfolders                                                       | redux4_sweep + custom_30_pairs unused |
| Validation tools                    | 8                   | 18 in `tools/`                                                     | 10 are MetaMatch grid only            |
| Config files                        | 3–4                 | 9 in `configs/` + 2 root JSON                                      | 5+ are historical variants            |
| Narrative docs                      | 1 master + 3 slices | 23 markdown files                                                  | Prefer WORK_REVIEW.md                 |
| Notebooks                           | 1 core (REDUX 4)    | 7 in proxytool_redux                                               | 6 are iteration history               |
| PowerShell pipelines                | 0 (frozen inputs)   | 7 scripts                                                          | 2–3 overlap                           |
| Gitignored deps                     | 2 paths required    | proxytool_redux, projected_pairs, scripts, analysis, results_plots | Clone gap                             |


---

## Minimal paper package (~22 paths)

These paths are sufficient to support paper claims G1–G8 without re-running the MetaMatch grid:

### Configs (3)

1. `configs/labeled_benchmark_pairs.json`
2. `configs/projected_pair_rubric.json`
3. `metamatch_hyperparams.json`

### Frozen MetaMatch archives (2)

1. `runs/experiments/penalty300_min700_cap22_queryv2/`
2. `runs/experiments/penalty300_min700_cap22_anchorsv2/`

### Validation outputs (12)

1. `results_benchmark/labeled_scored.json`
2. `results_benchmark/labeled/labeled_summary.csv`
3. `results_benchmark/labeled/labeled_strict_summary.csv`
4. `results_benchmark/run_manifest.json`
5. `results_benchmark/repo_access_validation.csv`
6. `results_benchmark/queryv2_redux/rollup_summary.csv`
7. `results_benchmark/queryv2_redux/run_manifest.json`
8. `results_benchmark/anchorsv2_redux/rollup_summary.csv`
9. `results_benchmark/anchorsv2_overlap.csv`
10. `results_benchmark/metadata_discrimination_canonical.csv`
11. `results_benchmark/three_test_argument_table.csv`
12. `results_benchmark/projected_pairs/full_summary.json`

### Narrative / gates (5)

1. `results_benchmark/WORK_REVIEW.md`
2. `results_benchmark/VALIDATION_MEMO.md`
3. `results_benchmark/PAPER_PACKAGE.md`
4. `runs/experiments/documentation/WINNER.md`
5. `results_benchmark/testing_case_study_airflow.md`

**Optional but useful:** `queryv2_spot_check.md`, `anchorsv2_spot_check.md`, `results_benchmark/README.md`, `REDUX_REPRO.md`.

### Tools required to regenerate (8)

Listed in [Tools overlap → Validation tools](#validation-tools-8--actively-used) above.

---

## Safe to ignore


| Path / category                                                                           | Why                                                 |
| ----------------------------------------------------------------------------------------- | --------------------------------------------------- |
| `runs/experiments/penalty{55,75,100,110,150,175,200,250,275}_`* (20 folders)              | Grid history; winner already selected               |
| `results_benchmark/archives/redux4_sweep/` (~40 CSVs)                                     | REDUX tuning sweep; not cited in validation         |
| `results_benchmark/_before_repro_run/`                                                    | Pre-archive duplicate of 3 CSVs                     |
| `results_benchmark/archives/custom_30_pairs/`                                             | Superseded by labeled cohort                        |
| `results_plots/` (46 PNGs)                                                                | Local plots; gitignored                             |
| `analysis/`                                                                               | Publication comparison draft; gitignored            |
| `Run-MetaMatchPipeline_old.ps1`                                                           | Superseded pipeline                                 |
| `configs/30_Pairs_*.json`, `projected_pair_rubric_old.json`, `tmp_rubric_low_volume.json` | Config variants                                     |
| Root `30_Pairs.json`                                                                      | Plausible cohort — **not ground truth**             |
| `proxytool_redux/proxytool*.ipynb` (6 of 7)                                               | Notebook iteration history if `_extracted/` present |
| `runs/2026-05-*-batch/`, `runs/manual-ml-py/`                                             | Live run outputs; gitignored                        |
| `*.log`, `repro_run.log`, `anchorsv2_redux_run.log`                                       | Execution logs                                      |
| `work-review.docx`, `work-p2.docx`                                                        | Word exports; superseded by WORK_REVIEW.md          |
| `.proxytool_cache/` (542 entries)                                                         | GitHub API cache                                    |


---

## Top actions


| Priority | Action                                                                 | Rationale                                                                             |
| -------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| **1**    | Keep `WORK_REVIEW.md` as single source of truth                        | Stops doc drift across 4 overlapping memos                                            |
| **2**    | Ensure `proxytool_redux/` + `projected_pairs/` are restorable on clone | Validation imports and G4 cite them; both gitignored                                  |
| **3**    | Ship minimal paper package (22 paths) to reviewers                     | Everything else is optional context                                                   |
| **4**    | Do **not** re-run MetaMatch grid or re-archive queryv2                 | G8 = no retune; frozen archives are inputs                                            |
| **5**    | Tag grid-history experiment folders as archive-only in README          | Prevents accidental re-runs                                                           |
| **6**    | Consider removing `_before_repro_run/` in a future cleanup             | Duplicates `archives/` symlinks (not done in this pass)                               |


---

## Related documents


| Document             | Role                                      |
| -------------------- | ----------------------------------------- |
| `WORK_REVIEW.md`     | Master validation document                |
| `VALIDATION_MEMO.md` | Reviewer statistics                       |
| `PAPER_PACKAGE.md`   | Gate checklist                            |
| `REDUX_REPRO.md`     | REDUX clone/setup (repo root; gitignored) |
|                      |                                           |


