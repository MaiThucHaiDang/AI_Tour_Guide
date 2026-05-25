"""Persistent conversation history for voice and unified sessions."""

from __future__ import annotations

import logging
from core.config import settings
from core.database import async_session_factory
from models.chat_history import ChatTurn
from sqlalchemy import select, delete

_LOGGER = logging.getLogger(__name__)

class ConversationMemory:
    """Store recent user/assistant turns by session id in PostgreSQL."""

    def __init__(
        self,
        max_turns: int | None = None,
        max_turn_chars: int | None = None,
    ) -> None:
        self._max_turns = max_turns or settings.VOICE_MAX_TURNS
        self._max_turn_chars = max_turn_chars or settings.VOICE_MAX_TURN_CHARS

    async def add_turn(self, session_id: str, role: str, content: str, context_data: dict | None = None) -> None:
        if not session_id or not content:
            return
        sanitized = self._truncate(content)
        try:
            async with async_session_factory() as session:
                turn = ChatTurn(
                    session_id=session_id,
                    role=role,
                    content=sanitized,
                    context_data=context_data
                )
                session.add(turn)
                await session.commit()
        except Exception as e:
            _LOGGER.error("Failed to save chat turn for session %s: %s", session_id, e)

    async def format_history(self, session_id: str) -> str:
        if not session_id:
            return ""
        try:
            async with async_session_factory() as session:
                result = await session.execute(
                    select(ChatTurn)
                    .where(ChatTurn.session_id == session_id)
                    .order_by(ChatTurn.created_at.desc())
                    .limit(self._max_turns * 2)
                )
                turns = result.scalars().all()
                # Reverse to get chronological order
                turns = list(turns)[::-1]
                
                if not turns:
                    return ""
                
                lines = [
                    f"{self._role_label(turn.role)}: {turn.content}"
                    for turn in turns
                ]
                return "\n".join(lines).strip()
        except Exception as e:
            _LOGGER.error("Failed to fetch chat history for session %s: %s", session_id, e)
            return ""

    async def get_recent_context(self, session_id: str, limit: int = 3) -> list[ChatTurn]:
        """Fetch raw recent turns for query rewriting or logic."""
        if not session_id:
            return []
        try:
            async with async_session_factory() as session:
                result = await session.execute(
                    select(ChatTurn)
                    .where(ChatTurn.session_id == session_id)
                    .order_by(ChatTurn.created_at.desc())
                    .limit(limit)
                )
                turns = result.scalars().all()
                turns = list(turns)[::-1]
                return turns
        except Exception as e:
            _LOGGER.error("Failed to fetch recent context for session %s: %s", session_id, e)
            return []

    async def clear(self, session_id: str) -> None:
        if not session_id:
            return
        try:
            async with async_session_factory() as session:
                await session.execute(
                    delete(ChatTurn).where(ChatTurn.session_id == session_id)
                )
                await session.commit()
        except Exception as e:
            _LOGGER.error("Failed to clear chat history for session %s: %s", session_id, e)

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
