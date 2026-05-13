from pathlib import Path
from dotenv import load_dotenv

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _BACKEND_ROOT.parents[1]
load_dotenv(_BACKEND_ROOT / ".env")
load_dotenv(_REPO_ROOT / ".env", override=False)
import os
import logging
import google.generativeai as genai

from models.schemas import ArtifactInfo, LLMResponse

logger = logging.getLogger(__name__)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

def build_system_prompt(artifact_data: ArtifactInfo, lang: str) -> str:
    artifact_name = artifact_data.name_vi if lang == "vi" else artifact_data.name_en
    history_text = artifact_data.history_text_vi if lang == "vi" else artifact_data.history_text_en
    response_lang = "tiếng Việt" if lang == "vi" else "English"
    word_limit_note = "dưới 100 từ" if lang == "vi" else "under 100 words"

    return f"""Bạn là hướng dẫn viên du lịch AI thông minh.
=== THÔNG TIN HIỆN VẬT ===
Tên: {artifact_name}
Năm xây dựng: {artifact_data.year or 'Không rõ'}
Nội dung: {history_text}
=========================
QUY TẮC:
1. CHỈ sử dụng thông tin trong khung trên. KHÔNG bịa đặt thêm.
2. Trả lời bằng {response_lang}, {word_limit_note}. Thân thiện và tự nhiên.
"""

async def generate_response(
    artifact_data: ArtifactInfo,
    lang: str = "vi",
    user_question: str = "Hãy giới thiệu ngắn gọn về hiện vật này."
) -> LLMResponse:
    
    system_prompt = build_system_prompt(artifact_data, lang)
    # Gemini ko dùng role "system" giống OpenAI, ta gộp thẳng vào prompt
    full_prompt = f"{system_prompt}\n\nCâu hỏi của khách tham quan: {user_question}"

    logger.info(f"Gọi Gemini text cho artifact: {artifact_data.art_id}")

    response = await model.generate_content_async(full_prompt)
    response_text = response.text.strip()

    return LLMResponse(
        response_text=response_text,
        token_count=0, # Gemini free API ko đếm token dễ như OpenAI nên ta mock số 0
        model_used="gemini-2.5-flash"
    )