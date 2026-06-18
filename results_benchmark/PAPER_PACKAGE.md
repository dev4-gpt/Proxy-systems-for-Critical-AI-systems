# Paper package and decision gate

**Master work review:** `results_benchmark/WORK_REVIEW.md` (phase table, tag legend, cross-verification index).

**Source tags:** `[Reproducible]` ground-truth tooling · `[Anchor/Query]` MetaMatch/queryv2 bridge · `[Pre-existing]` WINNER arc · `[Analysis]` this memo and gate docs.

## Gate results

| Gate | Criterion | Result | Notes |
|------|-----------|--------|-------|
| G1 | Labeled strict `known_match` separates @ threshold 50 | **PASS** | metadata/code_centric/cross_language F1=1.0 (`labeled_strict_summary.csv`) |
| G2 | Labeled lenient includes related pairs | **PASS** | metadata F1=1.00 (`target_uncertain` excluded per cohort rule); dynamic weaker (F1=0.67) |
| G3 | Do not claim plausible `30_Pairs` as ground truth | **PASS** | Use `labeled_scored.json` + limitations below |
| G4 | Cross-method agreement (authenticated, canonical) | **PASS** | Authenticated n=30 (`full_summary_authenticated_n30.json`): ρ=**+0.69** (p=2.34e-5), Pearson r=**+0.66**, **go=true**, all agreement gates pass. The prior ρ≈−0.21 fail was a rate-limiting artifact (see methods note below) |
| G5 | queryv2 retrieval winner frozen | **PASS** | 0 magnets, 20/0/0 Good/OK/Weak |
| G6 | queryv2 proxy REDUX bridge | **PASS** | 20 anchors × top-5 metadata REDUX; thin anchors (jina 96.4%, ray 92.3%, airflow 95.4%, OpenBB 93.8% means) — `queryv2_redux/rollup_summary.csv` |
| G7 | anchorsv2 sensitivity | **PASS** | Mean top-5 Jaccard **0.96** on 20 shared slugs (17/20 at 1.0); REDUX bridge in `anchorsv2_redux/` |
| G8 | MetaMatch retune required? | **NO** | G6 passed; do not re-archive queryv2 |

## Tables for paper

1. **MetaMatch arc:** penalty30 → penalty300 → queryv2 (`runs/experiments/documentation/WINNER.md`)
2. **Labeled ground truth:** `labeled/labeled_summary.csv` + `labeled_strict_summary.csv`
3. **Method comparison:** `metadata_discrimination_canonical.csv`, `continuous_scores_summary.csv`
4. **Proxy similarity:** `queryv2_redux/rollup_summary.csv` and `anchorsv2_redux/rollup_summary.csv`
5. **Anchor perturbation:** `anchorsv2_overlap.csv` + four swaps in `PHASE2_NOTES.md`

## Explicit limitations (include in paper)

- `30_Pairs.json` plausible pairs are a **realism** cohort, not verified ground truth.
- **Cross-method agreement holds once GitHub rate-limiting is removed.** The canonical authenticated n=30 run (`projected_pairs/full_summary_authenticated_n30.json`, same 10/10/10 allocation as the original baseline) gives Spearman ρ=**+0.69** (p=2.34e-5), Pearson r=**+0.66** (p=6.25e-5), **go=true** — clearing the `projected_pair_rubric.json` target (0.30). The authenticated n=25 current-rubric run (`full_summary_authenticated.json`) is consistent: ρ=**+0.78**, **go=true** (same sign, passes).
- **Honest methods note:** the original ρ=−0.21 (`full_summary.json`, **superseded unauthenticated artifact**, retained for transparency) was an artifact of **unauthenticated** GitHub rate-limiting — 38% of requests returned HTTP 403, starving the `target_uncertain` Search rows and injecting noise that dragged ρ negative. With a valid token at the same n=30 allocation the 403 share drops to 9.3% and ρ recovers to +0.69. Authentication — not the rubric/n change — drives the flip.
- Labeled mirror pairs use GitHub-centric REDUX scoring when upstream is non-GitHub.
- Magnets / Good-OK-Weak measure retrieval hygiene, not test-scenario adequacy.

## Appendix: anchorsv2

Same penalty (300), min (700), cap (2/2), and query overrides as queryv2. Four anchor swaps in `recommended_anchors_top_v2.csv`. On **20** folder slugs present in both archives, mean top-5 proxy Jaccard is **0.96** (**17/20** at 1.0; partial drift on `explosion/spaCy` and `huggingface/datasets` at 0.67, `jina-ai/serve` at 0.80 — see `anchorsv2_overlap.csv`). The four swapped anchors use different folders and are reported separately—not as a higher Good count vs queryv2.

**`anchorsv2_redux/` assembly:** four swapped anchors scored fresh; **17** shared slugs copied from `queryv2_redux/` (identical proxy URLs and metadata means); **3** shared slugs rescored (`apache/airflow`, `jina-ai/serve`, `ray-project/ray`). Full independent rerun: `bash tools/run_anchorsv2_redux.sh full`.
