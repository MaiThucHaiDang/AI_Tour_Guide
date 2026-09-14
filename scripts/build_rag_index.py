"""Build an idempotent pgvector document index for artifact retrieval.

Run after Alembic migrations and ``scripts/seed_data.py``. Existing FAQ rows
are reused by exact ``artifact_id`` + ``question_text`` identity; only missing
or null embeddings trigger an external embedding request.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import re
import sys
from collections import defaultdict
from pathlib import Path

from sqlalchemy import select

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from core.config import settings  # noqa: E402
from core.database import async_session_factory, engine  # noqa: E402
from models.artifact import Artifact  # noqa: E402
from models.bilingual_content import BilingualContent  # noqa: E402
from models.graph import ArtifactFAQ  # noqa: E402
from services.ai.embedding_service import EmbeddingService  # noqa: E402

LOGGER = logging.getLogger("rag_index")
MAX_DOCUMENT_CHARS = 360
EMBEDDING_BATCH_SIZE = 50


def _normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _split_text(text: str, max_chars: int = MAX_DOCUMENT_CHARS) -> list[str]:
    """Split text into deterministic, sentence-aware embedding documents."""
    cleaned = _normalize_space(text)
    if not cleaned:
        return []

    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if not sentence:
            continue
        candidate = f"{current} {sentence}".strip()
        if current and len(candidate) > max_chars:
            chunks.append(current)
            current = sentence
        else:
            current = candidate

        while len(current) > max_chars:
            split_at = current.rfind(" ", 0, max_chars)
            split_at = split_at if split_at > max_chars // 2 else max_chars
            chunks.append(current[:split_at].strip())
            current = current[split_at:].strip()

    if current:
        chunks.append(current)
    return chunks


def _artifact_documents(
    artifact: Artifact,
    bilingual_rows: list[BilingualContent],
) -> list[str]:
    """Create bilingual retrieval documents without asking an LLM to invent FAQs."""
    prefix = f"{artifact.name_vi} / {artifact.name_en}"
    documents = [
        f"{prefix}. Vietnamese history: {chunk}"
        for chunk in _split_text(artifact.history_text_vi)
    ]
    documents.extend(
        f"{prefix}. English history: {chunk}"
        for chunk in _split_text(artifact.history_text_en)
    )

    metadata = [prefix]
    if artifact.author:
        metadata.append(f"Builder or historical attribution: {artifact.author}")
    if artifact.year:
        metadata.append(f"Construction or historical year: {artifact.year}")
    documents.append(". ".join(metadata))

    for row in sorted(bilingual_rows, key=lambda item: (item.lang, item.content_type)):
        for chunk in _split_text(row.content_text):
            documents.append(
                f"{prefix}. {row.lang.upper()} {row.content_type}: {chunk}"
            )

    # Preserve order while removing duplicate documents.
    return list(dict.fromkeys(_normalize_space(item) for item in documents if item))


async def build_index(dry_run: bool = False) -> dict[str, int | str]:
    async with async_session_factory() as session:
        artifact_result = await session.execute(select(Artifact).order_by(Artifact.art_id))
        artifacts = list(artifact_result.scalars().all())
        content_result = await session.execute(
            select(BilingualContent).order_by(
                BilingualContent.artifact_id,
                BilingualContent.lang,
                BilingualContent.content_type,
            )
        )
        content_by_artifact: dict[int, list[BilingualContent]] = defaultdict(list)
        for row in content_result.scalars().all():
            content_by_artifact[row.artifact_id].append(row)

        existing_result = await session.execute(select(ArtifactFAQ))
        existing = {
            (row.artifact_id, row.question_text): row
            for row in existing_result.scalars().all()
        }

        pending: list[tuple[int, str, ArtifactFAQ | None]] = []
        document_count = 0
        covered_artifacts = 0
        for artifact in artifacts:
            documents = _artifact_documents(
                artifact, content_by_artifact.get(artifact.art_id, [])
            )
            if documents:
                covered_artifacts += 1
            document_count += len(documents)
            for document in documents:
                row = existing.get((artifact.art_id, document))
                if row is None or row.embedding is None:
                    pending.append((artifact.art_id, document, row))

        summary: dict[str, int | str] = {
            "artifacts": len(artifacts),
            "covered_artifacts": covered_artifacts,
            "documents": document_count,
            "embeddings_to_create": len(pending),
            "embedding_model": settings.GEMINI_EMBEDDING_MODEL,
        }
        if dry_run or not pending:
            return summary

        for offset in range(0, len(pending), EMBEDDING_BATCH_SIZE):
            batch = pending[offset : offset + EMBEDDING_BATCH_SIZE]
            embeddings = await EmbeddingService.get_embeddings(
                [document for _, document, _ in batch]
            )
            if len(embeddings) != len(batch):
                raise RuntimeError(
                    f"Embedding batch returned {len(embeddings)} vectors for {len(batch)} documents"
                )

            for (artifact_id, document, row), embedding in zip(batch, embeddings):
                if len(embedding) != 768:
                    raise RuntimeError(
                        f"Expected a 768-dimensional embedding, received {len(embedding)}"
                    )
                if row is None:
                    session.add(
                        ArtifactFAQ(
                            artifact_id=artifact_id,
                            question_text=document,
                            embedding=embedding,
                        )
                    )
                else:
                    row.embedding = embedding
            await session.commit()
            LOGGER.info(
                "Indexed %d/%d pending documents",
                min(offset + len(batch), len(pending)),
                len(pending),
            )

        summary["embeddings_created"] = len(pending)
        return summary


async def _main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Inspect artifact coverage without calling the embedding API or writing rows.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        summary = await build_index(dry_run=args.dry_run)
        for key, value in summary.items():
            print(f"{key}={value}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
