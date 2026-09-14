"""Small dependency-free metric helpers shared by evaluation runners."""

from __future__ import annotations

import math
from collections import defaultdict
from statistics import mean
from typing import Any, Iterable


def percentile(values: Iterable[float], percentile_value: float) -> float | None:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return None
    if not 0 <= percentile_value <= 100:
        raise ValueError("percentile_value must be between 0 and 100")
    if len(ordered) == 1:
        return ordered[0]

    position = (len(ordered) - 1) * percentile_value / 100.0
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def latency_summary(latencies_ms: Iterable[float]) -> dict[str, float | int | None]:
    values = [float(value) for value in latencies_ms]
    return {
        "count": len(values),
        "mean_ms": round(mean(values), 2) if values else None,
        "p50_ms": round(percentile(values, 50), 2) if values else None,
        "p95_ms": round(percentile(values, 95), 2) if values else None,
    }


def _ranking_summary(rows: list[dict[str, Any]]) -> dict[str, float | int]:
    if not rows:
        return {"count": 0, "hit_at_1": 0.0, "hit_at_3": 0.0, "mrr": 0.0}

    reciprocal_ranks: list[float] = []
    hit_at_1 = 0
    hit_at_3 = 0
    for row in rows:
        expected = int(row["expected_artifact_id"])
        ranked = [int(value) for value in row.get("ranked_artifact_ids", [])]
        try:
            rank = ranked.index(expected) + 1
        except ValueError:
            rank = 0
        hit_at_1 += int(rank == 1)
        hit_at_3 += int(0 < rank <= 3)
        reciprocal_ranks.append(1.0 / rank if rank else 0.0)

    count = len(rows)
    return {
        "count": count,
        "hit_at_1": round(hit_at_1 / count, 4),
        "hit_at_3": round(hit_at_3 / count, 4),
        "mrr": round(mean(reciprocal_ranks), 4),
    }


def ranking_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Return overall metrics plus language/query-type breakdowns."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[f"lang:{row.get('lang', 'unknown')}"] .append(row)
        grouped[f"type:{row.get('query_type', 'unknown')}"] .append(row)

    return {
        "overall": _ranking_summary(rows),
        "breakdown": {
            group_name: _ranking_summary(group_rows)
            for group_name, group_rows in sorted(grouped.items())
        },
        "latency": latency_summary(row.get("latency_ms", 0.0) for row in rows),
    }


def classification_metrics(
    expected_positive: list[bool], predicted_positive: list[bool]
) -> dict[str, float | int]:
    if len(expected_positive) != len(predicted_positive):
        raise ValueError("Expected and predicted labels must have equal length")

    tp = sum(e and p for e, p in zip(expected_positive, predicted_positive))
    tn = sum((not e) and (not p) for e, p in zip(expected_positive, predicted_positive))
    fp = sum((not e) and p for e, p in zip(expected_positive, predicted_positive))
    fn = sum(e and (not p) for e, p in zip(expected_positive, predicted_positive))
    total = len(expected_positive)

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "count": total,
        "true_positive": tp,
        "true_negative": tn,
        "false_positive": fp,
        "false_negative": fn,
        "accuracy": round((tp + tn) / total, 4) if total else 0.0,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "specificity": round(specificity, 4),
        "f1": round(f1, 4),
    }


def choose_distance_threshold(
    positive_distances: list[float], negative_distances: list[float]
) -> dict[str, float | dict[str, float | int]]:
    """Choose a dev-only cosine-distance threshold using balanced accuracy."""
    if not positive_distances or not negative_distances:
        raise ValueError("Both positive and negative development distances are required")

    unique_values = sorted(set(positive_distances + negative_distances))
    candidates = [unique_values[0] - 1e-6, unique_values[-1] + 1e-6]
    candidates.extend(
        (left + right) / 2.0 for left, right in zip(unique_values, unique_values[1:])
    )

    expected = [True] * len(positive_distances) + [False] * len(negative_distances)
    distances = positive_distances + negative_distances
    best: tuple[float, float, dict[str, float | int]] | None = None
    for threshold in candidates:
        predicted = [distance <= threshold for distance in distances]
        metrics = classification_metrics(expected, predicted)
        balanced_accuracy = (float(metrics["recall"]) + float(metrics["specificity"])) / 2
        # Prefer the stricter threshold when scores tie.
        candidate = (balanced_accuracy, -threshold, metrics)
        if best is None or candidate[:2] > best[:2]:
            best = candidate

    assert best is not None
    return {
        "threshold": round(-best[1], 6),
        "balanced_accuracy": round(best[0], 4),
        "classification": best[2],
    }
