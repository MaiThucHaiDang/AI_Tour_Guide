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

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import async_session_factory
from models.artifact import Artifact
from models.location import Location
from schemas.vision import ArtifactInfo

_LOGGER = logging.getLogger(__name__)

_STOP_WORDS = {
    "la", "ve", "noi", "ke", "gioi", "thieu", "cho", "toi", "ban",
    "please", "tell", "me", "about", "the", "a", "an", "this",
    "that", "is", "are",
    "hay", "duoc", "duoc", "xay", "dung", "nam", "nao", "ai",
    "o", "dau", "lich", "su", "y", "nghia", "what", "when", "where",
    "who", "built", "meaning", "history",
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


async def canonicalize_transcript_entities(text: str, lang: str = "vi") -> str:
    """Normalize STT entity spellings to known artifact/location names."""
    if not text or lang != "vi":
        return text

    try:
        async with async_session_factory() as session:
            artifacts_result = await session.execute(select(Artifact))
            locations_result = await session.execute(select(Location))
            artifacts = artifacts_result.scalars().all()
            locations = locations_result.scalars().all()
    except Exception as exc:
        _LOGGER.warning("Transcript canonicalization failed: %s", exc)
        return text

    phrases: list[str] = []
    token_terms: list[str] = []
    for artifact in artifacts:
        phrases.append(artifact.name_vi)
        token_terms.extend(_canonical_tokens(artifact.name_vi))
    for location in locations:
        phrases.append(location.name_vi)
        token_terms.extend(_canonical_tokens(location.name_vi))

    canonicalized = _replace_canonical_phrases(text, phrases)
    canonicalized = _replace_fuzzy_canonical_phrases(canonicalized, phrases)
    canonicalized = _replace_canonical_tokens(canonicalized, token_terms)
    canonicalized = _replace_fuzzy_canonical_tokens(canonicalized, token_terms)
    return canonicalized


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
    normalized_query = _normalize_text(query)
    for artifact in candidates:
        names = (artifact.name_vi, artifact.name_en)
        if any(name.lower() in query_lower for name in names):
            return artifact
        if any(_normalize_text(name) in normalized_query for name in names):
            return artifact
        if normalized_query and any(normalized_query in _normalize_text(name) for name in names):
            return artifact

    return None


async def _token_match(session: AsyncSession, tokens: list[str]):
    """Score token overlap against normalized artifact names."""
    if not tokens:
        return None

    result = await session.execute(select(Artifact))
    candidates = result.scalars().all()
    best_artifact = None
    best_score = 0.0

    for artifact in candidates:
        haystack = _normalize_text(f"{artifact.name_vi} {artifact.name_en}")
        matches = sum(1 for token in tokens if token in haystack)
        if not matches:
            continue
        score = matches / len(tokens)
        if score > best_score:
            best_score = score
            best_artifact = artifact

    if best_artifact and (best_score >= 0.5 or len(tokens) <= 2):
        return best_artifact
    return None


def _normalize_text(text: str) -> str:
    """Remove diacritics and normalize whitespace."""
    normalized = unicodedata.normalize("NFD", text or "")
    stripped = "".join(
        char for char in normalized if unicodedata.category(char) != "Mn"
    )
    return " ".join(stripped.lower().split())


def _canonical_tokens(text: str) -> list[str]:
    tokens = re.findall(r"[\wÀ-ỹ]+", text or "", flags=re.UNICODE)
    return [
        token
        for token in tokens
        if len(_normalize_text(token)) >= 3 and _normalize_text(token) not in _STOP_WORDS
    ]


def _replace_canonical_phrases(text: str, canonical_phrases: list[str]) -> str:
    result = text
    sorted_phrases = sorted(
        {phrase for phrase in canonical_phrases if phrase},
        key=lambda phrase: len(_normalize_text(phrase).split()),
        reverse=True,
    )
    for phrase in sorted_phrases:
        phrase_tokens = _normalize_text(phrase).split()
        if not phrase_tokens:
            continue
        result = _replace_token_window(result, phrase_tokens, phrase)
    return result


def _replace_fuzzy_canonical_phrases(text: str, canonical_phrases: list[str]) -> str:
    result = text
    sorted_phrases = sorted(
        {phrase for phrase in canonical_phrases if phrase},
        key=lambda phrase: len(_normalize_text(phrase).split()),
        reverse=True,
    )
    for phrase in sorted_phrases:
        phrase_tokens = _normalize_text(phrase).split()
        if len(phrase_tokens) < 2:
            continue
        result = _replace_fuzzy_token_window(result, phrase_tokens, phrase)
    return result


def _replace_token_window(text: str, normalized_phrase_tokens: list[str], replacement: str) -> str:
    token_pattern = re.compile(r"[\wÀ-ỹ]+", flags=re.UNICODE)
    matches = list(token_pattern.finditer(text))
    if not matches:
        return text

    window_size = len(normalized_phrase_tokens)
    output = text
    for start_index in range(len(matches) - window_size, -1, -1):
        window = matches[start_index:start_index + window_size]
        window_tokens = [_normalize_text(match.group(0)) for match in window]
        if window_tokens != normalized_phrase_tokens:
            continue
        start = window[0].start()
        end = window[-1].end()
        output = output[:start] + replacement + output[end:]
    return output


def _replace_fuzzy_token_window(text: str, normalized_phrase_tokens: list[str], replacement: str) -> str:
    token_pattern = re.compile(r"[\wÀ-ỹ]+", flags=re.UNICODE)
    matches = list(token_pattern.finditer(text))
    if not matches:
        return text

    window_size = len(normalized_phrase_tokens)
    output = text
    for start_index in range(len(matches) - window_size, -1, -1):
        window = matches[start_index:start_index + window_size]
        window_tokens = [_normalize_text(match.group(0)) for match in window]
        if window_tokens == normalized_phrase_tokens:
            continue
        if not _is_fuzzy_phrase_match(window_tokens, normalized_phrase_tokens):
            continue
        start = window[0].start()
        end = window[-1].end()
        output = output[:start] + replacement + output[end:]
    return output


def _replace_canonical_tokens(text: str, canonical_tokens: list[str]) -> str:
    replacements = {
        _normalize_text(token): token
        for token in canonical_tokens
        if _normalize_text(token)
    }
    if not replacements:
        return text

    token_pattern = re.compile(r"[\wÀ-ỹ]+", flags=re.UNICODE)

    def replace_match(match: re.Match) -> str:
        raw = match.group(0)
        normalized = _normalize_text(raw)
        replacement = replacements.get(normalized)
        if not replacement:
            return raw
        return replacement

    return token_pattern.sub(replace_match, text)


def _replace_fuzzy_canonical_tokens(text: str, canonical_tokens: list[str]) -> str:
    replacements = {
        _normalize_text(token): token
        for token in canonical_tokens
        if _normalize_text(token)
    }
    if not replacements:
        return text

    token_pattern = re.compile(r"[\wÀ-ỹ]+", flags=re.UNICODE)

    def replace_match(match: re.Match) -> str:
        raw = match.group(0)
        normalized = _normalize_text(raw)
        if normalized in replacements:
            return raw
        best_replacement = None
        best_score = 0.0
        for canonical_normalized, replacement in replacements.items():
            if not _is_fuzzy_token_match(normalized, canonical_normalized):
                continue
            score = _token_similarity(normalized, canonical_normalized)
            if score > best_score:
                best_score = score
                best_replacement = replacement
        return best_replacement or raw

    return token_pattern.sub(replace_match, text)


def _is_fuzzy_phrase_match(source_tokens: list[str], target_tokens: list[str]) -> bool:
    if len(source_tokens) != len(target_tokens):
        return False
    similarities = []
    for source, target in zip(source_tokens, target_tokens):
        if not _is_fuzzy_token_match(source, target):
            return False
        similarities.append(_token_similarity(source, target))
    return sum(similarities) / len(similarities) >= 0.74


def _is_fuzzy_token_match(source: str, target: str) -> bool:
    if not source or not target or source == target:
        return source == target
    if source[0] != target[0]:
        return False
    distance = _levenshtein_distance(source, target)
    max_len = max(len(source), len(target))
    if max_len <= 4:
        return distance <= 1
    return distance / max_len <= 0.25


def _token_similarity(source: str, target: str) -> float:
    max_len = max(len(source), len(target), 1)
    return 1.0 - (_levenshtein_distance(source, target) / max_len)


def _levenshtein_distance(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)

    previous = list(range(len(right) + 1))
    for left_index, left_char in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_char in enumerate(right, start=1):
            insertion = current[right_index - 1] + 1
            deletion = previous[right_index] + 1
            substitution = previous[right_index - 1] + (left_char != right_char)
            current.append(min(insertion, deletion, substitution))
        previous = current
    return previous[-1]


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
