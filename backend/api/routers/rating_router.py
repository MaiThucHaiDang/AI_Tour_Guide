"""Location rating and review API router."""

from __future__ import annotations

import logging
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.observability import increment
from models.location import Location
from models.location_rating import LocationRating
from schemas.rating import (
    RatingCreateRequest,
    RatingCreateResponse,
    RatingListResponse,
    RatingResponse,
    RatingSummaryResponse,
    LocationRatingSummary,
)

router = APIRouter(prefix="/api/v1/ratings", tags=["Ratings"])
_LOGGER = logging.getLogger(__name__)


def _rating_to_response(r: LocationRating) -> RatingResponse:
    return RatingResponse(
        id=r.id,
        locationId=r.location_id,
        locationName=r.location_name,
        serviceRating=r.service_rating,
        sceneryRating=r.scenery_rating,
        priceRating=r.price_rating,
        review=r.review,
        customerName=r.customer_name,
        createdAt=r.created_at,
    )


@router.post("", response_model=RatingCreateResponse, status_code=201)
async def create_rating(
    body: RatingCreateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> RatingCreateResponse:
    """Submit a rating and review for a location."""
    stmt = select(Location).where(Location.loc_id == body.location_id)
    result = await db.execute(stmt)
    location = result.scalar_one_or_none()
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found.")

    rating = LocationRating(
        location_id=body.location_id,
        location_name=location.name_vi,
        service_rating=body.service_rating,
        scenery_rating=body.scenery_rating,
        price_rating=body.price_rating,
        review=body.review,
        customer_name=body.customer_name,
    )
    db.add(rating)
    await db.flush()
    await db.commit()

    increment("rating.created")
    _LOGGER.info(
        "Rating created for location %s (id=%d), service=%d scenery=%d price=%d",
        location.name_vi, body.location_id,
        body.service_rating, body.scenery_rating, body.price_rating,
    )

    return RatingCreateResponse(rating=_rating_to_response(rating))


@router.get("/location/{location_id}", response_model=RatingListResponse)
async def list_location_ratings(
    location_id: int,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=50, alias="perPage"),
    db: AsyncSession = Depends(get_db_session),
) -> RatingListResponse:
    """Get paginated ratings for a specific location."""
    total_result = await db.execute(
        select(func.count()).select_from(LocationRating).where(
            LocationRating.location_id == location_id
        )
    )
    total = int(total_result.scalar_one() or 0)

    stmt = (
        select(LocationRating)
        .where(LocationRating.location_id == location_id)
        .order_by(LocationRating.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    ratings = result.scalars().all()

    increment("rating.list_viewed")
    return RatingListResponse(
        ratings=[_rating_to_response(r) for r in ratings],
        total=total,
    )


@router.get("/location/{location_id}/summary", response_model=RatingSummaryResponse)
async def get_location_rating_summary(
    location_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> RatingSummaryResponse:
    """Get average rating summary for a location."""
    stmt = select(Location).where(Location.loc_id == location_id)
    result = await db.execute(stmt)
    location = result.scalar_one_or_none()
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found.")

    agg_result = await db.execute(
        select(
            func.coalesce(func.avg(LocationRating.service_rating), 0),
            func.coalesce(func.avg(LocationRating.scenery_rating), 0),
            func.coalesce(func.avg(LocationRating.price_rating), 0),
            func.count(LocationRating.id),
        ).where(LocationRating.location_id == location_id)
    )
    row = agg_result.one()
    avg_service = round(float(row[0]), 1)
    avg_scenery = round(float(row[1]), 1)
    avg_price = round(float(row[2]), 1)
    total_ratings = int(row[3])
    avg_overall = round((avg_service + avg_scenery + avg_price) / 3, 1)

    increment("rating.summary_viewed")
    return RatingSummaryResponse(
        summary=LocationRatingSummary(
            locationId=location_id,
            locationName=location.name_vi,
            avgService=avg_service,
            avgScenery=avg_scenery,
            avgPrice=avg_price,
            avgOverall=avg_overall,
            totalRatings=total_ratings,
        )
    )
