"""RAG Debug Logger — Ghi lại dữ liệu context được trích xuất cho mỗi câu hỏi.

File log nằm tại: backend/data/rag_debug_log.txt
Format mỗi entry:
    [timestamp] (source: ...)
    Câu hỏi: ...
    Data lấy từ data của bạn: ...
    ────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from datetime import datetime

_LOGGER = logging.getLogger(__name__)
_LOG_FILE = Path(__file__).resolve().parents[1] / "data" / "rag_debug_log.txt"


def log_rag_context(question: str, db_context: str, answer_source: str = "") -> None:
    """Append a debug entry: question + extracted context to the log file.

    Parameters
    ----------
    question : str
        The user's original question / prompt.
    db_context : str
        The DB_CONTEXT string that was fed to the LLM.
    answer_source : str
        Where the answer originated (e.g. 'llm', 'cache', 'template', 'db_direct').
    """
    if os.getenv("RAG_DEBUG_LOG_ENABLED", "1").strip().lower() in {
        "0",
        "false",
        "no",
        "off",
    }:
        return

    try:
        _LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = (
            f"[{timestamp}] (source: {answer_source or 'unknown'})\n"
            f"Câu hỏi: {question}\n"
            f"Data lấy từ data của bạn: {db_context or '(không có)'}\n"
            f"{'─' * 60}\n"
        )
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as exc:
        _LOGGER.warning("Failed to write RAG debug log: %s", exc)
