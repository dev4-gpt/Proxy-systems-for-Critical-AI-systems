# REDUX_4 REPRO runbook

Location: **`proxytool_redux/REDUX_REPRO.md`** (not repo root). Validation repro uses `tools/` + extracted core; this runbook is for the slim REPRO notebook path.

## Quick start

1. Set `GITHUB_TOKEN` (or use `.env` / `token.txt` as in the full notebook).
2. Open and run **`../legacy_notebooks/proxytool_REDUX_4_REPRO.ipynb`** top to bottom (5 cells).
3. Outputs land in `../results_benchmark/`:
   - `three_test_argument_table.csv` — Test 2 + Test 3 only (no mirror self-match)
   - `metadata_discrimination_canonical.csv` — gap diagnostics (Test 2 + labeled cohort vs Test 3)

Historical `custom_30_pairs_*.csv` outputs were archived in `archives/off_repo/metamatch_grid_history.tar.gz`; the **primary labeled cohort** is v2 (24 pairs) under `results_benchmark/labeled_v2/`.

## vs full notebook

| | `../legacy_notebooks/proxytool_REDUX_4.ipynb` | `../legacy_notebooks/proxytool_REDUX_4_REPRO.ipynb` |
|---|---------------------------|----------------------------------|
| Cells | 168 | 5 |
| Mirror identity Test 1 | Yes (100% trivia) | **No** |
| Duplicate 30-pair runs | 3+ | **1** |
| Mirror retrieval appendix | In canonical block | Optional flag `RUN_MIRROR_APPENDIX` |

## Maintenance

After editing the full notebook's library or patch cells, refresh the extracted module:

```bash
python ../scripts/extract_redux4_core.py
```

Extracted source: `_extracted/redux4_core.py`

Orchestration: `benchmark.py` → `run_all_benchmarks()`
