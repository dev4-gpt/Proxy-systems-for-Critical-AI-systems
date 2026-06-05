# Paper package and decision gate

## Gate results

| Gate | Criterion | Result | Notes |
|------|-----------|--------|-------|
| G1 | Labeled strict `known_match` separates @ threshold 50 | **PASS** | metadata/code_centric/cross_language F1=1.0 (`labeled_strict_summary.csv`) |
| G2 | Labeled lenient includes related pairs | **PASS** | metadata F1=0.93; dynamic weaker (F1=0.62) |
| G3 | Do not claim plausible `30_Pairs` as ground truth | **PASS** | Use `labeled_scored.json` + limitations below |
| G4 | Spearman reported honestly | **PASS** | ρ≈-0.21 documented; rubric 0.30 not met |
| G5 | queryv2 retrieval winner frozen | **PASS** | 0 magnets, 20/0/0 Good/OK/Weak |
| G6 | queryv2 proxy REDUX bridge | **PASS** | 20 anchors × top-5 metadata REDUX; thin anchors (jina 96.4%, ray 92.3%, airflow 95.4%, OpenBB 93.8% means) — `queryv2_redux/rollup_summary.csv` |
| G7 | anchorsv2 sensitivity | **PASS** | Jaccard 1.0 on 20 shared anchors; REDUX bridge in `anchorsv2_redux/` |
| G8 | MetaMatch retune required? | **NO** | G6 passed; do not re-archive queryv2 |

## Tables for paper

1. **MetaMatch arc:** penalty30 → penalty300 → queryv2 (`runs/experiments/documentation/WINNER.md`)
2. **Labeled ground truth:** `labeled/labeled_summary.csv` + `labeled_strict_summary.csv`
3. **Method comparison:** `metadata_discrimination_canonical.csv`, `continuous_scores_summary.csv`
4. **Proxy similarity:** `queryv2_redux/rollup_summary.csv` and `anchorsv2_redux/rollup_summary.csv`
5. **Anchor perturbation:** `anchorsv2_overlap.csv` + four swaps in `PHASE2_NOTES.md`

## Explicit limitations (include in paper)

- `30_Pairs.json` plausible pairs are a **realism** cohort, not verified ground truth.
- Cross-method Spearman **below** `projected_pair_rubric.json` target (0.30); methods are complementary views.
- Labeled mirror pairs use GitHub-centric REDUX scoring when upstream is non-GitHub.
- Magnets / Good-OK-Weak measure retrieval hygiene, not test-scenario adequacy.

## Appendix: anchorsv2

Same penalty (300), min (700), cap (2/2), and query overrides as queryv2. Four anchor swaps in `recommended_anchors_top_v2.csv`. On 20 folder slugs present in both archives, top-5 proxy sets are **identical** (Jaccard = 1.0). The four swapped anchors use different folders and are reported separately in the anchor list—not as a higher Good count vs queryv2.
