# UTF-8 Mojibake Fix Summary

**Date:** 2026-06-05  
**Scope:** Text files (`*.md`, `*.txt`, `*.py`, `*.ps1`, `*.json`, `*.csv`, `*.ipynb`) under the research repo, excluding `.git`, `node_modules`, `agent-transcripts`, and binary assets.

## Files fixed (3)

| File | Changes |
|------|---------|
| `README.md` | ~98 mojibake sequences repaired (primary user complaint). Replaced curly/smart quotes with straight `"`/`'`, em/en dashes with `--`/`-`, arrows with `->`/`<->`, and `Spearman Ï` with `Spearman rho`. |
| `recommended_anchors_top.csv` | Em dash in Streamlit description (`--`); stripped cloud-emoji mojibake prefix on jina-ai/serve row; restored rocket emoji on ultralytics/yolov5 row. |
| `recommended_anchors_top_v2.csv` | Same fixes as `recommended_anchors_top.csv`. |

## Files checked — no `â€` / `â€œ` patterns found

These were explicitly searched per user request and were already clean:

- `results_benchmark/WORK_REVIEW.md`
- `results_benchmark/VALIDATION_MEMO.md`
- `results_benchmark/PAPER_PACKAGE.md`
- `results_benchmark/README.md`
- `REDUX_REPRO.md`
- `runs/README.md`
- `runs/experiments/README.md`
- `runs/experiments/documentation/*.md` (CAP_ANALYSIS, PHASE2_NOTES, WINNER, GRID_PHASE2_STATUS, etc.)
- All `*.py`, `*.ps1`, `*.json`, `*.ipynb` in the repo

## Replacement policy applied

| Mojibake | Replacement |
|----------|-------------|
| `â€œ` / `â€` (quotes) | `"` |
| `â€™` / `â€˜` | `'` |
| `â€"` (em dash, incl. double-encoded `â€"`) | `--` |
| `â€"` (en dash, incl. double-encoded `â€"`) | `-` |
| `â†'` / `â†"` | `->` / `<->` |
| `â€¦` | `...` |
| `Ï` (Spearman rho) | `rho` |

ASCII-first choices were used for GitHub/Markdown rendering consistency.

## Verification

Post-fix grep across all targeted extensions:

```
rg 'â€|â€œ' --glob '*.{md,txt,py,ps1,json,csv,ipynb}'
```

**Result:** 0 matches.

## Skipped / residual notes

| Item | Reason |
|------|--------|
| `30_Matches.csv` | Contains GitHub-ingested emoji/math-bold mojibake (`ðŸŒ€`, `ð\x9d—¦…`) — different triple-encoding chain, not the `â€`/`â€œ` class. Left unchanged to avoid corrupting match data. |
| `recommended_anchors_top*.csv` — `bbfamily/abu` description | Chinese repo description remains partially garbled (multi-pass UTF-8 mis-encoding from GitHub metadata). Does not match `â€`/`â€œ` patterns; needs `ftfy` or source re-fetch to repair safely. |
| `runs/2026-05-03-batch/**` | Contains legitimate UTF-8 (e.g. Vietnamese `Một cuốn sách…`) — not mojibake. |
| `.pdf`, images, binary notebooks | Excluded per task instructions. |
| `agent-transcripts/`, `.git/`, `node_modules/` | Excluded per task instructions. |

## README status

`README.md` now renders cleanly: straight quotes, ASCII dashes (`--`), ASCII arrows (`->`), and readable section headings with no `â€`/`â€œ` sequences.

---

## Appendix: 2026-06-05 encoding investigation — skipped (runs OK)

**Verdict:** No edits applied to `30_Matches.csv`, `recommended_anchors_top*.csv` `bbfamily/abu` row, or any queryv2 archive outputs.

### bbfamily/abu anchor

| Check | Result | Evidence |
|-------|--------|----------|
| MetaMatch run completed | **OK** | `runs/experiments/penalty300_min700_cap22_queryv2/manual-ml-py/bbfamily-abu/run_manifest.json` — 178 scored, 23 final |
| `30_Matches.csv` structure | **OK** | Valid `AnchorRepo`, `CandidateRepo`, `Score`, `Rank` (ranks 1–23); URLs intact |
| Retrieval hygiene tier | **Good** | `anchor_evaluation.csv` row: `Good,0,0,0` (0 top-5 magnets) |
| REDUX bridge | **OK** | `queryv2_redux/bbfamily-abu.csv` — 5 scored pairs; `rollup_summary.csv` metadata_mean=96.02 |
| Anchor metadata at run time | **OK** | `anchor_repo.json` has correct UTF-8 Chinese description from GitHub API |
| Garbled seed description | **Cosmetic only** | `recommended_anchors_top.csv` / `v2` row 21 still shows mojibake (`é˜¿å¸ƒ…`); did not affect run (MetaMatch re-fetches anchor metadata) |

### 30_Matches.csv emoji/math-bold mojibake (queryv2 archive)

| Scope | Finding |
|-------|---------|
| `runs/**/30_Matches.csv` (573 files) | **0** `ðŸ` / `â€` / `Ã` patterns — archive is clean |
| Display-only quirks in queryv2 | `:neckbeard:` GitHub emoji shortcode; valid UTF-8 Chinese (`交易猫数据系统`) — not functional corruption |
| Functional columns | `AnchorRepo`, `CandidateRepo`, `CandidateUrl`, `Score`, `Rank`, `Qualified` — all valid across sampled anchors (`bbfamily-abu`, `apache-airflow`, `gradio-app-gradio`) |
| Root `./30_Matches.csv` | Contains `ðŸŒ€` mojibake in `Description` only (lines 28, 31) — **outside** frozen queryv2 archive; left unchanged |

### Validation gates

All paper gates **PASS**; no failure attributable to encoding:

- **G5** queryv2 winner: 0 magnets, 20/0/0 Good/OK/Weak — `PAPER_PACKAGE.md`
- **G6** queryv2 REDUX bridge: 20 anchors × top-5, `bbfamily/abu` metadata_mean=96.02 — `queryv2_redux/rollup_summary.csv`
- **G8** MetaMatch retune: **NO** (G6 passed)

**Decision:** Per "fix only if runs failed" rule — skipped. Garbled `bbfamily/abu` description in anchor seed CSV and any display-column emoji artifacts did not break retrieval, scoring, or validation.
