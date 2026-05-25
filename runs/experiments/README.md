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

`penalty{W}_min{SCORE}_cap{owner}{sub}` — e.g. `cap21` = MaxPerOwner **2**, MaxPerOwnerPerSubdomain **1**.

Suffix `_nofallback` = `AllowFallbackFill` disabled.

## Experiment matrix

| Status | experiment_id | Penalty | MinScore | MaxOwner | MaxSub | Fallback | Notes |
|--------|---------------|---------|----------|----------|--------|----------|-------|
| done | `penalty30_min700_cap21` | 30 | 700 | 2 | 1 | on | Baseline |
| done | `penalty55_min700_cap21` | 55 | 700 | 2 | 1 | on | Improved Weak 8→5 |
| done | `penalty75_min700_cap21` | 75 | 700 | 2 | 1 | on | Higher penalty |
| **winner** | `penalty100_min700_cap21` | 100 | 700 | 2 | 1 | on | Best top-5 + Weak; applied as default |
| done | `penalty55_min750_cap21` | 55 | 750 | 2 | 1 | on | No gain vs 55 |
| done | `penalty55_min700_cap11` | 55 | 700 | 1 | 1 | on | No gain vs 55 |
| done | `penalty55_min700_cap21_nofallback` | 55 | 700 | 2 | 1 | off | Minor Lightning drop only |

See [EXPERIMENT_LOG.md](EXPERIMENT_LOG.md) for run dates and outcomes.

## Commands (from repo root)

From **bash**, use colon syntax for numeric params (e.g. `-CrossAnchorFreqPenaltyWeight:75`). From **pwsh** directly, space syntax works.

```powershell
# Run 1
pwsh ./Run-MetaMatchPipeline.ps1 -CrossAnchorFreqPenaltyWeight:75 `
  -ArchiveAsExperiment penalty75_min700_cap21 `
  -CompareWith penalty55_min700_cap21,penalty30_min700_cap21

# Run 2
pwsh ./Run-MetaMatchPipeline.ps1 -CrossAnchorFreqPenaltyWeight:100 `
  -ArchiveAsExperiment penalty100_min700_cap21 `
  -CompareWith penalty55_min700_cap21,penalty30_min700_cap21

# Run 3
pwsh ./Run-MetaMatchPipeline.ps1 -MinimumScore:750 `
  -ArchiveAsExperiment penalty55_min750_cap21 `
  -CompareWith penalty55_min700_cap21,penalty30_min700_cap21

# Run 4
pwsh ./Run-MetaMatchPipeline.ps1 -MaxPerOwner:1 `
  -ArchiveAsExperiment penalty55_min700_cap11 `
  -CompareWith penalty55_min700_cap21,penalty30_min700_cap21

# Run 5
pwsh ./Run-MetaMatchPipeline.ps1 -NoFallbackFill `
  -ArchiveAsExperiment penalty55_min700_cap21_nofallback `
  -CompareWith penalty55_min700_cap21,penalty30_min700_cap21
```

Or run the full sweep script (uses `-ExperimentPreset` for reliable tuning from bash):

```bash
bash runs/experiments/run_hyperparam_sweep.sh
```

Presets: `penalty75`, `penalty100`, `min750`, `cap11`, `nofallback`.

## Phase-2 grid (penalty 110–200 × min 700/750/800 × caps)

60 combinations. Champion to beat: **`penalty100_min700_cap21`**.

```bash
python3 tools/run_metamatch_grid.py          # all 60 runs (~50+ hours)
python3 tools/run_metamatch_grid.py --dry-run
python3 tools/run_metamatch_grid.py --only penalty150_min700_cap21
python3 tools/run_metamatch_grid.py --finalize-only   # after partial grid
```

Progress: `runs/experiments/grid_phase2_progress.jsonl`  
Background: `bash runs/experiments/run_grid_phase2.sh`

**Restart in tmux (recommended — attach anytime):**

```bash
bash runs/experiments/run_grid_phase2_tmux.sh          # stop old jobs + start
tmux attach -t metamatch-grid                         # live view (Ctrl+B D to detach)
bash runs/experiments/run_grid_phase2_tmux.sh stop    # kill grid + tmux
tail -f runs/experiments/grid_phase2_tmux.log
```

## Compare experiments

```bash
python3 tools/compare_experiments.py \
  --experiments penalty30_min700_cap21 penalty55_min700_cap21 penalty75_min700_cap21
```

Outputs in this folder:

- `experiment_comparison_summary.csv` — one row per experiment
- `anchor_comparison_by_experiment.csv` — per anchor × experiment
- `magnet_comparison_final30.csv` — magnet frequencies + delta

## Pick winner (after sweep)

```bash
python3 tools/pick_experiment_winner.py
```

## Optimization metrics (in order)

1. **TotalMagnetsInTop5** (lower is better)
2. **MagnetFinal30** counts for Lightning / Keras / Streamlit (lower is better)
3. **Weak** count (lower is better); guardrail: most anchors still have ~30 `30_Matches.csv` rows

## Live vs archive

- `runs/_summaries/` — **current** run (overwritten by pipeline)
- `runs/experiments/<id>/` — **saved** run
