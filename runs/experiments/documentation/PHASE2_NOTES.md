# Phase 2 — query tuning and alternate anchors

Completed 2026-05-27. Log: `runs/experiments/phase2_*.log` (latest: `phase2_20260527_061853.log`).

## Hyperparameter baseline (same 20 anchors)

Hyperparam grid best before query work: **penalty 300, min 700, cap 2/2** (`penalty300_min700_cap22`).  
**Overall winner after query + fallback tuning:** `penalty300_min700_cap22_queryv2` (see [WINNER.md](WINNER.md)).

| Metric | penalty 30 | penalty 300 | queryv2 |
|--------|--------------|---------------|---------|
| Top-five magnet hits (sum) | 30 | 5 | 0 |
| Good / OK / Weak | 10/2/8 | 20/0/0 | 20/0/0 |
| Lightning / Keras / Streamlit in final 30 | ~12/12/12 | 7/8/5 | 2/2/1 |

## Query and fallback changes

1. UI subdomain in `Get-Subdomain` (before `deep-learning` so Streamlit/Gradio avoid generic DL topic queries).
2. Per-anchor overrides: `metamatch_anchor_query_overrides.json`.
3. Fallback limits: max 1 unqualified in top 5, max 12 unqualified in final 30.

Archive: `penalty300_min700_cap22_queryv2/`.

## Alternate anchor set

`recommended_anchors_top_v2.csv` — four swaps vs original list:

- NLP-progress → scikit-learn
- ML-From-Scratch → mlflow
- recommenders → treeverse/dvc
- pytorch-lightning → pytorch/vision

Same penalty/query settings. Archive: `penalty300_min700_cap22_anchorsv2/`.

## Open work

REDUX / full similarity not run on these archives yet. See `REDUX_REPRO.md` and `proxytool_REDUX_4_REPRO.ipynb`.

Applied defaults: `metamatch_hyperparams.json`, `WINNER.md`.
