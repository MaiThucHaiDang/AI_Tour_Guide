"""Seed PostgreSQL database with ENRICHED Hue Imperial City data.

Run after generating enriched JSON: python scripts/seed_enriched_data.py
"""

from __future__ import annotations

import asyncio
import sys
import json
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from core.database import async_session_factory
from models.location import Location
from models.artifact import Artifact
from models.precomputed_audio import PrecomputedAudio
from models.bilingual_content import BilingualContent
from models.graph import ArtifactFAQ, ArtifactRelation, KnowledgeFact

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LOCATIONS = [
    {
        "name_vi": "Kinh thành Huế (Đại Nội)",
        "name_en": "Hue Imperial City (The Citadel)",
        "gps_coordinates": "16.4695,107.5780",
        "open_hours": "07:00 - 17:30",
        "latitude": 16.4695,
        "longitude": 107.5780
    }
]

# Baseline metadata for artifacts from seed_data.py
ARTIFACTS_METADATA = [
    {
        "name_vi": "Cửa Hòa Bình",
        "name_en": "Hoa Binh Gate (Gate of Peace)",
        "author": "Triều Nguyễn",
        "year": 1804,
        "latitude": 16.4721279,
        "longitude": 107.5762716
    },
    {
        "name_vi": "Điện Kiến Trung",
        "name_en": "Kien Trung Palace",
        "author": "Vua Khải Định",
        "year": 1921,
        "latitude": 16.4710479,
        "longitude": 107.5765559
    },
    {
        "name_vi": "Cung Trường Sanh",
        "name_en": "Truong Sanh Palace (Palace of Longevity)",
        "author": "Vua Minh Mạng",
        "year": 1821,
        "latitude": 16.469725,
        "longitude": 107.574694
    },
    {
        "name_vi": "Cung Diên Thọ",
        "name_en": "Dien Tho Palace (Palace of Longevity)",
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.4688556,
        "longitude": 107.5753417
    },
    {
        "name_vi": "Cửa Chương Đức",
        "name_en": "Chuong Duc Gate (Gate of Manifest Virtue)",
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.4673314,
        "longitude": 107.5757295
    },
    {
        "name_vi": "Hưng Miếu (Hưng Tổ Miếu)",
        "name_en": "Hung Mieu (Hung To Temple)",
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.4674263,
        "longitude": 107.5764189
    },
    {
        "name_vi": "Thế Miếu (Thế Tổ Miếu)",
        "name_en": "The Mieu (The To Temple)",
        "author": "Vua Minh Mạng",
        "year": 1821,
        "latitude": 16.4671621,
        "longitude": 107.5767333
    },
    {
        "name_vi": "Điện Thái Hòa",
        "name_en": "Thai Hoa Palace (Palace of Supreme Harmony)",
        "author": "Vua Gia Long",
        "year": 1805,
        "latitude": 16.4686747,
        "longitude": 107.578412
    },
    {
        "name_vi": "Nền điện Cần Chánh",
        "name_en": "Can Chanh Palace Foundation",
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.4695281,
        "longitude": 107.5777743
    },
    {
        "name_vi": "Duyệt Thị Đường",
        "name_en": "Duyet Thi Duong (Royal Theater)",
        "author": "Vua Minh Mạng",
        "year": 1826,
        "latitude": 16.470284,
        "longitude": 107.5785163
    },
    {
        "name_vi": "Phủ Nội Vụ",
        "name_en": "Phu Noi Vu (Ministry of the Interior)",
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.470755,
        "longitude": 107.5796368
    },
    {
        "name_vi": "Vườn Cơ Hạ",
        "name_en": "Co Ha Garden (Imperial Garden)",
        "author": "Vua Thiệu Trị",
        "year": 1847,
        "latitude": 16.4717727,
        "longitude": 107.5788666
    },
    {
        "name_vi": "Triệu Miếu (Triệu Tổ Miếu)",
        "name_en": "Trieu Mieu (Trieu To Temple)",
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.4701907,
        "longitude": 107.5801058
    },
    {
        "name_vi": "Thái Miếu (Thái Tổ Miếu)",
        "name_en": "Thai Mieu (Thai To Temple)",
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.4699109,
        "longitude": 107.5803246
    },
    {
        "name_vi": "Cửa Hiển Nhơn",
        "name_en": "Hien Nhon Gate (Gate of Manifest Benevolence)",
        "author": "Vua Gia Long",
        "year": 1804,
        "latitude": 16.4707473,
        "longitude": 107.5805514
    },
    {
        "name_vi": "Điện Long An (Bảo tàng Cổ vật Cung đình Huế)",
        "name_en": "Long An Palace (Hue Royal Antiquities Museum)",
        "author": "Vua Thiệu Trị",
        "year": 1845,
        "latitude": 16.4712819,
        "longitude": 107.5818602
    },
    {
        "name_vi": "Ngọ Môn",
        "name_en": "Ngo Mon Gate (Meridian Gate)",
        "author": "Triều Nguyễn / Vua Minh Mạng",
        "year": 1833,
        "latitude": 16.468083,
        "longitude": 107.578667
    }
]

async def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    
    from sqlalchemy import text
    
    # Load enriched artifacts JSON
    enriched_file = Path(__file__).resolve().parents[1] / "backend" / "data" / "enriched_artifacts.json"
    if not enriched_file.exists():
        logger.error(f"Enriched file {enriched_file} does not exist. Please run parse_and_enrich_data.py first.")
        return
        
    with open(enriched_file, "r", encoding="utf-8") as f:
        enriched_data = json.load(f)
        
    enriched_map = {item["name_vi"]: item for item in enriched_data}
    logger.info(f"Loaded {len(enriched_data)} enriched artifacts description.")

    async with async_session_factory() as session:
        # Clear existing data in reverse FK order
        logger.info("Clearing existing database data...")
        await session.execute(text("DELETE FROM artifact_relations"))
        await session.execute(text("UPDATE artifact_faqs SET fact_id = NULL"))
        await session.execute(text("DELETE FROM knowledge_facts"))
        await session.execute(text("DELETE FROM artifact_faqs"))
        await session.execute(text("DELETE FROM precomputed_audio"))
        await session.execute(text("DELETE FROM bilingual_content"))
        await session.execute(text("DELETE FROM artifacts"))
        await session.execute(text("DELETE FROM locations"))
        await session.execute(text("ALTER SEQUENCE locations_loc_id_seq RESTART WITH 1"))
        await session.execute(text("ALTER SEQUENCE artifacts_art_id_seq RESTART WITH 1"))
        await session.commit()

        # Check if calibrated file exists
        calibrated_file = Path(__file__).resolve().parents[1] / "backend" / "data" / "map_calibrated.json"
        seeded_bounds = None
        seeded_artifacts_coords = {}
        
        if calibrated_file.exists():
            try:
                with open(calibrated_file, "r", encoding="utf-8") as f:
                    cal_data = json.load(f)
                    seeded_bounds = cal_data.get("map_bounds")
                    for art_cfg in cal_data.get("artifacts", []):
                        seeded_artifacts_coords[art_cfg["name_vi"]] = (art_cfg["lat"], art_cfg["lng"])
                logger.info(f"Loaded calibrated coordinates and bounds from {calibrated_file}")
            except Exception as exc:
                logger.warning(f"Failed to load calibrated config from file: {exc}")

        # Seed locations
        location_objs = []
        for loc_data in LOCATIONS:
            data = loc_data.copy()
            if seeded_bounds:
                sw = seeded_bounds[0]
                ne = seeded_bounds[1]
                data["gps_coordinates"] = f"16.4695,107.5780|{sw[0]},{sw[1]};{ne[0]},{ne[1]}"
            loc = Location(**data)
            session.add(loc)
            location_objs.append(loc)
        await session.flush()
        logger.info(f"Seeded {len(LOCATIONS)} location(s)")

        hue_loc_id = location_objs[0].loc_id

        # Merge baseline metadata with enriched descriptions and Seed
        seeded_count = 0
        for art_meta in ARTIFACTS_METADATA:
            name_vi = art_meta["name_vi"]
            data = art_meta.copy()
            data["loc_id"] = hue_loc_id
            
            # Map coordinates from map_calibrated.json if available
            if name_vi in seeded_artifacts_coords:
                lat, lng = seeded_artifacts_coords[name_vi]
                data["latitude"] = lat
                data["longitude"] = lng
                
            # Fill enriched text
            if name_vi in enriched_map:
                data["history_text_vi"] = enriched_map[name_vi]["history_text_vi"]
                data["history_text_en"] = enriched_map[name_vi]["history_text_en"]
            else:
                logger.warning(f"No enriched text found for {name_vi}. Seeding with empty/fallback history text.")
                data["history_text_vi"] = "Thông tin đang được cập nhật."
                data["history_text_en"] = "Information is being updated."
                
            art = Artifact(**data)
            session.add(art)
            seeded_count += 1
            
        await session.flush()
        logger.info(f"Seeded {seeded_count} enriched artifact(s)")

        # Seed Knowledge Graph (facts and relations) from json file if available
        graph_file = Path(__file__).resolve().parents[1] / "backend" / "data" / "knowledge_graph_data.json"
        if graph_file.exists():
            try:
                with open(graph_file, "r", encoding="utf-8") as f:
                    graph_data = json.load(f)
                
                # Seed facts
                facts_list = graph_data.get("facts", [])
                for fact_data in facts_list:
                    session.add(KnowledgeFact(
                        artifact_id=fact_data["artifact_id"],
                        fact_text=fact_data["fact_text"]
                    ))
                await session.flush()
                logger.info(f"Seeded {len(facts_list)} knowledge facts from cache.")
                
                # Seed relations
                relations_list = graph_data.get("relations", [])
                for rel_data in relations_list:
                    session.add(ArtifactRelation(
                        source_artifact_id=rel_data["source_artifact_id"],
                        target_artifact_id=rel_data["target_artifact_id"],
                        relation_type=rel_data["relation_type"],
                        weight=rel_data["weight"]
                    ))
                await session.flush()
                logger.info(f"Seeded {len(relations_list)} artifact relations from cache.")
            except Exception as exc:
                logger.warning(f"Failed to seed Knowledge Graph from cache file: {exc}")

        await session.commit()
        logger.info("Database seeded successfully with ENRICHED descriptions and Knowledge Graph!")

        # Keep cache file for pre-generated intros so they do not rebuild on next backend start
        # cache_file = Path(__file__).resolve().parents[1] / "backend" / "data" / "pre_generated_intros.json"
        # if cache_file.exists():
        #     try:
        #         cache_file.unlink()
        #         logger.info("Removed pre-generated intros cache file to trigger regeneration.")
        #     except Exception as e:
        #         logger.warning(f"Could not remove cache file {cache_file}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
