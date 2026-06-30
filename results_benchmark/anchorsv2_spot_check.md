# anchorsv2 spot-check (read-only)

Archive: `runs/experiments/penalty300_min700_cap22_anchorsv2/manual-ml-py/`

Same penalty (300), min (700), cap (2/2), and query overrides as **queryv2**. **24 anchors total** — the queryv2 20 plus **four additions** in `recommended_anchors_top_v2.csv`: `scikit-learn/scikit-learn`, `mlflow/mlflow`, `treeverse/dvc`, `pytorch/vision`.

## Retrieval hygiene (anchorsv2 sensitivity run)

- Top-5 magnet hits: **0**
- Good / OK / Weak: **24 / 0 / 0** (24 anchors; do not compare head-to-head “24 vs 20 Good” with queryv2)
- Lightning / Keras / Streamlit in final 30: **2 / 2 / 2**

Magnets/Good-OK-Weak measure **GitHub retrieval hygiene**, not REDUX similarity.

## Proxy stability vs queryv2 (shared folder slugs)

On the **20** folder slugs present in both archives, mean top-5 Jaccard = **0.96** (**17/20** at 1.0). Partial proxy-set drift: `explosion/spaCy` and `huggingface/datasets` (0.67), `jina-ai/serve` (0.80). See `archives/metamatch_sensitivity/anchorsv2_overlap.csv` (symlink: `anchorsv2_overlap.csv`).

Four **added** anchors use different folders and are scored separately in REDUX:

| Added anchor | Folder slug | Notes |
|--------------|-------------|-------|
| scikit-learn/scikit-learn | scikit-learn-scikit-learn | ML / sklearn ecosystem neighbors |
| mlflow/mlflow | mlflow-mlflow | MLOps / experiment tracking neighbors |
| treeverse/dvc | treeverse-dvc | Thin pool (2 qualified in final 30) |
| pytorch/vision | pytorch-vision | CV / detection neighbors |

## REDUX proxy similarity

Per-anchor CSVs, rollup, and run manifest: `results_benchmark/anchorsv2_redux/` via `tools/score_metamatch_proxies_redux.py` or `tools/run_anchorsv2_redux.sh`. This rollup is a **full independent 24-anchor rerun** (all 24 anchors freshly scored from the frozen archive; `run_manifest.json` shows `n_pair_scores: 116`, all 24 anchors scored), not a bootstrap.
