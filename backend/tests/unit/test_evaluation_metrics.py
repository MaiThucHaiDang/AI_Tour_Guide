import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.metrics import (
    choose_distance_threshold,
    classification_metrics,
    latency_summary,
    percentile,
    ranking_metrics,
)


def test_percentile_interpolates_and_handles_empty_input():
    assert percentile([], 50) is None
    assert percentile([10], 95) == 10
    assert percentile([0, 10], 50) == 5


def test_ranking_metrics_reports_hits_mrr_and_breakdowns():
    rows = [
        {
            "expected_artifact_id": 1,
            "ranked_artifact_ids": [1, 2, 3],
            "lang": "vi",
            "query_type": "entity",
            "latency_ms": 10,
        },
        {
            "expected_artifact_id": 2,
            "ranked_artifact_ids": [1, 2, 3],
            "lang": "en",
            "query_type": "semantic",
            "latency_ms": 20,
        },
        {
            "expected_artifact_id": 4,
            "ranked_artifact_ids": [1, 2, 3],
            "lang": "en",
            "query_type": "semantic",
            "latency_ms": 30,
        },
    ]

    result = ranking_metrics(rows)
    assert result["overall"] == {
        "count": 3,
        "hit_at_1": 0.3333,
        "hit_at_3": 0.6667,
        "mrr": 0.5,
    }
    assert result["breakdown"]["lang:vi"]["hit_at_1"] == 1.0
    assert result["latency"] == {
        "count": 3,
        "mean_ms": 20.0,
        "p50_ms": 20.0,
        "p95_ms": 29.0,
    }


def test_classification_metrics_and_threshold_selection():
    result = classification_metrics(
        [True, True, False, False], [True, False, True, False]
    )
    assert result["accuracy"] == 0.5
    assert result["precision"] == 0.5
    assert result["recall"] == 0.5
    assert result["specificity"] == 0.5

    threshold = choose_distance_threshold([0.1, 0.2], [0.7, 0.8])
    assert 0.2 < threshold["threshold"] < 0.7
    assert threshold["balanced_accuracy"] == 1.0


def test_latency_summary_rounds_values():
    assert latency_summary([10.123, 20.456])["mean_ms"] == 15.29
