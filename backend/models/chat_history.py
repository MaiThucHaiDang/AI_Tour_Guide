"""Models for persistent chat history and session tracking."""

from __future__ import annotations
from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base

from sqlalchemy.sql import func

class ChatTurn(Base):
    """Stores individual conversational turns for contextual memory."""
    __tablename__ = "chat_turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False) # 'user' or 'assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Store context state such as current artifact ID discussed in this turn
    context_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
