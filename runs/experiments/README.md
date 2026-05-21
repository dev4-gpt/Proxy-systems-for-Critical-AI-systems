# MetaMatch experiment archives

Each subfolder is a **frozen snapshot** of one tuning run (hyperparameters + all outputs).

## Layout (per experiment, e.g. `penalty30_min700_cap21/`)

| Path | Contents |
|------|----------|
| `experiment_meta.json` | When archived, experiment id, description |
| `run_hyperparams.csv` | Per-anchor params from `run_manifest.json` |
| `anchor_evaluation.csv` | Good / OK / Weak, magnets in top 5, top 5 names |
| `magnet_frequency_final30.csv` | How often each repo appears in **final** `30_Matches` (not ranked pool) |
| `manual-ml-py/` | Full per-anchor folders (`30_Matches.csv`, `ranked_matches.csv`, …) |
| Other `*.csv` | Same as `runs/_summaries/` at archive time |

## Naming convention

`penalty{W}_min{SCORE}_cap{owner}{sub}`

Example: `penalty55_min700_cap21` → penalty weight **55**, MinimumScore **700**, MaxPerOwner **2**, MaxPerOwnerPerSubdomain **1**.

## Compare two runs

```bash
python3 tools/compare_experiments.py \
  --experiments penalty30_min700_cap21 penalty55_min700_cap21
```

Writes in this folder:

- `experiment_comparison_summary.csv` — one row per experiment (Good/OK/Weak counts, key magnet frequencies)
- `anchor_comparison_by_experiment.csv` — each anchor × experiment
- `magnet_comparison_final30.csv` — side-by-side magnet counts + delta

## Pipeline (match + summarize + archive + compare)

```bash
pwsh ./Run-MetaMatchPipeline.ps1 \
  -ArchiveAsExperiment penalty55_min700_cap21 \
  -CompareWith penalty30_min700_cap21
```

Requires `gh auth login` first.

## Live vs archive

- `runs/_summaries/` — **current** run (overwritten by pipeline)
- `runs/experiments/<id>/` — **saved** run (never overwritten unless you re-archive same id)
