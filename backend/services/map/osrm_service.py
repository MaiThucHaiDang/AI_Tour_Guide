"""OSRM Routing Service for walking directions."""

import logging
import httpx
from typing import List, Dict, Any, Optional

_LOGGER = logging.getLogger(__name__)

# Public OSRM API endpoint for foot routing (FOSSGIS server)
OSRM_WALKING_URL = "https://routing.openstreetmap.de/routed-foot/route/v1/foot/"

class OSRMService:
    @staticmethod
    async def get_route(
        start_lat: float, 
        start_lng: float, 
        end_lat: float, 
        end_lng: float,
        lang: str = "vi"
    ) -> Dict[str, Any]:
        """Fetch walking route from OSRM."""
        coords = f"{start_lng},{start_lat};{end_lng},{end_lat}"
        url = f"{OSRM_WALKING_URL}{coords}?overview=full&geometries=geojson&steps=true"
        
        try:
            async with httpx.AsyncClient(timeout=10.0, headers={"User-Agent": "AITourGuide/1.0"}) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                
                if data.get("code") != "Ok":
                    return {"success": False, "message": "Không tìm thấy đường đi bộ."}
                
                route = data["routes"][0]
                coordinates = route["geometry"]["coordinates"]
                # OSRM returns [lng, lat], Leaflet needs [lat, lng]
                leaflet_coords = [[c[1], c[0]] for c in coordinates]
                
                # Extract simple instructions
                instructions = OSRMService._parse_steps(route.get("legs", [])[0].get("steps", []), lang)
                
                return {
                    "success": True,
                    "coordinates": leaflet_coords,
                    "instructions": instructions,
                    "distance": route.get("distance"),
                    "duration": route.get("duration")
                }
                
        except Exception as e:
            _LOGGER.error(f"OSRM routing error: {e}")
            return {"success": False, "message": "Lỗi khi kết nối với dịch vụ bản đồ."}

    @staticmethod
    def _parse_steps(steps: List[Dict], lang: str) -> List[str]:
        """Convert OSRM steps into human readable text."""
        instructions = []
        if not steps:
            return instructions
            
        for step in steps:
            name = step.get("name", "")
            distance = step.get("distance", 0.0)
            maneuver = step.get("maneuver", {}).get("type", "")
            modifier = step.get("maneuver", {}).get("modifier", "")
            
            if lang == "vi":
                instr = OSRMService._translate_step_vi(maneuver, modifier, name, distance)
            else:
                instr = OSRMService._translate_step_en(maneuver, modifier, name, distance)
                
            instructions.append(instr)
            
        return instructions

    @staticmethod
    def _translate_step_vi(maneuver: str, modifier: str, name: str, distance: float) -> str:
        """Helper to create basic Vietnamese instructions from OSRM data."""
        dist_str = f" khoảng {int(distance)} mét" if distance > 0 else ""
        if maneuver == "depart":
            road = f" theo hướng đường {name}" if name else ""
            return f"Bắt đầu di chuyển từ vị trí hiện tại{road}{dist_str}."
        if maneuver == "arrive":
            return "Bạn đã đến nơi."
            
        direction = ""
        if "left" in modifier: direction = "rẽ trái"
        elif "right" in modifier: direction = "rẽ phải"
        elif "straight" in modifier: direction = "đi thẳng"
        else: direction = "tiếp tục đi"
        
        road = f" vào đường {name}" if name else ""
        return f"Hãy {direction}{road}{dist_str}."

    @staticmethod
    def _translate_step_en(maneuver: str, modifier: str, name: str, distance: float) -> str:
        """Helper to create basic English instructions from OSRM data."""
        dist_str = f" for about {int(distance)} meters" if distance > 0 else ""
        if maneuver == "depart":
            road = f" heading along {name}" if name else ""
            return f"Start moving from your current location{road}{dist_str}."
        if maneuver == "arrive":
            return "You have arrived at your destination."
            
        direction = ""
        if "left" in modifier: direction = "turn left"
        elif "right" in modifier: direction = "turn right"
        elif "straight" in modifier: direction = "go straight"
        else: direction = "continue walking"
        
        road = f" onto {name}" if name else ""
        return f"Please {direction}{road}{dist_str}."

osrm_service = OSRMService()
