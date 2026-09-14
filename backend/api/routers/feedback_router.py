"""User feedback endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.observability import increment
from core.config import settings
from core.security import limiter
from models.feedback_event import FeedbackEvent
from schemas.feedback import FeedbackRequest, FeedbackResponse
    
router = APIRouter(prefix="/api/v1", tags=["Feedback"])
_LOGGER = logging.getLogger(__name__)


@router.post("/feedback", response_model=FeedbackResponse)
@limiter.limit(settings.RATE_LIMIT)
async def submit_feedback(
    request: Request,
    body: FeedbackRequest,
    db: AsyncSession = Depends(get_db_session),
) -> FeedbackResponse:
    """Persist user feedback for quality analysis and future improvements."""
    request_id = getattr(request.state, "request_id", None)
    event = FeedbackEvent(
        request_id=request_id,
        session_id=body.session_id,
        message_id=body.message_id,
        artifact_id=body.artifact_id,
        rating=body.rating,
        comment=body.comment,
        intent=body.intent,
        answer_source=body.answer_source,
    )
    db.add(event)
    try:
        await db.flush()
        await db.commit()
    except Exception:
        await db.rollback()
        _LOGGER.exception(
            "feedback persist failed request_id=%s session_id=%s message_id=%s",
            request_id,
            body.session_id,
            body.message_id,
        )
        raise HTTPException(
            status_code=503,
            detail="Unable to record feedback right now.",
        )

    increment(f"feedback.{body.rating}")
    _LOGGER.info(
        "feedback request_id=%s session_id=%s message_id=%s artifact_id=%s rating=%s feedback_id=%s",
        request_id,
        body.session_id,
        body.message_id,
        body.artifact_id,
        body.rating,
        event.feedback_id,
    )
    # Explicitly return success=True to be clear about response status
    return FeedbackResponse(success=True, feedback_id=event.feedback_id)
