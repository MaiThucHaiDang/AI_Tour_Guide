"""Schemas for user feedback on guide answers."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    session_id: str | None = None
    message_id: str | None = None
    artifact_id: str | None = None
    rating: str = Field(pattern="^(helpful|not_helpful)$")
    comment: str | None = Field(default=None, max_length=500)


class FeedbackResponse(BaseModel):
    success: bool = True
