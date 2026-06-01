"""SQLAlchemy ORM model for user feedback events."""

from __future__ import annotations

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class FeedbackEvent(Base):
    __tablename__ = "feedback_events"

    feedback_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str | None] = mapped_column(String(64), index=True)
    session_id: Mapped[str | None] = mapped_column(String(128), index=True)
    message_id: Mapped[str | None] = mapped_column(String(128), index=True)
    artifact_id: Mapped[str | None] = mapped_column(String(64), index=True)
    rating: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    comment: Mapped[str | None] = mapped_column(Text)
    intent: Mapped[str | None] = mapped_column(String(64))
    answer_source: Mapped[str | None] = mapped_column(String(64), index=True)
    created_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
