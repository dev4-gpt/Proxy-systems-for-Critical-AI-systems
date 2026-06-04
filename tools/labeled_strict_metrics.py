#!/usr/bin/env python3
"""Compute labeled-benchmark metrics for strict (known_match only) and lenient cohorts."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List, Sequence

from proxytool_redux.benchmark_metrics import (
    compute_pair_classification_metrics,
    compute_score_separation,
    metrics_to_dict,
)

DEFAULT_METHODS = ["metadata", "code_centric", "dynamic", "cross_language"]
STRICT_POSITIVE = {"known_match"}
LENIENT_POSITIVE = {"known_match", "known_related"}
NEGATIVE_LABELS = {"known_non_match"}


def load_pairs(path: Path) -> List[Dict[str, object]]:
    with path.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    return list(payload.get("pairs", []))


def cohort_rows(
    pairs: Sequence[Dict[str, object]],
    methods: Sequence[str],
    *,
    labels: set[str],
    exclude: set[str],
) -> Dict[str, List[Dict[str, object]]]:
    by_method: Dict[str, List[Dict[str, object]]] = {m: [] for m in methods}
    for pair in pairs:
        label = str(pair.get("label", ""))
        if label in exclude:
            continue
        if label not in labels and label not in NEGATIVE_LABELS:
            continue
        for method in methods:
            key = f"{method}_score"
            val = pair.get(key)
            if val in (None, ""):
                continue
            by_method[method].append({"label": label, "score": float(val)})
    return by_method


def summarize(
    rows_by_method: Dict[str, List[Dict[str, object]]],
    *,
    positive_labels: set[str],
    threshold: float,
) -> List[Dict[str, object]]:
    summary: List[Dict[str, object]] = []
    for method, rows in rows_by_method.items():
        if not rows:
            continue
        clf = compute_pair_classification_metrics(
            rows,
            positive_labels=positive_labels,
            threshold=threshold,
        )
        sep = compute_score_separation(
            rows,
            positive_labels=positive_labels,
            negative_labels=NEGATIVE_LABELS,
        )
        row = {"method": method, "threshold": threshold}
        row.update(metrics_to_dict(clf))
        row.update(metrics_to_dict(sep))
        summary.append(row)
    return summary


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", default="results_benchmark/labeled_scored.json")
    parser.add_argument("--output-dir", default="results_benchmark/labeled")
    parser.add_argument("--threshold", type=float, default=50.0)
    parser.add_argument("--methods", nargs="*", default=DEFAULT_METHODS)
    args = parser.parse_args()

    pairs = load_pairs(Path(args.benchmark))
    out_dir = Path(args.output_dir)

    strict_rows = cohort_rows(
        pairs,
        args.methods,
        labels=STRICT_POSITIVE,
        exclude={"target_uncertain"},
    )
    lenient_rows = cohort_rows(
        pairs,
        args.methods,
        labels=LENIENT_POSITIVE,
        exclude={"target_uncertain"},
    )

    strict_summary = summarize(strict_rows, positive_labels=STRICT_POSITIVE, threshold=args.threshold)
    lenient_summary = summarize(lenient_rows, positive_labels=LENIENT_POSITIVE, threshold=args.threshold)

    write_csv(out_dir / "labeled_strict_summary.csv", strict_summary)
    write_csv(out_dir / "labeled_lenient_summary.csv", lenient_summary)
    (out_dir / "labeled_strict_summary.json").write_text(
        json.dumps(strict_summary, indent=2),
        encoding="utf-8",
    )
    (out_dir / "labeled_lenient_summary.json").write_text(
        json.dumps(lenient_summary, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote strict/lenient summaries to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
