import asyncio
import os
import pyodbc
from typing import Optional
from models.schemas import ArtifactInfo
from dotenv import load_dotenv

load_dotenv()

# 1. Cấu hình kết nối SQL Server từ file .env
DB_CONN_STR = os.getenv(
    "DB_CONN_STR", 
    "Driver={ODBC Driver 17 for SQL Server};Server=LAPTOP-66FHV83O\SQLEXPRESS;Database=AI_Tour_Guide;Trusted_Connection=yes;"
)

# 2. CẬP NHẬT VISION_LABEL_MAP THEO ID TRONG SQL SERVER
# Ánh xạ từ nhãn nhận diện của AI (lowercase) sang art_id (INT) trong bảng Artifacts
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
    "uh1 huey": "15"
}

def fetch_artifact_sync(artifact_id: str) -> Optional[ArtifactInfo]:
    """Hàm đồng bộ thực hiện truy vấn SQL Server."""
    try:
        # Chuyển ID từ chuỗi (từ API) sang số nguyên (cho SQL)
        art_id_int = int(artifact_id)
        
        conn = pyodbc.connect(DB_CONN_STR)
        cursor = conn.cursor()
        
        # Truy vấn dữ liệu dựa trên schema trong file SQL
        query = """
            SELECT art_id, loc_id, name_vi, name_en, history_text_vi, history_text_en, author, year
            FROM Artifacts 
            WHERE art_id = ?
        """
        cursor.execute(query, art_id_int)
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return ArtifactInfo(
                art_id=str(row.art_id),
                loc_id=str(row.loc_id),
                name_vi=row.name_vi,
                name_en=row.name_en,
                history_text_vi=row.history_text_vi,
                history_text_en=row.history_text_en,
                author=row.author,
                year=row.year
            )
        return None
    except Exception as e:
        print(f"Lỗi truy vấn SQL Server: {e}")
        return None

async def get_artifact_by_id(artifact_id: str) -> Optional[ArtifactInfo]:
    """
    Lấy thông tin hiện vật thật từ SQL Server.
    Sử dụng asyncio.to_thread để không làm nghẽn hệ thống khi đợi DB.
    """
    return await asyncio.to_thread(fetch_artifact_sync, artifact_id)


def map_vision_label_to_artifact_id(raw_label: str) -> Optional[str]:
    normalized = raw_label.lower().strip()
    
    # Ưu tiên khớp hoàn toàn
    if normalized in VISION_LABEL_MAP:
        return VISION_LABEL_MAP[normalized]
    
    # Nếu không khớp hoàn toàn, tìm xem từ khóa có nằm TRONG câu trả lời của AI không
    for key, art_id in VISION_LABEL_MAP.items():
        if key in normalized: # Ví dụ: "thế miếu" nằm trong "đây là thế miếu"
            return art_id
            
    return None