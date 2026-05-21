"""Vision label to artifact ID mapping.

Extracted from: src/backend/services/database.py (VISION_LABEL_MAP)
"""

from __future__ import annotations
from typing import Optional

# Mapping from AI vision labels (lowercase) to artifact IDs in the DB
VISION_LABEL_MAP: dict[str, str] = {
    # Kinh thành Huế (loc_id = 1)
    "ngọ môn": "1",
    "ngo mon": "1",
    "ngo mon gate": "1",
    "noon gate": "1",

    "điện thái hòa": "2",
    "dien thai hoa": "2",
    "thai hoa palace": "2",

    "tử cấm thành": "3",
    "tu cam thanh": "3",
    "forbidden purple city": "3",

    "cửu đỉnh": "4",
    "cuu dinh": "4",
    "the nine dynastic urns": "4",
    "nine dynastic urns": "4",

    "thế miếu": "5",
    "thế tổ miếu": "5",
    "the mieu": "5",
    "the mieu temple": "5",

    # === DINH ĐỘC LẬP (loc_id = 2) ===
    "dinh độc lập": "6",
    "dinh doc lap": "6",
    "independence palace": "6",

    "hầm chỉ huy": "7",
    "ham chi huy": "7",
    "command bunker": "7",

    "phòng khánh tiết": "8",
    "phong khanh tiet": "8",
    "state banquet hall": "8",

    "xe tăng 843": "9",
    "xe tang 843": "9",
    "tank 843": "9",

    "sân thượng trực thăng": "10",
    "san thuong truc thang": "10",
    "helicopter landing roof": "10",

    # === BẢO TÀNG CHỨNG TÍCH CHIẾN TRANH (loc_id = 3) ===
    "máy bay f-5e tiger": "11",
    "may bay f5e": "11",
    "f-5e tiger aircraft": "11",
    "f5e tiger": "11",

    "xe tăng m48 patton": "12",
    "xe tang m48": "12",
    "m48 patton tank": "12",
    "m48 patton": "12",

    "chuồng cọp côn đảo": "13",
    "chuong cop con dao": "13",
    "con dao tiger cages": "13",
    "tiger cages": "13",

    "bộ sưu tập ảnh chiến tranh": "14",
    "bo suu tap anh chien tranh": "14",
    "war photography collection": "14",
    "war photography": "14",

    "trực thăng uh-1 huey": "15",
    "truc thang uh1": "15",
    "uh-1 huey helicopter": "15",
    "uh1 huey": "15",
}


def map_vision_label_to_artifact_id(raw_label: str) -> Optional[str]:
    """Map a raw vision label to an artifact ID.

    Tries exact match first, then substring match.
    """
    normalized = raw_label.lower().strip()

    # Exact match
    if normalized in VISION_LABEL_MAP:
        return VISION_LABEL_MAP[normalized]

    # Substring match
    for key, art_id in VISION_LABEL_MAP.items():
        if key in normalized:
            return art_id

    return None
