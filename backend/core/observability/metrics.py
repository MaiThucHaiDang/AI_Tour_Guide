"""Small in-memory metrics collector for local and single-instance deployments."""

from __future__ import annotations

from collections import defaultdict
from time import perf_counter
from typing import Any

_COUNTERS: dict[str, int] = defaultdict(int)
_DURATIONS: dict[str, list[float]] = defaultdict(list)


def increment(name: str, value: int = 1) -> None:
    _COUNTERS[name] += value


def observe_duration(name: str, started_at: float) -> None:
    elapsed_ms = (perf_counter() - started_at) * 1000
    values = _DURATIONS[name]
    values.append(elapsed_ms)
    if len(values) > 200:
        del values[: len(values) - 200]


def snapshot() -> dict[str, Any]:
    durations: dict[str, dict[str, float]] = {}
    for name, values in _DURATIONS.items():
        if not values:
            continue
        sorted_values = sorted(values)
        durations[name] = {
            "count": len(values),
            "avg_ms": round(sum(values) / len(values), 2),
            "p95_ms": round(sorted_values[int((len(sorted_values) - 1) * 0.95)], 2),
            "max_ms": round(max(values), 2),
        }
    return {
        "counters": dict(_COUNTERS),
        "durations": durations,
    }
