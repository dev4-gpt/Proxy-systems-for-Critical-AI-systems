# CAIS validation memo

Generated as part of the final validation plan (feedback + queryv2 / anchorsv2 MetaMatch results).

**Master work review:** `WORK_REVIEW.md` — executive summary, phases A–G, repro commands, and source tags (`[Reproducible]`, `[Anchor/Query]`, `[Pre-existing]`, `[Analysis]`).

## Reviewer concern 1 — Ground truth

**Problem:** `30_Pairs.json` “plausible” pairs are script-discovered; they must not be claimed as ground truth.

**Response:** Evidence-backed cohort in `configs/labeled_benchmark_pairs.json`, scored in `results_benchmark/labeled_scored.json`, metrics in `results_benchmark/labeled/`.

| Cohort | Pairs | Role |
|--------|-------|------|
| `known_match` (5) | Official/read-only mirrors | Strict ground truth |
| `known_related` (2) | Fork/lineage (MariaDB/MySQL, LibreOffice/OpenOffice) | Lenient positive |
| `known_non_match` (2) | Cross-domain hard negatives | Negative |
| `target_uncertain` (1) | MONAI vs TensorFlow | Realism only — **exclude from P/R/F1 claims** |

### Labeled metrics @ threshold 50 (0–100 scale)

**Lenient** (`known_match` + `known_related` vs `known_non_match`; `target_uncertain` excluded from P/R/F1): see `labeled/labeled_summary.csv` (identical to `labeled/labeled_lenient_summary.csv`).

| Method | F1 | Accuracy | Pos/neg mean gap |
|--------|-----|----------|------------------|
| metadata | 1.00 | 1.00 | 82.3 |
| code_centric | 0.83 | 0.78 | 68.8 |
| cross_language | 0.92 | 0.89 | 63.5 |
| dynamic | 0.67 | 0.56 | 9.3 |

**Strict** (`known_match` only): see `labeled/labeled_strict_summary.csv`.

| Method | F1 | Accuracy | Pos/neg mean gap |
|--------|-----|----------|------------------|
| metadata | 1.00 | 1.00 | 88.2 |
| code_centric | 1.00 | 1.00 | 85.3 |
| cross_language | 1.00 | 1.00 | 78.2 |
| dynamic | 0.80 | 0.71 | 28.5 |

Sensitivity: `labeled/threshold45/` and `labeled/threshold55/`.

**Repo access:** `results_benchmark/repo_access_validation.csv` (18 unique URLs; `ls_remote_ok` for labeled set).

**Mirror scoring note:** Non-GitHub upstream URLs are validated via git; REDUX scores use GitHub mirror identity / pairwise rows from `known_mirror_benchmark_canonical_candidate_rows.csv` where applicable.

---

## Reviewer concern 2 — Testing / QA / security outcomes

**Problem:** Similarity must connect to test-relevant outcomes, not retrieval metrics alone.

**Response:**

1. **MetaMatch queryv2** — retrieval hygiene (0 top-5 magnets, 20/0/0 Good/OK/Weak). Documented in `runs/experiments/documentation/WINNER.md` and `results_benchmark/queryv2_spot_check.md`.
2. **REDUX on proxies** — `results_benchmark/queryv2_redux/` and `results_benchmark/anchorsv2_redux/` (anchor→top-k proxy similarity).
3. **Case study** — `results_benchmark/testing_case_study_airflow.md` (anchor → proxies → CAIS scenario mapping).

Do **not** equate magnets/Good-OK-Weak with test adequacy.

---

## Reviewer concern 3 — Statistics and method positioning

### Discrimination (similar vs dissimilar)

From `metadata_discrimination_canonical.csv` (Test 2 similar + 30-pair similar vs Test 3 dissimilar):

| Metric | Value |
|--------|-------|
| Similar mean metadata % | 94.4 |
| Dissimilar mean metadata % | 4.7 |
| Gap | 89.7 |
| Pairwise AUC-like | 1.0 |

Metadata **separates** cohorts even when cross-method rank agreement is weak.

### Cross-method agreement (authenticated, canonical)

From the **canonical authenticated** run `projected_pairs/full_summary_authenticated_n30.json` (projected-pair workflow, n=30, original 10/10/10 allocation, telemetry `authenticated=true`):

| Stat | Value | vs rubric `minimum_spearman: 0.30` |
|------|-------|-------------------------------------|
| Spearman ρ | **+0.69** (p=2.34e-5) | **Passes** |
| Pearson r | **+0.66** (p=6.25e-5) | Passes |
| Paired t | 2.574 (p=0.015) | n/a |
| Decision `go` | **true** | agreement gates pass |
| API non-200 ratio | 0.093 (9.3% 403) | healthy (authenticated) |

The authenticated n=25 current-rubric run (`full_summary_authenticated.json`) is consistent: ρ=**+0.78** (p=4.87e-6), Pearson r=**+0.78**, **go=true** — same sign, also passes.

**Honest methods note:** The original frozen run `projected_pairs/full_summary.json` reported Spearman ρ=**−0.21** (p=0.26, Pearson −0.35), `go=false`. That negative result was an **artifact of unauthenticated GitHub rate-limiting**: 38% of requests returned HTTP 403 (`remaining_min_seen=0`), starving the `target_uncertain` GitHub-Search rows and injecting noise that dragged the rank correlation negative. Holding the allocation fixed at n=30 and changing **only** authentication moves ρ from −0.21 to +0.69 (fails→passes), so authentication — not the rubric/n change — is the driver. `full_summary.json` is **retained unchanged as the superseded unauthenticated artifact** for transparency; it is **not** deleted.

**Interpretation:** With rate-limiting removed, the four methods **agree** on pair ranking (ρ≈+0.69–0.78, `go=true`). The methods remain complementary multi-view signals (metadata fingerprints vs clone vs dynamic vs cross-language), but the corrected canonical evidence supports — rather than refutes — cross-method rank correlation.

### Mirror vs non-mirror continuous scores

From `continuous_scores_summary.csv`:

- **Mirror identity:** code_centric/dynamic strong; metadata rank-pct ~46% (expected under contrastive pool).
- **Non-mirror pairs:** metadata gap ~10.3 pts (true vs false match).

---

## MetaMatch experiment arc (queryv2 / anchorsv2)

| Experiment | Anchors | Top5 magnets | Good/OK/Weak | Role |
|------------|---------|--------------|--------------|------|
| penalty30 | 20 | 30 | 10/2/8 | Baseline |
| penalty300 cap22 | 20 | 5 | 20/0/0 | Hyperparam step |
| **queryv2** | 20 | **0** | **20/0/0** | **Primary winner** |
| anchorsv2 | 24 (4 swaps) | 0 | 24 Good | Anchor-list sensitivity |

**anchorsv2:** Same penalty/query; 4 anchor swaps (sklearn, mlflow, dvc, vision). On 20 shared folder slugs, mean top-5 Jaccard = **0.96** (**17/20** at 1.0; `explosion/spaCy` and `huggingface/datasets` at 0.67, `jina-ai/serve` at 0.80) — `results_benchmark/anchorsv2_overlap.csv`. REDUX bridge in `anchorsv2_redux/` (116 pair scores) — now a **full independent 24-anchor rerun** (all 24 anchors freshly scored; replaces the earlier 17-fresh / 3-rescored / 96-reused bootstrap; overall metadata mean 92.82 → 94.04, largest per-anchor shifts `huggingface/transformers` +7.59, `ultralytics/yolov5` +4.36, `mlflow/mlflow` +4.00). Do not compare “24 Good” vs “20 Good” as a head-to-head win.

---

## Artifacts index

| Path | Contents |
|------|----------|
| `run_manifest.json` | Repro SHA256 + auth snapshot |
| `projected_pairs/full_summary_authenticated_n30.json` | **Canonical** cross-method stats (authenticated, n=30): ρ=+0.69, go=true |
| `projected_pairs/full_summary_authenticated.json` | Authenticated n=25 (current rubric): ρ=+0.78, go=true |
| `projected_pairs/full_summary.json` | Superseded **unauthenticated** artifact (ρ=−0.21, 38% 403) — retained for transparency |
| `labeled_scored.json` | 10-pair REDUX scores |
| `labeled/` | Threshold 50/45/55 + strict/lenient summaries |
| `queryv2_redux/` | Proxy similarity (queryv2 winner; pilot + full) |
| `anchorsv2_redux/` | Proxy similarity (anchorsv2 sensitivity; 24 anchors) |
| `anchorsv2_overlap.csv` | Anchor perturbation stability (→ `archives/metamatch_sensitivity/`) |
| `README.md` | Directory map; historical CSVs under `archives/` |
| `PAPER_PACKAGE.md` | Gate checklist + limitations |
