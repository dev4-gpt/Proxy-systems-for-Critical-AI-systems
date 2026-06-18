#!/usr/bin/env python3
"""Generate lightweight labeled benchmark summaries.

This script does not replace the notebook. It gives the project a stable place
for benchmark bookkeeping and summary outputs so the paper can cite consistent
artifacts.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List

from proxytool_redux.benchmark_metrics import (
    compute_pair_classification_metrics,
    compute_score_separation,
    metrics_to_dict,
)


DEFAULT_METHODS = ["metadata", "code_centric", "dynamic", "cross_language"]
POSITIVE_LABELS = {"known_match", "known_related"}
NEGATIVE_LABELS = {"known_non_match"}
# target_uncertain is a realism-only pair (configs/labeled_benchmark_pairs.json
# labeling_notes) and is excluded from precision/recall/F1, matching
# tools/labeled_strict_metrics.py and the documented cohort rule.
EXCLUDE_FROM_METRICS = {"target_uncertain"}


def load_pairs(path: Path) -> List[Dict[str, object]]:
    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    if isinstance(payload, dict):
        return list(payload.get("pairs", []))
    if isinstance(payload, list):
        return payload
    raise ValueError(f"Unsupported benchmark manifest structure in {path}")



def infer_pair_row(pair: Dict[str, object], methods: List[str]) -> Dict[str, object]:
    row: Dict[str, object] = {
        "pair_id": pair.get("pair_id", ""),
        "label": pair.get("label", ""),
        "repo_a_url": pair.get("repo_a_url", ""),
        "repo_b_url": pair.get("repo_b_url", ""),
        "evidence_type": pair.get("evidence_type", ""),
        "evidence_note": pair.get("evidence_note", ""),
    }
    for method in methods:
        key = f"{method}_score"
        value = pair.get(key)
        row[key] = float(value) if value not in (None, "") else ""
    return row



def build_summary(rows: List[Dict[str, object]], methods: List[str], threshold: float) -> List[Dict[str, object]]:
    summary: List[Dict[str, object]] = []
    for method in methods:
        scored_rows = [
            {"label": row["label"], "score": row[f"{method}_score"]}
            for row in rows
            if row.get(f"{method}_score") not in (None, "")
            and row.get("label") not in EXCLUDE_FROM_METRICS
        ]
        if not scored_rows:
            continue
        classification = compute_pair_classification_metrics(
            scored_rows,
            score_key="score",
            label_key="label",
            positive_labels=POSITIVE_LABELS,
            threshold=threshold,
        )
        separation = compute_score_separation(
            scored_rows,
            score_key="score",
            label_key="label",
            positive_labels=POSITIVE_LABELS,
            negative_labels=NEGATIVE_LABELS,
        )
        merged = {"method": method}
        merged.update(metrics_to_dict(classification))
        merged.update(metrics_to_dict(separation))
        summary.append(merged)
    return summary



def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)



def write_claim_checks(path: Path, summary_rows: List[Dict[str, object]]) -> None:
    lines = [
        "# Labeled Benchmark Claim Checks",
        "",
        "This file is generated from the labeled benchmark manifest and currently reports only score-threshold and cohort-separation summaries.",
        "Use it as a paper-writing aid, not as a substitute for the full notebook analysis.",
        "",
    ]
    for row in summary_rows:
        lines.append(f"## {row['method']}")
        lines.append(f"- Accuracy @ threshold {row['threshold']}: {row['accuracy']:.3f}")
        lines.append(f"- Precision: {row['precision']:.3f}")
        lines.append(f"- Recall: {row['recall']:.3f}")
        lines.append(f"- F1: {row['f1']:.3f}")
        lines.append(f"- Positive/negative mean gap: {row['mean_gap']:.3f}")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")



def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", default="configs/labeled_benchmark_pairs.json")
    parser.add_argument("--output-dir", default="results_benchmark/labeled")
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--methods", nargs="*", default=DEFAULT_METHODS)
    args = parser.parse_args()

    pairs = load_pairs(Path(args.benchmark))
    rows = [infer_pair_row(pair, args.methods) for pair in pairs]
    summary = build_summary(rows, args.methods, args.threshold)
    output_dir = Path(args.output_dir)
    write_csv(output_dir / "labeled_pair_table.csv", rows)
    write_csv(output_dir / "labeled_summary.csv", summary)
    write_claim_checks(output_dir / "labeled_claim_checks.md", summary)
    (output_dir / "labeled_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote labeled benchmark outputs to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
