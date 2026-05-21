"""SQLAlchemy ORM model for the Pre_computed_Audio table."""

from __future__ import annotations
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class PrecomputedAudio(Base):
    __tablename__ = "precomputed_audio"

    audio_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    artifact_id: Mapped[int] = mapped_column(Integer, ForeignKey("artifacts.art_id"), nullable=False, index=True)
    question_vi: Mapped[str] = mapped_column(String(255), nullable=False)
    question_en: Mapped[str] = mapped_column(String(255), nullable=False)
    answer_vi: Mapped[str] = mapped_column(Text, nullable=False)
    answer_en: Mapped[str] = mapped_column(Text, nullable=False)
    audio_vi: Mapped[str | None] = mapped_column(String(255))
    audio_en: Mapped[str | None] = mapped_column(String(255))

    artifact = relationship("Artifact", back_populates="precomputed_audio")
