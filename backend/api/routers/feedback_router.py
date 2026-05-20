"""User feedback endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request

from core.observability import increment
from schemas.feedback import FeedbackRequest, FeedbackResponse

router = APIRouter(prefix="/api/v1", tags=["Feedback"])
_LOGGER = logging.getLogger(__name__)


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: Request, body: FeedbackRequest) -> FeedbackResponse:
    """Record lightweight feedback for improving answer quality."""
    request_id = getattr(request.state, "request_id", None)
    increment(f"feedback.{body.rating}")
    _LOGGER.info(
        "feedback request_id=%s session_id=%s message_id=%s artifact_id=%s rating=%s",
        request_id,
        body.session_id,
        body.message_id,
        body.artifact_id,
        body.rating,
    )
    return FeedbackResponse()
