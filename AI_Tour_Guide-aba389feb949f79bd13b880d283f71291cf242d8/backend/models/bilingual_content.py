"""SQLAlchemy ORM model for the Bilingual_Content table."""

from __future__ import annotations
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class BilingualContent(Base):
    __tablename__ = "bilingual_content"

    content_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    artifact_id: Mapped[int] = mapped_column(Integer, ForeignKey("artifacts.art_id"), nullable=False, index=True)
    lang: Mapped[str] = mapped_column(String(10), nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)

    artifact = relationship("Artifact", back_populates="bilingual_content")
