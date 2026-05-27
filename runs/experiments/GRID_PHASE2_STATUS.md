# Phase-2 grid — stopped early

**Stopped:** 2026-05-22 (after run 4 of 60 completed; run 5 aborted if in progress)

## Progress

| Metric | Value |
|--------|--------|
| Planned | 60 experiments (penalty 110–200 × min 700/750/800 × caps 11/12/21/22) |
| **Completed** | **4** |
| **Remaining** | **56** |
| Champion to beat | `penalty100_min700_cap21` |

## Completed archives (full 20 anchors each)

| # | experiment_id | Params | Notes |
|---|---------------|--------|--------|
| 1 | `penalty110_min700_cap11` | penalty=110, min=700, cap=1/1 | |
| 2 | `penalty110_min700_cap12` | penalty=110, min=700, cap=1/2 | |
| 3 | `penalty110_min700_cap21` | penalty=110, min=700, cap=2/1 | |
| 4 | `penalty110_min700_cap22` | penalty=110, min=700, cap=2/2 | |

All four reported **Good=15, OK=3, Weak=2, Lightning final30=11** at archive time.

## Stopped before / during

- **Next queued:** `penalty110_min750_cap11` (penalty=110, min=750, cap=1/1) — grid halted here; do not use partial `runs/manual-ml-py` for this config without re-running.

## Partial result vs champion

Among the 4 completed runs, all beat `penalty100_min700_cap21` on **TotalMagnetsInTop5** (17 vs 18), same **Weak=2**. Best of the four: `penalty110_min700_cap22` (cap 2/2).

**Script defaults left at penalty100 / cap 2/1** until you run a shorter confirmation screen. See `WINNER.md` for the full comparison table.

## Targeted runs (completed)

| experiment_id | penalty | min | cap | Top5 mag | Weak |
|---------------|---------|-----|-----|----------|------|
| `penalty150_min700_cap22` | 150 | 700 | 2/2 | 12 | 2 |
| `penalty200_min600_cap22` | 200 | 600 | 2/2 | (see archive) | 1 |

## Batch 3 (in progress) — cap 2/2 for all; see `CAP_ANALYSIS.md`

| experiment_id | penalty | min |
|---------------|---------|-----|
| `penalty150_min600_cap22` | 150 | 600 |
| `penalty200_min700_cap22` | 200 | 700 |
| `penalty175_min700_cap22` | 175 | 700 |
| `penalty175_min600_cap22` | 175 | 600 |

```bash
bash runs/experiments/run_targeted_batch3_tmux.sh
tmux attach -t metamatch-batch3
```

## How to resume later

```bash
python3 tools/run_metamatch_grid.py   # skips the 4 archives above
```

Or a smaller fast screen (see README phase-2 section).

## Logs

- `grid_phase2_tmux.log`
- `grid_phase2_progress.jsonl` (4 lines)
