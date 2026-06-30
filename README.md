# Proxytool: Metadata-Driven Proxy Discovery for Critical AI Systems (CAIS)

Executable research code aligned with:

**Mark Kennedy, Joanna F. DeFranco & Philip A. Laplante**,  
*"Discovering Proxy Systems to Test Critical AI Systems: A Metadata-Driven Software Similarity Approach"* (IEEE Computer, 2026).

---

## What this repository is

Research code for **CAIS proxy discovery**: given a Critical AI System anchor you cannot fully inspect, find and score **open-source proxy repositories** that plausibly stand in for safety-oriented testing. The repo holds:

- **MetaMatch** — GitHub retrieval and ranking (Stage 1)
- **REDUX 4** — four-method similarity scoring (Stage 2)
- A **completed validation pass** (labeled ground truth, proxy bridges, gates G1–G9) under `results_benchmark/`, frozen for review in [`CANONICAL_RESULTS/`](CANONICAL_RESULTS/)
- The original **paper pipeline notebook** (`proxytool_redux/proxytool.ipynb`) for Figures 2–3 and domain sweeps

---

## Two-stage pipeline

| Stage | What | Where |
|-------|------|-------|
| **1 — MetaMatch retrieval** | GitHub search + ranking; **queryv2** winner frozen | `runs/experiments/penalty300_min700_cap22_queryv2/` — **0** magnets, **20/0/0** Good/OK/Weak |
| **2 — REDUX 4 similarity** | metadata, code_centric, dynamic, cross_language | Core: [`proxytool_redux/_extracted/redux4_core.py`](proxytool_redux/_extracted/redux4_core.py) |
| **Validation** | Labeled ground truth, retrieval→REDUX bridges, gates G1–G9 | [`results_benchmark/`](results_benchmark/) |

**Primary labeled metrics (v2, 24 pairs):** strict metadata F1 = **0.909**; lenient metadata F1 = **0.941**; code/cross_language strict F1 = **1.0**; dynamic strict = **0.842**. v1 (10-pair) frozen as comparison (strict F1 = 1.0). Cross-method Spearman ρ = **+0.69** (authenticated n=30). Downstream G9: **24 anchors** (20 queryv2 + **4 anchorsv2 additions**, not swaps).

---

## Consolidation (what changed)

Four pillars from the repo cleanup pass:

1. **Frozen headline bundle** — [`CANONICAL_RESULTS/`](CANONICAL_RESULTS/) symlinks primary artifacts (gates, v2 metrics, bridges, Spearman, G9) with SHA256 manifest.
2. **Validation package** — [`results_benchmark/`](results_benchmark/) holds outputs + master docs; v2 is primary, v1 frozen for comparison.
3. **Extracted scoring core** — REDUX 4 logic in tracked `proxytool_redux/_extracted/redux4_core.py`; notebook iterations archived under [`legacy_notebooks/`](legacy_notebooks/) (see [`proxytool_redux/REDUX_REPRO.md`](proxytool_redux/REDUX_REPRO.md)).
4. **Repo hygiene** — Tier A/B cleanup done; grid history (`redux4_sweep/`, `custom_30_pairs/`, penalty-grid folders) tarball'd to [`archives/off_repo/metamatch_grid_history.tar.gz`](archives/off_repo/README.md) (gitignored locally).

Pre-consolidation narrative (SharePoint baseline + before/after): [`results_benchmark/CAIS_REVIEW_REFERENCE.md`](results_benchmark/CAIS_REVIEW_REFERENCE.md) — not a duplicate of that doc elsewhere.

---

## Where to start

1. [`CANONICAL_RESULTS/`](CANONICAL_RESULTS/) — five-minute proof bundle (G1–G9 headlines)
2. [`results_benchmark/RESULTS_REVIEW.md`](results_benchmark/RESULTS_REVIEW.md) — navigator (which file to open next)
3. [`results_benchmark/WORK_REVIEW.md`](results_benchmark/WORK_REVIEW.md) — master repro (phases A–I, commands)

| Path | Role |
|------|------|
| [`CANONICAL_RESULTS/`](CANONICAL_RESULTS/) | Frozen headline bundle |
| [`results_benchmark/RESULTS_REVIEW.md`](results_benchmark/RESULTS_REVIEW.md) | Navigator — files in order + headline numbers |
| [`results_benchmark/PAPER_PACKAGE.md`](results_benchmark/PAPER_PACKAGE.md) | Gate checklist G1–G8 (+ G9 informational) |
| [`results_benchmark/VALIDATION_MEMO.md`](results_benchmark/VALIDATION_MEMO.md) | Stats prose, reviewer concerns |
| [`results_benchmark/WORK_REVIEW.md`](results_benchmark/WORK_REVIEW.md) | Master — phases A–I, repro commands |
| [`results_benchmark/REPO_AUDIT.md`](results_benchmark/REPO_AUDIT.md) | What matters vs archived junk |
| [`results_benchmark/README.md`](results_benchmark/README.md) | Directory map + doc roles |

---

## Repository layout (key folders)

| Path | Purpose |
|------|---------|
| [`CANONICAL_RESULTS/`](CANONICAL_RESULTS/) | Frozen validation headlines (start here) |
| [`results_benchmark/`](results_benchmark/) | Validation outputs + narrative docs |
| [`proxytool_redux/`](proxytool_redux/) | REDUX 4 core (`_extracted/redux4_core.py`), `benchmark.py`, [`REDUX_REPRO.md`](proxytool_redux/REDUX_REPRO.md) |
| [`legacy_notebooks/`](legacy_notebooks/) | Archived REDUX notebook iterations |
| [`runs/experiments/`](runs/experiments/) | Frozen MetaMatch archives (winner: `penalty300_min700_cap22_queryv2`) |
| [`tools/`](tools/) | Validation repro scripts (labeled cohort, bridges, downstream) |
| [`scripts/`](scripts/) | REDUX extraction + repro harness |
| [`configs/`](configs/) | Labeled pair manifests (v2 primary), rubrics, hyperparams |
| [`archives/off_repo/`](archives/off_repo/) | Grid-history tarball (local; gitignored) |

---

## Reproduce the validation pass

Full command sequence: [`results_benchmark/WORK_REVIEW.md`](results_benchmark/WORK_REVIEW.md) and [`CANONICAL_RESULTS/README.md`](CANONICAL_RESULTS/README.md). REDUX setup: [`proxytool_redux/REDUX_REPRO.md`](proxytool_redux/REDUX_REPRO.md) (lives under `proxytool_redux/`, not repo root).

```bash
cd "$(git rev-parse --show-toplevel)"
export GITHUB_TOKEN="$(gh auth token)"
export PYTHONPATH=.
# See WORK_REVIEW.md for phases A–I
```

---

## Paper → code (Figures 2 & 3)

The sections below map the IEEE paper to the **original notebook pipeline** (`proxytool.ipynb`). The **validation pass** uses the extracted REDUX core above, not a full notebook re-run.

---

## Why this exists

Teams need **safety-oriented evidence** for Critical AI Systems (CAIS), but the real system is often behind **NDAs, export controls, or operational secrecy**. You still have to argue that an **open-source proxy** is a plausible **behavioral stand-in** for the CAIS you cannot inspect.

**"Pick a similar GitHub repo" is not a strategy**--it is a guess. Stars, topics, and vague similarity do not answer: *Does this proxy match the risk and validation dimensions we care about?* You also need more than a leaderboard: a bridge from **ranked repos** to **what we would actually test**.

This project implements **multi-signal similarity**, **explicit taxonomy alignment** (NIST-style CAIS dimensions), and a path from **ranking -> scenario-backed test planning**--so the story can survive review, not just look good on a chart.

---

## Notebook pipeline (`proxytool.ipynb`)

The paper's **six-step loop** lives in **`proxytool_redux/proxytool.ipynb`** (plus REDUX variants under `proxytool_redux/` and `legacy_notebooks/`):

**config → data pull → features → similarity → validation → plots → test plans.**

Outputs include `results_plots/`, `validation_results.csv`, and structured proxy test plans. The **validation pass** scores via `proxytool_redux/_extracted/redux4_core.py` and `tools/` scripts instead.

### Figure 2 — Six-step pipeline (end-to-end in `proxytool_redux/proxytool.ipynb`)

| Step | What happens | Primary symbols / entry points |
|------|----------------|--------------------------------|
| 1 | Anchor per-domain CAIS profiles (NIST 5D-style dimensions) | `CAIS_DOMAIN_CONFIGS` |
| 2 | Discover or fix candidate sets | GitHub discovery via `DISCOVERY_QUERIES`; `run_discover_and_compare(...)` |
| 3 | Extract **behavioral fingerprints** from **public Git metadata** (not proprietary source) | Four indicator families (below) |
| 4 | Normalize + weight features | `CAIS_WEIGHTS`, tuning helpers such as `tune_weights` |
| 5 | Score + rank | Weighted vectors + **cosine similarity** |
| 6 | Validate taxonomy alignment | Overall vs taxonomy-restricted similarity; `compare_taxonomy_vs_standalone(...)`, `_taxonomy_similarity_report(...)` |

![Figure 2: Six-step proxy discovery pipeline](assets/figure2.png)

### Figure 3 -- Similarity -> taxonomy validation -> proxy selection -> test campaigns

- **Failure-mode scenarios per domain:** `CAIS_TEST_SCENARIOS`
- **Structured plans:** `plan_proxy_tests(...)`, `print_proxy_test_plan(...)`

The notebook turns ranked proxies into **scenario-backed test campaign sketches** mapped to **indicator families**--the paper's safety loop, operationalized in code.

![Figure 3: Similarity -> taxonomy validation -> proxy test planning](assets/figure3.png)

---

## The 11 CAIS domains (`CAIS_DOMAIN_CONFIGS`)

Each domain is a separate **world**: its own anchor repo, candidate set, expected high-similarity proxies, controls, and NIST-style profile. The same pipeline is stress-tested across heterogeneous, high-stakes settings--not a single vertical toy example.

| # | Domain key | Intuition |
|---|------------|-----------|
| 1 | `autonomous_driving` | Road autonomy / perception-planning style systems |
| 2 | `medical_ai` | Clinical / imaging ML style stacks |
| 3 | `robotics` | ROS-class navigation & integration ecosystems |
| 4 | `aerial_autonomy` | PX4 / flight-stack style autonomy |
| 5 | `financial_risk` | Credit / risk-scoring ML (high-stakes decisions) |
| 6 | `industrial_robotics` | Arms, motion, industrial automation stacks |
| 7 | `recommender_systems` | Large-scale ranking / recsys codebases |
| 8 | `security_identity` | IAM / auth / identity-heavy systems |
| 9 | `content_moderation` | Moderation / policy-enforcement style ML |
| 10 | `public_sector_fairness` | Fairness / public-sector ML risk framing |
| 11 | `cybersecurity_threat_detection` | IDS / SIEM / threat-detection style systems |

---

## What the notebook actually does

The workflow is **layered**: shallow smoke tests or deep research runs.

- **Static vs discovery paths** -- Fixed candidate lists (reproducible) or GitHub discovery per domain.
- **Multi-domain sweeps** -- e.g. `run_all_domain_suites`, `run_discover_and_compare` across configured domains.
- **Weight learning** -- `tune_weights(...)` per domain to search family-level weights against expected proxy lists.
- **Taxonomy vs standalone** -- `compare_taxonomy_vs_standalone`: A/B between taxonomy-augmented metric bundles and a baseline set (the paper's "does taxonomy help?" claim in code).
- **Separation analysis** -- `domain_vs_control_analysis`: do domain peers separate from controls (sanity check that signal isn't random).
- **Baseline triangulation** -- `side_by_side_comparison`, `deep_code_similarity`, `code_clone_similarity`, `dynamic_behavior_similarity`: metadata similarity vs lightweight public-metadata baselines.
- **Method agreement** -- `correlate_methods`: Spearman correlations across Metadata / CodeClone / Behavioral / DeepCode.
- **Safety-loop artifacts** -- `plan_proxy_tests`, `print_proxy_test_plan`: ranked proxies -> scenario-backed sketches (Figure 3).
- **Reporting** -- Plots under `results_plots/`; `validation_results.csv` for tabular outcomes and regression-style checks.

Together, this is **repeatable experiments, ablations, and cross-domain checks** on top of the paper.

---

## Four indicator families ("metadata-only" signals)

What public metadata is actually measuring:

1. **Commit semantics** -- Intent/sentiment; optional **sentence-transformer** embeddings when `sentence-transformers` is installed.
2. **Contributor behavior** -- Collaboration / authorship-style signals from commit history.
3. **File change histories** -- Co-change + churn from commit numstat and file-graph-style signals.
4. **Temporal evolution** -- Development rhythm, cadence, burstiness.

---

## Taxonomy + metrics (not "just embeddings")

- **`CAIS_METRICS`** bundles the paper's indicator families with explicit **NIST 5D** taxonomy dimensions (environment, purpose, operational O1-O5, algorithm, language) so similarity is not only "commit-text similarity."
- The evaluation path contrasts **taxonomy-augmented similarity** vs **standalone** metric sets--i.e. the paper's accuracy claims, expressed as runnable comparisons.

---

## Baselines & robustness checks

- **Domain vs control** -- Quantify separation between domain peers and controls (not isolated high scores).
- **Side-by-side comparison** -- Metadata similarity vs code-structure / behavioral / deep-readme+tree style baselines.
- **Rank correlations across methods** -- `correlate_methods` (Spearman): when different views agree or diverge.

---

## Tech stack

- Python, **GitHub REST API**, `requests`
- Feature normalization + **weighted cosine similarity**
- **matplotlib**, **scipy** (rank correlations)
- **sentence-transformers**, **vaderSentiment** (optional / graceful fallback)
- Historical note: a **CLI** (`proxytool.py`) and **PowerShell** harness were used in some workflows for batch plots; the canonical path today is the notebook--check the repo for what is currently tracked.

---

## Optional "meta" tooling

- **`scripts/proxy_doc_analyzer.py`** -- PDF/taxonomy-driven gap notes vs the implementation (research hygiene, traceability). Generated notes may live under `analysis/` locally (often gitignored).

---

## Proof points

| Artifact | Role |
|----------|------|
| `proxytool_redux/proxytool.ipynb` | Full pipeline: discovery -> evaluation -> test-plan output |
| `README.md` | Paper <-> code mapping (this file) |
| `results_plots/` | Saved figures for comparisons and talks |
| `validation_results.csv` | Summarized runs across domains / settings |

**After your next full run**, add 1-2 quantitative bullets (e.g. taxonomy-augmented MRR vs `BASE_METRICS` on a domain; Spearman rho between Metadata and DeepCode)--reviewers and recruiters scan for numbers.

---

## Research insight

The hardest part is not "compute a similarity score." It is making the pipeline **CAIS-aligned**: rankings **explainable against taxonomy dimensions**, and ranked proxies connected to **how you will test**. If the proxy story does not connect to test strategy, it will not pass a safety review--even if the leaderboard looks good.

---

## Honest scope (what metadata does and doesn't do)

The foundation is intentionally honest:

- **Git metadata** captures **development behavior**, not full runtime semantics.
- **Discovery quality** reflects real **GitHub search and API** behavior.
- **Embeddings** use general-purpose sentence models unless you plug in something stronger.

The **LOOKING AHEAD** section below is how we **tighten the science** without pretending runtime behavior was fully measured from metadata alone.

---

## LOOKING AHEAD

This work already shows what metadata-only similarity can do; the exciting part is what comes next--deeper signals, stronger baselines, and real-world CAIS studies.

The foundation is intentionally honest: Git metadata captures development behavior (not full runtime semantics), discovery quality tracks GitHub search and API realities, and embeddings use general-purpose sentence models today--so the roadmap below is how we tighten the science without pretending we already measured everything.

- **Richer dynamic baselines** -- where CI and test artifacts are public, layer in pass/fail distributions, coverage overlap, and execution-aware signals alongside Git metadata.
- **Cross-language code understanding** -- upgrade the code-centric view with models like CodeBERT / UniXcoder on carefully sampled public files (with clear licensing discipline).
- **Ensemble scoring** -- fuse metadata similarity, behavioral signals, and code-centric views into a single multi-view score with explicit uncertainty.
- **Temporal calibration** -- track how proxy rankings drift as repositories evolve; refresh rankings and flag when a proxy diverges from the CAIS fingerprint.
- **Industrial & regulated CAIS** -- extend the same harness to proprietary or restricted domains (defense, energy, transportation) where only metadata can be shared--exactly where proxy testing matters most.
- **Ground-truth expansion** -- grow per-domain validation pairs and rubrics so weight tuning and taxonomy-vs-standalone claims stay statistically grounded as the harness scales.

---

## How to run

1. **GitHub token:** `export GITHUB_TOKEN=...` (or use a `.env` file as described in the notebook; never commit secrets).
2. **Dependencies** (not all required for every cell):
   ```bash
   pip install requests tqdm matplotlib ipython scipy sentence-transformers vaderSentiment
   ```
3. Open and run **`proxytool_redux/proxytool.ipynb`**.

If `sentence-transformers` is missing, optional embedding cells degrade gracefully.

---

## Additional paths

| Path | Purpose |
|------|---------|
| `assets/` | Paper PDFs, figures, harness PS1 |
| `runs/manual-ml-py/`, `runs/_summaries/` | Live MetaMatch outputs (gitignored) |
| `results_plots/`, `validation_results.csv` | Notebook run artifacts (may be gitignored locally) |
| `analysis/` | Optional PDF gap notes from `scripts/proxy_doc_analyzer.py` |

**MetaMatch winner:** `penalty300_min700_cap22_queryv2` — see [`metamatch_hyperparams.json`](metamatch_hyperparams.json) and [`runs/experiments/documentation/WINNER.md`](runs/experiments/documentation/WINNER.md).

```powershell
pwsh ./Run-MetaMatchPipeline.ps1 -SummarizeOnly   # re-summarize live runs only
pwsh ./Run-MetaMatchPipeline.ps1 -CrossAnchorFreqPenaltyWeight:300 -MinimumScore:700 `
  -MaxPerOwner:2 -MaxPerOwnerPerSubdomain:2 -ArchiveAsExperiment my_id
```

---

## References & assets (in `assets/`)

- `Discovering_Proxy_Systems_to_Test_Critical_AI_Systems_A_Metadata-Driven_Software_Similarity_Approach.pdf`
- `IEEE PROOF Computer Software Column - v2.pdf`
- `NIST.CSWP.31.pdf`
- `A_Taxonomy_of_Critical_AI_System_Characteristics_for_Use_in_Proxy_System_Testing.pdf`
- `CAIS-NIST.docx`

---

## Collaboration

If you work on **safety evaluation**, **test strategy**, or **AI governance under source constraints**, feedback and collaboration ideas are welcome. Use the repo's Issues/Discussions if enabled, or reach out directly.
## MetaMatch 2.0 run artifacts

**Defaults:** penalty 300, min score 700, owner caps 2/2 (`Get-AnchorMatches.ps1` / `metamatch_hyperparams.json`). Docs: `runs/experiments/README.md`, `runs/README.md`.

Each per-anchor run folder includes:
- `ranked_matches.csv` (all scored candidates with diagnostics + explainability columns)
- `30_Matches.csv` (Top-K final selection)
- `run_manifest.json` (parameters, weights, counts, and outputs for reproducibility)

### New diversity / reliability knobs
- Retrieval signals are excluded from similarity scoring by default:
  - Use `-IncludeRetrievalSignalsInScore` to include QueryCoverage in Score.
- Optional cross-anchor "magnet" penalty:
  - `-CrossAnchorFreqPenaltyWeight 25` (example) to gently downweight candidates that appear often across prior anchors.
- Diversity caps:
  - `-MaxPerOwner 3` (global owner cap)
  - `-MaxPerOwnerPerSubdomain 2` (owner cap within a subdomain bucket)

### Cross-anchor summaries
After you have multiple anchors under `runs/manual-ml-py`, generate summaries:
```bash
python tools/summarize_runs.py --runs-dir runs/manual-ml-py --topk 10
```
Outputs are written to `runs/_summaries/`.
