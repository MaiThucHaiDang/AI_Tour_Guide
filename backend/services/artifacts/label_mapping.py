"""Vision label to artifact ID mapping.

Extracted from: src/backend/services/database.py (VISION_LABEL_MAP)
"""

from __future__ import annotations
from typing import Optional

# Mapping from AI vision labels (lowercase) to artifact IDs in the DB
# === KINH THÀNH HUẾ (ĐẠI NỘI) ===
VISION_LABEL_MAP: dict[str, str] = {
    # 1 - Cửa Hòa Bình
    "cửa hòa bình": "1",
    "cua hoa binh": "1",
    "hoa binh gate": "1",
    "gate of peace": "1",

    # 2 - Điện Kiến Trung
    "điện kiến trung": "2",
    "dien kien trung": "2",
    "kien trung palace": "2",
    "kiến trung": "2",

    # 3 - Cung Trường Sanh
    "cung trường sanh": "3",
    "cung truong sanh": "3",
    "truong sanh palace": "3",
    "palace of longevity": "3",

    # 4 - Cung Diên Thọ
    "cung diên thọ": "4",
    "cung dien tho": "4",
    "dien tho palace": "4",

    # 5 - Cửa Chương Đức
    "cửa chương đức": "5",
    "cua chuong duc": "5",
    "chuong duc gate": "5",
    "gate of manifest virtue": "5",

    # 6 - Hưng Miếu
    "hưng miếu": "6",
    "hung mieu": "6",
    "hưng tổ miếu": "6",
    "hung to temple": "6",

    # 7 - Thế Miếu
    "thế miếu": "7",
    "the mieu": "7",
    "thế tổ miếu": "7",
    "the to temple": "7",

    # 8 - Điện Thái Hòa
    "điện thái hòa": "8",
    "dien thai hoa": "8",
    "thai hoa palace": "8",
    "palace of supreme harmony": "8",

    # 9 - Nền điện Cần Chánh
    "nền điện cần chánh": "9",
    "nen dien can chanh": "9",
    "can chanh palace": "9",
    "can chanh palace foundation": "9",
    "điện cần chánh": "9",

    # 10 - Duyệt Thị Đường
    "duyệt thị đường": "10",
    "duyet thi duong": "10",
    "royal theater": "10",

    # 11 - Phủ Nội Vụ
    "phủ nội vụ": "11",
    "phu noi vu": "11",
    "ministry of the interior": "11",

    # 12 - Vườn Cơ Hạ
    "vườn cơ hạ": "12",
    "vuon co ha": "12",
    "co ha garden": "12",
    "imperial garden": "12",

    # 13 - Triệu Miếu
    "triệu miếu": "13",
    "trieu mieu": "13",
    "triệu tổ miếu": "13",
    "trieu to temple": "13",

    # 14 - Thái Miếu
    "thái miếu": "14",
    "thai mieu": "14",
    "thái tổ miếu": "14",
    "thai to temple": "14",

    # 15 - Cửa Hiển Nhơn
    "cửa hiển nhơn": "15",
    "cua hien nhon": "15",
    "hien nhon gate": "15",
    "gate of manifest benevolence": "15",

    # 16 - Điện Long An (Bảo tàng Cổ vật)
    "điện long an": "16",
    "dien long an": "16",
    "long an palace": "16",
    "bảo tàng cổ vật cung đình huế": "16",
    "bao tang co vat cung dinh hue": "16",
    "hue royal antiquities museum": "16",
    
    # 17 - Ngọ Môn
    "ngọ môn": "17",
    "ngo mon": "17",
    "ngo mon gate": "17",
    "meridian gate": "17",
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
