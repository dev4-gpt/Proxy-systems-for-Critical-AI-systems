#!/usr/bin/env python3
"""Bootstrap 95% CIs for labeled benchmark F1 (pair-level resampling)."""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path
from typing import Dict, List, Sequence, Set

from proxytool_redux.benchmark_metrics import compute_pair_classification_metrics

DEFAULT_METHODS = ["metadata", "code_centric", "dynamic", "cross_language"]
LENIENT_POSITIVE = {"known_match", "known_related"}
STRICT_POSITIVE = {"known_match"}
EXCLUDE = {"target_uncertain"}


def load_pairs(path: Path) -> List[Dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return list(payload.get("pairs", []))


def cohort_rows(
    pairs: Sequence[Dict[str, object]],
    method: str,
    positive_labels: Set[str],
) -> List[Dict[str, object]]:
    key = f"{method}_score"
    rows: List[Dict[str, object]] = []
    for pair in pairs:
        label = str(pair.get("label", ""))
        if label in EXCLUDE:
            continue
        score = pair.get(key)
        if score in (None, ""):
            continue
        rows.append({"label": label, "score": float(score)})
    return rows


def bootstrap_f1(
    rows: List[Dict[str, object]],
    positive_labels: Set[str],
    threshold: float,
    n: int,
    seed: int,
) -> List[float]:
    rng = random.Random(seed)
    if not rows:
        return []
    out: List[float] = []
    for _ in range(n):
        sample = [rows[rng.randrange(len(rows))] for _ in range(len(rows))]
        m = compute_pair_classification_metrics(
            sample,
            score_key="score",
            label_key="label",
            positive_labels=positive_labels,
            threshold=threshold,
        )
        out.append(m.f1)
    return out


def ci(values: Sequence[float], alpha: float = 0.05) -> tuple[float, float, float]:
    if not values:
        return 0.0, 0.0, 0.0
    xs = sorted(values)
    lo = xs[int((alpha / 2) * len(xs))]
    hi = xs[int((1 - alpha / 2) * len(xs)) - 1]
    return sum(xs) / len(xs), lo, hi


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", default="results_benchmark/labeled_scored_v2.json")
    parser.add_argument("--output", default="results_benchmark/labeled_v2/bootstrap_ci.csv")
    parser.add_argument("--threshold", type=float, default=50.0)
    parser.add_argument("--n-bootstrap", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--methods", nargs="*", default=DEFAULT_METHODS)
    args = parser.parse_args()

    pairs = load_pairs(Path(args.benchmark))
    rows_out: List[Dict[str, object]] = []

    for method in args.methods:
        base = cohort_rows(pairs, method, LENIENT_POSITIVE)
        strict_base = cohort_rows(pairs, method, STRICT_POSITIVE)
        for cohort, pos, name in (
            (base, LENIENT_POSITIVE, "lenient"),
            (strict_base, STRICT_POSITIVE, "strict"),
        ):
            f1s = bootstrap_f1(cohort, pos, args.threshold, args.n_bootstrap, args.seed)
            mean, lo, hi = ci(f1s)
            rows_out.append(
                {
                    "method": method,
                    "cohort": name,
                    "threshold": args.threshold,
                    "n_pairs": len(cohort),
                    "f1_mean": round(mean, 4),
                    "f1_ci_lo": round(lo, 4),
                    "f1_ci_hi": round(hi, 4),
                    "n_bootstrap": args.n_bootstrap,
                }
            )

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows_out[0].keys()))
        writer.writeheader()
        writer.writerows(rows_out)
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
