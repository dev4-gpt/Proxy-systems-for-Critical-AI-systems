# Removable history inventory

> **Current state:** [`WORK_REVIEW.md`](WORK_REVIEW.md) and [`../CANONICAL_RESULTS/`](../CANONICAL_RESULTS/). **Execution complete** — Tier A deleted, Tier B tarball'd.

Actionable cleanup guide derived from [`REPO_AUDIT.md`](REPO_AUDIT.md) and [`MASTER_EVALUATION.md`](MASTER_EVALUATION.md). Paths are relative to the repo root.

**Rule:** Do not delete frozen `runs/experiments/**/30_Matches.csv` scores under the two primary validation archives.

---

## Tier A — Safe to delete **(EXECUTED)**

Byte-identical duplicates, superseded scripts, scratch configs, execution logs. **Removed from tree.**

| Path | Reason |
|------|--------|
| `results_benchmark/_before_repro_run/` | Pre-reorg backup — **removed** |
| `Run-MetaMatchPipeline_old.ps1` | Superseded — **removed** |
| `Apply-MetaMatch2Updates.ps1` | One-time migration script |
| `configs/projected_pair_rubric_old.json` | Prior rubric; canonical run uses `projected_pair_rubric.json` |
| `configs/tmp_rubric_low_volume.json` | Scratch rubric |
| `configs/30_Pairs_run1.json` | Unused run variant |
| `configs/30_Pairs_run2.json` | Unused run variant |
| `results_benchmark/labeled/labeled_lenient_summary.csv` | **Removed** — use `labeled_summary.csv` |
| `results_benchmark/labeled/labeled_lenient_summary.json` | **Removed** — use `labeled_summary.json` |
| `*.log`, `repro_run.log`, `anchorsv2_redux_run.log` | Execution logs |
| `work-p2.docx`, `work-review.docx` (if present) | Word exports; superseded by `WORK_REVIEW.md` |

---

## Tier B — Archive tarball, then remove from repo **(EXECUTED)**

Grid history and exploratory sweeps not cited in validation gates G1–G8.

| Path | Notes |
|------|-------|
| `runs/experiments/penalty55_*` (4 folders) | MetaMatch grid history |
| `runs/experiments/penalty75_min700_cap21/` | Grid history |
| `runs/experiments/penalty100_min700_cap21/` | Grid history |
| `runs/experiments/penalty110_*` (4 folders) | Grid history |
| `runs/experiments/penalty150_*` (2 folders) | Grid history |
| `runs/experiments/penalty175_*` (2 folders) | Grid history |
| `runs/experiments/penalty200_*` (2 folders) | Grid history |
| `runs/experiments/penalty250_*` (2 folders) | Grid history |
| `runs/experiments/penalty275_min700_cap22/` | Grid history |
| `results_benchmark/archives/redux4_sweep/` | **Removed** — ~40 REDUX CSVs in tarball |
| `results_benchmark/archives/custom_30_pairs/` | **Removed** — superseded by labeled cohort |
| `runs/experiments/documentation/EXPERIMENT_LOG.md` | Grid log; winner arc in `WINNER.md` |
| `runs/experiments/documentation/GRID_PHASE2_STATUS.md` | Stale grid status |

**Tarball target:** `archives/off_repo/metamatch_grid_history.tar.gz` (gitignored).

**Keep in repo:** `penalty300_min700_cap22_queryv2/`, `penalty300_min700_cap22_anchorsv2/`, comparison CSVs at `runs/experiments/` root, `documentation/WINNER.md`, `PHASE2_NOTES.md`, `CAP_ANALYSIS.md`.

---

## Tier C — Keep but demote

Reference material or superseded artifacts retained for transparency. Add `ARCHIVE_ONLY.md` banner in each folder.

| Path | Role |
|------|------|
| `results_benchmark/projected_pairs/full_summary.json` | Superseded unauthenticated Spearman (ρ ≈ −0.21); canonical is `full_summary_authenticated_n30.json` |
| `runs/experiments/penalty300_min700_cap22/` | Pre-queryv2 step (5 magnets) |
| `runs/experiments/penalty30_min700_cap21/` | Phase 2 baseline (30 magnets) |
| `proxytool_redux/proxytool.ipynb` | Notebook iteration history |
| `proxytool_redux/proxytool_REDUX.ipynb` | v1 |
| `proxytool_redux/proxytool_REDUX_2.ipynb` | v2 |
| `proxytool_redux/proxytool_REDUX_3.ipynb` | v3 |
| `proxytool_redux/proxytool_REDUX_4.ipynb` | v4 (superseded by extracted core) |
| `proxytool_redux/proxytool_final.ipynb` | Consolidated draft |

**Canonical scoring code:** `proxytool_redux/_extracted/redux4_core.py`, `benchmark.py`, `benchmark_metrics.py`, `proxytool_redux/REDUX_REPRO.md`, `legacy_notebooks/proxytool_REDUX_4_REPRO.ipynb`. Notebook iterations (REDUX 1–4, REPRO) live under `legacy_notebooks/`; `proxytool_redux/proxytool.ipynb` retained for reference.

---

## Tier D — Never remove

Minimal paper package supporting gates G1–G9.

### Configs

- `configs/labeled_benchmark_pairs_v2.json` (primary)
- `configs/labeled_benchmark_pairs.json` (v1 frozen)
- `configs/projected_pair_rubric.json`
- `metamatch_hyperparams.json`

### Frozen MetaMatch archives

- `runs/experiments/penalty300_min700_cap22_queryv2/`
- `runs/experiments/penalty300_min700_cap22_anchorsv2/`

### Validation outputs

- `results_benchmark/labeled_scored_v2.json`
- `results_benchmark/labeled_v2/labeled_summary.csv`
- `results_benchmark/labeled_v2/labeled_strict_summary.csv`
- `results_benchmark/labeled_v2/bootstrap_ci.csv`
- `results_benchmark/labeled_scored.json` (v1)
- `results_benchmark/labeled/labeled_summary.csv`
- `results_benchmark/labeled/labeled_strict_summary.csv`
- `results_benchmark/downstream_validation/` (G9)
- `results_benchmark/run_manifest.json`
- `results_benchmark/repo_access_validation.csv`
- `results_benchmark/queryv2_redux/rollup_summary.csv`
- `results_benchmark/queryv2_redux/run_manifest.json`
- `results_benchmark/anchorsv2_redux/rollup_summary.csv`
- `results_benchmark/anchorsv2_overlap.csv`
- `results_benchmark/metadata_discrimination_canonical.csv`
- `results_benchmark/three_test_argument_table.csv`
- `results_benchmark/projected_pairs/full_summary_authenticated_n30.json`

### Narrative

- `results_benchmark/WORK_REVIEW.md`
- `results_benchmark/VALIDATION_MEMO.md`
- `results_benchmark/PAPER_PACKAGE.md`
- `runs/experiments/documentation/WINNER.md`
- `results_benchmark/testing_case_study_airflow.md`
- `CANONICAL_RESULTS/` (frozen headline bundle)

---

## Duplicate content map

| Duplicate | Canonical copy |
|-----------|----------------|
| `labeled_lenient_summary.csv` / `.json` | **Removed** — use `labeled_summary.csv` / `.json` |
| `_before_repro_run/*.csv` | **Removed** — archived in tarball |
| 7 REDUX notebook iterations | `proxytool_redux/_extracted/redux4_core.py` + `proxytool_redux/REDUX_REPRO.md` |
| Four overlapping gate docs | `WORK_REVIEW.md` (SSOT); others are reviewer slices |
| `30_Pairs.json` / `configs/30_Pairs_*.json` | `configs/labeled_benchmark_pairs.json` is ground truth |
| `projected_pairs/full_summary.json` | `projected_pairs/full_summary_authenticated_n30.json` |

---

## Doc drift to fix (not deletion)

| File | Issue | Fix |
|------|-------|-----|
| `REPO_AUDIT.md` minimal package item #12 | Lists superseded `full_summary.json` | Cite `full_summary_authenticated_n30.json` |
| Root `README.md` | Predates validation pass | Point to `CANONICAL_RESULTS/` first |
| `RESULTS_REVIEW.md` | No canonical bundle pointer | Banner → `../CANONICAL_RESULTS/` |

---

## Execution order

1. Ship `CANONICAL_RESULTS/` and fix doc drift. **Done**
2. Delete Tier A. **Done**
3. Tarball Tier B → `archives/off_repo/metamatch_grid_history.tar.gz`, then remove from tree. **Done**
4. Add `ARCHIVE_ONLY.md` to Tier C folders. **Done**
5. Promote v2 labeled cohort + downstream validation to `CANONICAL_RESULTS/`. **Done (2026-06-27)**
