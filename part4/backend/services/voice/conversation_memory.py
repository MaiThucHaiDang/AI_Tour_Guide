"""In-memory conversation history for voice sessions."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import os
from threading import Lock
import time


_DEFAULT_MAX_TURNS = int(os.getenv("VOICE_MAX_TURNS", "6"))
_DEFAULT_TTL_SECONDS = int(os.getenv("VOICE_SESSION_TTL_SECONDS", "3600"))
_MAX_TURN_CHARS = int(os.getenv("VOICE_MAX_TURN_CHARS", "240"))


@dataclass
class _SessionHistory:
    turns: deque[tuple[str, str]] = field(default_factory=deque)
    updated_at: float = field(default_factory=time.time)


class ConversationMemory:
    """Store recent user/assistant turns by session id."""

    def __init__(
        self,
        max_turns: int | None = None,
        ttl_seconds: int | None = None,
        max_turn_chars: int | None = None,
    ) -> None:
        self._max_turns = max_turns or _DEFAULT_MAX_TURNS
        self._ttl_seconds = ttl_seconds or _DEFAULT_TTL_SECONDS
        self._max_turn_chars = max_turn_chars or _MAX_TURN_CHARS
        self._sessions: dict[str, _SessionHistory] = {}
        self._lock = Lock()

    def add_turn(self, session_id: str, role: str, content: str) -> None:
        if not session_id or not content:
            return

        sanitized = self._truncate(content)

        with self._lock:
            self._cleanup_locked()
            history = self._sessions.get(session_id)
            if history is None:
                history = _SessionHistory()
                self._sessions[session_id] = history
            history.turns.append((role, sanitized))
            history.updated_at = time.time()

            # Keep only the latest max_turns * 2 (user + assistant pairs)
            while len(history.turns) > self._max_turns * 2:
                history.turns.popleft()

    def format_history(self, session_id: str) -> str:
        if not session_id:
            return ""

        with self._lock:
            self._cleanup_locked()
            history = self._sessions.get(session_id)
            if history is None:
                return ""
            lines = [
                f"{self._role_label(role)}: {content}" for role, content in history.turns
            ]

        return "\n".join(lines).strip()

    def clear(self, session_id: str) -> None:
        if not session_id:
            return
        with self._lock:
            self._sessions.pop(session_id, None)

    def _cleanup_locked(self) -> None:
        now = time.time()
        stale_ids = [
            session_id
            for session_id, history in self._sessions.items()
            if now - history.updated_at > self._ttl_seconds
        ]
        for session_id in stale_ids:
            self._sessions.pop(session_id, None)

    def _truncate(self, text: str) -> str:
        trimmed = text.strip()
        if len(trimmed) <= self._max_turn_chars:
            return trimmed
        return trimmed[: self._max_turn_chars].rstrip() + "..."

    @staticmethod
    def _role_label(role: str) -> str:
        normalized = role.strip().lower()
        if normalized in {"assistant", "ai", "bot"}:
            return "Assistant"
        return "User"
