"""
services/database.py
--------------------
Tầng truy cập Database.
- Hiện dùng mock data (dict) để dev độc lập trước khi hoàn thành DB.
- Schema bảng Artifacts: art_id, loc_id, name_vi, name_en,
history_text_vi, history_text_en, author, year
- Schema bảng Locations: loc_id, name_vi, name_en, gps_coordinates
"""

import asyncio
from typing import Optional
from models.schemas import ArtifactInfo

# data test
# Cấu trúc: art_id → ArtifactInfo

MOCK_ARTIFACTS: dict[str, dict] = {
    "ngo_mon_hue": {
        "art_id": "ngo_mon_hue",
        "loc_id": "kinh_thanh_hue",
        "name_vi": "Ngọ Môn",
        "name_en": "Ngo Mon Gate",
        "history_text_vi": (
            "Ngọ Môn là cổng chính phía nam của Hoàng thành Huế, được xây dựng năm 1833 "
            "dưới triều vua Minh Mạng. Đây là công trình kiến trúc tiêu biểu của triều Nguyễn, "
            "nơi diễn ra lễ đọc chiếu Thoái vị của vua Bảo Đại vào ngày 30/8/1945."
        ),
        "history_text_en": (
            "Ngo Mon Gate is the main southern entrance of the Hue Imperial City, "
            "built in 1833 under Emperor Minh Mang. It is a landmark of Nguyen dynasty architecture "
            "and the site where Emperor Bao Dai abdicated on August 30, 1945."
        ),
        "author": "Triều Nguyễn",
        "year": 1833,
    },
    "the_to_mieu_hue": {
        "art_id": "the_to_mieu_hue",
        "loc_id": "kinh_thanh_hue",
        "name_vi": "Thế Tổ Miếu",
        "name_en": "The To Mieu Temple",
        "history_text_vi": (
            "Thế Tổ Miếu hay Thái Miếu, được xây dựng năm 1804, là nơi thờ các vị vua triều Nguyễn. "
            "Công trình mang đậm phong cách kiến trúc cung đình Huế với hệ thống cột gỗ lim và mái ngói hoàng lưu ly."
        ),
        "history_text_en": (
            "The To Mieu Temple, built in 1804, is dedicated to the emperors of the Nguyen dynasty. "
            "The structure reflects classic Hue imperial architectural style with ironwood columns and yellow glazed roof tiles."
        ),
        "author": "Triều Nguyễn",
        "year": 1804,
    },
    "dien_thai_hoa_hue": {
        "art_id": "dien_thai_hoa_hue",
        "loc_id": "kinh_thanh_hue",
        "name_vi": "Điện Thái Hòa",
        "name_en": "Thai Hoa Palace",
        "history_text_vi": (
            "Điện Thái Hòa là tòa nhà quan trọng nhất trong Hoàng thành Huế, xây năm 1805, "
            "nơi vua Nguyễn tiếp kiến triều thần và tổ chức các lễ lớn. "
            "Kiến trúc 80 cột sơn son thếp vàng tạo nên vẻ tráng lệ đặc trưng."
        ),
        "history_text_en": (
            "Thai Hoa Palace is the most important building in the Hue Imperial City, built in 1805, "
            "where the Nguyen emperors held court audiences and grand ceremonies. "
            "Its 80 lacquered and gilded columns create its signature grandeur."
        ),
        "author": "Triều Nguyễn",
        "year": 1805,
    },
    "dinh_doc_lap_hcm": {
        "art_id": "dinh_doc_lap_hcm",
        "loc_id": "tp_hcm",
        "name_vi": "Dinh Độc Lập",
        "name_en": "Independence Palace",
        "history_text_vi": (
            "Dinh Độc Lập, còn gọi là Dinh Thống Nhất, được xây dựng lại năm 1962–1966 "
            "theo thiết kế của kiến trúc sư Ngô Viết Thụ. Đây là nơi đặt văn phòng Tổng thống "
            "Việt Nam Cộng hòa và là biểu tượng lịch sử của sự thống nhất đất nước ngày 30/4/1975."
        ),
        "history_text_en": (
            "Independence Palace, also known as Reunification Palace, was rebuilt between 1962 and 1966 "
            "to a design by architect Ngo Viet Thu. It served as the office of the President of South Vietnam "
            "and is a historic symbol of national reunification on April 30, 1975."
        ),
        "author": "Ngô Viết Thụ",
        "year": 1966,
    },
    "bao_tang_chung_tich_hcm": {
        "art_id": "bao_tang_chung_tich_hcm",
        "loc_id": "tp_hcm",
        "name_vi": "Bảo tàng Chứng tích Chiến tranh",
        "name_en": "War Remnants Museum",
        "history_text_vi": (
            "Bảo tàng Chứng tích Chiến tranh tại TP.HCM lưu giữ hơn 20.000 tài liệu, "
            "hiện vật và hình ảnh về cuộc chiến tranh Việt Nam. Được thành lập năm 1975, "
            "đây là một trong những bảo tàng được tham quan nhiều nhất Đông Nam Á."
        ),
        "history_text_en": (
            "The War Remnants Museum in Ho Chi Minh City houses over 20,000 documents, artifacts, "
            "and photographs about the Vietnam War. Founded in 1975, "
            "it is one of the most visited museums in Southeast Asia."
        ),
        "author": None,
        "year": 1975,
    },
}

# Map từ Google Vision label (lowercase) → art_id trong DB
# Người 2 tự mở rộng danh sách này khi thêm hiện vật mới
# Map từ AI label → art_id trong DB
VISION_LABEL_MAP: dict[str, str] = {
    "ngọ môn": "ngo_mon_hue",
    "thế tổ miếu": "the_to_mieu_hue",
    "điện thái hòa": "dien_thai_hoa_hue",
    "dinh độc lập": "dinh_doc_lap_hcm",
    "bảo tàng chứng tích chiến tranh": "bao_tang_chung_tich_hcm",
    
    "ngo mon": "ngo_mon_hue",
    "ngo mon gate": "ngo_mon_hue",
    "meridian gate hue": "ngo_mon_hue",
    "the to mieu": "the_to_mieu_hue",
    "thai mieu": "the_to_mieu_hue",
    "thai hoa palace": "dien_thai_hoa_hue",
    "dien thai hoa": "dien_thai_hoa_hue",
    "palace of supreme harmony": "dien_thai_hoa_hue",
    "independence palace": "dinh_doc_lap_hcm",
    "reunification palace": "dinh_doc_lap_hcm",
    "dinh doc lap": "dinh_doc_lap_hcm",
    "dinh thong nhat": "dinh_doc_lap_hcm",
    "war remnants museum": "bao_tang_chung_tich_hcm",
    "bao tang chung tich chien tranh": "bao_tang_chung_tich_hcm",
}


# Database Access Functions 
async def get_artifact_by_id(artifact_id: str) -> Optional[ArtifactInfo]:
    """
    Lấy thông tin hiện vật từ DB theo art_id.
    
    TODO Thay mock bằng:
        async with AsyncSession(engine) as session:
            result = await session.execute(
                select(Artifact).where(Artifact.art_id == artifact_id)
            )
            row = result.scalar_one_or_none()
            return ArtifactInfo(**row.__dict__) if row else None
    """
    await asyncio.sleep(0.01)

    data = MOCK_ARTIFACTS.get(artifact_id)
    if not data:
        return None
    return ArtifactInfo(**data)


def map_vision_label_to_artifact_id(raw_label: str) -> Optional[str]:
    """
    Map label thô từ Google Vision API → art_id trong DB.
    
    Google Vision trả về text như "Ngo Mon Gate", "Independence Palace"
    → cần chuẩn hóa lowercase và tra bảng VISION_LABEL_MAP.
    """
    normalized = raw_label.lower().strip()
    
    # Tìm exact match trước
    if normalized in VISION_LABEL_MAP:
        return VISION_LABEL_MAP[normalized]
    
    # Tìm partial match 
    for key, art_id in VISION_LABEL_MAP.items():
        if key in normalized or normalized in key:
            return art_id
    
    return None