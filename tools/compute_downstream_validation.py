#!/usr/bin/env python3
"""Compute downstream usefulness metrics from frozen queryv2 archives."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
QUERYV2_ARCHIVE = REPO_ROOT / "runs/experiments/penalty300_min700_cap22_queryv2/manual-ml-py"
ANCHORSV2_ARCHIVE = REPO_ROOT / "runs/experiments/penalty300_min700_cap22_anchorsv2/manual-ml-py"
QUERYV2_REDUX = REPO_ROOT / "results_benchmark/queryv2_redux"
ANCHORSV2_REDUX = REPO_ROOT / "results_benchmark/anchorsv2_redux"
OUT_DIR = REPO_ROOT / "results_benchmark/downstream_validation"
THRESHOLD = 50.0

# ponytail: anchorsv2-only additions — not in queryv2 archive; use anchorsv2 archive + redux.
ANCHORSV2_ONLY = frozenset(
    {
        "mlflow-mlflow",
        "pytorch-vision",
        "scikit-learn-scikit-learn",
        "treeverse-dvc",
    }
)

# ponytail: explicit CAIS scenario rubric only for anchors with narrative case studies.
SCENARIO_MAP: Dict[str, Dict[str, object]] = {
    "apache-airflow": {
        "scenarios": {
            "feast-dev/feast": ["data_pipeline_reliability", "offline_online_consistency"],
            "dagster-io/dagster": ["orchestration_dependency_graphs", "retry_semantics"],
            "abhishek-ch/around-dataengineering": ["etl_integration_hygiene", "connector_failure_handling"],
        },
        "baseline_bottom": ["elyra-ai/elyra", "san089/goodreads_etl_pipeline"],
    },
    "ray-project-ray": {
        "scenarios": {
            "NVIDIA/TensorRT-LLM": ["distributed_inference", "model_serving_latency"],
            "torchpipe/torchpipe": ["pipeline_parallelism", "gpu_utilization"],
            "run-llama/llama_deploy": ["deployment_orchestration", "service_reliability"],
        },
        "baseline_bottom": ["OpenBMB/UltraRAG", "hiyouga/EasyR1"],
    },
    "huggingface-transformers": {
        "scenarios": {
            "speechbrain/speechbrain": ["model_hub_compatibility", "multimodal_training"],
            "Tencent/AngelSlim": ["model_compression", "inference_efficiency"],
            "GradientHQ/parallax": ["distributed_training", "parameter_sharding"],
        },
        "baseline_bottom": ["OpenBMB/UltraRAG", "hiyouga/EasyR1"],
    },
}


def discover_anchors() -> List[str]:
    queryv2 = sorted(p.name for p in QUERYV2_ARCHIVE.iterdir() if p.is_dir())
    return sorted(set(queryv2) | ANCHORSV2_ONLY)


def _sources(slug: str) -> Tuple[Path, Path]:
    if slug in ANCHORSV2_ONLY:
        return ANCHORSV2_ARCHIVE, ANCHORSV2_REDUX
    return QUERYV2_ARCHIVE, QUERYV2_REDUX


def _resolve_redux_path(slug: str, redux_dir: Path) -> Path:
    direct = redux_dir / f"{slug}.csv"
    if direct.exists():
        return direct
    for path in redux_dir.glob("*.csv"):
        if path.name == "rollup_summary.csv":
            continue
        if path.stem.lower() == slug.lower():
            return path
    raise FileNotFoundError(f"No REDUX CSV for anchor slug {slug!r}")


def _read_ranked(slug: str, archive: Path) -> List[Dict[str, str]]:
    path = archive / slug / "ranked_matches.csv"
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _read_redux(slug: str, redux_dir: Path) -> List[Dict[str, str]]:
    with _resolve_redux_path(slug, redux_dir).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def triage_and_search(slug: str, archive: Path, redux_dir: Path) -> Tuple[Dict[str, object], Dict[str, object]]:
    ranked = _read_ranked(slug, archive)
    redux = _read_redux(slug, redux_dir)
    qualified = [r for r in ranked if str(r.get("Qualified", "")).lower() == "true"]
    pool_size = len(qualified)
    top5 = redux[:5]
    redux_pass = [r for r in top5 if float(r["metadata_pct"]) >= THRESHOLD]
    triage = {
        "anchor_slug": slug,
        "raw_qualified_pool": pool_size,
        "metamatch_top5": len(top5),
        "redux_pass_top5": len(redux_pass),
        "pct_reduction_vs_pool": round(100.0 * (1 - len(redux_pass) / pool_size), 2) if pool_size else 0.0,
        "pct_reduction_vs_top5": round(100.0 * (1 - len(redux_pass) / len(top5)), 2) if top5 else 0.0,
    }
    search = {
        "anchor_slug": slug,
        "baseline_unfiltered_qualified": pool_size,
        "metamatch_only_top5": len(top5),
        "metamatch_redux_filtered": len(redux_pass),
        "median_repos_to_high_similarity": len(redux_pass) if redux_pass else len(top5),
    }
    return triage, search


def scenario_coverage_cais(slug: str, cfg: Dict[str, object], redux_dir: Path) -> Dict[str, object]:
    redux = _read_redux(slug, redux_dir)
    top3 = [r["candidate_repo"] for r in redux[:3]]
    bottom = cfg["baseline_bottom"]  # type: ignore[index]
    scenarios = cfg["scenarios"]  # type: ignore[index]
    top_dims: set[str] = set()
    for repo in top3:
        for dim in scenarios.get(repo, []):  # type: ignore[union-attr]
            top_dims.add(dim)
    bottom_dims = {"generic_repo_activity"} if bottom else set()
    return {
        "anchor_slug": slug,
        "mapping_mode": "cais_explicit",
        "top3_proxies": ";".join(top3),
        "nist_dimensions_covered_top3": len(top_dims),
        "nist_dimensions_covered_baseline_bottom2": len(bottom_dims),
        "dimensions_top3": ";".join(sorted(top_dims)),
    }


def scenario_coverage_heuristic(slug: str, redux_dir: Path) -> Dict[str, object]:
    redux = _read_redux(slug, redux_dir)
    top3 = redux[:3]
    bottom2 = redux[3:5] if len(redux) >= 5 else redux[-2:]
    top_pass = sum(1 for r in top3 if float(r["metadata_pct"]) >= THRESHOLD)
    bottom_pass = sum(1 for r in bottom2 if float(r["metadata_pct"]) >= THRESHOLD)
    if top_pass == len(top3) and top3:
        dims = "metadata_stand_in_adequacy"
    elif top_pass:
        dims = f"partial_metadata_adequacy_{top_pass}_of_{len(top3)}"
    else:
        dims = "none_at_threshold"
    return {
        "anchor_slug": slug,
        "mapping_mode": "metadata_heuristic",
        "top3_proxies": ";".join(r["candidate_repo"] for r in top3),
        "nist_dimensions_covered_top3": top_pass,
        "nist_dimensions_covered_baseline_bottom2": bottom_pass,
        "dimensions_top3": dims,
    }


def scenario_coverage(slug: str, redux_dir: Path) -> Dict[str, object]:
    cfg = SCENARIO_MAP.get(slug)
    if cfg:
        return scenario_coverage_cais(slug, cfg, redux_dir)
    return scenario_coverage_heuristic(slug, redux_dir)


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    anchors = discover_anchors()
    triage_rows: List[Dict[str, object]] = []
    search_rows: List[Dict[str, object]] = []
    scenario_rows: List[Dict[str, object]] = []

    anchorsv2_only_n = sum(1 for s in anchors if s in ANCHORSV2_ONLY)
    for slug in anchors:
        archive, redux_dir = _sources(slug)
        triage, search = triage_and_search(slug, archive, redux_dir)
        triage_rows.append(triage)
        search_rows.append(search)
        scenario_rows.append(scenario_coverage(slug, redux_dir))

    write_csv(OUT_DIR / "triage_metrics.csv", triage_rows)
    write_csv(OUT_DIR / "search_effort.csv", search_rows)
    write_csv(OUT_DIR / "scenario_coverage.csv", scenario_rows)

    cais_n = sum(1 for r in scenario_rows if r["mapping_mode"] == "cais_explicit")
    heuristic_n = len(scenario_rows) - cais_n
    summary = [
        "# Downstream validation summary",
        "",
        f"Quantified proxy triage, candidate search effort, and testing-relevance coverage",
        f"for **{len(anchors)}** anchors (20 queryv2 + {anchorsv2_only_n} anchorsv2-only additions)",
        f"using frozen MetaMatch + REDUX outputs.",
        "",
        "## Proxy triage efficiency",
        "",
        "| Anchor | Qualified pool | REDUX pass @50 (top-5) | Reduction vs pool |",
        "|--------|----------------|------------------------|-----------------|",
    ]
    for r in triage_rows:
        summary.append(
            f"| {r['anchor_slug']} | {r['raw_qualified_pool']} | {r['redux_pass_top5']} | {r['pct_reduction_vs_pool']}% |"
        )
    summary.extend(
        [
            "",
            "## Candidate search effort",
            "",
            "Repos a reviewer inspects to reach high-similarity proxy (REDUX metadata ≥ 50):",
            "",
        ]
    )
    for r in search_rows:
        summary.append(
            f"- **{r['anchor_slug']}**: unfiltered qualified={r['baseline_unfiltered_qualified']}, "
            f"MetaMatch top-5={r['metamatch_only_top5']}, REDUX-filtered={r['metamatch_redux_filtered']}"
        )
    summary.extend(
        [
            "",
            "## Testing relevance (scenario coverage)",
            "",
            f"- **CAIS explicit rubric:** {cais_n} anchors (`apache-airflow`, `ray-project-ray`, `huggingface-transformers`).",
            f"- **Metadata heuristic:** {heuristic_n} anchors — top-3/bottom-2 of REDUX top-5 scored at ≥50 threshold;",
            "  no hand-authored CAIS scenario map (see `scenario_coverage.csv` `mapping_mode` column).",
            "",
            "Narrative case study: `testing_case_study_airflow.md`.",
            "",
            "## Gate G9 (informational)",
            "",
            "Downstream usefulness is supportive evidence; it does not replace G1–G8 retrieval hygiene gates.",
            "",
        ]
    )
    (OUT_DIR / "SUMMARY.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(f"Wrote downstream validation for {len(anchors)} anchors to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
