import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from fastapi import HTTPException
from pydantic import ValidationError

from schemas.rating import RatingCreateRequest
from api.routers.rating_router import (
    _rating_to_response,
    create_rating,
    list_location_ratings,
    get_location_rating_summary,
)
from models.artifact_rating import ArtifactRating

# --- RatingCreateRequest ---

def test_rating_request_bounds_1_to_5():
    # Should pass
    req = RatingCreateRequest(locationId=1, serviceRating=1, sceneryRating=5, priceRating=3, customerName="Khách")
    assert req.service_rating == 1
    assert req.scenery_rating == 5
    assert req.price_rating == 3
    
    # Should fail if < 1
    with pytest.raises(ValidationError):
        RatingCreateRequest(locationId=1, serviceRating=0, sceneryRating=5, priceRating=3)
    
    with pytest.raises(ValidationError):
        RatingCreateRequest(locationId=1, serviceRating=5, sceneryRating=0, priceRating=3)
        
    with pytest.raises(ValidationError):
        RatingCreateRequest(locationId=1, serviceRating=5, sceneryRating=5, priceRating=0)
    
    # Should fail if > 5
    with pytest.raises(ValidationError):
        RatingCreateRequest(locationId=1, serviceRating=6, sceneryRating=5, priceRating=3)
        
    with pytest.raises(ValidationError):
        RatingCreateRequest(locationId=1, serviceRating=5, sceneryRating=6, priceRating=3)
        
    with pytest.raises(ValidationError):
        RatingCreateRequest(locationId=1, serviceRating=5, sceneryRating=5, priceRating=6)

def test_rating_request_review_max_length():
    # Should pass
    RatingCreateRequest(locationId=1, review="a" * 2000)
    
    # Should fail if > 2000
    with pytest.raises(ValidationError):
        RatingCreateRequest(locationId=1, review="a" * 2001)

def test_rating_clean_name_defaults_guest():
    req1 = RatingCreateRequest(locationId=1, customerName="  ")
    assert req1.customer_name == "Khách"
    
    req2 = RatingCreateRequest(locationId=1, customerName="  Tên Của Tôi  ")
    assert req2.customer_name == "Tên Của Tôi"
    
    req3 = RatingCreateRequest(locationId=1)
    assert req3.customer_name == "Khách"
    
    req4 = RatingCreateRequest(locationId=1, customerName="")
    assert req4.customer_name == "Khách"

def test_rating_clean_name_max_length():
    # Should pass
    RatingCreateRequest(locationId=1, customerName="a" * 100)
    
    # Should fail if > 100
    with pytest.raises(ValidationError):
        RatingCreateRequest(locationId=1, customerName="a" * 101)

# --- _rating_to_response ---

def test_rating_to_response_alias_fields():
    dt = datetime.now(timezone.utc)
    rating = ArtifactRating(
        id=1, artifact_id=10, artifact_name="Hue", service_rating=5, 
        scenery_rating=4, price_rating=3, review="Great", customer_name="Alice", created_at=dt
    )
    resp = _rating_to_response(rating)
    assert resp.id == 1
    assert resp.location_id == 10
    assert resp.location_name == "Hue"
    assert resp.service_rating == 5
    assert resp.scenery_rating == 4
    assert resp.price_rating == 3
    assert resp.review == "Great"
    assert resp.customer_name == "Alice"
    assert resp.created_at == dt

def test_rating_to_response_none_review():
    dt = datetime.now(timezone.utc)
    rating = ArtifactRating(
        id=1, artifact_id=10, artifact_name="Hue", service_rating=5, 
        scenery_rating=4, price_rating=3, review=None, customer_name="Alice", created_at=dt
    )
    resp = _rating_to_response(rating)
    assert resp.review is None

# --- create_rating ---

@pytest.mark.asyncio
async def test_create_rating_404_missing_location():
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    req = RatingCreateRequest(locationId=99)
    with pytest.raises(HTTPException) as exc:
        await create_rating(req, mock_db)
    assert exc.value.status_code == 404

@pytest.mark.asyncio
async def test_create_rating_success():
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = MagicMock(name_vi="Hue Location")
    mock_db.execute.return_value = mock_result
    
    def mock_add_side_effect(obj):
        obj.id = 1
        obj.created_at = datetime.now(timezone.utc)
    mock_db.add = MagicMock(side_effect=mock_add_side_effect)
    
    req = RatingCreateRequest(locationId=1, serviceRating=5, sceneryRating=4, priceRating=3, review="Nice", customerName="Bob")
    resp = await create_rating(req, mock_db)
    
    assert resp.success is True
    assert resp.rating.location_id == 1
    assert resp.rating.location_name == "Hue Location"
    assert resp.rating.service_rating == 5
    assert resp.rating.scenery_rating == 4
    assert resp.rating.price_rating == 3
    assert resp.rating.review == "Nice"
    assert resp.rating.customer_name == "Bob"
    
    # Verify that commit was called
    mock_db.add.assert_called_once()
    mock_db.flush.assert_called_once()
    mock_db.commit.assert_called_once()

# --- list_location_ratings ---

@pytest.mark.asyncio
async def test_list_ratings_pagination_bounds():
    mock_db = AsyncMock()
    # first call is count
    mock_count = MagicMock()
    mock_count.scalar_one.return_value = 15
    
    # second call is list
    mock_list = MagicMock()
    mock_list.scalars.return_value.all.return_value = []
    
    mock_db.execute.side_effect = [mock_count, mock_list]
    
    resp = await list_location_ratings(location_id=1, page=2, per_page=10, db=mock_db)
    assert resp.total == 15
    assert len(resp.ratings) == 0

@pytest.mark.asyncio
async def test_list_ratings_success():
    mock_db = AsyncMock()
    mock_count = MagicMock()
    mock_count.scalar_one.return_value = 1
    
    dt = datetime.now(timezone.utc)
    rating = ArtifactRating(
        id=1, artifact_id=1, artifact_name="Hue", service_rating=5, 
        scenery_rating=4, price_rating=3, review="Great", customer_name="Alice", created_at=dt
    )
    
    mock_list = MagicMock()
    mock_list.scalars.return_value.all.return_value = [rating]
    
    mock_db.execute.side_effect = [mock_count, mock_list]
    
    resp = await list_location_ratings(location_id=1, page=1, per_page=10, db=mock_db)
    assert resp.total == 1
    assert len(resp.ratings) == 1
    assert resp.ratings[0].id == 1

# --- get_location_rating_summary ---

@pytest.mark.asyncio
async def test_rating_summary_404_missing_location():
    mock_db = AsyncMock()
    mock_loc = MagicMock()
    mock_loc.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_loc
    
    with pytest.raises(HTTPException) as exc:
        await get_location_rating_summary(location_id=99, db=mock_db)
    assert exc.value.status_code == 404

@pytest.mark.asyncio
async def test_rating_summary_zero_when_no_ratings():
    mock_db = AsyncMock()
    mock_loc = MagicMock()
    mock_loc.scalar_one_or_none.return_value = MagicMock(name_vi="Hue")
    
    mock_agg = MagicMock()
    # return tuple of (avg_service, avg_scenery, avg_price, count)
    mock_agg.one.return_value = (0, 0, 0, 0)
    
    mock_db.execute.side_effect = [mock_loc, mock_agg]
    
    resp = await get_location_rating_summary(location_id=1, db=mock_db)
    summary = resp.summary
    assert summary.avg_service == 0.0
    assert summary.avg_scenery == 0.0
    assert summary.avg_price == 0.0
    assert summary.avg_overall == 0.0
    assert summary.total_ratings == 0

@pytest.mark.asyncio
async def test_rating_summary_rounds_one_decimal():
    mock_db = AsyncMock()
    mock_loc = MagicMock()
    mock_loc.scalar_one_or_none.return_value = MagicMock(name_vi="Hue")
    
    mock_agg = MagicMock()
    # simulate values that need rounding
    mock_agg.one.return_value = (4.56, 3.12, 4.88, 10)
    
    mock_db.execute.side_effect = [mock_loc, mock_agg]
    
    resp = await get_location_rating_summary(location_id=1, db=mock_db)
    summary = resp.summary
    assert summary.avg_service == 4.6
    assert summary.avg_scenery == 3.1
    assert summary.avg_price == 4.9
    # overall = (4.6 + 3.1 + 4.9) / 3 = 12.6 / 3 = 4.2
    assert summary.avg_overall == 4.2
