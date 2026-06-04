import sys
from pathlib import Path
from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

load_dotenv(BACKEND_ROOT / ".env")

from fastapi.testclient import TestClient
from main import app

client = TestClient(app, raise_server_exceptions=False)

def test_plan_tour_endpoint():
    """Test generating a tour plan when starting close to Hue Citadel."""
    response = client.get(
        "/api/v1/map/plan-tour",
        params={
            "start_lat": 16.4677,
            "start_lng": 107.5780,
            "max_duration": 60,
            "max_places": 3,
            "lang": "vi"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "route" in data
    assert len(data["route"]) <= 3
    assert "coordinates" in data
    assert "instructions" in data
    assert data["is_start_far"] is False

def test_plan_tour_far_fallback():
    """Test that starting far away triggers the Ngọ Môn fallback."""
    response = client.get(
        "/api/v1/map/plan-tour",
        params={
            "start_lat": 10.8231, # Saigon latitude
            "start_lng": 106.6297, # Saigon longitude
            "max_duration": 90,
            "max_places": 4,
            "lang": "en"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["is_start_far"] is True
    # Check that it plans successfully starting from Ngọ Môn
    assert len(data["route"]) > 0

def test_next_suggestion_endpoint():
    """Test that next suggestions are generated correctly."""
    response = client.get(
        "/api/v1/map/next-suggestion",
        params={
            "current_artifact_id": 8, # Điện Thái Hòa
            "visited_ids": "1,2", # Cửa Hòa Bình, Điện Kiến Trung
            "lang": "vi"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "suggestions" in data
    suggestions = data["suggestions"]
    assert len(suggestions) <= 3
    # Visited IDs and current ID should not be in suggestions
    for sugg in suggestions:
        assert sugg["id"] not in [1, 2]
        assert sugg["id"] != 8
        assert "distance" in sugg
        assert "reason" in sugg
