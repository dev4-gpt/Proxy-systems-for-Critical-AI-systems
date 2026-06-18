#!/usr/bin/env python3
"""Stdlib-only recompute of labeled-benchmark metrics (no pandas, no network).

Authoritative offline regeneration of the labeled summaries. Mirrors the metric
semantics in proxytool_redux/benchmark_metrics.py but depends only on the
standard library so it cannot segfault on a heavy pandas/torch import and never
touches the network.

Documented cohort rule (configs/labeled_benchmark_pairs.json labeling_notes):
  - target_uncertain is realism-only and is EXCLUDED from precision/recall/F1.
  - lenient positives = known_match + known_related; negatives = known_non_match.
  - threshold 50 on the 0-100 method scores.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List, Sequence

METHODS = ["metadata", "code_centric", "dynamic", "cross_language"]
LENIENT_POSITIVE = {"known_match", "known_related"}
STRICT_POSITIVE = {"known_match"}
NEGATIVE_LABELS = {"known_non_match"}
EXCLUDE = {"target_uncertain"}

FIELDS = [
    "method", "threshold", "precision", "recall", "f1", "accuracy",
    "true_positives", "false_positives", "true_negatives", "false_negatives",
    "positive_mean", "negative_mean", "mean_gap",
    "positive_median", "negative_median", "median_gap",
    "positive_count", "negative_count",
]


def _div(num: float, den: float) -> float:
    return float(num) / float(den) if den else 0.0


def _median(values: Sequence[float]) -> float:
    xs = sorted(float(v) for v in values)
    if not xs:
        return 0.0
    mid = len(xs) // 2
    if len(xs) % 2 == 1:
        return xs[mid]
    return 0.5 * (xs[mid - 1] + xs[mid])


def load_pairs(path: Path) -> List[Dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return list(payload.get("pairs", []))


def summarize(pairs, *, positive: set, threshold: float) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    for method in METHODS:
        key = f"{method}_score"
        rows = []
        for p in pairs:
            label = str(p.get("label", ""))
            if label in EXCLUDE:
                continue
            if label not in positive and label not in NEGATIVE_LABELS:
                continue
            val = p.get(key)
            if val in (None, ""):
                continue
            rows.append((label, float(val)))
        if not rows:
            continue
        tp = fp = tn = fn = 0
        pos_scores: List[float] = []
        neg_scores: List[float] = []
        for label, score in rows:
            actual_pos = label in positive
            pred_pos = score >= threshold
            if actual_pos and pred_pos:
                tp += 1
            elif actual_pos and not pred_pos:
                fn += 1
            elif not actual_pos and pred_pos:
                fp += 1
            else:
                tn += 1
            if label in positive:
                pos_scores.append(score)
            elif label in NEGATIVE_LABELS:
                neg_scores.append(score)
        precision = _div(tp, tp + fp)
        recall = _div(tp, tp + fn)
        f1 = _div(2.0 * precision * recall, precision + recall)
        accuracy = _div(tp + tn, tp + tn + fp + fn)
        pos_mean = _div(sum(pos_scores), len(pos_scores))
        neg_mean = _div(sum(neg_scores), len(neg_scores))
        out.append({
            "method": method,
            "threshold": float(threshold),
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "accuracy": accuracy,
            "true_positives": tp,
            "false_positives": fp,
            "true_negatives": tn,
            "false_negatives": fn,
            "positive_mean": pos_mean,
            "negative_mean": neg_mean,
            "mean_gap": pos_mean - neg_mean,
            "positive_median": _median(pos_scores),
            "negative_median": _median(neg_scores),
            "median_gap": _median(pos_scores) - _median(neg_scores),
            "positive_count": len(pos_scores),
            "negative_count": len(neg_scores),
        })
    return out


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark", default="results_benchmark/labeled_scored.json")
    ap.add_argument("--output-dir", default="results_benchmark/labeled")
    ap.add_argument("--threshold", type=float, default=50.0)
    args = ap.parse_args()

    pairs = load_pairs(Path(args.benchmark))
    out_dir = Path(args.output_dir)

    lenient = summarize(pairs, positive=LENIENT_POSITIVE, threshold=args.threshold)
    strict = summarize(pairs, positive=STRICT_POSITIVE, threshold=args.threshold)

    # labeled_summary.* and labeled_lenient_summary.* are the same lenient cohort.
    write_csv(out_dir / "labeled_summary.csv", lenient)
    write_csv(out_dir / "labeled_lenient_summary.csv", lenient)
    write_csv(out_dir / "labeled_strict_summary.csv", strict)
    (out_dir / "labeled_summary.json").write_text(json.dumps(lenient, indent=2), encoding="utf-8")
    (out_dir / "labeled_lenient_summary.json").write_text(json.dumps(lenient, indent=2), encoding="utf-8")
    (out_dir / "labeled_strict_summary.json").write_text(json.dumps(strict, indent=2), encoding="utf-8")

    meta_f1 = next((r["f1"] for r in lenient if r["method"] == "metadata"), None)
    print(f"lenient metadata F1 = {meta_f1}")
    print(f"Wrote stdlib labeled summaries to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
