# Paper package and decision gate

> **Current state:** [`WORK_REVIEW.md`](WORK_REVIEW.md) and [`../CANONICAL_RESULTS/`](../CANONICAL_RESULTS/) — v2 labeled cohort (24 pairs) is **primary**; v1 frozen as 10-pair demo. Two-stage system: MetaMatch `queryv2` retrieval → REDUX 4 scoring.

**Master work review:** `results_benchmark/WORK_REVIEW.md` (phase table, tag legend, cross-verification index).

**Source tags:** `[Reproducible]` ground-truth tooling · `[Anchor/Query]` MetaMatch/queryv2 bridge · `[Pre-existing]` WINNER arc · `[Analysis]` this memo and gate docs.

## Gate results


| Gate | Criterion                                             | Result   | Notes                                                                                                                                                                                                                         |
| ---- | ----------------------------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| G1   | Labeled strict `known_match` separates @ threshold 50 | **PASS** | **v2 primary:** strict metadata F1=**0.909** (`labeled_v2/labeled_strict_summary.csv`, 22-pair metric cohort). v1 demo: metadata F1=1.0 (`labeled/labeled_strict_summary.csv`) |
| G2   | Labeled lenient includes related pairs                | **PASS** | **v2 primary:** lenient metadata F1=**0.941** (`labeled_v2/labeled_summary.csv`; `target_uncertain` excluded). Bootstrap CIs in `labeled_v2/bootstrap_ci.csv`. v1 frozen: metadata F1=1.00 |
| G3   | Do not claim plausible `30_Pairs` as ground truth     | **PASS** | Use `labeled_scored_v2.json` (primary) + `labeled_scored.json` (v1) + limitations below |
| G4   | Cross-method agreement (authenticated, canonical)     | **PASS** | Authenticated n=30 (`full_summary_authenticated_n30.json`): ρ=**+0.69** (p=2.34e-5), Pearson r=**+0.66**, **go=true**, all agreement gates pass. The prior ρ≈−0.21 fail was a rate-limiting artifact (see methods note below) |
| G5   | queryv2 retrieval winner frozen                       | **PASS** | 0 magnets, 20/0/0 Good/OK/Weak                                                                                                                                                                                                |
| G6   | queryv2 proxy REDUX bridge                            | **PASS** | 20 anchors × top-5 metadata REDUX; thin anchors (jina 96.4%, ray 92.3%, airflow 95.4%, OpenBB 93.8% means) — `queryv2_redux/rollup_summary.csv`                                                                               |
| G7   | anchorsv2 sensitivity                                 | **PASS** | Mean top-5 Jaccard **0.96** on 20 shared slugs (17/20 at 1.0); REDUX bridge in `anchorsv2_redux/`                                                                                                                             |
| G8   | MetaMatch retune required?                            | **NO**   | G6 passed; do not re-archive queryv2                                                                                                                                                                                          |
| G9   | Downstream usefulness (informational)                 | **INFO** | Triage/search/scenario metrics for 24 anchors in `downstream_validation/` (20 queryv2 + 4 anchorsv2 additions; 3 CAIS-mapped + 21 metadata-heuristic); supports proxy triage story; not a pass/fail gate                     |


## Tables for paper

1. **MetaMatch arc:** penalty30 → penalty300 → queryv2 (`runs/experiments/documentation/WINNER.md`)
2. **Labeled ground truth (v2 primary):** `labeled_v2/labeled_summary.csv` + `labeled_v2/labeled_strict_summary.csv` + `labeled_v2/bootstrap_ci.csv`
3. **Labeled ground truth (v1 frozen demo):** `labeled/labeled_summary.csv` + `labeled/labeled_strict_summary.csv`
3. **Method comparison:** `metadata_discrimination_canonical.csv`, `continuous_scores_summary.csv`
4. **Proxy similarity:** `queryv2_redux/rollup_summary.csv` and `anchorsv2_redux/rollup_summary.csv`
5. **Anchor perturbation:** `anchorsv2_overlap.csv` + four additions in `PHASE2_NOTES.md`
6. **Downstream usefulness (G9):** `downstream_validation/SUMMARY.md` + CSVs

## Explicit limitations (include in paper)

- `30_Pairs.json` plausible pairs are a **realism** cohort, not verified ground truth.
- **Cross-method agreement holds once GitHub rate-limiting is removed.** The canonical authenticated n=30 run (`projected_pairs/full_summary_authenticated_n30.json`, same 10/10/10 allocation as the original baseline) gives Spearman ρ=**+0.69** (p=2.34e-5), Pearson r=**+0.66** (p=6.25e-5), **go=true** — clearing the `projected_pair_rubric.json` target (0.30). The authenticated n=25 current-rubric run (`full_summary_authenticated.json`) is consistent: ρ=**+0.78**, **go=true** (same sign, passes).
- **Honest methods note:** the original ρ=−0.21 (`full_summary.json`, **superseded unauthenticated artifact**, retained for transparency) was an artifact of **unauthenticated** GitHub rate-limiting — 38% of requests returned HTTP 403, starving the `target_uncertain` Search rows and injecting noise that dragged ρ negative. With a valid token at the same n=30 allocation the 403 share drops to 9.3% and ρ recovers to +0.69. Authentication drives the flip, not the rubric/n change.
- Labeled mirror pairs use GitHub-centric REDUX scoring when upstream is non-GitHub.
- Magnets / Good-OK-Weak measure retrieval hygiene, not test-scenario adequacy.

## Appendix: anchorsv2

Same penalty (300), min (700), cap (2/2), and query overrides as queryv2. **24 anchors total** — the queryv2 20 plus **four additions** in `recommended_anchors_top_v2.csv` (`mlflow/mlflow`, `pytorch/vision`, `scikit-learn/scikit-learn`, `treeverse/dvc`). On **20** folder slugs present in both archives, mean top-5 proxy Jaccard is **0.96** (**17/20** at 1.0; partial drift on `explosion/spaCy` and `huggingface/datasets` at 0.67, `jina-ai/serve` at 0.80; see `anchorsv2_overlap.csv`). The four added anchors use different folders and are reported separately, not as a higher Good count vs queryv2.

`**anchorsv2_redux/` is now a full independent 24-anchor REDUX rerun:** all 24 anchors were freshly scored from the `penalty300_min700_cap22_anchorsv2` archive (`run_manifest.json`: `n_pair_scores: 116`, all 24 anchors in `anchors_scored_this_run`), **replacing the earlier 17-fresh / 3-rescored / 96-reused bootstrap**. Per-anchor metadata-mean shifts vs that bootstrap are modest (overall mean 92.82 → 94.04; largest: `huggingface/transformers` +7.59, `ultralytics/yolov5` +4.36, `mlflow/mlflow` +4.00, `explosion/spaCy` +3.32). Reproduce: `bash tools/run_anchorsv2_redux.sh full`.