"""Single-pass REDUX_4 benchmark runner (no mirror-identity headline metrics)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# Pairs used across tables (same as proxytool_REDUX_4.ipynb cells 152–154)
FUNCTIONAL_SIMILAR_PAIRS: List[Tuple[str, str, str]] = [
    ("1: TensorFlow vs PyTorch", "https://github.com/tensorflow/tensorflow", "https://github.com/pytorch/pytorch"),
    ("2: VSCode vs Electron", "https://github.com/microsoft/vscode", "https://github.com/electron/electron"),
    ("3: OpenPilot vs Autoware", "https://github.com/commaai/openpilot", "https://github.com/autowarefoundation/autoware"),
    ("4: MONAI vs TensorFlow", "https://github.com/Project-MONAI/MONAI", "https://github.com/tensorflow/tensorflow"),
]

DISSIMILAR_PAIRS: List[Tuple[str, str, str]] = [
    ("1: TensorFlow vs Django", "https://github.com/tensorflow/tensorflow", "https://github.com/django/django"),
    ("2: VSCode vs XGBoost", "https://github.com/microsoft/vscode", "https://github.com/dmlc/xgboost"),
    ("3: OpenPilot vs Scikit-learn", "https://github.com/commaai/openpilot", "https://github.com/scikit-learn/scikit-learn"),
    ("4: MONAI vs Electron", "https://github.com/Project-MONAI/MONAI", "https://github.com/electron/electron"),
]


def _with_average_row(table: pd.DataFrame, known_similarity_pct: float) -> pd.DataFrame:
    avg = {
        "Test": "Average",
        "Known similarity": f"{known_similarity_pct:.0f} %" if known_similarity_pct >= 1 else "0 %",
        "Metadata": round(float(table["Metadata"].mean()), 1),
        "Code centric": round(float(table["Code centric"].mean()), 1),
        "Dynamic": round(float(table["Dynamic"].mean()), 1),
        "Cross language": round(float(table["Cross language"].mean()), 1),
        "Query": "",
        "Target": "",
    }
    if "TestGroup" in table.columns:
        avg["TestGroup"] = table["TestGroup"].iloc[0]
    return pd.concat([table, pd.DataFrame([avg])], ignore_index=True)


def _domain_summary(table_30: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for domain, grp in table_30.groupby("Domain"):
        meta = grp["Metadata"].astype(float)
        rows.append(
            {
                "Domain": domain,
                "n_pairs": len(grp),
                "metadata_mean": round(float(meta.mean()), 1),
                "metadata_median": round(float(meta.median()), 1),
                "metadata_min": round(float(meta.min()), 1),
                "metadata_max": round(float(meta.max()), 1),
                "n_at_0": int((meta == 0).sum()),
                "n_at_100": int((meta == 100).sum()),
            }
        )
    overall = table_30["Metadata"].astype(float)
    rows.append(
        {
            "Domain": "ALL",
            "n_pairs": len(table_30),
            "metadata_mean": round(float(overall.mean()), 1),
            "metadata_median": round(float(overall.median()), 1),
            "metadata_min": round(float(overall.min()), 1),
            "metadata_max": round(float(overall.max()), 1),
            "n_at_0": int((overall == 0).sum()),
            "n_at_100": int((overall == 100).sum()),
        }
    )
    return pd.DataFrame(rows)


def run_all_benchmarks(
    g: Dict[str, Any],
    *,
    export_dir: str | Path = "results_benchmark",
    pairs_path: str = "30_Pairs.json",
    max_commits: int = 150,
    clear_cache_first: bool = False,
    run_mirror_appendix: bool = False,
    make_mirror_plots: bool = False,
    github_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the REPRO benchmark path using functions already loaded in ``g`` (from bootstrap).

    Primary metrics:
      - Test 2 functional-similar + Test 3 dissimilar (``three_test_argument_table.csv``)
      - 30-pair vertical cohort (``custom_30_pairs_canonical.csv``)
      - Discrimination diagnostics from Test 2 + 30-pair only (no mirror self-match)

    Optional appendix:
      - ``run_mirror_appendix=True`` runs known-mirror retrieval benchmark (strict contrastive).
    """
    token = github_token or g.get("github_token")
    results_dir = Path(export_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    fit_global = g["fit_global_minmax_for_all_benchmark_tables"]
    build_argument_table = g["build_argument_table"]
    build_custom_30_table = g["build_custom_30_table"]
    metadata_discrimination_diagnostics = g["metadata_discrimination_diagnostics"]

    REDUX3_DEFAULT_REPORTING_RETRIEVAL = g["REDUX3_DEFAULT_REPORTING_RETRIEVAL"]
    REDUX3_DEFAULT_REPORTING_BENCHMARK = g["REDUX3_DEFAULT_REPORTING_BENCHMARK"]
    REDUX3_METADATA_WINDOWS = g["REDUX3_METADATA_WINDOWS"]
    REDUX3_WINDOW_WEIGHTS = g["REDUX3_WINDOW_WEIGHTS"]
    REDUX3_COVERAGE_PENALTY_LAMBDA = g["REDUX3_COVERAGE_PENALTY_LAMBDA"]
    CAIS_WEIGHTS_REDUX3_BLEND = g["CAIS_WEIGHTS_REDUX3_BLEND"]

    print("Fitting global min-max normalizer (shared across tables)...")
    fit_global()

    print("Test 2: functional-similar pairs...")
    table_test2 = build_argument_table(
        FUNCTIONAL_SIMILAR_PAIRS,
        known_similarity_pct=100.0,
        token=token,
        max_commits=max_commits,
    )
    table_test2 = _with_average_row(table_test2, 100.0)
    table_test2["TestGroup"] = "Test 2: Functional similar"

    print("Test 3: dissimilar pairs...")
    table_test3 = build_argument_table(
        DISSIMILAR_PAIRS,
        known_similarity_pct=0.0,
        token=token,
        max_commits=max_commits,
    )
    table_test3 = _with_average_row(table_test3, 0.0)
    table_test3["TestGroup"] = "Test 3: Dissimilar"

    three_test = pd.concat(
        [
            table_test2[table_test2["Test"] != "Average"],
            table_test3[table_test3["Test"] != "Average"],
            table_test2[table_test2["Test"] == "Average"],
            table_test3[table_test3["Test"] == "Average"],
        ],
        ignore_index=True,
    )
    three_path = results_dir / "three_test_argument_table.csv"
    three_test.to_csv(three_path, index=False)
    print(f"Saved {three_path}")

    print("30-pair vertical cohort (canonical)...")
    table_30 = build_custom_30_table(
        pairs_path=pairs_path,
        metadata_weights=CAIS_WEIGHTS_REDUX3_BLEND,
        metadata_windows=REDUX3_METADATA_WINDOWS,
        metadata_window_weights=REDUX3_WINDOW_WEIGHTS,
        max_commits=max_commits,
        clear_cache_first=clear_cache_first,
        label="Custom 30-pair cohort (canonical)",
        metadata_scoring_mode="family_cosine",
        family_score_norm="raw_cosine",
        reporting_mode=REDUX3_DEFAULT_REPORTING_RETRIEVAL,
        coverage_penalty_lambda=REDUX3_COVERAGE_PENALTY_LAMBDA,
        use_domain_hard_negatives=True,
        token=token,
    )
    canonical_path = results_dir / "custom_30_pairs_canonical.csv"
    table_30.to_csv(canonical_path, index=False)
    print(f"Saved {canonical_path}")

    domain_summary = _domain_summary(table_30)
    domain_path = results_dir / "custom_30_pairs_domain_summary.csv"
    domain_summary.to_csv(domain_path, index=False)
    print(f"Saved {domain_path}")

    similar_df = pd.concat(
        [
            table_test2[table_test2["Test"] != "Average"],
            table_30,
        ],
        ignore_index=True,
    )
    dissimilar_df = table_test3[table_test3["Test"] != "Average"].copy()
    diag_df = metadata_discrimination_diagnostics(
        similar_df, dissimilar_df, col="Metadata", threshold=50.0
    )
    diag_path = results_dir / "metadata_discrimination_canonical.csv"
    diag_df.to_csv(diag_path, index=False)
    print(f"Saved {diag_path} (similar = Test2 + 30-pair; excludes mirror identity)")

    out: Dict[str, Any] = {
        "table_test2": table_test2,
        "table_test3": table_test3,
        "three_test": three_test,
        "table_30": table_30,
        "domain_summary": domain_summary,
        "diagnostics": diag_df,
        "paths": {
            "three_test": three_path,
            "canonical_30": canonical_path,
            "domain_summary": domain_path,
            "diagnostics": diag_path,
        },
    }

    if run_mirror_appendix and "run_known_pair_benchmark" in g:
        print("Appendix: known-mirror retrieval benchmark...")
        bm = g["run_known_pair_benchmark"](
            max_commits=max_commits,
            save_prefix="known_mirror_benchmark_canonical",
            make_plots=make_mirror_plots,
            strict_only=True,
            metadata_reporting_mode=REDUX3_DEFAULT_REPORTING_BENCHMARK,
            token=token,
        )
        out["mirror_benchmark"] = bm

    return out
