# anchorsv2 spot-check (read-only)

Archive: `runs/experiments/penalty300_min700_cap22_anchorsv2/manual-ml-py/`

Same penalty (300), min (700), cap (2/2), and query overrides as **queryv2**. Four anchor swaps vs `recommended_anchors_top.csv` → `recommended_anchors_top_v2.csv` (sklearn, mlflow, dvc, vision replace prior anchors).

## Retrieval hygiene (anchorsv2 sensitivity run)

- Top-5 magnet hits: **0**
- Good / OK / Weak: **24 / 0 / 0** (24 anchors; do not compare head-to-head “24 vs 20 Good” with queryv2)
- Lightning / Keras / Streamlit in final 30: **2 / 2 / 2**

Magnets/Good-OK-Weak measure **GitHub retrieval hygiene**, not REDUX similarity.

## Proxy stability vs queryv2 (shared folder slugs)

On the **20** folder slugs present in both archives, top-5 proxy sets match queryv2 (Jaccard = 1.0 on all rows). See `archives/metamatch_sensitivity/anchorsv2_overlap.csv` (symlink: `anchorsv2_overlap.csv`).

Four **swapped** anchors use different folders and are scored separately in REDUX:

| Swapped anchor | Folder slug | Notes |
|----------------|-------------|-------|
| scikit-learn/scikit-learn | scikit-learn-scikit-learn | Replaces prior sklearn-family anchor |
| mlflow/mlflow | mlflow-mlflow | MLOps / experiment tracking neighbors |
| treeverse/dvc | treeverse-dvc | Thin pool (2 qualified in final 30) |
| pytorch/vision | pytorch-vision | CV / detection neighbors |

## REDUX proxy similarity

Per-anchor CSVs, rollup, and run manifest: `results_benchmark/anchorsv2_redux/` via `tools/score_metamatch_proxies_redux.py` or `tools/run_anchorsv2_redux.sh`.
