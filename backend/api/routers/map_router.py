"""Router for map routing and calibration config API."""

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any
from sqlalchemy import select, update
import json
from pathlib import Path

from services.map.osrm_service import osrm_service
from services.map.routing import routing_service
from core.database import async_session_factory
from models.location import Location
from models.artifact import Artifact

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/map",
    tags=["map"]
)

# Persistent file backup path
CALIBRATED_FILE_PATH = Path(__file__).resolve().parents[2] / "data" / "map_calibrated.json"
DEFAULT_MAP_BOUNDS = [[16.46369, 107.57258], [16.47554, 107.58376]]


def _load_calibrated_config() -> dict[str, Any]:
    try:
        with open(CALIBRATED_FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {}
        return data
    except FileNotFoundError:
        return {}
    except Exception:
        logger.exception("Failed to load calibrated map config")
        return {}


def _is_valid_lat_lng(lat: Any, lng: Any, bounds: list[list[float]] | None = None) -> bool:
    try:
        lat_value = float(lat)
        lng_value = float(lng)
    except (TypeError, ValueError):
        return False

    if lat_value == 0.0 and lng_value == 0.0:
        return False
    if not (-90 <= lat_value <= 90 and -180 <= lng_value <= 180):
        return False
    if not bounds or len(bounds) != 2:
        return True

    try:
        sw, ne = bounds
        lat_min, lat_max = sorted([float(sw[0]), float(ne[0])])
        lng_min, lng_max = sorted([float(sw[1]), float(ne[1])])
    except (TypeError, ValueError, IndexError):
        return True

    padding = 0.003
    return (
        lat_min - padding <= lat_value <= lat_max + padding
        and lng_min - padding <= lng_value <= lng_max + padding
    )


def _normalize_bounds(value: Any) -> list[list[float]]:
    if isinstance(value, list) and len(value) == 2:
        try:
            sw, ne = value
            return [[float(sw[0]), float(sw[1])], [float(ne[0]), float(ne[1])]]
        except (TypeError, ValueError, IndexError):
            pass
    return DEFAULT_MAP_BOUNDS

class RouteResponse(BaseModel):
    success: bool
    message: str | None = None
    coordinates: List[List[float]] = []
    instructions: List[str] = []

class MapArtifactConfig(BaseModel):
    id: int
    lat: float
    lng: float

class MapConfigData(BaseModel):
    map_bounds: List[List[float]]
    artifacts: List[MapArtifactConfig]

class MapConfigResponse(BaseModel):
    success: bool
    map_bounds: List[List[float]]
    artifacts: List[Dict[str, Any]]
    google_maps_api_key: str | None = None

@router.get("/route", response_model=RouteResponse)
async def get_route(
    start_lat: float = Query(..., description="Latitude of starting point"),
    start_lng: float = Query(..., description="Longitude of starting point"),
    end_lat: float = Query(..., description="Latitude of destination"),
    end_lng: float = Query(..., description="Longitude of destination"),
    lang: str = Query("vi", description="Language code")
):
    """Calculate the shortest walking path using OpenStreetMap (OSRM) with local graph fallback."""
    result = await osrm_service.get_route(start_lat, start_lng, end_lat, end_lng, lang)

    if result.get("success"):
        return RouteResponse(**result)

    logger.info("OSRM failed, falling back to local graph routing.")
    fallback = routing_service.calculate_route(start_lat, start_lng, end_lat, end_lng)
    if fallback.get("success"):
        return RouteResponse(**fallback)

    raise HTTPException(status_code=400, detail=fallback.get("message", "Routing failed."))

@router.get("/config", response_model=MapConfigResponse)
async def get_map_config():
    """Fetch current map bounds and artifact coordinates."""
    calibrated = _load_calibrated_config()
    calibrated_bounds = _normalize_bounds(calibrated.get("map_bounds"))
    calibrated_artifacts = {
        int(item["id"]): item
        for item in calibrated.get("artifacts", [])
        if isinstance(item, dict) and str(item.get("id", "")).isdigit()
    }

    async with async_session_factory() as session:
        loc_stmt = select(Location).limit(1)
        loc_res = await session.execute(loc_stmt)
        location = loc_res.scalar_one_or_none()
        
        map_bounds = calibrated_bounds
        
        if location and location.gps_coordinates and "|" in location.gps_coordinates:
            try:
                bounds_str = location.gps_coordinates.split("|")[1]
                sw_str, ne_str = bounds_str.split(";")
                sw_lat, sw_lng = map(float, sw_str.split(","))
                ne_lat, ne_lng = map(float, ne_str.split(","))
                map_bounds = _normalize_bounds([[sw_lat, sw_lng], [ne_lat, ne_lng]])
            except Exception:
                pass
                
        art_stmt = select(Artifact).order_by(Artifact.art_id)
        art_res = await session.execute(art_stmt)
        artifacts = art_res.scalars().all()
        
        artifacts_list = []
        for art in artifacts:
            calibrated_artifact = calibrated_artifacts.get(int(art.art_id), {})
            lat = calibrated_artifact.get("lat", art.latitude)
            lng = calibrated_artifact.get("lng", art.longitude)
            if not _is_valid_lat_lng(lat, lng, map_bounds):
                lat = art.latitude
                lng = art.longitude
            artifacts_list.append({
                "id": art.art_id,
                "name_vi": art.name_vi or calibrated_artifact.get("name_vi", ""),
                "name_en": art.name_en or calibrated_artifact.get("name_en", ""),
                "lat": lat if _is_valid_lat_lng(lat, lng, map_bounds) else 0.0,
                "lng": lng if _is_valid_lat_lng(lat, lng, map_bounds) else 0.0
            })

        existing_ids = {int(item["id"]) for item in artifacts_list}
        for art_id, item in calibrated_artifacts.items():
            if art_id in existing_ids:
                continue
            lat = item.get("lat")
            lng = item.get("lng")
            if not _is_valid_lat_lng(lat, lng, map_bounds):
                continue
            artifacts_list.append({
                "id": art_id,
                "name_vi": item.get("name_vi", ""),
                "name_en": item.get("name_en", ""),
                "lat": lat,
                "lng": lng
            })

        from core.config import settings
        return MapConfigResponse(
            success=True,
            map_bounds=map_bounds,
            artifacts=artifacts_list,
            google_maps_api_key=None
        )

@router.post("/config")
async def save_map_config(data: MapConfigData):
    """Save map bounds and artifact coordinates to DB and persistent backup json file."""
    from core.config import settings
    if settings.ENVIRONMENT == "production":
        raise HTTPException(status_code=403, detail="Calibration endpoint disabled in production.")
    try:
        # 1. Update Database
        async with async_session_factory() as session:
            loc_stmt = select(Location).limit(1)
            loc_res = await session.execute(loc_stmt)
            location = loc_res.scalar_one_or_none()
            
            if location:
                center_coords = location.gps_coordinates.split("|")[0] if location.gps_coordinates else "16.4695,107.5780"
                sw = data.map_bounds[0]
                ne = data.map_bounds[1]
                new_gps_str = f"{center_coords}|{sw[0]},{sw[1]};{ne[0]},{ne[1]}"
                location.gps_coordinates = new_gps_str
                
            for art_cfg in data.artifacts:
                await session.execute(
                    update(Artifact)
                    .where(Artifact.art_id == art_cfg.id)
                    .values(latitude=art_cfg.lat, longitude=art_cfg.lng)
                )
            
            await session.commit()
            
        # 2. Update Backup Config File
        CALIBRATED_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        async with async_session_factory() as session:
            art_stmt = select(Artifact).order_by(Artifact.art_id)
            art_res = await session.execute(art_stmt)
            db_artifacts = art_res.scalars().all()
            
            backup_artifacts = []
            for art in db_artifacts:
                backup_artifacts.append({
                    "id": art.art_id,
                    "name_vi": art.name_vi,
                    "name_en": art.name_en,
                    "lat": art.latitude,
                    "lng": art.longitude
                })
                
        backup_data = {
            "map_bounds": data.map_bounds,
            "artifacts": backup_artifacts
        }
        
        with open(CALIBRATED_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
        return {"success": True, "message": "Map configuration saved successfully."}
        
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("Failed to save map config")
        raise HTTPException(status_code=500, detail=f"Failed to save configuration: {str(e)}")

@router.get("/plan-tour")
async def plan_tour(
    start_lat: float = Query(..., description="Latitude of starting point"),
    start_lng: float = Query(..., description="Longitude of starting point"),
    max_duration: int = Query(60, description="Maximum duration in minutes"),
    max_places: int = Query(5, description="Maximum number of places"),
    lang: str = Query("vi", description="Language code")
):
    """Generate a tour itinerary limited by time and number of locations."""
    try:
        from services.map.tour_service import tour_service
        result = await tour_service.plan_tour(
            start_lat=start_lat,
            start_lng=start_lng,
            max_duration=max_duration,
            max_places=max_places,
            lang=lang
        )
        return result
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("Failed to plan tour")
        raise HTTPException(status_code=500, detail=f"Failed to generate tour plan: {str(e)}")

@router.get("/next-suggestion")
async def get_next_suggestion(
    current_artifact_id: int = Query(..., description="ID of the current artifact"),
    visited_ids: str = Query("", description="Comma-separated list of visited artifact IDs"),
    lang: str = Query("vi", description="Language code")
):
    """Retrieve recommended next destinations."""
    try:
        from services.map.tour_service import tour_service
        # Parse visited_ids string to List[int]
        parsed_visited_ids = []
        if visited_ids:
            try:
                parsed_visited_ids = [int(x.strip()) for x in visited_ids.split(",") if x.strip()]
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid visited_ids format. Must be comma-separated integers.")
                
        result = await tour_service.get_next_suggestion(
            current_artifact_id=current_artifact_id,
            visited_ids=parsed_visited_ids,
            lang=lang
        )
        return {"success": True, "suggestions": result}
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("Failed to get next suggestion")
        raise HTTPException(status_code=500, detail=f"Failed to get next suggestions: {str(e)}")

