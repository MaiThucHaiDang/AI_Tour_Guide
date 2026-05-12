"""SQL Server helpers for the voice feature."""

from __future__ import annotations

import logging
import os
import re
import unicodedata

import pyodbc


_LOGGER = logging.getLogger(__name__)

_STOP_WORDS = {
    "la",
    "ve",
    "noi",
    "ke",
    "gioi",
    "thieu",
    "cho",
    "toi",
    "ban",
    "please",
    "tell",
    "me",
    "about",
    "the",
    "a",
    "an",
    "this",
    "that",
    "is",
    "are",
}


def _env_bool(name: str, default: str) -> bool:
    value = os.getenv(name, default).strip().lower()
    return value in {"1", "true", "yes", "y", "on"}


def build_connection_string() -> str:
    driver = os.getenv("SQL_DRIVER", "ODBC Driver 18 for SQL Server")
    server = os.getenv("SQL_SERVER", "localhost")
    database = os.getenv("SQL_DATABASE", "AI_Tour_Guide")
    encrypt = os.getenv("SQL_ENCRYPT", "yes")
    trust_cert = os.getenv("SQL_TRUST_SERVER_CERT", "yes")
    use_trusted = _env_bool("SQL_TRUSTED_CONNECTION", "true")

    parts = [
        f"Driver={{{driver}}}",
        f"Server={server}",
        f"Database={database}",
        f"Encrypt={encrypt}",
        f"TrustServerCertificate={trust_cert}",
    ]

    if use_trusted:
        parts.append("Trusted_Connection=yes")
    else:
        username = os.getenv("SQL_USERNAME")
        password = os.getenv("SQL_PASSWORD")
        if not username or not password:
            raise ValueError(
                "SQL_USERNAME and SQL_PASSWORD are required when SQL_TRUSTED_CONNECTION=false."
            )
        parts.append(f"UID={username}")
        parts.append(f"PWD={password}")

    return ";".join(parts)


def _open_connection() -> pyodbc.Connection:
    return pyodbc.connect(build_connection_string(), timeout=5)


def get_artifact_context(query_text: str, db_field: str) -> str:
    allowed_fields = {"history_text_vi", "history_text_en"}
    if db_field not in allowed_fields:
        raise ValueError(f"Unsupported db_field '{db_field}'")

    normalized_query = (query_text or "").strip()
    if not normalized_query:
        return ""

    # 1. Try direct substring match first (most accurate)
    sql = (
        "SELECT TOP 1 name_vi, name_en, history_text_vi, history_text_en "
        "FROM Artifacts "
        "WHERE ? LIKE '%' + name_vi + '%' OR ? LIKE '%' + name_en + '%' "
        "ORDER BY LEN(name_vi) DESC, LEN(name_en) DESC"
    )

    try:
        with _open_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, normalized_query, normalized_query)
            row = cursor.fetchone()

            # 2. Try unaccented direct match
            if not row:
                unaccented_query = _normalize_text(normalized_query)
                sql_unaccent = (
                    "SELECT TOP 1 name_vi, name_en, history_text_vi, history_text_en "
                    "FROM Artifacts "
                    "WHERE ? LIKE '%' + name_vi + '%' OR ? LIKE '%' + name_en + '%' "
                    "ORDER BY LEN(name_vi) DESC, LEN(name_en) DESC"
                )
                cursor.execute(sql_unaccent, unaccented_query, unaccented_query)
                row = cursor.fetchone()

            # 3. Fallback to token-based search
            if not row:
                tokens = _tokenize_query(normalized_query)
                if tokens:
                    row = _query_by_tokens(cursor, tokens)
    except Exception as exc:
        _LOGGER.warning("Database lookup failed: %s", exc)
        return "Database is temporarily unavailable."

    if not row:
        return "No matching artifact found in database."

    name_vi, name_en, text_vi, text_en = row
    history_text = text_vi if db_field == "history_text_vi" else text_en
    if not history_text:
        return "No matching artifact found in database."

    name_label = f"{name_vi} / {name_en}"
    return f"{name_label}: {history_text}"


def get_artifact_context_by_id(artifact_id: str, db_field: str) -> str:
    allowed_fields = {"history_text_vi", "history_text_en"}
    if db_field not in allowed_fields:
        raise ValueError(f"Unsupported db_field '{db_field}'")

    normalized_id = (artifact_id or "").strip()
    if not normalized_id:
        return ""

    sql = (
        "SELECT TOP 1 name_vi, name_en, history_text_vi, history_text_en "
        "FROM Artifacts "
        "WHERE art_id = ?"
    )

    try:
        with _open_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, normalized_id)
            row = cursor.fetchone()
    except Exception as exc:
        _LOGGER.warning("Database lookup by id failed: %s", exc)
        return "Database is temporarily unavailable."

    if not row:
        return "No matching artifact found in database."

    name_vi, name_en, text_vi, text_en = row
    history_text = text_vi if db_field == "history_text_vi" else text_en
    if not history_text:
        return "No matching artifact found in database."

    name_label = f"{name_vi} / {name_en}"
    return f"{name_label}: {history_text}"


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text or "")
    stripped = "".join(
        char for char in normalized if unicodedata.category(char) != "Mn"
    )
    return " ".join(stripped.lower().split())


def _tokenize_query(text: str) -> list[str]:
    normalized = _normalize_text(text)
    cleaned = re.sub(r"[^a-z0-9\s]", " ", normalized)
    tokens = [
        token
        for token in cleaned.split()
        if len(token) >= 3 and token not in _STOP_WORDS
    ]
    return tokens[:6]


def _query_by_tokens(cursor: pyodbc.Cursor, tokens: list[str]):
    conditions = []
    params: list[str] = []

    for token in tokens:
        conditions.append("name_vi LIKE ? OR name_en LIKE ?")
        like = f"%{token}%"
        params.extend([like, like])

    sql = (
        "SELECT TOP 1 name_vi, name_en, history_text_vi, history_text_en "
        "FROM Artifacts WHERE "
        + " OR ".join(conditions)
        + " ORDER BY LEN(name_vi) DESC, LEN(name_en) DESC"
    )
    cursor.execute(sql, *params)
    return cursor.fetchone()
