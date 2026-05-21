"""Repository for artifact database operations.

Replaces raw pyodbc calls from both:
  - src/backend/services/database.py  (vision pipeline)
  - part4/backend/services/voice/sqlserver_db.py  (voice pipeline)

Uses async SQLAlchemy with PostgreSQL.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from typing import Optional

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import async_session_factory
from models.artifact import Artifact
from schemas.vision import ArtifactInfo

_LOGGER = logging.getLogger(__name__)

_STOP_WORDS = {
    "la", "ve", "noi", "ke", "gioi", "thieu", "cho", "toi", "ban",
    "please", "tell", "me", "about", "the", "a", "an", "this",
    "that", "is", "are",
}


# ─── Vision Pipeline Methods ────────────────────────────────────────────────


async def get_artifact_by_id(artifact_id: str) -> Optional[ArtifactInfo]:
    """Fetch artifact info by ID. Used by the vision pipeline."""
    try:
        art_id_int = int(artifact_id)
    except (ValueError, TypeError):
        return None

    async with async_session_factory() as session:
        result = await session.execute(
            select(Artifact).where(Artifact.art_id == art_id_int)
        )
        row = result.scalar_one_or_none()

        if row is None:
            return None

        return ArtifactInfo(
            art_id=str(row.art_id),
            loc_id=str(row.loc_id),
            name_vi=row.name_vi,
            name_en=row.name_en,
            history_text_vi=row.history_text_vi,
            history_text_en=row.history_text_en,
            author=row.author,
            year=row.year,
        )


async def find_artifact_by_name(name: str) -> Optional[ArtifactInfo]:
    """Robustly find an artifact by its name (VI or EN).
    
    Used by the vision pipeline to resolve AI-detected labels to DB entities.
    """
    if not name:
        return None

    try:
        async with async_session_factory() as session:
            # 1. Direct match (checks if any DB name is in the input name)
            row = await _direct_match(session, name)

            # 2. Unaccented match
            if not row:
                unaccented = _normalize_text(name)
                row = await _direct_match(session, unaccented)

            # 3. Token-based match
            if not row:
                tokens = _tokenize_query(name)
                if tokens:
                    row = await _token_match(session, tokens)

            if row:
                return ArtifactInfo(
                    art_id=str(row.art_id),
                    loc_id=str(row.loc_id),
                    name_vi=row.name_vi,
                    name_en=row.name_en,
                    history_text_vi=row.history_text_vi,
                    history_text_en=row.history_text_en,
                    author=row.author,
                    year=row.year,
                )
    except Exception as exc:
        _LOGGER.warning("Database lookup by name failed: %s", exc)

    return None


# ─── Voice Pipeline Methods ─────────────────────────────────────────────────


async def get_artifact_context(query_text: str, db_field: str) -> str:
    """Async text-based artifact search for the voice pipeline."""
    allowed_fields = {"history_text_vi", "history_text_en"}
    if db_field not in allowed_fields:
        raise ValueError(f"Unsupported db_field '{db_field}'")

    normalized_query = (query_text or "").strip()
    if not normalized_query:
        return ""

    try:
        async with async_session_factory() as session:
            # 1. Direct substring match
            row = await _direct_match(session, normalized_query)

            # 2. Unaccented match
            if not row:
                unaccented = _normalize_text(normalized_query)
                row = await _direct_match(session, unaccented)

            # 3. Token-based search
            if not row:
                tokens = _tokenize_query(normalized_query)
                if tokens:
                    row = await _token_match(session, tokens)

    except Exception as exc:
        _LOGGER.warning("Database lookup failed: %s", exc)
        return "Database is temporarily unavailable."

    if not row:
        return "No matching artifact found in database."

    history_text = row.history_text_vi if db_field == "history_text_vi" else row.history_text_en
    if not history_text:
        return "No matching artifact found in database."

    name_label = f"{row.name_vi} / {row.name_en}"
    return f"{name_label}: {history_text}"


async def get_artifact_context_by_id(artifact_id: str, db_field: str) -> str:
    """Fetch artifact context by ID for the voice pipeline."""
    allowed_fields = {"history_text_vi", "history_text_en"}
    if db_field not in allowed_fields:
        raise ValueError(f"Unsupported db_field '{db_field}'")

    normalized_id = (artifact_id or "").strip()
    if not normalized_id:
        return ""

    try:
        async with async_session_factory() as session:
            result = await session.execute(
                select(Artifact).where(Artifact.art_id == int(normalized_id))
            )
            row = result.scalar_one_or_none()
    except Exception as exc:
        _LOGGER.warning("Database lookup by id failed: %s", exc)
        return "Database is temporarily unavailable."

    if not row:
        return "No matching artifact found in database."

    history_text = row.history_text_vi if db_field == "history_text_vi" else row.history_text_en
    if not history_text:
        return "No matching artifact found in database."

    name_label = f"{row.name_vi} / {row.name_en}"
    return f"{name_label}: {history_text}"


# ─── Private Helpers ─────────────────────────────────────────────────────────


async def _direct_match(session: AsyncSession, query: str):
    """Try matching query text against artifact names using LIKE."""
    # Check if any artifact name appears within the query text
    # We fetch all artifacts and check in Python for maximum compatibility
    result = await session.execute(select(Artifact))
    all_artifacts = result.scalars().all()

    # Sort by name length (longer names first for more specific matches)
    candidates = sorted(
        all_artifacts,
        key=lambda a: max(len(a.name_vi), len(a.name_en)),
        reverse=True,
    )

    query_lower = query.lower()
    for artifact in candidates:
        if artifact.name_vi.lower() in query_lower or artifact.name_en.lower() in query_lower:
            return artifact

    return None


async def _token_match(session: AsyncSession, tokens: list[str]):
    """Match by individual tokens against artifact names.
    
    Requires ALL tokens to match for a more robust result.
    """
    if not tokens:
        return None
        
    # Build conditions where each token must appear in either name_vi or name_en
    # This is an "AND" of "OR"s: (vi LIKE %t1% OR en LIKE %t1%) AND (vi LIKE %t2% OR en LIKE %t2%)
    token_conditions = []
    for token in tokens:
        token_conditions.append(
            or_(
                Artifact.name_vi.ilike(f"%{token}%"),
                Artifact.name_en.ilike(f"%{token}%")
            )
        )

    from sqlalchemy import and_
    result = await session.execute(
        select(Artifact)
        .where(and_(*token_conditions))
        .order_by(func.length(Artifact.name_vi).desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


def _normalize_text(text: str) -> str:
    """Remove diacritics and normalize whitespace."""
    normalized = unicodedata.normalize("NFD", text or "")
    stripped = "".join(
        char for char in normalized if unicodedata.category(char) != "Mn"
    )
    return " ".join(stripped.lower().split())


def _tokenize_query(text: str) -> list[str]:
    """Extract meaningful search tokens from query text."""
    normalized = _normalize_text(text)
    cleaned = re.sub(r"[^a-z0-9\s]", " ", normalized)
    tokens = [
        token
        for token in cleaned.split()
        if len(token) >= 3 and token not in _STOP_WORDS
    ]
    return tokens[:6]
