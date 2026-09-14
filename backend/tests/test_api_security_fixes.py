from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from main import app


def test_map_config_get_hides_api_key() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    with patch("api.routers.map_router.async_session_factory") as mock_db:
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        mock_db.return_value.__aenter__.return_value = mock_session
        response = client.get("/api/v1/map/config")
    assert response.status_code == 200
    data = response.json()
    assert "google_maps_api_key" in data
    assert data["google_maps_api_key"] is None


def test_map_config_post_disabled_in_production() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    with patch("core.config.settings.settings.ENVIRONMENT", "production"):
        response = client.post(
            "/api/v1/map/config",
            json={
                "map_bounds": [[16.4, 107.5], [16.5, 107.6]],
                "artifacts": []
            }
        )
    assert response.status_code == 403
    assert response.json()["detail"] == "Calibration endpoint disabled in production."


def test_health_ai_disabled_in_production() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    with patch("core.config.settings.settings.ENVIRONMENT", "production"):
        response = client.get("/api/v1/health/ai")
    assert response.status_code == 403
    assert response.json()["status"] == "disabled_in_production"


def test_payment_create_invalid_email_and_food_item() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    # Test invalid email
    response = client.post(
        "/api/v1/payment/create",
        json={
            "location": "Ngọ Môn",
            "customerName": "Test",
            "customerEmail": "invalid-email",
            "customerPhone": "0987654321",
            "adultCount": 1
        }
    )
    assert response.status_code == 422
    data = response.json()
    assert any(err["loc"][-1] == "customerEmail" for err in data["detail"])

    # Test invalid food item
    response = client.post(
        "/api/v1/payment/create",
        json={
            "location": "Ngọ Môn",
            "customerName": "Test",
            "customerEmail": "test@example.com",
            "customerPhone": "0987654321",
            "adultCount": 1,
            "items": [
                {"key": "unknown_item", "quantity": 1}
            ]
        }
    )
    assert response.status_code == 422
    data = response.json()
    assert any("Invalid food item" in err["msg"] for err in data["detail"])
