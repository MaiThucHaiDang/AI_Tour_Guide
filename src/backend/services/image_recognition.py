from pathlib import Path
from dotenv import load_dotenv

_BACKEND_ROOT = Path(__file__).resolve().parent.parent  # src/backend
_REPO_ROOT = _BACKEND_ROOT.parents[1]                  # project root
load_dotenv(_BACKEND_ROOT / ".env")
load_dotenv(_REPO_ROOT / ".env", override=False)
import os
import base64
import io
import logging
from PIL import Image
import google.generativeai as genai

from models.schemas import VisionResult
from services.database import map_vision_label_to_artifact_id

logger = logging.getLogger(__name__)

# Cấu hình Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-flash-latest')

async def recognize_image(image_base64: str) -> VisionResult:
    try:
        # Xử lý base64 prefix nếu có
        if "," in image_base64:
            image_base64 = image_base64.split(",", 1)[1]

        image_bytes = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_bytes))

        # Prompt ép mô hình nhận diện theo danh sách DB mình có
        prompt = """
        Đây là địa danh nào trong số các địa danh sau: Ngọ Môn, Thế Tổ Miếu, Điện Thái Hòa, Dinh Độc Lập, Bảo tàng Chứng tích Chiến tranh. 
        Chỉ trả về ĐÚNG MỘT TÊN địa danh, tuyệt đối không giải thích thêm. Nếu không phải các nơi này, trả về "KHÔNG BIẾT".
        """
        
        # Gọi Gemini
        response = await model.generate_content_async([prompt, image])
        label = response.text.strip()
        logger.info(f"Gemini Vision nhận diện: {label}")

        if "KHÔNG BIẾT" in label.upper():
            return VisionResult(recognized=False, error="UNRECOGNIZED")

        # Map tên tiếng Việt về artifact_id
        artifact_id = map_vision_label_to_artifact_id(label)
        
        if artifact_id:
            return VisionResult(
                recognized=True, 
                raw_label=label, 
                artifact_id=artifact_id, 
                confidence_score=0.9
            )
            
        return VisionResult(recognized=False, error="UNRECOGNIZED")

    except Exception as e:
        logger.error(f"Lỗi nhận diện Gemini: {e}")
        return VisionResult(recognized=False, error=str(e))