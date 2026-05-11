import pytest
from services.llm_orchestrator import generate_response
from models.schemas import ArtifactInfo
from dotenv import load_dotenv

load_dotenv()

@pytest.mark.asyncio
async def test_llm_anti_hallucination():
    """
    Unit Test 3: Kiểm thử chống Hallucination (Ảo giác AI).
    """
    # Dữ liệu giả lập từ DB
    mock_artifact = ArtifactInfo(
        art_id="ngo_mon_hue",
        loc_id="kinh_thanh_hue",
        name_vi="Ngọ Môn",
        name_en="Ngo Mon Gate",
        history_text_vi="Ngọ Môn là cổng chính phía nam của Hoàng thành Huế...",
        history_text_en="Ngo Mon Gate is the main southern entrance...",
        author="Triều Nguyễn",
        year=1833
    )

    # Câu hỏi bẫy (ngoài phạm vi dữ liệu)
    trick_question = "Kể cho tôi nghe về Tháp Eiffel ở Pháp."
    
    response = await generate_response(
        artifact_data=mock_artifact, 
        lang="vi", 
        user_question=trick_question
    )
    
    answer = response.response_text.lower()
    print(f"\n--- Phản hồi của AI cho câu hỏi bẫy ---\n{answer}\n")
    
    # AI không được phép trả lời về Tháp Eiffel
    assert "tháp eiffel" not in answer, "LỖI: AI bị ảo giác, trả lời thông tin ngoài Database!"
    
    # AI phải từ chối lịch sự
    assert "xin lỗi" in answer or "chỉ có thể" in answer, "LỖI: AI không từ chối câu hỏi ngoài phạm vi."
    
    # Kiểm tra giới hạn 100 từ
    word_count = len(answer.split())
    assert word_count < 100, f"LỖI: Câu trả lời quá dài ({word_count} từ)."