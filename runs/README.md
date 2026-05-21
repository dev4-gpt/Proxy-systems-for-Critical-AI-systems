# MetaMatch run outputs

## Folders

| Path | Git | Purpose |
|------|-----|---------|
| `manual-ml-py/` | **Ignored** (local only) | Live per-anchor outputs from `Get-AnchorMatches.ps1` — overwritten when you re-run matching |
| `_summaries/` | **Ignored** (local only) | Live cross-anchor tables from `summarize_runs.py` / `evaluate_anchor_runs.py` |
| `experiments/<id>/` | **Committed** | Frozen snapshot for one hyperparameter run (includes copies of summaries + `manual-ml-py/`) |

## Per-anchor files (7 files each)

Each `manual-ml-py/<anchor-folder>/` contains:

- `anchor_repo.json` — anchor metadata
- `candidate_repos.csv` / `.json` — search pool
- `ranked_matches.csv` / `.json` — all scored candidates
- `30_Matches.csv` — final Top-30 proxies
- `run_manifest.json` — parameters for reproducibility

Seeing many files under `manual-ml-py` is normal (20 anchors × 7 files ≈ 140 files, plus a few root CSVs).

## What to share with your professor

Point them to **`runs/experiments/`** (e.g. `penalty30_min700_cap21`, `penalty55_min700_cap21`) and the comparison CSVs at `runs/experiments/*.csv` — not the live `manual-ml-py/` folder.

## After each tuning run

```bash
pwsh ./Run-MetaMatchPipeline.ps1 -ArchiveAsExperiment penalty75_min700_cap21 -CompareWith penalty55_min700_cap21
```

Then commit only `runs/experiments/` (and any updated comparison CSVs at `runs/experiments/` root).
