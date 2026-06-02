"""SQLAlchemy ORM model for the Locations table."""

from __future__ import annotations
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class Location(Base):
    __tablename__ = "locations"

    loc_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name_vi: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    gps_coordinates: Mapped[str | None] = mapped_column(String(100))
    open_hours: Mapped[str | None] = mapped_column(String(100))
    latitude: Mapped[float | None] = mapped_column(nullable=True)
    longitude: Mapped[float | None] = mapped_column(nullable=True)

    artifacts = relationship("Artifact", back_populates="location")
