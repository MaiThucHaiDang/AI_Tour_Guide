"""SQLAlchemy ORM model for artifact stop ratings and reviews."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class ArtifactRating(Base):
    __tablename__ = "artifact_ratings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    artifact_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("artifacts.art_id", ondelete="CASCADE"), nullable=False, index=True
    )
    artifact_name: Mapped[str] = mapped_column(String(255), nullable=False)
    service_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    scenery_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    price_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    review: Mapped[str | None] = mapped_column(Text, nullable=True)
    customer_name: Mapped[str] = mapped_column(String(100), nullable=False, default="Khách")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
