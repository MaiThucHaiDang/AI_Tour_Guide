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
from typing import List, Optional

from sqlalchemy import select, func, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from aiocache import cached

from core.database import async_session_factory
from core.config import settings
from models.artifact import Artifact
from models.location import Location
from models.graph import ArtifactFAQ, ArtifactRelation
from schemas.vision import ArtifactInfo
from services.ai.embedding_service import EmbeddingService

_LOGGER = logging.getLogger(__name__)

# ─── Graph-Augmented Retrieval ──────────────────────────────────────────────

@cached(ttl=settings.CACHE_TTL_SECONDS, key_builder=lambda f, query: f"hybrid:{query}")
async def graph_augmented_search(query: str, top_k: int = 3) -> List[ArtifactInfo]:
    """State-of-the-Art Hybrid Search: Vector FAQ + Knowledge Graph.
    
    1. Vector Search on FAQ to find Entry Points.
    2. Graph Traversal to find related artifacts.
    3. Merge and return enriched context.
    """
    if not query:
        return []

    try:
        # Step 1: Vector Search on FAQs to get Entry Points
        query_vector = await EmbeddingService.get_embedding(query)
        
        async with async_session_factory() as session:
            # PostgreSQL <-> is Euclidean distance, <=> is Cosine distance
            stmt = select(ArtifactFAQ.artifact_id).order_by(
                ArtifactFAQ.embedding.cosine_distance(query_vector)
            ).limit(top_k)
            
            result = await session.execute(stmt)
            entry_artifact_ids = result.scalars().all()

        if not entry_artifact_ids:
            # Fallback to fuzzy search if vector finds nothing
            fuzzy_art = await find_artifact_by_name(query)
            if fuzzy_art:
                entry_artifact_ids = [int(fuzzy_art.art_id)]
            else:
                return []

        async with async_session_factory() as session:
            # Step 2: Graph Traversal (Get neighbors of entry points)
            # We want artifacts related by SAME_AUTHOR, SAME_PERIOD, or LOCATED_NEAR
            related_stmt = select(ArtifactRelation.target_artifact_id).where(
                ArtifactRelation.source_artifact_id.in_(entry_artifact_ids)
            ).limit(top_k)
            
            rel_result = await session.execute(related_stmt)
            related_ids = rel_result.scalars().all()
            
            # Combine all unique IDs
            all_ids = list(set(entry_artifact_ids) | set(related_ids))
            
            # Step 3: Fetch full Artifact Info
            final_stmt = select(Artifact).where(Artifact.art_id.in_(all_ids))
            final_result = await session.execute(final_stmt)
            rows = final_result.scalars().all()
            
            return [
                ArtifactInfo(
                    art_id=str(row.art_id),
                    loc_id=str(row.loc_id),
                    name_vi=row.name_vi,
                    name_en=row.name_en,
                    history_text_vi=row.history_text_vi,
                    history_text_en=row.history_text_en,
                    author=row.author,
                    year=row.year,
                ) for row in rows
            ]

    except Exception as exc:
        _LOGGER.error("Graph-Augmented search failed: %s", exc)
        return []

_STOP_WORDS = {
    "la", "ve", "noi", "ke", "gioi", "thieu", "cho", "toi", "ban",
    "please", "tell", "me", "about", "the", "a", "an", "this",
    "that", "is", "are",
    "hay", "duoc", "duoc", "xay", "dung", "nam", "nao", "ai",
    "o", "dau", "lich", "su", "y", "nghia", "what", "when", "where",
    "who", "built", "meaning", "history",
}


# ─── Vision Pipeline Methods ────────────────────────────────────────────────


@cached(ttl=settings.CACHE_TTL_SECONDS, key_builder=lambda f, artifact_id: f"art:{artifact_id}")
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


@cached(ttl=settings.CACHE_TTL_SECONDS, key_builder=lambda f, name, lat=None, lng=None: f"name:{name}:{lat}:{lng}")
async def find_artifact_by_name(name: str, lat: float = None, lng: float = None) -> Optional[ArtifactInfo]:
    """Robustly find an artifact by its name (VI or EN) with GPS reranking.
    
    Now uses PostgreSQL pg_trgm for fuzzy/similarity search.
    If GPS coordinates are provided, it reranks candidates by proximity.
    Also handles Location queries by returning a synthesized summary of its artifacts.
    """
    if not name:
        return None

    try:
        async with async_session_factory() as session:
            # 0. Check for Location matches first
            loc_stmt = select(Location).where(
                or_(
                    func.word_similarity(Location.name_vi, name) > 0.4,
                    func.word_similarity(Location.name_en, name) > 0.4,
                    Location.name_vi.ilike(f"%{name}%"),
                    Location.name_en.ilike(f"%{name}%")
                )
            ).order_by(
                func.word_similarity(Location.name_vi, name).desc()
            ).limit(1)
            
            loc_result = await session.execute(loc_stmt)
            best_location = loc_result.scalar_one_or_none()
            
            if best_location:
                # Synthesize virtual ArtifactInfo for Location
                art_stmt = select(Artifact).where(Artifact.loc_id == best_location.loc_id)
                art_result = await session.execute(art_stmt)
                location_artifacts = art_result.scalars().all()
                
                if location_artifacts:
                    summary_vi_parts = [f"Địa điểm {best_location.name_vi}. Các hiện vật nổi bật tại đây bao gồm:"]
                    summary_en_parts = [f"Location {best_location.name_en}. Prominent artifacts here include:"]
                    
                    for a in location_artifacts:
                        vi_sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", (a.history_text_vi or ""))]
                        en_sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", (a.history_text_en or ""))]
                        
                        vi_short = " ".join(vi_sentences[:2]) if vi_sentences else ""
                        en_short = " ".join(en_sentences[:2]) if en_sentences else ""
                        
                        summary_vi_parts.append(f"- {a.name_vi}: {vi_short}")
                        summary_en_parts.append(f"- {a.name_en}: {en_short}")
                    
                    return ArtifactInfo(
                        art_id=f"loc_{best_location.loc_id}",
                        loc_id=str(best_location.loc_id),
                        name_vi=best_location.name_vi,
                        name_en=best_location.name_en,
                        history_text_vi="\n".join(summary_vi_parts),
                        history_text_en="\n".join(summary_en_parts),
                        author="Unknown",
                        year=None,
                    )

            # 1. Fetch potential candidates using word_similarity
            # We take up to 5 candidates to allow for GPS reranking
            stmt = select(Artifact).join(Location).where(
                or_(
                    func.word_similarity(Artifact.name_vi, name) > 0.4,
                    func.word_similarity(Artifact.name_en, name) > 0.4,
                    Artifact.name_vi.ilike(f"%{name}%"),
                    Artifact.name_en.ilike(f"%{name}%")
                )
            ).order_by(
                func.word_similarity(Artifact.name_vi, name).desc()
            ).limit(5)
            
            result = await session.execute(stmt)
            rows = result.scalars().all()

            if not rows:
                # Unaccented fallback
                unaccented = _normalize_text(name)
                if unaccented != name.lower():
                    stmt = select(Artifact).join(Location).where(
                        or_(
                            func.word_similarity(Artifact.name_vi, unaccented) > 0.5,
                            func.word_similarity(Artifact.name_en, unaccented) > 0.5
                        )
                    ).order_by(func.word_similarity(Artifact.name_vi, unaccented).desc()).limit(5)
                    result = await session.execute(stmt)
                    rows = result.scalars().all()

            if not rows:
                return None

            # 2. Rerank by GPS if available
            best_row = rows[0]
            if lat is not None and lng is not None:
                min_dist = float('inf')
                for row in rows:
                    # Fetch location to get GPS
                    loc_stmt = select(Location).where(Location.loc_id == row.loc_id)
                    loc_res = await session.execute(loc_stmt)
                    location = loc_res.scalar_one_or_none()
                    
                    if location and location.gps_coordinates:
                        try:
                            # Assume center is before "|" if bounds are present
                            center_part = location.gps_coordinates.split('|')[0]
                            l_lat, l_lng = map(float, center_part.split(','))
                            dist = (l_lat - lat)**2 + (l_lng - lng)**2 # Euclidean is fine for local
                            if dist < min_dist:
                                min_dist = dist
                                best_row = row
                        except Exception:
                            continue

            return ArtifactInfo(
                art_id=str(best_row.art_id),
                loc_id=str(best_row.loc_id),
                name_vi=best_row.name_vi,
                name_en=best_row.name_en,
                history_text_vi=best_row.history_text_vi,
                history_text_en=best_row.history_text_en,
                author=best_row.author,
                year=best_row.year,
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

    # If the match is a Location, synthesize its artifacts' summaries
    if isinstance(row, Location):
        try:
            async with async_session_factory() as session:
                art_stmt = select(Artifact).where(Artifact.loc_id == row.loc_id)
                art_result = await session.execute(art_stmt)
                location_artifacts = art_result.scalars().all()
                
                if location_artifacts:
                    summary_parts = [f"Địa điểm {row.name_vi} / {row.name_en}. Các hiện vật nổi bật:"]
                    for a in location_artifacts:
                        text = a.history_text_vi if db_field == "history_text_vi" else a.history_text_en
                        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", (text or ""))]
                        short_text = " ".join(sentences[:2]) if sentences else ""
                        name = a.name_vi if db_field == "history_text_vi" else a.name_en
                        summary_parts.append(f"- {name}: {short_text}")
                    return "\n".join(summary_parts)
                else:
                    return f"Địa điểm {row.name_vi} hiện chưa có hiện vật nào trong cơ sở dữ liệu."
        except Exception as exc:
            _LOGGER.warning("Failed to fetch location artifacts for context: %s", exc)
            return "Database is temporarily unavailable."

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
    """Try matching query text against artifact/location names using SQL ILIKE."""
    query_lower = query.lower()
    normalized_query = _normalize_text(query)

    # Step 0: Check Location first
    loc_stmt = select(Location).where(
        or_(
            func.lower(Location.name_vi).contains(query_lower),
            func.lower(Location.name_en).contains(query_lower),
        )
    )
    loc_result = await session.execute(loc_stmt)
    locations = loc_result.scalars().all()
    for loc in locations:
        names = (loc.name_vi, loc.name_en)
        if any(name.lower() in query_lower for name in names) or any(query_lower in name.lower() for name in names):
            return loc

    # Step 1: SQL-filtered candidates (push work to database)
    stmt = select(Artifact).where(
        or_(
            func.lower(Artifact.name_vi).contains(query_lower),
            func.lower(Artifact.name_en).contains(query_lower),
            # Also check if an artifact name appears within the query
            func.lower(func.concat('%', query_lower, '%')).contains(func.lower(Artifact.name_vi)),
        )
    )
    result = await session.execute(stmt)
    candidates = result.scalars().all()

    # Sort by name length (longer names first for more specific matches)
    candidates = sorted(
        candidates,
        key=lambda a: max(len(a.name_vi), len(a.name_en)),
        reverse=True,
    )

    for artifact in candidates:
        names = (artifact.name_vi, artifact.name_en)
        if any(name.lower() in query_lower for name in names):
            return artifact
        if any(query_lower in name.lower() for name in names):
            return artifact

    # Step 2: Fallback — diacritic-free matching on full table (rare path)
    if normalized_query:
        fallback_result = await session.execute(select(Artifact))
        for artifact in fallback_result.scalars().all():
            names = (artifact.name_vi, artifact.name_en)
            if any(_normalize_text(name) in normalized_query for name in names):
                return artifact
            if any(normalized_query in _normalize_text(name) for name in names):
                return artifact

    return None


async def _token_match(session: AsyncSession, tokens: list[str]):
    """Score token overlap against artifact names using SQL pre-filtering."""
    if not tokens:
        return None

    # Pre-filter: only load artifacts whose names contain at least one token
    token_filters = [
        or_(
            func.lower(Artifact.name_vi).contains(token),
            func.lower(Artifact.name_en).contains(token),
        )
        for token in tokens[:5]  # Limit to avoid overly complex queries
    ]
    stmt = select(Artifact).where(or_(*token_filters))
    result = await session.execute(stmt)
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
