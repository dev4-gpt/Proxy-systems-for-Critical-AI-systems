#!/usr/bin/env python3
"""Run REPRO benchmark (same as proxytool_REDUX_4_REPRO.ipynb cell 3)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    os.chdir(ROOT)
    t0 = time.perf_counter()
    print("Loading redux4_core...")
    from proxytool_redux.bootstrap import load_redux4_core
    from proxytool_redux.benchmark import run_all_benchmarks

    g = load_redux4_core()
    print(f"Core loaded in {time.perf_counter() - t0:.1f}s")

    print("Running run_all_benchmarks (CLEAR_CACHE_FIRST=False)...")
    t1 = time.perf_counter()
    results = run_all_benchmarks(
        g,
        export_dir=ROOT / "results_benchmark",
        pairs_path=str(ROOT / "30_Pairs.json"),
        max_commits=150,
        clear_cache_first=False,
        run_mirror_appendix=False,
        github_token=g.get("github_token"),
    )
    elapsed = time.perf_counter() - t1
    print(f"Benchmark finished in {elapsed / 60:.1f} min")

    summary = {
        "elapsed_min": round(elapsed / 60, 2),
        "domain_summary": results["domain_summary"].to_dict(orient="records"),
        "diagnostics": results["diagnostics"].to_dict(orient="records"),
        "test2_metadata_mean": float(
            results["table_test2"].loc[
                results["table_test2"]["Test"] == "Average", "Metadata"
            ].iloc[0]
        ),
        "test3_metadata_mean": float(
            results["table_test3"].loc[
                results["table_test3"]["Test"] == "Average", "Metadata"
            ].iloc[0]
        ),
        "pairs_30_metadata_mean": float(results["table_30"]["Metadata"].mean()),
        "pairs_30_metadata_median": float(results["table_30"]["Metadata"].median()),
        "pairs_30_n_zero": int((results["table_30"]["Metadata"] == 0).sum()),
        "pairs_30_n_100": int((results["table_30"]["Metadata"] == 100).sum()),
    }
    out = ROOT / "results_benchmark" / "repro_run_summary.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
