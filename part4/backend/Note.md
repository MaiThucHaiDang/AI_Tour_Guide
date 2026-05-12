# Note bàn giao - Person 4: Bilingual Voice Feature

Tài liệu này mô tả trạng thái tích hợp hiện tại của luồng **STT -> LLM -> TTS** trong backend và các đầu mối cần phối hợp với các thành viên khác trong team.

---

## 1. Trạng thái kỹ thuật hiện tại

### 1.1 Stack công nghệ

- **STT**: Groq Whisper Large v3 thông qua `GroqSTTProvider`
- **LLM**: Groq Llama 3 (llama3-70b-8192) thông qua `GroqLLMProvider`
- **TTS**: Microsoft Edge TTS thông qua `EdgeTTSProvider`
- **Luồng điều phối**: `VoiceOrchestrator` với dependency injection
- **Ngôn ngữ hỗ trợ**: `vi` (Tiếng Việt) và `en` (Tiếng Anh)

### 1.2 Pipeline luồng xử lý

```
[Audio Upload] 
    ↓ (multipart/form-data)
[VoiceOrchestrator.process_voice_request(audio_bytes, lang)]
    ↓
[LanguageManager.setup_context(lang)]  ← Chạy trước, định tuyến ngôn ngữ
    ↓
[GroqSTTProvider.transcribe(audio_bytes)] → text_query, detected_lang
    ↓
[Database lookup via db_lookup hook] → context_data
    ↓
[GroqLLMProvider.generate_response(text_query, context_data, lang)] → response_text
    ↓
[EdgeTTSProvider.synthesize(response_text, lang)] → audio bytes
    ↓
[HTTP Response: audio/mpeg]
```

### 1.3 Language Manager mapping

`VoiceOrchestrator` đang dùng `LanguageManager` để map ngôn ngữ sang field dữ liệu phù hợp:

| Language | DB Field | UI Locale | TTS Voice |
|----------|----------|-----------|-----------|
| `vi` | `history_text_vi` | `vi-VN` | `vi-VN-HoaiMyNeural` |
| `en` | `history_text_en` | `en-US` | `en-US-AriaNeural` |

---

## 2. Gửi Người 2 (API Gateway)

### 2.1 Endpoint

- **Route**: `POST /api/voice/chat`
- **Path**: `routers/voice_router.py`

### 2.2 Request Payload

```
Content-Type: multipart/form-data

Fields:
- audio (file): file âm thanh (.wav, .m4a hoặc định dạng hỗ trợ khác)
- lang (string): `vi` hoặc `en`
```

### 2.3 Response

```
Content-Type: audio/mpeg
Body: audio bytes (synthesized speech)

Error cases:
- 400: Unsupported language (lang không phải 'vi' hoặc 'en')
- 500: Configuration error (missing API keys) hoặc processing error
```

### 2.4 Yêu cầu tích hợp ở API Gateway

- ✅ Forward đúng phương thức `POST` cho endpoint này (không GET)
- ✅ Bật CORS cho luồng upload file từ frontend
- ✅ Áp dụng Rate Limiting riêng vì request có thể gọi STT/LLM/TTS (tốn resource đáng kể)
- ✅ Giữ nguyên `multipart/form-data` ở gateway layer, không biến thành JSON
- ✅ Configure timeout đủ dài (ít nhất 30 giây) vì STT/LLM có thể chậm

---

## 3. Gửi Người 5 (Database)

### 3.1 Hiện tại: Mock implementation

`VoiceOrchestrator` hiện tại vẫn dùng mock method nội bộ:

```python
def _mock_get_db_data(self, text: str, db_field: str) -> str:
    """Return dummy data in place of the real database lookup."""
    return f"Mock data for '{text}' from {db_field}."
```

### 3.2 Thay thế bằng DB thật

**Cách 1: Truyền hook qua constructor (Recommended)**

```python
# Ở router hoặc initialization point
from services.database import get_artifact_info  # function từ team 5

orchestrator = VoiceOrchestrator(
    stt=stt_provider,
    llm=llm_provider,
    tts=tts_provider,
    db_lookup=get_artifact_info  # Pass function reference
)
```

**Cách 2: Thay trực tiếp ở orchestrator nếu DB query không phải injectable**

```python
# Sửa trong voice_pipeline.py
# Thay dòng:
db_data = self._db_lookup(text_query, context["db_field"])

# Bằng:
from services.database import get_artifact_info
db_data = get_artifact_info(text_query, context["db_field"])
```

### 3.3 Chữ ký hàm cần từ team DB

```python
def get_artifact_info(query_text: str, db_field: str) -> str:
    """
    Args:
        query_text: Câu hỏi hoặc nội dung STT trả về (ví dụ: "Kể về Ngọ Môn")
        db_field: Field name đã được map từ ngôn ngữ (history_text_vi hoặc history_text_en)
    
    Returns:
        str: Mô tả của hiện vật/điểm tham quan, tối đa vài trăm từ
    """
```

---

## 4. Gửi Người 6 (Software Architect)

### 4.1 Thay đổi công nghệ so với kế hoạch ban đầu

Xin lưu ý thay đổi cho sơ đồ C4 Level 2:

**Kế hoạch ban đầu:**
- STT: Google Cloud Speech-to-Text
- LLM: Google Gemini API
- TTS: Google Cloud Text-to-Speech

**Thực tế hiện tại:**
- STT: Groq (Whisper Large v3)
- LLM: Groq (Llama 3 70B)
- TTS: Microsoft Edge TTS

### 4.2 Lý do thay đổi

- Groq có latency thấp hơn và giá thành rẻ hơn Google APIs
- Edge-TTS không cần API key, free và ổn định
- Stack hiện tại đã được kiểm thử và hoạt động ổn định

---

## 5. Testing

### 5.1 Unit Test 4: Language Accuracy (100 cases)

**File**: `tests/test_voice_features.py::test_unit_4_language_accuracy`

**Chi tiết:**
- 50 test cases tiếng Anh (index 1-50)
- 50 test cases tiếng Việt (index 1-50)
- Mục tiêu: 100% đúng ngôn ngữ, 0% lỗi trộn ngôn ngữ
- Kiểm tra: language routing, DB field mapping, response word count < 100

**Kết quả:** ✅ PASSED

### 5.2 Unit Test 5: Language Switching

**File**: `tests/test_voice_features.py::test_unit_5_language_switching`

**Chi tiết:**
- Mô phỏng 2 lượt liên tiếp: VI → EN
- Lượt 1: Nhập tiếng Việt → Dự kiến phản hồi tiếng Việt với `history_text_vi`
- Lượt 2: Nhập tiếng Anh → Dự kiến phản hồi tiếng Anh với `history_text_en`
- Kiểm tra: Language switching đúng, DB field không bị trộn lẫn

**Kết quả:** ✅ PASSED

### 5.3 Unit Test Groq LLM Provider

**File**: `tests/test_voice_features.py::test_groq_llm_provider_uses_groq_api_key`

**Chi tiết:**
- Kiểm tra Groq provider khởi tạo đúng với API key
- Mock Groq API response và verify output

**Kết quả:** ✅ PASSED

### 5.4 Chạy test

```bash
# Chạy tất cả test voice
pytest tests/test_voice_features.py -v

# Chạy test cụ thể
pytest tests/test_voice_features.py::test_unit_4_language_accuracy -v
pytest tests/test_voice_features.py::test_unit_5_language_switching -v

# Chạy với output chi tiết
pytest tests/test_voice_features.py -vv -s
```

---

## 6. Cấu trúc thư mục

```
part4/backend/
├── routers/
│   └── voice_router.py              # Endpoint POST /api/voice/chat
├── services/voice/
│   ├── interfaces.py                # Base classes: BaseSTT, BaseLLM, BaseTTS
│   ├── groq_stt.py                  # GroqSTTProvider
│   ├── groq_llm.py                  # GroqLLMProvider
│   ├── edge_tts_provider.py         # EdgeTTSProvider
│   ├── language_manager.py          # LanguageManager
│   ├── voice_pipeline.py            # VoiceOrchestrator (với db_lookup hook)
├── tests/
│   └── test_voice_features.py       # 100+ test cases
└── main.py                          # FastAPI app entrypoint
```

---

## 7. Ghi chú thêm

### 7.1 Error Handling

- **Missing API keys**: Throw `ValueError` ngay ở constructor của provider, endpoint return 500
- **Unsupported language**: LanguageManager throw `ValueError`, endpoint return 400
- **STT/LLM/TTS failure**: Catch exception và return 500 với message chi tiết

### 7.2 Design Pattern

- **Dependency Injection**: Tất cả providers được inject vào VoiceOrchestrator, dễ test và mock
- **Strategy Pattern**: Có thể thay STT/LLM/TTS provider mà không sửa orchestrator
- **Hook Pattern**: DB lookup có thể inject qua constructor hoặc override

### 7.3 Future improvements

- Auto-detect language từ `detected_lang` của STT thay vì rely on `lang` parameter
- Add language confidence score từ STT để decide khi nào override user's lang choice
- Cache LLM responses để tránh gọi API lại cho câu hỏi giống nhau
- Add streaming support cho TTS nếu audio response quá lớn

---

## 8. Checklist hoàn thành

- ✅ STT Service: Nhận audio stream, gọi Groq STT API, trả về text + language
- ✅ Language Manager: Map ngôn ngữ → DB field + UI locale + TTS voice
- ✅ LLM Orchestrator: Sinh phản hồi < 100 words bằng ngôn ngữ đúng
- ✅ TTS Service: Nhận text + lang, gọi Edge TTS API, stream audio
- ✅ Unit Test 4: 50 EN + 50 VI cases, 0% trộn ngôn ngữ
- ✅ Unit Test 5: VI → EN switching, DB field mapping đúng
- ✅ Database hook: Cho phép thay mock bằng DB thật
- ⚠️ Database integration: Chờ Người 5 cung cấp hàm `get_artifact_info()`
- ⚠️ Architecture doc: Chờ Người 6 cập nhật C4 Level 2 diagram

---

**Last Updated**: May 8, 2026  
**Status**: Ready for Integration  
**Pending**: Database service from Person 5