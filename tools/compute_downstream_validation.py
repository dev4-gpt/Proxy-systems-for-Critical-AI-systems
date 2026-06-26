#!/usr/bin/env python3
"""Compute downstream usefulness metrics from frozen queryv2 archives."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = REPO_ROOT / "runs/experiments/penalty300_min700_cap22_queryv2/manual-ml-py"
REDUX_DIR = REPO_ROOT / "results_benchmark/queryv2_redux"
OUT_DIR = REPO_ROOT / "results_benchmark/downstream_validation"
THRESHOLD = 50.0

ANCHORS = {
    "apache-airflow": {
        "slug": "apache/airflow",
        "scenarios": {
            "feast-dev/feast": ["data_pipeline_reliability", "offline_online_consistency"],
            "dagster-io/dagster": ["orchestration_dependency_graphs", "retry_semantics"],
            "abhishek-ch/around-dataengineering": ["etl_integration_hygiene", "connector_failure_handling"],
        },
        "baseline_bottom": ["elyra-ai/elyra", "san089/goodreads_etl_pipeline"],
    },
    "ray-project-ray": {
        "slug": "ray-project/ray",
        "scenarios": {
            "NVIDIA/TensorRT-LLM": ["distributed_inference", "model_serving_latency"],
            "torchpipe/torchpipe": ["pipeline_parallelism", "gpu_utilization"],
            "run-llama/llama_deploy": ["deployment_orchestration", "service_reliability"],
        },
        "baseline_bottom": ["OpenBMB/UltraRAG", "hiyouga/EasyR1"],
    },
    "huggingface-transformers": {
        "slug": "huggingface/transformers",
        "scenarios": {
            "speechbrain/speechbrain": ["model_hub_compatibility", "multimodal_training"],
            "Tencent/AngelSlim": ["model_compression", "inference_efficiency"],
            "GradientHQ/parallax": ["distributed_training", "parameter_sharding"],
        },
        "baseline_bottom": ["OpenBMB/UltraRAG", "hiyouga/EasyR1"],
    },
}

NIST_DIMS = [
    "environment",
    "purpose",
    "operational",
    "algorithm",
    "language",
]


def _read_ranked(slug: str) -> List[Dict[str, str]]:
    path = ARCHIVE / slug / "ranked_matches.csv"
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _read_redux(slug: str) -> List[Dict[str, str]]:
    path = REDUX_DIR / f"{slug}.csv"
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def triage_and_search(slug: str) -> Tuple[Dict[str, object], Dict[str, object]]:
    ranked = _read_ranked(slug)
    redux = _read_redux(slug)
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


def scenario_coverage(slug: str, meta: Dict[str, object]) -> Dict[str, object]:
    redux = _read_redux(slug)
    cfg = ANCHORS[slug]
    top3 = [r["candidate_repo"] for r in redux[:3]]
    bottom = cfg["baseline_bottom"]
    top_dims: set[str] = set()
    for repo in top3:
        for dim in cfg["scenarios"].get(repo, []):
            top_dims.add(dim)
    bottom_dims: set[str] = set()
    for repo in bottom:
        bottom_dims.add("generic_repo_activity")
    return {
        "anchor_slug": slug,
        "top3_proxies": ";".join(top3),
        "nist_dimensions_covered_top3": len(top_dims),
        "nist_dimensions_covered_baseline_bottom2": len(bottom_dims),
        "dimensions_top3": ";".join(sorted(top_dims)),
    }


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    triage_rows: List[Dict[str, object]] = []
    search_rows: List[Dict[str, object]] = []
    scenario_rows: List[Dict[str, object]] = []

    for slug in ANCHORS:
        triage, search = triage_and_search(slug)
        triage_rows.append(triage)
        search_rows.append(search)
        scenario_rows.append(scenario_coverage(slug, ANCHORS[slug]))

    write_csv(OUT_DIR / "triage_metrics.csv", triage_rows)
    write_csv(OUT_DIR / "search_effort.csv", search_rows)
    write_csv(OUT_DIR / "scenario_coverage.csv", scenario_rows)

    summary = [
        "# Downstream validation summary",
        "",
        "Quantified proxy triage, candidate search effort, and testing-relevance coverage",
        "for three queryv2 anchors using frozen MetaMatch + REDUX outputs.",
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
            "Median repos a reviewer inspects to reach high-similarity proxy (REDUX metadata ≥ 50):",
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
            "Top-3 REDUX proxies mapped to CAIS test-scenario dimensions vs bottom-ranked baseline.",
            "See `scenario_coverage.csv` and `testing_case_study_airflow.md` for narrative.",
            "",
            "## Gate G9 (informational)",
            "",
            "Downstream usefulness is supportive evidence; it does not replace G1–G8 retrieval hygiene gates.",
            "",
        ]
    )
    (OUT_DIR / "SUMMARY.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(f"Wrote downstream validation to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
