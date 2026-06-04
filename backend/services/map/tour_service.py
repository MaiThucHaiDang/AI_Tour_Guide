"""Service for tour planning and next-stop recommendations."""

import math
import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy import select
from models.artifact import Artifact
from models.graph import ArtifactRelation
from core.database import async_session_factory
from services.map.osrm_service import osrm_service

_LOGGER = logging.getLogger(__name__)

# Coordinates for Ngọ Môn Gate (ID 17 / default start point)
NGO_MON_COORDS = (16.467766, 107.579146)
HUE_CENTER_LAT = 16.4695
HUE_CENTER_LNG = 107.5780
MAX_HUE_DISTANCE_DEG = 0.05 # Approx 5.5 km

class TourService:
    @staticmethod
    def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate the great-circle distance between two points in meters."""
        r = 6371000 # Earth radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        d_phi = math.radians(lat2 - lat1)
        d_lambda = math.radians(lng2 - lng1)
        
        a = (math.sin(d_phi / 2.0) ** 2 +
             math.cos(phi1) * math.cos(phi2) * (math.sin(d_lambda / 2.0) ** 2))
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return r * c

    @staticmethod
    def is_far_from_hue(lat: float, lng: float) -> bool:
        """Check if coordinates are too far from the Hue Imperial City center."""
        # simple check: if the point is more than ~5km away from the center of Hue
        dist = math.hypot(lat - HUE_CENTER_LAT, lng - HUE_CENTER_LNG)
        return dist > MAX_HUE_DISTANCE_DEG

    async def plan_tour(
        self,
        start_lat: float,
        start_lng: float,
        max_duration: int = 60, # in minutes
        max_places: int = 5,
        lang: str = "vi"
    ) -> Dict[str, Any]:
        """Generate a smart tour route using greedy search, then fetch actual OSRM paths."""
        is_vi = lang == "vi"
        
        # 1. Fallback starting point if far from Hue
        if self.is_far_from_hue(start_lat, start_lng):
            _LOGGER.info(f"User coords ({start_lat}, {start_lng}) too far from Hue. Using Ngo Mon Gate.")
            curr_lat, curr_lng = NGO_MON_COORDS
            is_start_far = True
        else:
            curr_lat, curr_lng = start_lat, start_lng
            is_start_far = False

        # 2. Fetch all artifacts from database
        async with async_session_factory() as session:
            stmt = select(Artifact)
            res = await session.execute(stmt)
            all_artifacts = res.scalars().all()
            
        if not all_artifacts:
            return {"success": False, "message": "Không tìm thấy hiện vật nào trong cơ sở dữ liệu." if is_vi else "No artifacts found in the database."}

        # Filter out artifacts without coordinates
        candidates = [a for a in all_artifacts if a.latitude is not None and a.longitude is not None]
        if not candidates:
            return {"success": False, "message": "Không có hiện vật nào có tọa độ hợp lệ." if is_vi else "No artifacts with valid coordinates."}

        # 3. Path construction (Greedy Search using Haversine)
        # Average walking speed: 1.2 m/s -> 72 m/minute
        walk_speed = 72.0 
        visit_time = 10.0 # 10 minutes per stop
        
        tour_artifacts: List[Artifact] = []
        visited_ids = set()
        
        remaining_time = float(max_duration)
        remaining_places = max_places
        
        current_coords = (curr_lat, curr_lng)
        
        while remaining_places > 0 and remaining_time > 0:
            # Find the closest unvisited artifact
            best_candidate = None
            min_dist = float('inf')
            
            for art in candidates:
                if art.art_id in visited_ids:
                    continue
                d = self.haversine_distance(current_coords[0], current_coords[1], art.latitude, art.longitude)
                if d < min_dist:
                    min_dist = d
                    best_candidate = art
                    
            if not best_candidate:
                break
                
            # Calculate time to walk and visit
            t_walk = min_dist / walk_speed
            total_cost = t_walk + visit_time
            
            # If this is the very first step, allow it even if it slightly exceeds the budget,
            # so the user always gets at least one recommendation. Otherwise, enforce strictly.
            if len(tour_artifacts) > 0 and remaining_time < total_cost:
                break
                
            tour_artifacts.append(best_candidate)
            visited_ids.add(best_candidate.art_id)
            remaining_time -= total_cost
            remaining_places -= 1
            current_coords = (best_candidate.latitude, best_candidate.longitude)

        if not tour_artifacts:
            return {
                "success": False,
                "message": "Thời gian quá ngắn để di chuyển đến bất kỳ địa điểm nào." if is_vi 
                          else "Duration is too short to reach any location."
            }

        # 4. Fetch detailed path geometry and instructions via OSRM for each leg
        combined_coords: List[List[float]] = []
        combined_instructions: List[str] = []
        total_distance = 0.0
        total_walk_seconds = 0.0
        
        # Start coordinate for OSRM queries
        leg_start = (curr_lat, curr_lng)
        
        for idx, art in enumerate(tour_artifacts):
            leg_end = (art.latitude, art.longitude)
            
            # Get route segment
            res_route = await osrm_service.get_route(
                start_lat=leg_start[0],
                start_lng=leg_start[1],
                end_lat=leg_end[0],
                end_lng=leg_end[1],
                lang=lang
            )
            
            art_name = art.name_vi if is_vi else art.name_en
            
            if res_route.get("success"):
                # OSRM coordinates
                coords = res_route["coordinates"]
                # Append coordinates, skipping the first element to avoid duplicates (except for first leg)
                if combined_coords and coords:
                    combined_coords.extend(coords[1:])
                else:
                    combined_coords.extend(coords)
                    
                # Parse OSRM steps
                steps = res_route["instructions"]
                
                # Add transition instruction if it's not the first leg
                if idx > 0:
                    prev_name = tour_artifacts[idx - 1].name_vi if is_vi else tour_artifacts[idx - 1].name_en
                    transition = (
                        f"Sau khi tham quan {prev_name}, bắt đầu chặng tiếp theo đến {art_name}." if is_vi
                        else f"After exploring {prev_name}, start the next leg to {art_name}."
                    )
                    combined_instructions.append(transition)
                    
                combined_instructions.extend(steps)
                total_distance += res_route.get("distance", 0.0)
                total_walk_seconds += res_route.get("duration", 0.0)
            else:
                # Fallback to straight line coordinate path
                if combined_coords:
                    combined_coords.append([leg_end[0], leg_end[1]])
                else:
                    combined_coords.extend([[leg_start[0], leg_start[1]], [leg_end[0], leg_end[1]]])
                    
                fallback_instr = (
                    f"Di chuyển hướng thẳng tới {art_name}." if is_vi
                    else f"Walk straight towards {art_name}."
                )
                combined_instructions.append(fallback_instr)
                # straight distance approximation
                fallback_dist = self.haversine_distance(leg_start[0], leg_start[1], leg_end[0], leg_end[1])
                total_distance += fallback_dist
                total_walk_seconds += fallback_dist / 1.2
                
            # Set the start of the next leg to be the current artifact
            leg_start = leg_end

        # Calculate final metrics
        total_walk_minutes = total_walk_seconds / 60.0
        total_visit_minutes = len(tour_artifacts) * visit_time
        final_total_duration = total_walk_minutes + total_visit_minutes

        return {
            "success": True,
            "is_start_far": is_start_far,
            "total_distance": round(total_distance, 1), # meters
            "total_duration": round(final_total_duration, 1), # minutes
            "total_walk_duration": round(total_walk_minutes, 1), # minutes
            "total_visit_duration": round(total_visit_minutes, 1), # minutes
            "coordinates": combined_coords,
            "instructions": combined_instructions,
            "route": [
                {
                    "id": a.art_id,
                    "name_vi": a.name_vi,
                    "name_en": a.name_en,
                    "lat": a.latitude,
                    "lng": a.longitude,
                    "author": a.author,
                    "year": a.year,
                    "summary_vi": a.history_text_vi[:120] + "..." if a.history_text_vi else "",
                    "summary_en": a.history_text_en[:120] + "..." if a.history_text_en else "",
                    "visit_duration": 10
                }
                for a in tour_artifacts
            ]
        }

    async def get_next_suggestion(
        self,
        current_artifact_id: int,
        visited_ids: List[int],
        lang: str = "vi"
    ) -> List[Dict[str, Any]]:
        """Get the top 3 next destination suggestions based on proximity and Knowledge Graph relations."""
        is_vi = lang == "vi"
        
        # 1. Fetch current artifact and all candidate artifacts
        async with async_session_factory() as session:
            stmt = select(Artifact)
            res = await session.execute(stmt)
            all_artifacts = res.scalars().all()
            
        if not all_artifacts:
            return []
            
        current_art = next((a for a in all_artifacts if a.art_id == current_artifact_id), None)
        if not current_art or current_art.latitude is None or current_art.longitude is None:
            return []

        # 2. Fetch all relations involving current artifact
        async with async_session_factory() as session:
            rel_stmt = select(ArtifactRelation).where(
                (ArtifactRelation.source_artifact_id == current_artifact_id) |
                (ArtifactRelation.target_artifact_id == current_artifact_id)
            )
            rel_res = await session.execute(rel_stmt)
            relations = rel_res.scalars().all()

        # Build a dictionary of relations for quick lookup
        # key: target_artifact_id, value: relationship type and weight
        relation_map = {}
        for r in relations:
            other_id = r.target_artifact_id if r.source_artifact_id == current_artifact_id else r.source_artifact_id
            # Keep the highest weight relation if multiple exist
            if other_id not in relation_map or r.weight > relation_map[other_id]["weight"]:
                relation_map[other_id] = {
                    "type": r.relation_type,
                    "weight": r.weight
                }

        # 3. Calculate scores for all unvisited candidates
        suggestions = []
        for art in all_artifacts:
            # Exclude current and already visited
            if art.art_id == current_artifact_id or art.art_id in visited_ids:
                continue
            if art.latitude is None or art.longitude is None:
                continue
                
            # Geo distance
            dist = self.haversine_distance(
                current_art.latitude, current_art.longitude,
                art.latitude, art.longitude
            )
            
            # Relation boost
            rel_info = relation_map.get(art.art_id)
            rel_type = rel_info["type"] if rel_info else None
            rel_weight = rel_info["weight"] if rel_info else 0.0
            
            # Type multiplier to boost thematic linkages
            type_multiplier = 1.0
            if rel_type == "LOCATED_NEAR":
                type_multiplier = 1.5
            elif rel_type == "HISTORICAL_LINK":
                type_multiplier = 1.2
            elif rel_type in ("SAME_AUTHOR", "SAME_PERIOD"):
                type_multiplier = 1.0
                
            score_boost = 15.0 * rel_weight * type_multiplier
            
            # Score formula: closer is better + relationship boost
            # +10 on denominator to prevent divide by zero / extreme scores at < 1m
            score = (1000.0 / (dist + 10.0)) + score_boost
            
            # Human friendly reason for suggestion
            reason = ""
            if rel_type == "SAME_AUTHOR":
                author_name = art.author or current_art.author or ""
                reason = (
                    f"Cùng tác giả/triều đại xây dựng ({author_name})" if is_vi
                    else f"Same builder/dynasty ({author_name})"
                )
            elif rel_type == "SAME_PERIOD":
                reason = (
                    "Cùng thời kỳ lịch sử triều Nguyễn" if is_vi
                    else "Same Nguyen dynasty historical period"
                )
            elif rel_type == "HISTORICAL_LINK":
                reason = (
                    "Có liên kết sự kiện lịch sử" if is_vi
                    else "Has shared historical events"
                )
            elif rel_type == "LOCATED_NEAR":
                reason = (
                    "Nằm rất gần vị trí hiện tại của bạn" if is_vi
                    else "Located very close to you"
                )
            else:
                reason = (
                    "Địa điểm tham quan lân cận" if is_vi
                    else "Nearby tour stop"
                )
                
            suggestions.append({
                "id": art.art_id,
                "name_vi": art.name_vi,
                "name_en": art.name_en,
                "lat": art.latitude,
                "lng": art.longitude,
                "distance": round(dist, 1),
                "walk_duration_min": round(dist / 72.0, 1), # minutes at 1.2m/s
                "relation_type": rel_type,
                "reason": reason,
                "score": score
            })

        # Sort by score descending and return top 3
        suggestions.sort(key=lambda x: x["score"], reverse=True)
        return suggestions[:3]

tour_service = TourService()
