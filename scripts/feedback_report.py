"""Print a lightweight feedback quality report.

Run from project root after migrations:
    python scripts/feedback_report.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sqlalchemy import desc, func, select

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from core.database import async_session_factory
from models.feedback_event import FeedbackEvent


async def print_feedback_report(limit: int = 10) -> None:
    async with async_session_factory() as session:
        totals = await session.execute(
            select(FeedbackEvent.rating, func.count().label("count"))
            .group_by(FeedbackEvent.rating)
            .order_by(desc("count"))
        )
        by_artifact = await session.execute(
            select(
                FeedbackEvent.artifact_id,
                FeedbackEvent.rating,
                FeedbackEvent.answer_source,
                func.count().label("count"),
            )
            .group_by(
                FeedbackEvent.artifact_id,
                FeedbackEvent.rating,
                FeedbackEvent.answer_source,
            )
            .order_by(desc("count"))
            .limit(limit)
        )
        recent_not_helpful = await session.execute(
            select(
                FeedbackEvent.created_at,
                FeedbackEvent.session_id,
                FeedbackEvent.message_id,
                FeedbackEvent.artifact_id,
                FeedbackEvent.answer_source,
                FeedbackEvent.comment,
            )
            .where(FeedbackEvent.rating == "not_helpful")
            .order_by(FeedbackEvent.created_at.desc())
            .limit(limit)
        )

    print("\nFeedback totals")
    print("---------------")
    for rating, count in totals:
        print(f"{rating}: {count}")

    print("\nTop feedback groups")
    print("-------------------")
    for artifact_id, rating, answer_source, count in by_artifact:
        artifact_label = artifact_id or "unknown_artifact"
        source_label = answer_source or "unknown_source"
        print(f"{count:>4}  {rating:<12} artifact={artifact_label:<8} source={source_label}")

    print("\nRecent not_helpful")
    print("------------------")
    for created_at, session_id, message_id, artifact_id, answer_source, comment in recent_not_helpful:
        print(
            f"{created_at} artifact={artifact_id or '-'} source={answer_source or '-'} "
            f"session={session_id or '-'} message={message_id or '-'} comment={comment or '-'}"
        )


if __name__ == "__main__":
    asyncio.run(print_feedback_report())
