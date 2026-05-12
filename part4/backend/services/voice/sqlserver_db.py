"""SQL Server helpers for the voice feature."""

from __future__ import annotations

import logging
import os

import pyodbc


_LOGGER = logging.getLogger(__name__)


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
