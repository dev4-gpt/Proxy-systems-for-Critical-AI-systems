"""Benchmark metrics for labeled-pair evaluation.

These helpers are intentionally dependency-light so they can be reused from
notebooks or scripts without pulling in the entire exploratory environment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence


@dataclass(frozen=True)
class TopKMetrics:
    top1_accuracy: float
    recall_at_3: float
    recall_at_5: float
    mrr: float
    pair_count: int


@dataclass(frozen=True)
class ClassificationMetrics:
    threshold: float
    precision: float
    recall: float
    f1: float
    accuracy: float
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int


@dataclass(frozen=True)
class ScoreSeparationMetrics:
    positive_mean: float
    negative_mean: float
    mean_gap: float
    positive_median: float
    negative_median: float
    median_gap: float
    positive_count: int
    negative_count: int


def _safe_divide(numerator: float, denominator: float) -> float:
    return float(numerator) / float(denominator) if denominator else 0.0


def _median(values: Sequence[float]) -> float:
    xs = sorted(float(v) for v in values)
    if not xs:
        return 0.0
    mid = len(xs) // 2
    if len(xs) % 2 == 1:
        return xs[mid]
    return 0.5 * (xs[mid - 1] + xs[mid])


def compute_topk_metrics(rows: Sequence[Mapping[str, object]], *, relevant_labels: Optional[Iterable[str]] = None) -> TopKMetrics:
    """Compute retrieval-style metrics from ranked rows.

    Expected row keys:
      - pair_id
      - rank (1 = best)
      - is_relevant (preferred) OR label in relevant_labels
    """
    relevant_set = set(relevant_labels or {"known_match", "known_related", "positive", "relevant"})
    grouped: MutableMapping[str, List[Mapping[str, object]]] = {}
    for row in rows:
        pair_id = str(row.get("pair_id", "")).strip()
        if not pair_id:
            continue
        grouped.setdefault(pair_id, []).append(row)

    top1_hits = 0
    r3_hits = 0
    r5_hits = 0
    reciprocal_rank_total = 0.0

    for pair_rows in grouped.values():
        ordered = sorted(pair_rows, key=lambda r: int(r.get("rank", 10**9)))
        relevant_rank: Optional[int] = None
        for row in ordered:
            is_relevant = row.get("is_relevant")
            if is_relevant is None:
                is_relevant = str(row.get("label", "")).strip() in relevant_set
            if bool(is_relevant):
                relevant_rank = int(row.get("rank", 0))
                break
        if relevant_rank is None:
            continue
        if relevant_rank == 1:
            top1_hits += 1
        if relevant_rank <= 3:
            r3_hits += 1
        if relevant_rank <= 5:
            r5_hits += 1
        reciprocal_rank_total += 1.0 / float(relevant_rank)

    pair_count = len(grouped)
    return TopKMetrics(
        top1_accuracy=_safe_divide(top1_hits, pair_count),
        recall_at_3=_safe_divide(r3_hits, pair_count),
        recall_at_5=_safe_divide(r5_hits, pair_count),
        mrr=_safe_divide(reciprocal_rank_total, pair_count),
        pair_count=pair_count,
    )


def compute_pair_classification_metrics(
    rows: Sequence[Mapping[str, object]],
    *,
    score_key: str = "score",
    label_key: str = "label",
    positive_labels: Optional[Iterable[str]] = None,
    threshold: float = 0.5,
) -> ClassificationMetrics:
    positive_set = set(positive_labels or {"known_match", "known_related", "positive", "relevant"})
    tp = fp = tn = fn = 0
    for row in rows:
        actual_positive = str(row.get(label_key, "")).strip() in positive_set
        predicted_positive = float(row.get(score_key, 0.0)) >= float(threshold)
        if actual_positive and predicted_positive:
            tp += 1
        elif actual_positive and not predicted_positive:
            fn += 1
        elif not actual_positive and predicted_positive:
            fp += 1
        else:
            tn += 1
    precision = _safe_divide(tp, tp + fp)
    recall = _safe_divide(tp, tp + fn)
    f1 = _safe_divide(2.0 * precision * recall, precision + recall)
    accuracy = _safe_divide(tp + tn, tp + tn + fp + fn)
    return ClassificationMetrics(
        threshold=float(threshold),
        precision=precision,
        recall=recall,
        f1=f1,
        accuracy=accuracy,
        true_positives=tp,
        false_positives=fp,
        true_negatives=tn,
        false_negatives=fn,
    )



def compute_score_separation(
    rows: Sequence[Mapping[str, object]],
    *,
    score_key: str = "score",
    label_key: str = "label",
    positive_labels: Optional[Iterable[str]] = None,
    negative_labels: Optional[Iterable[str]] = None,
) -> ScoreSeparationMetrics:
    positive_set = set(positive_labels or {"known_match", "known_related", "positive", "relevant"})
    negative_set = set(negative_labels or {"known_non_match", "negative", "non_match"})
    pos_scores: List[float] = []
    neg_scores: List[float] = []
    for row in rows:
        label = str(row.get(label_key, "")).strip()
        score = float(row.get(score_key, 0.0))
        if label in positive_set:
            pos_scores.append(score)
        elif label in negative_set:
            neg_scores.append(score)
    pos_mean = _safe_divide(sum(pos_scores), len(pos_scores))
    neg_mean = _safe_divide(sum(neg_scores), len(neg_scores))
    return ScoreSeparationMetrics(
        positive_mean=pos_mean,
        negative_mean=neg_mean,
        mean_gap=pos_mean - neg_mean,
        positive_median=_median(pos_scores),
        negative_median=_median(neg_scores),
        median_gap=_median(pos_scores) - _median(neg_scores),
        positive_count=len(pos_scores),
        negative_count=len(neg_scores),
    )



def metrics_to_dict(obj: object) -> Dict[str, object]:
    if hasattr(obj, "__dataclass_fields__"):
        return {field: getattr(obj, field) for field in obj.__dataclass_fields__}
    raise TypeError(f"Unsupported metrics object: {type(obj)!r}")
