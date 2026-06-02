"""Router for map routing and calibration config API."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any
from sqlalchemy import select, update
import json
from pathlib import Path

from services.map.osrm_service import osrm_service
from core.database import async_session_factory
from models.location import Location
from models.artifact import Artifact

router = APIRouter(
    prefix="/api/v1/map",
    tags=["map"]
)

# Persistent file backup path
CALIBRATED_FILE_PATH = Path(__file__).resolve().parents[2] / "data" / "map_calibrated.json"

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
    """Calculate the shortest walking path using OpenStreetMap (OSRM)."""
    result = await osrm_service.get_route(start_lat, start_lng, end_lat, end_lng, lang)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Routing failed."))
        
    return RouteResponse(**result)

@router.get("/config", response_model=MapConfigResponse)
async def get_map_config():
    """Fetch current map bounds and artifact coordinates."""
    async with async_session_factory() as session:
        loc_stmt = select(Location).limit(1)
        loc_res = await session.execute(loc_stmt)
        location = loc_res.scalar_one_or_none()
        
        # Default bounds fallback
        sw_lat, sw_lng = 16.46369, 107.57258
        ne_lat, ne_lng = 16.47554, 107.58376
        
        if location and location.gps_coordinates and "|" in location.gps_coordinates:
            try:
                bounds_str = location.gps_coordinates.split("|")[1]
                sw_str, ne_str = bounds_str.split(";")
                sw_lat, sw_lng = map(float, sw_str.split(","))
                ne_lat, ne_lng = map(float, ne_str.split(","))
            except Exception:
                pass
                
        art_stmt = select(Artifact).order_by(Artifact.art_id)
        art_res = await session.execute(art_stmt)
        artifacts = art_res.scalars().all()
        
        artifacts_list = []
        for art in artifacts:
            artifacts_list.append({
                "id": art.art_id,
                "name_vi": art.name_vi,
                "name_en": art.name_en,
                "lat": art.latitude or 0.0,
                "lng": art.longitude or 0.0
            })
            
        from core.config import settings
        return MapConfigResponse(
            success=True,
            map_bounds=[[sw_lat, sw_lng], [ne_lat, ne_lng]],
            artifacts=artifacts_list,
            google_maps_api_key=settings.GOOGLE_MAPS_API_KEY
        )

@router.post("/config")
async def save_map_config(data: MapConfigData):
    """Save map bounds and artifact coordinates to DB and persistent backup json file."""
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
