"""SQLAlchemy ORM model for the Artifacts table."""

from __future__ import annotations
from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class Artifact(Base):
    __tablename__ = "artifacts"
    __table_args__ = (UniqueConstraint("name_vi"),)

    art_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    loc_id: Mapped[int] = mapped_column(Integer, ForeignKey("locations.loc_id"), nullable=False)
    name_vi: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    history_text_vi: Mapped[str] = mapped_column(Text, nullable=False)
    history_text_en: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str | None] = mapped_column(String(255))
    year: Mapped[int | None] = mapped_column(Integer)

    location = relationship("Location", back_populates="artifacts")
    precomputed_audio = relationship("PrecomputedAudio", back_populates="artifact")
    bilingual_content = relationship("BilingualContent", back_populates="artifact")
