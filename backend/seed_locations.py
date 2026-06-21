"""Seed the locations table with all destinations matching frontend IDs 1-17."""

import asyncio
import logging

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import async_session_factory
from models.location import Location

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DESTINATIONS = [
    {"loc_id": 17, "name_vi": "Ngọ Môn", "name_en": "Ngo Mon Gate"},
    {"loc_id": 8, "name_vi": "Điện Thái Hòa", "name_en": "Thai Hoa Palace"},
    {"loc_id": 2, "name_vi": "Điện Kiến Trung", "name_en": "Kien Trung Palace"},
    {"loc_id": 4, "name_vi": "Cung Diên Thọ", "name_en": "Dien Tho Palace"},
    {"loc_id": 7, "name_vi": "Thế Miếu", "name_en": "The Mieu Temple"},
    {"loc_id": 12, "name_vi": "Vườn Cơ Hạ", "name_en": "Co Ha Garden"},
    {"loc_id": 10, "name_vi": "Duyệt Thị Đường", "name_en": "Duyet Thi Duong Theater"},
    {"loc_id": 16, "name_vi": "Điện Long An", "name_en": "Long An Palace"},
    {"loc_id": 1, "name_vi": "Cửa Hòa Bình", "name_en": "Hoa Binh Gate"},
    {"loc_id": 3, "name_vi": "Cung Trường Sanh", "name_en": "Truong Sanh Palace"},
    {"loc_id": 5, "name_vi": "Cửa Chương Đức", "name_en": "Chuong Duc Gate"},
    {"loc_id": 6, "name_vi": "Hưng Miếu", "name_en": "Hung Mieu Temple"},
    {"loc_id": 9, "name_vi": "Nền điện Cần Chánh", "name_en": "Can Chanh Palace Foundation"},
    {"loc_id": 11, "name_vi": "Phủ Nội Vụ", "name_en": "Phu Noi Vu"},
    {"loc_id": 13, "name_vi": "Triệu Miếu", "name_en": "Trieu Mieu Temple"},
    {"loc_id": 14, "name_vi": "Thái Miếu", "name_en": "Thai Mieu Temple"},
    {"loc_id": 15, "name_vi": "Cửa Hiển Nhơn", "name_en": "Hien Nhon Gate"},
]


async def seed():
    async with async_session_factory() as session:
        for dest in DESTINATIONS:
            stmt = select(Location).where(Location.loc_id == dest["loc_id"])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                logger.info("SKIP  loc_id=%d – already exists (%s)", dest["loc_id"], existing.name_vi)
            else:
                loc = Location(
                    loc_id=dest["loc_id"],
                    name_vi=dest["name_vi"],
                    name_en=dest["name_en"],
                )
                session.add(loc)
                logger.info("ADD   loc_id=%d – %s", dest["loc_id"], dest["name_vi"])

        await session.commit()
        logger.info("Done.")


if __name__ == "__main__":
    asyncio.run(seed())
