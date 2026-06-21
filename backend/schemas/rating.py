"""Pydantic schemas for location ratings and reviews."""

from __future__ import annotations
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RatingCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    location_id: int = Field(alias="locationId")
    service_rating: int = Field(default=5, ge=1, le=5, alias="serviceRating")
    scenery_rating: int = Field(default=5, ge=1, le=5, alias="sceneryRating")
    price_rating: int = Field(default=5, ge=1, le=5, alias="priceRating")
    review: str | None = Field(default=None, max_length=2000)
    customer_name: str = Field(default="Khách", max_length=100, alias="customerName")

    @field_validator("customer_name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return value.strip() or "Khách"


class RatingResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    location_id: int = Field(alias="locationId")
    location_name: str = Field(alias="locationName")
    service_rating: int = Field(alias="serviceRating")
    scenery_rating: int = Field(alias="sceneryRating")
    price_rating: int = Field(alias="priceRating")
    review: str | None
    customer_name: str = Field(alias="customerName")
    created_at: datetime = Field(alias="createdAt")


class RatingListResponse(BaseModel):
    success: bool = True
    ratings: list[RatingResponse]
    total: int


class LocationRatingSummary(BaseModel):
    location_id: int = Field(alias="locationId")
    location_name: str = Field(alias="locationName")
    avg_service: float = Field(alias="avgService")
    avg_scenery: float = Field(alias="avgScenery")
    avg_price: float = Field(alias="avgPrice")
    avg_overall: float = Field(alias="avgOverall")
    total_ratings: int = Field(alias="totalRatings")


class RatingSummaryResponse(BaseModel):
    success: bool = True
    summary: LocationRatingSummary


class RatingCreateResponse(BaseModel):
    success: bool = True
    rating: RatingResponse
