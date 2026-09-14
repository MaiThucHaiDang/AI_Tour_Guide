"""Evaluate entity lookup and pgvector retrieval on a labeled bilingual set."""

from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from sqlalchemy import func, select

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(BACKEND_ROOT))

from core.config import settings  # noqa: E402
from core.database import async_session_factory, engine  # noqa: E402
from models.graph import ArtifactFAQ, ArtifactRelation, KnowledgeFact  # noqa: E402
from repositories.artifact_repository import find_artifact_by_name  # noqa: E402
from services.ai.embedding_service import EmbeddingService  # noqa: E402
from evaluation.metrics import (  # noqa: E402
    choose_distance_threshold,
    classification_metrics,
    latency_summary,
    ranking_metrics,
)

DEFAULT_DATASET = PROJECT_ROOT / "evaluation" / "data" / "rag_cases.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "evaluation" / "results" / "rag_results.json"
BATCH_SIZE = 100


def _git_commit() -> str:
    try:
        return subprocess.run(
            [
                "git",
                "-c",
                f"safe.directory={PROJECT_ROOT}",
                "rev-parse",
                "HEAD",
            ],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except Exception:
        return "unknown"


def _load_cases(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    positives: list[dict[str, Any]] = []
    for artifact in payload["artifacts"]:
        for query_type in ("entity", "semantic"):
            query_map = artifact[f"{query_type}_queries"]
            for lang in ("vi", "en"):
                queries = query_map[lang]
                if len(queries) != 2:
                    raise ValueError(
                        f"Artifact {artifact['artifact_id']} must have one dev and one test "
                        f"query for {query_type}/{lang}"
                    )
                for index, text in enumerate(queries):
                    positives.append(
                        {
                            "text": text,
                            "lang": lang,
                            "query_type": query_type,
                            "split": "dev" if index == 0 else "test",
                            "expected_artifact_id": int(artifact["artifact_id"]),
                            "expected_name_vi": artifact["name_vi"],
                            "expected_name_en": artifact["name_en"],
                        }
                    )

    negatives = list(payload.get("ood_queries", []))
    return positives, negatives


async def _embed_queries(texts: list[str]) -> list[list[float]]:
    embeddings: list[list[float]] = []
    for offset in range(0, len(texts), BATCH_SIZE):
        batch = texts[offset : offset + BATCH_SIZE]
        batch_embeddings = await EmbeddingService.get_query_embeddings(batch)
        if len(batch_embeddings) != len(batch):
            raise RuntimeError(
                f"Expected {len(batch)} query embeddings, received {len(batch_embeddings)}"
            )
        embeddings.extend(batch_embeddings)
    return embeddings


async def _rank_vector(
    query_embedding: list[float], top_k: int
) -> tuple[list[int], list[float]]:
    distance = ArtifactFAQ.embedding.cosine_distance(query_embedding)
    grouped_distance = func.min(distance).label("distance")
    stmt = (
        select(ArtifactFAQ.artifact_id, grouped_distance)
        .where(ArtifactFAQ.embedding.is_not(None))
        .group_by(ArtifactFAQ.artifact_id)
        .order_by(grouped_distance.asc())
        .limit(top_k)
    )
    async with async_session_factory() as session:
        result = await session.execute(stmt)
        rows = result.all()
    return [int(row.artifact_id) for row in rows], [float(row.distance) for row in rows]


async def _expand_graph(entry_ids: list[int], top_k: int) -> list[int]:
    """Mirror the bounded, directed graph expansion used by production search."""
    if not entry_ids:
        return []
    stmt = (
        select(ArtifactRelation.target_artifact_id)
        .where(ArtifactRelation.source_artifact_id.in_(entry_ids))
        .order_by(ArtifactRelation.weight.desc(), ArtifactRelation.id.asc())
        .limit(top_k)
    )
    async with async_session_factory() as session:
        result = await session.execute(stmt)

    expanded = list(entry_ids)
    for target_id in result.scalars().all():
        artifact_id = int(target_id)
        if artifact_id not in expanded:
            expanded.append(artifact_id)
    return expanded


async def _evaluate_vector_cases(
    cases: list[dict[str, Any]], top_k: int
) -> list[dict[str, Any]]:
    embeddings = await _embed_queries([case["text"] for case in cases])
    rows: list[dict[str, Any]] = []
    for index, (case, embedding) in enumerate(zip(cases, embeddings), start=1):
        started = time.perf_counter()
        ranked_ids, distances = await _rank_vector(embedding, top_k)
        expanded_ids = await _expand_graph(ranked_ids, top_k)
        latency_ms = (time.perf_counter() - started) * 1000
        rows.append(
            {
                **case,
                "ranked_artifact_ids": ranked_ids,
                "graph_context_artifact_ids": expanded_ids,
                "best_distance": distances[0] if distances else None,
                "distances": distances,
                "latency_ms": round(latency_ms, 3),
            }
        )
        if index % 20 == 0 or index == len(cases):
            print(f"vector retrieval: {index}/{len(cases)}")
    return rows


async def _evaluate_entity_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in cases:
        started = time.perf_counter()
        result = await find_artifact_by_name(case["text"])
        latency_ms = (time.perf_counter() - started) * 1000
        predicted = int(result.art_id) if result and str(result.art_id).isdigit() else None
        rows.append(
            {
                **case,
                "predicted_artifact_id": predicted,
                "correct": predicted == int(case["expected_artifact_id"]),
                "latency_ms": round(latency_ms, 3),
            }
        )
    return rows


def _entity_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for split in ("dev", "test"):
        split_rows = [row for row in rows if row["split"] == split]
        summary[split] = {
            "count": len(split_rows),
            "accuracy": round(
                sum(bool(row["correct"]) for row in split_rows) / len(split_rows), 4
            ) if split_rows else 0.0,
            "latency": latency_summary(row["latency_ms"] for row in split_rows),
        }
        for lang in ("vi", "en"):
            lang_rows = [row for row in split_rows if row["lang"] == lang]
            summary[split][f"accuracy_{lang}"] = round(
                sum(bool(row["correct"]) for row in lang_rows) / len(lang_rows), 4
            ) if lang_rows else 0.0
    return summary


def _threshold_summary(
    positives: list[dict[str, Any]], negatives: list[dict[str, Any]]
) -> dict[str, Any]:
    dev_positive = [
        float(row["best_distance"])
        for row in positives
        if row["split"] == "dev" and row["best_distance"] is not None
    ]
    dev_negative = [
        float(row["best_distance"])
        for row in negatives
        if row["split"] == "dev" and row["best_distance"] is not None
    ]
    selected = choose_distance_threshold(dev_positive, dev_negative)
    threshold = float(selected["threshold"])

    test_positive = [row for row in positives if row["split"] == "test"]
    test_negative = [row for row in negatives if row["split"] == "test"]
    test_rows = test_positive + test_negative
    expected = [True] * len(test_positive) + [False] * len(test_negative)
    predicted = [
        row["best_distance"] is not None and float(row["best_distance"]) <= threshold
        for row in test_rows
    ]
    in_domain_classification = classification_metrics(expected, predicted)
    ood_detection = classification_metrics(
        [not value for value in expected],
        [not value for value in predicted],
    )
    correct_and_accepted = sum(
        row["best_distance"] is not None
        and float(row["best_distance"]) <= threshold
        and row["ranked_artifact_ids"]
        and int(row["ranked_artifact_ids"][0]) == int(row["expected_artifact_id"])
        for row in test_positive
    )
    return {
        "selected_on_dev": selected,
        "test_in_domain_classification": in_domain_classification,
        "test_ood_detection": ood_detection,
        "test_ood_rejection_rate": ood_detection["recall"],
        "test_positive_correct_and_accepted_rate": round(
            correct_and_accepted / len(test_positive), 4
        ) if test_positive else 0.0,
    }


def _load_reusable_vector_cases(
    cache_path: Path,
    positives: list[dict[str, Any]],
    negatives: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cached = json.loads(cache_path.read_text(encoding="utf-8"))["cases"]
    cached_positive = list(cached["vector_positive"])
    cached_negative = list(cached["vector_ood"])

    def identity(row: dict[str, Any]) -> tuple[Any, ...]:
        return (
            row["text"],
            row["lang"],
            row.get("query_type"),
            row["split"],
            row.get("expected_artifact_id"),
        )

    if [identity(row) for row in cached_positive] != [
        identity(row) for row in positives
    ]:
        raise ValueError("Cached positive vector cases do not match the dataset")
    if [identity(row) for row in cached_negative] != [
        identity(row) for row in negatives
    ]:
        raise ValueError("Cached OOD vector cases do not match the dataset")
    return cached_positive, cached_negative


async def _refresh_graph_context(
    rows: list[dict[str, Any]], top_k: int
) -> list[dict[str, Any]]:
    """Recompute graph-only fields while preserving audited vector rankings."""
    refreshed: list[dict[str, Any]] = []
    for row in rows:
        current = dict(row)
        ranked_ids = [int(value) for value in current["ranked_artifact_ids"]]
        current["graph_context_artifact_ids"] = await _expand_graph(
            ranked_ids,
            top_k,
        )
        refreshed.append(current)
    return refreshed


async def run(
    dataset: Path,
    output: Path,
    top_k: int,
    reuse_vector_cases: Path | None = None,
) -> dict[str, Any]:
    positives, negatives = _load_cases(dataset)

    async with async_session_factory() as session:
        unique_documents = (
            select(ArtifactFAQ.artifact_id, ArtifactFAQ.question_text)
            .distinct()
            .subquery()
        )
        index_count = int(
            (
                await session.execute(
                    select(func.count()).select_from(unique_documents)
                )
            ).scalar_one()
        )
        indexed_artifact_count = int(
            (
                await session.execute(
                    select(func.count(func.distinct(ArtifactFAQ.artifact_id)))
                )
            ).scalar_one()
        )
        relation_count = int(
            (
                await session.execute(select(func.count(ArtifactRelation.id)))
            ).scalar_one()
        )
        fact_count = int(
            (await session.execute(select(func.count(KnowledgeFact.id)))).scalar_one()
        )
    if index_count == 0:
        raise RuntimeError(
            "artifact_faqs is empty. Run `python scripts/build_rag_index.py` first."
        )

    if reuse_vector_cases is None:
        vector_rows = await _evaluate_vector_cases(positives + negatives, top_k)
        vector_positive = vector_rows[: len(positives)]
        vector_negative = vector_rows[len(positives) :]
    else:
        vector_positive, vector_negative = _load_reusable_vector_cases(
            reuse_vector_cases,
            positives,
            negatives,
        )
        vector_positive = await _refresh_graph_context(vector_positive, top_k)
        vector_negative = await _refresh_graph_context(vector_negative, top_k)
    entity_rows = await _evaluate_entity_cases(
        [case for case in positives if case["query_type"] == "entity"]
    )

    vector_dev = [row for row in vector_positive if row["split"] == "dev"]
    vector_test = [row for row in vector_positive if row["split"] == "test"]
    graph_context_recall = sum(
        int(row["expected_artifact_id"]) in row["graph_context_artifact_ids"]
        for row in vector_test
    ) / len(vector_test)
    graph_context_size = sum(
        len(row["graph_context_artifact_ids"]) for row in vector_test
    ) / len(vector_test)
    base_hit_at_3 = float(ranking_metrics(vector_test)["overall"]["hit_at_3"])

    result = {
        "metadata": {
            "git_commit": _git_commit(),
            "dataset": str(dataset.relative_to(PROJECT_ROOT)),
            "positive_queries": len(positives),
            "ood_queries": len(negatives),
            "indexed_documents": index_count,
            "indexed_artifacts": indexed_artifact_count,
            "knowledge_facts": fact_count,
            "graph_relations": relation_count,
            "top_k": top_k,
            "embedding_model": settings.GEMINI_EMBEDDING_MODEL,
        },
        "entity_lookup": _entity_summary(entity_rows),
        "vector_retrieval": {
            "dev": ranking_metrics(vector_dev),
            "test": ranking_metrics(vector_test),
            "test_graph_context_recall": round(graph_context_recall, 4),
            "test_graph_context_recall_gain": round(
                graph_context_recall - base_hit_at_3, 4
            ),
            "test_graph_context_mean_artifacts": round(graph_context_size, 2),
            "ood_threshold": _threshold_summary(vector_positive, vector_negative),
        },
        "cases": {
            "entity": entity_rows,
            "vector_positive": vector_positive,
            "vector_ood": vector_negative,
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument(
        "--reuse-vector-cases",
        type=Path,
        help=(
            "Reuse audited per-query vector results from a previous result file. "
            "Useful for report/schema migrations that do not change retrieval."
        ),
    )
    args = parser.parse_args()
    if args.top_k < 1:
        parser.error("--top-k must be at least 1")

    try:
        result = await run(
            args.dataset.resolve(),
            args.output.resolve(),
            args.top_k,
            args.reuse_vector_cases.resolve() if args.reuse_vector_cases else None,
        )
        test_metrics = result["vector_retrieval"]["test"]["overall"]
        print(json.dumps({
            "entity_test_accuracy": result["entity_lookup"]["test"]["accuracy"],
            "vector_test_hit_at_1": test_metrics["hit_at_1"],
            "vector_test_hit_at_3": test_metrics["hit_at_3"],
            "vector_test_mrr": test_metrics["mrr"],
            "output": str(args.output),
        }, indent=2))
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
