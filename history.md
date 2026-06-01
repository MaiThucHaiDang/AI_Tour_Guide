## USER 🧑‍💻

<session_context>
This is the Gemini CLI. We are setting up the context for our chat.
Today's date is Sunday, May 31, 2026 (formatted according to the user's locale).
My operating system is: win32
The project's temporary directory is: C:\Users\ADMIN\.gemini\tmp\ai-tour-guide-2
- **Workspace Directories:**
  - C:\TranNhatTruong_2026\HK1\Tu duy tinh toan\Project\main\AI_Tour_Guide
- **Directory Structure:**

Showing up to 200 items (files + folders). Folders or files indicated with ... contain more items not shown, were ignored, or the display limit (200 items) was reached.

C:\TranNhatTruong_2026\HK1\Tu duy tinh toan\Project\main\AI_Tour_Guide\
├───.dockerignore
├───.env.example
├───.gitignore
├───alembic.ini
├───guideRun.md
├───parsed_data.json
├───README.md
├───report.md
├───reportbackendanddata.md
├───.git\...
├───.venv\...
├───backend\
│   ├───main.py
│   ├───requirements.txt
│   ├───__pycache__\...
│   ├───api\
│   │   ├───__init__.py
│   │   ├───__pycache__\...
│   │   ├───routers\
│   │   │   ├───__init__.py
│   │   │   ├───chat_router.py
│   │   │   ├───feedback_router.py
│   │   │   ├───health_router.py
│   │   │   ├───vision_router.py
│   │   │   ├───voice_router.py
│   │   │   └───__pycache__\...
│   │   └───v1\
│   │       └───__init__.py
│   ├───core\
│   │   ├───__init__.py
│   │   ├───cache.py
│   │   ├───dependencies.py
│   │   ├───__pycache__\...
│   │   ├───config\
│   │   │   ├───__init__.py
│   │   │   ├───settings.py
│   │   │   └───__pycache__\...
│   │   ├───database\
│   │   │   ├───__init__.py
│   │   │   ├───session.py
│   │   │   └───__pycache__\...
│   │   ├───logging\
│   │   │   ├───__init__.py
│   │   │   ├───logger.py
│   │   │   └───__pycache__\...
│   │   ├───observability\
│   │   │   ├───__init__.py
│   │   │   ├───metrics.py
│   │   │   └───__pycache__\...
│   │   └───security\
│   │       ├───__init__.py
│   │       ├───rate_limit.py
│   │       └───__pycache__\...
│   ├───middleware\
│   │   ├───__init__.py
│   │   ├───error_handler.py
│   │   └───__pycache__\...
│   ├───models\
│   │   ├───__init__.py
│   │   ├───artifact.py
│   │   ├───bilingual_content.py
│   │   ├───chat_history.py
│   │   ├───feedback_event.py
│   │   ├───graph.py
│   │   ├───location.py
│   │   ├───precomputed_audio.py
│   │   └───__pycache__\...
│   ├───orchestrators\
│   │   ├───__init__.py
│   │   ├───unified_orchestrator.py
│   │   ├───voice_orchestrator.py
│   │   └───__pycache__\...
│   ├───repositories\
│   │   ├───__init__.py
│   │   ├───artifact_repository.py
│   │   └───__pycache__\...
│   ├───schemas\
│   │   ├───__init__.py
│   │   ├───feedback.py
│   │   ├───vision.py
│   │   ├───voice.py
│   │   └───__pycache__\...
│   ├───services\
│   │   ├───__init__.py
│   │   ├───__pycache__\...
│   │   ├───ai\
│   │   │   ├───__init__.py
│   │   │   ├───embedding_service.py
│   │   │   ├───interfaces.py
│   │   │   └───__pycache__\...
│   │   ├───artifacts\
│   │   │   ├───__init__.py
│   │   │   ├───label_mapping.py
│   │   │   └───__pycache__\...
│   │   ├───llm\
│   │   │   ├───__init__.py
│   │   │   ├───gemini_llm.py
│   │   │   ├───groq_llm.py
│   │   │   ├───llm_fallback.py
│   │   │   └───__pycache__\...
│   │   ├───memory\
│   │   │   ├───__init__.py
│   │   │   ├───conversation_memory.py
│   │   │   └───__pycache__\...
│   │   ├───vision\
│   │   │   ├───__init__.py
│   │   │   ├───image_recognition.py
│   │   │   ├───response_generator.py
│   │   │   └───__pycache__\...
│   │   └───voice\
│   │       ├───__init__.py
│   │       ├───edge_tts_provider.py
│   │       ├───groq_stt.py
│   │       └───__pycache__\...
│   ├───tests\
│   │   ├───__init__.py
│   │   ├───test_api_contract.py
│   │   ├───test_unified_chatbot.py
│   │   └───test_voice_features.py
│   └───utils\
│       ├───__init__.py
│       ├───ai_utils.py
│       ├───language_manager.py
│       ├───prompt_templates.py
│       ├───request_validation.py
│       └───__pycache__\...
├───docker\
│   ├───docker-compose.yml
│   └───Dockerfile
├───docs\
│   ├───architecture.md
│   ├───demo_script.md
│   └───troubleshooting.md
├───frontend\
│   ├───eslint.config.js
│   ├───index.html
│   ├───package-lock.json
│   ├───package.json
│   ├───vite.config.js
│   ├───node_modules\...
│   └───src\
│       ├───App.jsx
│       ├───index.css
│       ├───main.jsx
│       ├───components\
│       │   ├───CameraScanner.jsx
│       │   ├───ErrorPopup.jsx
│       │   ├───HomeScreen.jsx
│       │   ├───ResultView.jsx
│       │   ├───ScanningLoader.jsx
│       │   ├───shared\
│       │   │   └───LanguageToggle.jsx
│       │   └───voice\
│       │       ├───UnifiedChatPage.jsx
│       │       ├───VoiceErrorPopup.jsx
│       │       ├───VoicePage.jsx
│       │       ├───VoiceProcessing.jsx
│       │       ├───VoiceRecorder.jsx
│       │       └───VoiceResult.jsx
│       ├───hooks\
│       │   └───useAudioRecorder.js
│       ├───services\
│       │   └───apiService.js
│       └───utils\
│           └───imageUtils.js
├───migrations\
│   ├───env.py
│   ├───script.py.mako
│   ├───__pycache__\...
│   └───versions\
│       ├───0001_initial_schema.py
│       ├───0002_feedback_events.py
│       └───__pycache__\...
├───scripts\
│   ├───build_graph.py
│   ├───feedback_report.py
│   └───seed_data.py
└───test_images\
    ├───f5e_tiger.jpg
    ├───ngo_mon.jpg
    ├───ngo_mon.png
    ├───tank_843.jpg
    └───tank_843.png


</session_context>

---

## USER 🧑‍💻

đọc và phân tích toàn bộ codebase hiện tại

---

## MODEL ✨

**Tool Command**:
```json
{
  "name": "update_topic",
  "args": {
    "title": "Codebase Analysis",
    "summary": "I am starting a comprehensive analysis of the AI Tour Guide project. I will read key documentation and entry point files (like README.md, backend/main.py, and frontend/package.json) to understand the project's purpose, technologies used, and overall structure.",
    "strategic_intent": "Analyzing the codebase architecture, tech stack, and core functionalities of the AI Tour Guide project."
  },
  "id": "update_topic__update_topic_1780166055949_0"
}
```**Tool Command**:
```json
{
  "name": "read_file",
  "args": {
    "file_path": "README.md"
  },
  "id": "read_file__read_file_1780166055988_1"
}
```**Tool Command**:
```json
{
  "name": "read_file",
  "args": {
    "file_path": "backend/main.py"
  },
  "id": "read_file__read_file_1780166056052_2"
}
```**Tool Command**:
```json
{
  "name": "read_file",
  "args": {
    "file_path": "frontend/package.json"
  },
  "id": "read_file__read_file_1780166056055_3"
}
```

---

## USER 🧑‍💻

**Tool Response**:
```json
{
  "id": "update_topic__update_topic_1780166055949_0",
  "name": "update_topic",
  "response": {
    "output": "Current topic: \"Codebase Analysis\"\nTopic summary: I am starting a comprehensive analysis of the AI Tour Guide project. I will read key documentation and entry point files (like README.md, backend/main.py, and frontend/package.json) to understand the project's purpose, technologies used, and overall structure.\n\nStrategic Intent: Analyzing the codebase architecture, tech stack, and core functionalities of the AI Tour Guide project."
  }
}
```**Tool Response**:
```json
{
  "id": "read_file__read_file_1780166055988_1",
  "name": "read_file",
  "response": {
    "output": "# AI Tour Guide\n\nAI Tour Guide là web app hướng dẫn du lịch thông minh. Ứng dụng chạy trên trình duyệt, dùng React/Vite ở frontend và FastAPI ở backend để xử lý hội thoại, nhận diện ảnh, giọng nói, RAG theo dữ liệu hiện vật và đọc câu trả lời.\n\n## Tính năng chính\n\n- Trải nghiệm hướng dẫn tham quan tập trung vào người dùng.\n- Hỏi đáp bằng text, ảnh upload/webcam và giọng nói.\n- Nhận diện hiện vật bằng Gemini Vision.\n- Tìm dữ liệu hiện vật trong PostgreSQL và trả lời nhanh từ DB/cache khi đủ thông tin.\n- Gọi LLM Gemini/Groq khi cần diễn giải tự nhiên.\n- Tạo audio bằng Edge TTS hoặc Web Speech API ở trình duyệt.\n- Ghi nhận phản hồi hữu ích/chưa đúng để cải thiện chất lượng câu trả lời.\n\n## Cấu trúc\n\n```text\nbackend/       FastAPI unified backend\nfrontend/      React + Vite web app\nscripts/       Seed data PostgreSQL\ndocker/        PostgreSQL + backend compose\nmigrations/    Alembic config\ndocs/          Architecture và improvement plan\n```\n\n## Yêu cầu\n\n- Python 3.10+\n- Node.js 18+\n- Docker Desktop nếu dùng PostgreSQL qua Docker\n- API keys:\n  - `GEMINI_API_KEY`\n  - `GROQ_API_KEY`\n\n## Chạy trên máy local\n\n### 1. Tạo file môi trường\n\nTạo `.env` ở thư mục root:\n\n```env\nENVIRONMENT=development\nLOG_LEVEL=INFO\nGEMINI_API_KEY=your_gemini_api_key_here\nGROQ_API_KEY=your_groq_api_key_here\nDATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_tour_guide\nLLM_PROVIDER_ORDER=gemini,groq\n```\n\n### 2. Chạy PostgreSQL\n\n```bash\ncd docker\ndocker-compose up -d postgres\ncd ..\n```\n\n### 3. Cài và chạy backend\n\n```bash\ncd backend\npython -m venv .venv\n.venv\\Scripts\\activate\npip install -r requirements.txt\ncd ..\nalembic upgrade head\npython scripts\\seed_data.py\ncd backend\nuvicorn main:app --host 127.0.0.1 --port 8000 --reload\n```\n\nBackend chạy tại:\n\n```text\nhttp://127.0.0.1:8000\n```\n\nHealth check:\n\n```text\nhttp://127.0.0.1:8000/api/v1/health\nhttp://127.0.0.1:8000/api/v1/health/ready\n```\n\n### 4. Cài và chạy frontend\n\nMở terminal mới:\n\n```bash\ncd frontend\nnpm install\nnpm run dev\n```\n\nFrontend chạy tại:\n\n```text\nhttps://localhost:5173\n```\n\nVite dùng HTTPS self-signed để trình duyệt cho phép camera/microphone. Nếu trình duyệt cảnh báo bảo mật, chọn Advanced/Proceed để vào ứng dụng local.\n\n## Cách sử dụng nhanh\n\n1. Mở `https://localhost:5173`.\n2. Chọn `Bắt đầu tham quan`.\n3. Dùng một trong các cách:\n   - nhập câu hỏi về hiện vật;\n   - tải ảnh từ thiết bị;\n   - chụp ảnh bằng camera;\n   - ghi âm bằng microphone.\n4. Xem câu trả lời ở panel giữa và thông tin hiện vật ở panel bên phải.\n\n## Lệnh kiểm tra\n\nBackend:\n\n```bash\ncd backend\npython -m pytest tests\n```\n\nFrontend:\n\n```bash\ncd frontend\nnpm run build\nnpm run lint\n```\n\n## Ghi chú hiện tại\n\n- Web hiện tối ưu cho máy tính và laptop. Mobile web/PWA là hướng phát triển sau.\n- Nếu backend chưa chạy, frontend vẫn mở được nhưng các request AI sẽ báo lỗi.\n- Nếu thiếu API key hoặc hết quota, các bước Vision/STT/LLM có thể thất bại.\n- Nếu chưa chạy PostgreSQL/migration/seed data, hệ thống vẫn có thể chat general nhưng RAG hiện vật sẽ thiếu dữ liệu.\n"
  }
}
```**Tool Response**:
```json
{
  "id": "read_file__read_file_1780166056052_2",
  "name": "read_file",
  "response": {
    "output": "\"\"\"Unified FastAPI application entrypoint.\n\nMerges both Backend 1 (port 8000, vision) and Backend 2 (port 8001, voice)\ninto a single application running on port 8000.\n\"\"\"\n\nfrom __future__ import annotations\n\nimport logging\nfrom time import perf_counter\nimport uuid\nfrom contextlib import asynccontextmanager\n\nfrom fastapi import FastAPI, HTTPException, Request\nfrom fastapi.middleware.cors import CORSMiddleware\nfrom slowapi.errors import RateLimitExceeded\nfrom fastapi.responses import JSONResponse\n\nfrom core.config import settings\nfrom core.cache import setup_cache\nfrom core.logging import setup_logging\nfrom core.observability import increment, observe_duration, snapshot\nfrom core.security import limiter, rate_limit_exceeded_handler\nfrom middleware.error_handler import global_exception_handler\nfrom services.ai.embedding_service import EmbeddingService\n\n# Setup logging before anything else\nsetup_logging()\nlogger = logging.getLogger(__name__)\n\n\n@asynccontextmanager\nasync def lifespan(app: FastAPI):\n    logger.info(\"AI Tour Guide Backend starting...\")\n    setup_cache()\n    logger.info(f\"Environment: {settings.ENVIRONMENT}\")\n    logger.info(\"Routers: vision (/api/v1/recognize), voice (/api/v1/voice/chat)\")\n    yield\n    logger.info(\"Backend shutting down.\")\n\n\n# ─── Application ─────────────────────────────────────────────────────────────\napp = FastAPI(\n    title=\"AI Tour Guide - Unified Backend API\",\n    description=\"Smart tourism backend for vision, voice, chat, and artifact context\",\n    version=\"2.0.0\",\n    lifespan=lifespan,\n)\n\napp.state.limiter = limiter\napp.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)\napp.add_exception_handler(Exception, global_exception_handler)\n\n\n@app.exception_handler(HTTPException)\nasync def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:\n    request_id = getattr(request.state, \"request_id\", None)\n    detail = exc.detail if isinstance(exc.detail, str) else \"Yêu cầu không hợp lệ.\"\n    error_code = \"HTTP_ERROR\"\n    if exc.status_code == 413:\n        error_code = \"PAYLOAD_TOO_LARGE\"\n    elif exc.status_code == 429:\n        error_code = \"RATE_LIMIT_EXCEEDED\"\n    elif exc.status_code >= 500:\n        error_code = \"SERVER_ERROR\"\n\n    return JSONResponse(\n        status_code=exc.status_code,\n        content={\n            \"success\": False,\n            \"error_code\": error_code,\n            \"message\": detail,\n            \"detail\": detail,\n            \"request_id\": request_id,\n        },\n        headers=getattr(exc, \"headers\", None),\n    )\n\n\n@app.middleware(\"http\")\nasync def request_id_middleware(request: Request, call_next):\n    started_at = perf_counter()\n    request_id = request.headers.get(\"x-request-id\") or str(uuid.uuid4())\n    request.state.request_id = request_id\n    response = await call_next(request)\n    response.headers[\"x-request-id\"] = request_id\n    route_key = f\"{request.method} {request.url.path}\"\n    increment(f\"http.{response.status_code}\")\n    observe_duration(route_key, started_at)\n    logger.info(\n        \"request_id=%s method=%s path=%s status=%s duration_ms=%.2f\",\n        request_id,\n        request.method,\n        request.url.path,\n        response.status_code,\n        (perf_counter() - started_at) * 1000,\n    )\n    return response\n\n# CORS\napp.add_middleware(\n    CORSMiddleware,\n    allow_origins=settings.CORS_ORIGINS,\n    allow_credentials=True,\n    allow_methods=[\"GET\", \"POST\"],\n    allow_headers=[\"*\"],\n)\n\n# ─── Register Routers ────────────────────────────────────────────────────────\nfrom api.routers.health_router import router as health_router\nfrom api.routers.vision_router import router as vision_router\nfrom api.routers.voice_router import router as voice_router\nfrom api.routers.chat_router import router as chat_router\nfrom api.routers.feedback_router import router as feedback_router\n\napp.include_router(health_router)\napp.include_router(vision_router)\napp.include_router(voice_router)\napp.include_router(chat_router)\napp.include_router(feedback_router)\n\n\n@app.get(\"/api/v1/metrics\")\nasync def metrics_snapshot():\n    return snapshot()\n\n\nif __name__ == \"__main__\":\n    import uvicorn\n    uvicorn.run(\"main:app\", host=\"0.0.0.0\", port=8000, reload=True)\n"
  }
}
```**Tool Response**:
```json
{
  "id": "read_file__read_file_1780166056055_3",
  "name": "read_file",
  "response": {
    "output": "{\n  \"name\": \"ai-tour-guide-frontend\",\n  \"private\": true,\n  \"version\": \"1.0.0\",\n  \"type\": \"module\",\n  \"scripts\": {\n    \"dev\": \"vite\",\n    \"build\": \"vite build\",\n    \"lint\": \"eslint .\",\n    \"preview\": \"vite preview\"\n  },\n  \"dependencies\": {\n    \"lucide-react\": \"^0.475.0\",\n    \"react\": \"^18.3.1\",\n    \"react-dom\": \"^18.3.1\"\n  },\n  \"devDependencies\": {\n    \"@eslint/js\": \"^9.20.0\",\n    \"@types/react\": \"^18.3.18\",\n    \"@types/react-dom\": \"^18.3.5\",\n    \"@vitejs/plugin-basic-ssl\": \"^2.3.0\",\n    \"@vitejs/plugin-react\": \"^4.3.4\",\n    \"eslint\": \"^9.20.0\",\n    \"eslint-plugin-react\": \"^7.37.4\",\n    \"eslint-plugin-react-hooks\": \"^5.0.0\",\n    \"eslint-plugin-react-refresh\": \"^0.4.19\",\n    \"globals\": \"^15.15.0\",\n    \"vite\": \"^6.1.0\"\n  }\n}\n"
  }
}
```

---

## MODEL ✨

**Tool Command**:
```json
{
  "name": "read_file",
  "args": {
    "file_path": "frontend/src/App.jsx"
  },
  "id": "read_file__read_file_1780166064079_0"
}
```**Tool Command**:
```json
{
  "name": "read_file",
  "args": {
    "file_path": "backend/core/config/settings.py"
  },
  "id": "read_file__read_file_1780166064146_1"
}
```

---

## USER 🧑‍💻

**Tool Response**:
```json
{
  "id": "read_file__read_file_1780166064079_0",
  "name": "read_file",
  "response": {
    "output": "import React, { useState, useEffect } from 'react';\nimport HomeScreen from './components/HomeScreen';\nimport UnifiedChatPage from './components/voice/UnifiedChatPage';\n\nfunction App() {\n  const [appState, setAppState] = useState(() => {\n    return new URLSearchParams(window.location.search).get('view') === 'chat' ? 'chat' : 'home';\n  });\n  const [language, setLanguage] = useState(() => {\n    return localStorage.getItem('ai_tour_lang') || 'vi';\n  });\n\n  useEffect(() => {\n    localStorage.setItem('ai_tour_lang', language);\n  }, [language]);\n\n  const resetToHome = () => {\n    setAppState('home');\n  };\n\n  const handleSelectFeature = () => {\n    setAppState('chat');\n  };\n\n  return (\n    <div style={{ width: '100%', height: '100%', position: 'relative' }}>\n\n      {/* Main Views */}\n      {appState === 'home' && (\n        <HomeScreen\n          onSelectFeature={handleSelectFeature}\n          language={language}\n          setLanguage={setLanguage}\n        />\n      )}\n\n      {appState === 'chat' && (\n        <UnifiedChatPage\n          onBack={resetToHome}\n          language={language}\n          setLanguage={setLanguage}\n        />\n      )}\n\n    </div>\n  );\n}\n\nexport default App;\n"
  }
}
```**Tool Response**:
```json
{
  "id": "read_file__read_file_1780166064146_1",
  "name": "read_file",
  "response": {
    "output": "\"\"\"Centralized configuration using Pydantic Settings.\"\"\"\n\nfrom __future__ import annotations\nfrom functools import lru_cache\nfrom pathlib import Path\nfrom pydantic_settings import BaseSettings\n\n# .parent = config/, .parent.parent = core/, .parent.parent.parent = backend/\n_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent\n_PROJECT_ROOT = _BACKEND_ROOT.parent\n\n\nclass Settings(BaseSettings):\n    ENVIRONMENT: str = \"development\"\n    DEBUG: bool = False\n    LOG_LEVEL: str = \"INFO\"\n\n    GEMINI_API_KEY: str = \"\"\n    GROQ_API_KEY: str = \"\"\n    HUGGINGFACE_API_KEY: str = \"\"\n\n    DATABASE_URL: str = \"postgresql+asyncpg://postgres:postgres@localhost:5432/ai_tour_guide\"\n    DATABASE_POOL_SIZE: int = 10\n    DATABASE_MAX_OVERFLOW: int = 20\n    DATABASE_ECHO: bool = False\n\n    REDIS_URL: str = \"redis://localhost:6379/0\"\n    CACHE_TTL_SECONDS: int = 3600\n\n    LLM_PROVIDER_ORDER: str = \"gemini, groq\"\n    GEMINI_TEXT_MODEL: str = \"gemini-2.0-flash\"\n    GEMINI_EMBEDDING_MODEL: str = \"gemini-embedding-2\"\n    GEMINI_VISION_MODEL: str = \"gemini-flash-latest\"\n    GROQ_LLM_MODEL: str = \"llama-3.3-70b-versatile\"\n    GROQ_STT_MODEL: str = \"whisper-large-v3\"\n    LLM_TEMPERATURE: float = 0.6\n    LLM_MAX_TOKENS: int = 400\n    VISION_CONFIDENCE_THRESHOLD: float = 0.6\n\n    TEXT_MAX_CHARS: int = 1200\n    IMAGE_MAX_BYTES: int = 5_000_000\n    AUDIO_MAX_BYTES: int = 8_000_000\n\n    VOICE_MAX_TURNS: int = 6\n    VOICE_SESSION_TTL_SECONDS: int = 3600\n    VOICE_MAX_TURN_CHARS: int = 240\n    STT_DOMAIN_HINTS: str = \"\"\n\n    EDGE_TTS_VOICE_VI: str = \"vi-VN-HoaiMyNeural\"\n    EDGE_TTS_VOICE_EN: str = \"en-US-AriaNeural\"\n\n    RATE_LIMIT: str = \"30/minute\"\n    CORS_ORIGINS: list[str] = [\"https://localhost:5173\", \"http://localhost:5173\"]\n\n    model_config = {\n        \"env_file\": [str(_BACKEND_ROOT / \".env\"), str(_PROJECT_ROOT / \".env\")],\n        \"env_file_encoding\": \"utf-8\",\n        \"case_sensitive\": True,\n        \"extra\": \"ignore\",\n    }\n\n    @property\n    def llm_provider_list(self) -> list[str]:\n        return [p.strip().lower() for p in self.LLM_PROVIDER_ORDER.split(\",\") if p.strip()]\n\n    @property\n    def is_production(self) -> bool:\n        return self.ENVIRONMENT.strip().lower() in {\"production\", \"prod\"}\n\n    def validate_runtime(self) -> None:\n        \"\"\"Fail fast for configuration that should never be missing in production.\"\"\"\n        if not self.is_production:\n            return\n\n        missing = []\n        if not self.GEMINI_API_KEY.strip():\n            missing.append(\"GEMINI_API_KEY\")\n        if not self.GROQ_API_KEY.strip():\n            missing.append(\"GROQ_API_KEY\")\n        if not self.DATABASE_URL.strip():\n            missing.append(\"DATABASE_URL\")\n        if missing:\n            joined = \", \".join(missing)\n            raise ValueError(f\"Missing required production settings: {joined}\")\n\n\n@lru_cache()\ndef get_settings() -> Settings:\n    current_settings = Settings()\n    current_settings.validate_runtime()\n    return current_settings\n\n\nsettings: Settings = get_settings()\n"
  }
}
```

---

## MODEL ✨

Dựa vào cấu trúc thư mục và nội dung các file cấu hình cốt lõi, tôi xin trình bày phân tích tổng quan về codebase của dự án **AI Tour Guide**:

### 1. Tổng quan kiến trúc hệ thống
Đây là một ứng dụng Web Full-stack (React + FastAPI) với mục tiêu làm **Hướng dẫn viên du lịch thông minh**. Hệ thống được thiết kế linh hoạt, kết hợp nhiều mô hình AI để xử lý đa dạng các luồng đầu vào: văn bản, hình ảnh, và giọng nói.
- **Frontend:** React.js, đóng gói bằng Vite.
- **Backend:** Python FastAPI, thiết kế theo kiến trúc Module/Layer.
- **Database:** PostgreSQL (có thể sử dụng extension để lưu trữ Vector Embeddings phục vụ RAG).
- **AI Providers:** Tích hợp chủ yếu qua Google (Gemini) và Groq.

---

### 2. Phân tích chi tiết Frontend (`frontend/`)
Frontend được tổ chức dưới dạng một Single Page Application (SPA) nhẹ:
- **Công nghệ chính:** React 18, Vite, ES Modules. Không sử dụng TypeScript hay các framework cồng kềnh, styling trực tiếp bằng CSS thuần (`index.css`) giúp UI đơn giản và nhẹ nhàng. Icon dùng `lucide-react`.
- **Luồng hoạt động (App.jsx):** Quản lý state tập trung ở cấp độ App để chuyển đổi giữa 2 màn hình chính:
  - `HomeScreen`: Màn hình chờ hoặc chọn chức năng ban đầu.
  - `UnifiedChatPage`: Giao diện tương tác AI thống nhất. Hỗ trợ đầy đủ chức năng: quét ảnh (CameraScanner), tải ảnh lên, thu âm giọng nói (VoiceRecorder) và khung chat.
- **Quản lý đa ngôn ngữ:** Hỗ trợ song ngữ (tiếng Việt & tiếng Anh), lưu trữ tùy chọn trong `localStorage` qua khóa `ai_tour_lang`.

---

### 3. Phân tích chi tiết Backend (`backend/`)
Backend được xây dựng rất chuyên nghiệp với kiến trúc sạch, phân lớp rõ ràng:
- **Điểm vào (`main.py`):** Khởi tạo ứng dụng FastAPI thống nhất. Bao gồm Middleware bắt lỗi (Error Handling), theo dõi thời gian thực thi (Observability), Rate Limit và CORS.
- **Core (`core/`):** Xử lý thiết lập cốt lõi:
  - `config/settings.py`: Nạp biến môi trường bằng Pydantic. Quản lý cấu hình linh hoạt cho mô hình AI (Gemini Flash/Embeddings, Llama qua Groq), Database pool, Redis Cache. Cấu hình sẵn cơ chế Fallback LLM (ưu tiên Gemini, dự phòng Groq).
  - Cấu trúc thư mục cho thấy có logging riêng, module security (Rate Limiting) và observability (metrics).
- **API Routers (`api/routers/`):** Phân chia rõ ràng các module API: `vision`, `voice`, `chat`, `feedback`, `health`.
- **Dịch vụ (`services/`):** Chứa logic nghiệp vụ lõi:
  - `ai/`: Gọi model embeddings.
  - `llm/`: Strategy pattern cho các LLM providers khác nhau (Gemini, Groq, Fallback).
  - `vision/`: Xử lý logic nhận diện ảnh (gửi lên Gemini Vision).
  - `voice/`: Tích hợp Groq STT (Speech-to-Text - Whisper) và Edge TTS (Text-to-Speech) để tổng hợp giọng nói đọc cho người dùng.
- **Database & Models:** Dùng SQLAlchemy / Alembic để quản lý Schema. Cấu trúc DB thiết kế rất thực tế bao gồm `artifact` (hiện vật), `location`, `bilingual_content` (cho đa ngôn ngữ), `feedback_event` (để AI học hỏi/cải thiện) và `chat_history`.

---

### 4. Cơ sở hạ tầng & DevOps
- **Docker (`docker/`):** Sử dụng `docker-compose` để dễ dàng khởi tạo local database (PostgreSQL). Có `Dockerfile` chuẩn bị sẵn để đóng gói Backend khi deploy.
- **Database Migration (`migrations/`):** Sử dụng `Alembic` để tự động hóa và quản lý lịch sử các thay đổi schema database một cách an toàn.
- **Scripts (`scripts/`):** Có file `seed_data.py` dùng để thiết lập dữ liệu (hiện vật) mẫu ban đầu cho RAG và `build_graph.py` (có thể liên quan đến xử lý knowledge graph hoặc routing/state machine cho agent).

### 💡 Đánh giá điểm mạnh:
- **Kiến trúc rõ ràng & Scalable:** Cấu trúc backend chia theo domain (routes, services, orchestrators) giúp codebase cực kì dễ mở rộng.
- **Trải nghiệm người dùng đa phương thức (Multimodal):** Hỗ trợ đủ cả chữ, ảnh và giọng nói là một điểm cộng lớn cho ứng dụng du lịch. Cơ chế cache và precomputed audio giúp tăng tốc phản hồi đáng kể.
- **Chiến lược dự phòng (Fallback):** Đã tính toán đến giới hạn API bằng cách luân chuyển giữa Gemini và Groq (`LLM_PROVIDER_ORDER`).

Bạn có muốn đi sâu vào bất kỳ luồng xử lý cụ thể nào không (ví dụ: luồng nhận diện ảnh bằng Vision, xử lý hội thoại bằng RAG, hoặc cấu trúc Database cụ thể)?

---

## USER 🧑‍💻

giờ tôi muốn phát triển theo hướng khác không đơn thuần là chatbot nữa, bây giờ hệ thống sẽ hiện trước các địa điểm đã có trong hệ thống, sau đó người dùng muốn khám phá nó thì bấm vào phần đó, khi này trong đây sẽ có 2 luồng hoạt động chính đó là phần chatbot để hỏi đáp, thuyết minh về từng địa điểm người dùng yêu cầu, 1 cái là phần map hiển thị vị trị hiện tại của người dùng thông qua bản đồ nội bộ do tôi tự thiết kế đưa vào, bạn phải mapping vị trí hiện tại của tôi trên gps để mapping qua cái map nội bộ đó để biết tôi đang ở đâu trong map đó, sau đó trên bản đồ ấy tôi có thể chọn 1 địa điểm bất kì và bạn sẽ phải đọc hướng dẫn chỉ đường đi đến đó sau đó hỏi người dùng có muốn thuyết minh về cái này không các thứ, hiển thị 1 vài đề xuất cho người dùng và tôi muốn nó hoạt động thuyết trình chuyên sâu như 1 hướng dẫn viên thực thụ, hãy lên kế hoạch cho tôi check xem triển khai nó thế nào và phương hướng làm tốt nhất

---

## MODEL ✨

**Tool Command**:
```json
{
  "name": "update_topic",
  "args": {
    "summary": "I will analyze the user's request to pivot the application's core functionality. The new direction involves displaying a list of available locations, an interactive custom internal map with GPS-to-internal-map coordinate mapping, a dedicated chatbot/presentation mode per location, and turn-by-turn audio navigation to selected points of interest, followed by deep-dive storytelling. I will formulate a comprehensive plan covering UI/UX restructuring, custom map integration, GPS mapping logic, and agentic orchestration for navigation and storytelling.",
    "title": "Architectural Shift: Map-Based Interactive Guide",
    "strategic_intent": "Proposing a strategic architectural shift and implementation plan to transition the application from a pure chatbot to an interactive, map-based, location-aware tour guide."
  },
  "id": "update_topic__update_topic_1780166350568_0"
}
```**Tool Command**:
```json
{
  "name": "ask_user",
  "args": {
    "questions": [
      {
        "header": "Map Format",
        "options": [
          {
            "label": "Static Image Map",
            "description": "A static image file (PNG/JPG/SVG) mapped to GPS bounds. Good for small sites."
          },
          {
            "label": "Interactive Vector/Tile Map",
            "description": "A custom tiled map (GeoJSON/Mapbox/Leaflet) with real coordinate systems. Best for complex, accurate routing."
          }
        ],
        "question": "Về \"bản đồ nội bộ do bạn tự thiết kế\", bạn dự định cung cấp bản đồ này dưới định dạng nào?",
        "type": "choice"
      },
      {
        "header": "GPS Context",
        "type": "choice",
        "question": "Mục tiêu triển khai cuối cùng của phần mapping GPS là gì?",
        "options": [
          {
            "label": "Real On-site GPS",
            "description": "Ứng dụng chạy trên điện thoại/tablet thực tế tại địa điểm tham quan."
          },
          {
            "description": "Dùng trong môi trường giả lập/web để test (cho phép fake GPS).",
            "label": "Simulated/Web testing"
          }
        ]
      },
      {
        "type": "choice",
        "header": "Navigation Method",
        "options": [
          {
            "description": "Chỉ cần vạch một đường thẳng (as the crow flies) trên bản đồ.",
            "label": "Direct Line"
          },
          {
            "label": "Pathfinding/Routing",
            "description": "Cần tính toán đường đi qua các lối đi/đường nội bộ hợp lệ (yêu cầu dữ liệu graph/path)."
          }
        ],
        "question": "Khi \"đọc hướng dẫn chỉ đường đi đến đó\", hệ thống cần tính toán đường đi chi tiết như thế nào?"
      }
    ]
  },
  "id": "ask_user__ask_user_1780166350610_1"
}
```

---

## USER 🧑‍💻

**Tool Response**:
```json
{
  "id": "update_topic__update_topic_1780166350568_0",
  "name": "update_topic",
  "response": {
    "output": "Current topic: \"Architectural Shift: Map-Based Interactive Guide\"\nTopic summary: I will analyze the user's request to pivot the application's core functionality. The new direction involves displaying a list of available locations, an interactive custom internal map with GPS-to-internal-map coordinate mapping, a dedicated chatbot/presentation mode per location, and turn-by-turn audio navigation to selected points of interest, followed by deep-dive storytelling. I will formulate a comprehensive plan covering UI/UX restructuring, custom map integration, GPS mapping logic, and agentic orchestration for navigation and storytelling.\n\nStrategic Intent: Proposing a strategic architectural shift and implementation plan to transition the application from a pure chatbot to an interactive, map-based, location-aware tour guide."
  }
}
```**Tool Response**:
```json
{
  "id": "ask_user__ask_user_1780166350610_1",
  "name": "ask_user",
  "response": {
    "output": "{\"answers\":{\"0\":\"Interactive Vector/Tile Map\",\"1\":\"Real On-site GPS\",\"2\":\"Pathfinding/Routing\"}}"
  }
}
```

---

## MODEL ✨

**Tool Command**:
```json
{
  "name": "write_file",
  "args": {
    "file_path": "plans/map_integration_plan.md",
    "content": "# Kế Hoạch Chuyển Đổi: AI Tour Guide -> Bản Đồ Tương Tác & Thuyết Minh Chuyên Sâu\n\n## 1. Bối cảnh & Mục tiêu (Background & Motivation)\nỨng dụng hiện tại đang hoạt động dưới dạng một Chatbot thuần túy. Yêu cầu mới chuyển đổi ứng dụng thành một **Hướng dẫn viên du lịch tương tác dựa trên vị trí (Location-aware Interactive Guide)**. \n\nHệ thống sẽ cung cấp:\n- Danh sách các địa điểm (locations) có sẵn.\n- **Bản đồ nội bộ tương tác (Vector/Tile Map)** kết hợp định vị GPS thực tế (Real On-site GPS).\n- Hệ thống tìm đường (Pathfinding/Routing) giữa vị trí hiện tại và điểm đến được chọn.\n- Luồng âm thanh chỉ đường tuần tự.\n- Chế độ **Thuyết minh chuyên sâu (Deep-dive Storytelling)** khi đến nơi, hoạt động như một hướng dẫn viên thực thụ (đề xuất chủ đề, kể chuyện tương tác, trả lời câu hỏi).\n\n## 2. Phạm vi & Tác động (Scope & Impact)\n\nSự thay đổi này tác động lớn đến cả Frontend và Backend:\n- **Frontend:** Cần tích hợp thư viện bản đồ (như Leaflet.js hoặc Mapbox GL JS), xử lý Web Geolocation API, và thiết kế lại luồng UI/UX (Màn hình chính -> Bản đồ -> Chế độ dẫn đường -> Chế độ Thuyết minh).\n- **Backend:** Cần thêm logic tìm đường (Routing Engine), quản lý tọa độ/polygon của bản đồ nội bộ, và nâng cấp Agent (Orchestrator) để hỗ trợ \"State\" dẫn đường và \"State\" thuyết minh sâu.\n- **Dữ liệu (Database):** Mở rộng bảng `Location` và `Artifact` để lưu trữ tọa độ GeoJSON, các node/edge cho đồ thị tìm đường (Path Graph).\n\n## 3. Kiến trúc Đề xuất (Proposed Solution)\n\n### 3.1. Frontend (React + Vite)\n- **Thư viện Bản đồ:** Sử dụng `React-Leaflet` (mã nguồn mở, dễ tích hợp custom vector/tiles) hoặc `Mapbox GL JS` (mượt mà, phù hợp vector map phức tạp).\n- **Định vị (Geolocation):** Sử dụng `navigator.geolocation.watchPosition` để liên tục cập nhật vị trí người dùng.\n- **Biến đổi Tọa độ (Coordinate Mapping):** Nếu bản đồ nội bộ không khớp hoàn hảo với GPS chuẩn, cần một hàm nội suy (Affine Transformation) ở Frontend hoặc Backend để map từ `[vĩ độ, kinh độ GPS]` sang `[x, y bản đồ nội bộ]`.\n- **UI States:**\n  - `LocationList`: Danh sách địa điểm tham quan.\n  - `MapExplore`: Xem bản đồ, vị trí hiện tại (Blue dot), các điểm tham quan (Pins).\n  - `Navigating`: Chế độ dẫn đường (hiển thị path, phát audio chỉ đường).\n  - `StoryTelling`: Chế độ thuyết minh chuyên sâu khi đã tới nơi (hiển thị hình ảnh hiện vật, audio guide, chat bổ sung).\n\n### 3.2. Backend & Dữ liệu (FastAPI + PostgreSQL)\n- **Geospatial Data:** Sử dụng `PostGIS` (extension của PostgreSQL) hoặc lưu trữ tọa độ chuẩn dạng JSON (GeoJSON) nếu map nhỏ gọn.\n- **Routing Engine (Tìm đường):**\n  - Xây dựng một đồ thị (Graph) các đường đi nội bộ hợp lệ (Nodes & Edges). Có thể dùng script `build_graph.py` hiện tại làm nền tảng.\n  - Áp dụng thuật toán Dijkstra hoặc A* để tìm đường ngắn nhất.\n  - Chuyển đổi tuyến đường (Path) thành tập hợp các chỉ dẫn văn bản (ví dụ: \"Đi thẳng 20 mét, rẽ trái tại khu vực A\").\n- **Voice Orchestrator (Nâng cấp):**\n  - State 1: **Chỉ đường (Navigation Agent):** Đọc hướng dẫn tìm đường qua TTS.\n  - State 2: **Đề xuất (Hooking Agent):** Khi GPS nhận diện người dùng đã đến gần (radius < 5m), kích hoạt câu hỏi: *\"Bạn đã đến Cổng Ngọ Môn, bạn có muốn nghe tôi kể về lịch sử xây dựng của nó không?\"*\n  - State 3: **Thuyết minh (Storytelling Agent):** Lấy dữ liệu RAG sâu về hiện vật, chia nhỏ nội dung thành các đoạn hấp dẫn thay vì đọc một bài text dài, kết hợp hỏi đáp tương tác.\n\n## 4. Các Bước Triển Khai (Phased Implementation Plan)\n\n### Phase 1: Chuẩn bị Dữ liệu Bản đồ & Routing (Backend/Data)\n1. **Thiết kế Cấu trúc Dữ liệu Bản đồ:** Mở rộng DB để lưu tọa độ `(lat, lng)` cho các `Location` và `Artifact`.\n2. **Xây dựng Đồ thị Tìm đường:** Xác định các điểm nối (waypoints) trên bản đồ nội bộ để tạo Graph.\n3. **API Routing:** Viết API endpoint `/api/v1/map/route` nhận vị trí hiện tại và điểm đến, trả về đường dẫn (Array of coordinates) và Text chỉ dẫn.\n\n### Phase 2: Tích hợp Bản đồ vào Frontend\n1. Cài đặt thư viện `leaflet` và `react-leaflet`.\n2. Hiển thị Bản đồ nội bộ (Render custom vector/tiles) lên giao diện.\n3. Tích hợp Geolocation API để hiển thị vị trí người dùng theo thời gian thực (Blue dot).\n4. Viết hàm nội suy (Mapping function) nếu cần thiết để khớp GPS thực tế với Bản đồ thiết kế.\n\n### Phase 3: Luồng Dẫn đường (Navigation & Voice)\n1. Thêm tính năng chọn điểm đến trên bản đồ. Nhận luồng dẫn đường từ API.\n2. Vẽ đường đi (Polyline) trên bản đồ.\n3. Gọi Edge TTS (có sẵn trong `services/voice/`) để đọc các bước chỉ đường theo từng checkpoint người dùng đi qua.\n\n### Phase 4: Chế độ Thuyết minh Chuyên sâu (Storytelling Agent)\n1. **Trigger theo Vị trí (Geofencing):** Khi vị trí người dùng gần mục tiêu, Frontend báo Backend chuyển trạng thái sang `StoryTelling`.\n2. **Prompt Engineering:** Tạo `prompt_templates` mới cho vai trò \"Hướng dẫn viên thực thụ\" (Giọng điệu lôi cuốn, chia nhỏ thông tin, đặt câu hỏi gợi mở).\n3. **Tích hợp UI:** Mở panel/modal Thuyết minh chuyên sâu, kết hợp hiển thị ảnh chất lượng cao và giao diện Chat/Voice để người dùng đào sâu chủ đề.\n\n## 5. Alternatives Considered (Các Lựa chọn Thay thế)\n- **Map hiển thị:** Thay vì Vector Map phức tạp, có thể bắt đầu bằng **Image Overlay trên Leaflet** (dùng một ảnh tĩnh chất lượng cao đè lên tọa độ GPS) để Proof of Concept nhanh hơn.\n- **Routing:** Nếu không muốn tự viết thuật toán A* trên Backend, có thể cấu hình dữ liệu mạng lưới đường đi nội bộ và dùng thư viện Routing trên Frontend (ví dụ `turf.js`) nếu dung lượng file dữ liệu đồ thị nhỏ.\n\n## 6. Xác nhận & Kiểm tra (Verification)\n- **Test GPS Mapping:** Chạy Frontend với fake GPS (trên trình duyệt) để kiểm tra chấm xanh có di chuyển mượt mà trên bản đồ không.\n- **Test Routing:** Kiểm tra API trả về tuyến đường có đâm xuyên tường/khu vực cấm không.\n- **Test Chuyển đổi Trạng thái:** Đi bộ vào bán kính hiện vật -> Audio chỉ đường dừng lại -> Audio đề xuất thuyết minh phát ra.\n"
  },
  "id": "write_file__write_file_1780166492122_0"
}
```

---

## USER 🧑‍💻

**Tool Response**:
```json
{
  "id": "write_file__write_file_1780166492122_0",
  "name": "write_file",
  "response": {
    "error": "Tool execution denied by policy. You are in Plan Mode and cannot modify source code. You may ONLY use write_file or replace to save plans to the designated plans directory as .md files."
  }
}
```

---

## MODEL ✨

**Tool Command**:
```json
{
  "name": "write_file",
  "args": {
    "content": "# Kế Hoạch Chuyển Đổi: AI Tour Guide -> Bản Đồ Tương Tác & Thuyết Minh Chuyên Sâu\n\n## 1. Bối cảnh & Mục tiêu (Background & Motivation)\nỨng dụng hiện tại đang hoạt động dưới dạng một Chatbot thuần túy. Yêu cầu mới chuyển đổi ứng dụng thành một **Hướng dẫn viên du lịch tương tác dựa trên vị trí (Location-aware Interactive Guide)**. \n\nHệ thống sẽ cung cấp:\n- Danh sách các địa điểm (locations) có sẵn.\n- **Bản đồ nội bộ tương tác (Vector/Tile Map)** kết hợp định vị GPS thực tế (Real On-site GPS).\n- Hệ thống tìm đường (Pathfinding/Routing) giữa vị trí hiện tại và điểm đến được chọn.\n- Luồng âm thanh chỉ đường tuần tự.\n- Chế độ **Thuyết minh chuyên sâu (Deep-dive Storytelling)** khi đến nơi, hoạt động như một hướng dẫn viên thực thụ (đề xuất chủ đề, kể chuyện tương tác, trả lời câu hỏi).\n\n## 2. Phạm vi & Tác động (Scope & Impact)\n\nSự thay đổi này tác động lớn đến cả Frontend và Backend:\n- **Frontend:** Cần tích hợp thư viện bản đồ (như Leaflet.js hoặc Mapbox GL JS), xử lý Web Geolocation API, và thiết kế lại luồng UI/UX (Màn hình chính -> Bản đồ -> Chế độ dẫn đường -> Chế độ Thuyết minh).\n- **Backend:** Cần thêm logic tìm đường (Routing Engine), quản lý tọa độ/polygon của bản đồ nội bộ, và nâng cấp Agent (Orchestrator) để hỗ trợ \"State\" dẫn đường và \"State\" thuyết minh sâu.\n- **Dữ liệu (Database):** Mở rộng bảng `Location` và `Artifact` để lưu trữ tọa độ GeoJSON, các node/edge cho đồ thị tìm đường (Path Graph).\n\n## 3. Kiến trúc Đề xuất (Proposed Solution)\n\n### 3.1. Frontend (React + Vite)\n- **Thư viện Bản đồ:** Sử dụng `React-Leaflet` (mã nguồn mở, dễ tích hợp custom vector/tiles) hoặc `Mapbox GL JS` (mượt mà, phù hợp vector map phức tạp).\n- **Định vị (Geolocation):** Sử dụng `navigator.geolocation.watchPosition` để liên tục cập nhật vị trí người dùng.\n- **Biến đổi Tọa độ (Coordinate Mapping):** Nếu bản đồ nội bộ không khớp hoàn hảo với GPS chuẩn, cần một hàm nội suy (Affine Transformation) ở Frontend hoặc Backend để map từ `[vĩ độ, kinh độ GPS]` sang `[x, y bản đồ nội bộ]`.\n- **UI States:**\n  - `LocationList`: Danh sách địa điểm tham quan.\n  - `MapExplore`: Xem bản đồ, vị trí hiện tại (Blue dot), các điểm tham quan (Pins).\n  - `Navigating`: Chế độ dẫn đường (hiển thị path, phát audio chỉ đường).\n  - `StoryTelling`: Chế độ thuyết minh chuyên sâu khi đã tới nơi (hiển thị hình ảnh hiện vật, audio guide, chat bổ sung).\n\n### 3.2. Backend & Dữ liệu (FastAPI + PostgreSQL)\n- **Geospatial Data:** Sử dụng `PostGIS` (extension của PostgreSQL) hoặc lưu trữ tọa độ chuẩn dạng JSON (GeoJSON) nếu map nhỏ gọn.\n- **Routing Engine (Tìm đường):**\n  - Xây dựng một đồ thị (Graph) các đường đi nội bộ hợp lệ (Nodes & Edges). Có thể dùng script `build_graph.py` hiện tại làm nền tảng.\n  - Áp dụng thuật toán Dijkstra hoặc A* để tìm đường ngắn nhất.\n  - Chuyển đổi tuyến đường (Path) thành tập hợp các chỉ dẫn văn bản (ví dụ: \"Đi thẳng 20 mét, rẽ trái tại khu vực A\").\n- **Voice Orchestrator (Nâng cấp):**\n  - State 1: **Chỉ đường (Navigation Agent):** Đọc hướng dẫn tìm đường qua TTS.\n  - State 2: **Đề xuất (Hooking Agent):** Khi GPS nhận diện người dùng đã đến gần (radius < 5m), kích hoạt câu hỏi: *\"Bạn đã đến Cổng Ngọ Môn, bạn có muốn nghe tôi kể về lịch sử xây dựng của nó không?\"*\n  - State 3: **Thuyết minh (Storytelling Agent):** Lấy dữ liệu RAG sâu về hiện vật, chia nhỏ nội dung thành các đoạn hấp dẫn thay vì đọc một bài text dài, kết hợp hỏi đáp tương tác.\n\n## 4. Các Bước Triển Khai (Phased Implementation Plan)\n\n### Phase 1: Chuẩn bị Dữ liệu Bản đồ & Routing (Backend/Data)\n1. **Thiết kế Cấu trúc Dữ liệu Bản đồ:** Mở rộng DB để lưu tọa độ `(lat, lng)` cho các `Location` và `Artifact`.\n2. **Xây dựng Đồ thị Tìm đường:** Xác định các điểm nối (waypoints) trên bản đồ nội bộ để tạo Graph. Có thể lưu bằng bảng Nodes và Edges trong DB.\n3. **API Routing:** Viết API endpoint `/api/v1/map/route` nhận vị trí hiện tại và điểm đến, trả về đường dẫn (Array of coordinates) và Text chỉ dẫn dạng Turn-by-Turn.\n\n### Phase 2: Tích hợp Bản đồ vào Frontend\n1. Cài đặt thư viện `leaflet` và `react-leaflet`.\n2. Hiển thị Bản đồ nội bộ (Render custom vector/tiles) lên giao diện bằng một Component mới (ví dụ: `MapExplore.jsx`).\n3. Tích hợp Web Geolocation API để hiển thị vị trí người dùng theo thời gian thực.\n4. Viết hàm nội suy (Mapping function) để khớp tọa độ GPS thực tế với Bản đồ thiết kế (nếu cần xử lý độ lệch).\n\n### Phase 3: Luồng Dẫn đường (Navigation & Voice)\n1. Thêm tính năng chọn điểm đến trên bản đồ. Giao tiếp với API Routing.\n2. Vẽ đường đi (Polyline) trên bản đồ.\n3. Liên kết với `EdgeTTSProvider` hiện tại để đọc các bước chỉ đường mỗi khi GPS báo người dùng đi qua một node mới trên Graph.\n\n### Phase 4: Chế độ Thuyết minh Chuyên sâu (Storytelling Agent)\n1. **Trigger theo Vị trí (Geofencing):** Khi vị trí người dùng nằm trong bán kính (vd: < 5m) của điểm đến, Frontend báo Backend.\n2. **Nâng cấp LLM System Prompt:** Cập nhật `prompt_templates.py` bổ sung hệ thống Prompt mới cho vai trò \"Hướng dẫn viên thực thụ\" - giọng điệu kể chuyện hấp dẫn, gợi mở câu hỏi.\n3. **Tích hợp UI:** Hiển thị Popup/Panel Thuyết minh chuyên sâu khi đến nơi, cho phép phát Audio tự động, hiển thị ảnh chất lượng cao và giao diện Chat để đào sâu thông tin.\n\n## 5. Alternatives Considered (Các Lựa chọn Thay thế)\n- **Map hiển thị:** Thay vì Vector Map (như GeoJSON) có thể tốn thời gian dựng, có thể sử dụng **Image Overlay trên Leaflet** (Map một ảnh tĩnh sơ đồ nội bộ chất lượng cao khớp 4 góc với tọa độ GPS thực tế). Rất tốt cho proof-of-concept.\n- **Routing Engine:** Thay vì triển khai A* phức tạp trên Backend, có thể đóng gói file `graph.json` và dùng `turf.js` hoặc custom logic pathfinding ngay tại Frontend để giảm tải độ trễ (latency).\n\n## 6. Xác nhận & Kiểm tra (Verification)\n- **Test GPS Mapping:** Chạy Web trên điện thoại thực tế hoặc dùng công cụ giả lập GPS để kiểm tra hiển thị Blue dot.\n- **Test Pathfinding:** Kiểm tra xem các tuyến đường vẽ ra có tránh được vật cản và có hướng dẫn audio chính xác không.\n- **Test Workflow:** Mô phỏng đi bộ đến gần hiện vật xem trigger \"Thuyết minh chuyên sâu\" có nhảy đúng lúc không.",
    "file_path": "C:\\Users\\ADMIN\\.gemini\\tmp\\ai-tour-guide-2\\cecbaae4-0cf5-4f56-bf4d-854ca8131387\\plans/map_integration_plan.md"
  },
  "id": "write_file__write_file_1780166510533_0"
}
```

---

## USER 🧑‍💻

**Tool Response**:
```json
{
  "id": "write_file__write_file_1780166510533_0",
  "name": "write_file",
  "response": {
    "output": "Successfully created and wrote to new file: C:\\Users\\ADMIN\\.gemini\\tmp\\ai-tour-guide-2\\cecbaae4-0cf5-4f56-bf4d-854ca8131387\\plans/map_integration_plan.md. Here is the updated code:\n# Kế Hoạch Chuyển Đổi: AI Tour Guide -> Bản Đồ Tương Tác & Thuyết Minh Chuyên Sâu\r\n\r\n## 1. Bối cảnh & Mục tiêu (Background & Motivation)\r\nỨng dụng hiện tại đang hoạt động dưới dạng một Chatbot thuần túy. Yêu cầu mới chuyển đổi ứng dụng thành một **Hướng dẫn viên du lịch tương tác dựa trên vị trí (Location-aware Interactive Guide)**. \r\n\r\nHệ thống sẽ cung cấp:\r\n- Danh sách các địa điểm (locations) có sẵn.\r\n- **Bản đồ nội bộ tương tác (Vector/Tile Map)** kết hợp định vị GPS thực tế (Real On-site GPS).\r\n- Hệ thống tìm đường (Pathfinding/Routing) giữa vị trí hiện tại và điểm đến được chọn.\r\n- Luồng âm thanh chỉ đường tuần tự.\r\n- Chế độ **Thuyết minh chuyên sâu (Deep-dive Storytelling)** khi đến nơi, hoạt động như một hướng dẫn viên thực thụ (đề xuất chủ đề, kể chuyện tương tác, trả lời câu hỏi).\r\n\r\n## 2. Phạm vi & Tác động (Scope & Impact)\r\n\r\nSự thay đổi này tác động lớn đến cả Frontend và Backend:\r\n- **Frontend:** Cần tích hợp thư viện bản đồ (như Leaflet.js hoặc Mapbox GL JS), xử lý Web Geolocation API, và thiết kế lại luồng UI/UX (Màn hình chính -> Bản đồ -> Chế độ dẫn đường -> Chế độ Thuyết minh).\r\n- **Backend:** Cần thêm logic tìm đường (Routing Engine), quản lý tọa độ/polygon của bản đồ nội bộ, và nâng cấp Agent (Orchestrator) để hỗ trợ \"State\" dẫn đường và \"State\" thuyết minh sâu.\r\n- **Dữ liệu (Database):** Mở rộng bảng `Location` và `Artifact` để lưu trữ tọa độ GeoJSON, các node/edge cho đồ thị tìm đường (Path Graph).\r\n\r\n## 3. Kiến trúc Đề xuất (Proposed Solution)\r\n\r\n### 3.1. Frontend (React + Vite)\r\n- **Thư viện Bản đồ:** Sử dụng `React-Leaflet` (mã nguồn mở, dễ tích hợp custom vector/tiles) hoặc `Mapbox GL JS` (mượt mà, phù hợp vector map phức tạp).\r\n- **Định vị (Geolocation):** Sử dụng `navigator.geolocation.watchPosition` để liên tục cập nhật vị trí người dùng.\r\n- **Biến đổi Tọa độ (Coordinate Mapping):** Nếu bản đồ nội bộ không khớp hoàn hảo với GPS chuẩn, cần một hàm nội suy (Affine Transformation) ở Frontend hoặc Backend để map từ `[vĩ độ, kinh độ GPS]` sang `[x, y bản đồ nội bộ]`.\r\n- **UI States:**\r\n  - `LocationList`: Danh sách địa điểm tham quan.\r\n  - `MapExplore`: Xem bản đồ, vị trí hiện tại (Blue dot), các điểm tham quan (Pins).\r\n  - `Navigating`: Chế độ dẫn đường (hiển thị path, phát audio chỉ đường).\r\n  - `StoryTelling`: Chế độ thuyết minh chuyên sâu khi đã tới nơi (hiển thị hình ảnh hiện vật, audio guide, chat bổ sung).\r\n\r\n### 3.2. Backend & Dữ liệu (FastAPI + PostgreSQL)\r\n- **Geospatial Data:** Sử dụng `PostGIS` (extension của PostgreSQL) hoặc lưu trữ tọa độ chuẩn dạng JSON (GeoJSON) nếu map nhỏ gọn.\r\n- **Routing Engine (Tìm đường):**\r\n  - Xây dựng một đồ thị (Graph) các đường đi nội bộ hợp lệ (Nodes & Edges). Có thể dùng script `build_graph.py` hiện tại làm nền tảng.\r\n  - Áp dụng thuật toán Dijkstra hoặc A* để tìm đường ngắn nhất.\r\n  - Chuyển đổi tuyến đường (Path) thành tập hợp các chỉ dẫn văn bản (ví dụ: \"Đi thẳng 20 mét, rẽ trái tại khu vực A\").\r\n- **Voice Orchestrator (Nâng cấp):**\r\n  - State 1: **Chỉ đường (Navigation Agent):** Đọc hướng dẫn tìm đường qua TTS.\r\n  - State 2: **Đề xuất (Hooking Agent):** Khi GPS nhận diện người dùng đã đến gần (radius < 5m), kích hoạt câu hỏi: *\"Bạn đã đến Cổng Ngọ Môn, bạn có muốn nghe tôi kể về lịch sử xây dựng của nó không?\"*\r\n  - State 3: **Thuyết minh (Storytelling Agent):** Lấy dữ liệu RAG sâu về hiện vật, chia nhỏ nội dung thành các đoạn hấp dẫn thay vì đọc một bài text dài, kết hợp hỏi đáp tương tác.\r\n\r\n## 4. Các Bước Triển Khai (Phased Implementation Plan)\r\n\r\n### Phase 1: Chuẩn bị Dữ liệu Bản đồ & Routing (Backend/Data)\r\n1. **Thiết kế Cấu trúc Dữ liệu Bản đồ:** Mở rộng DB để lưu tọa độ `(lat, lng)` cho các `Location` và `Artifact`.\r\n2. **Xây dựng Đồ thị Tìm đường:** Xác định các điểm nối (waypoints) trên bản đồ nội bộ để tạo Graph. Có thể lưu bằng bảng Nodes và Edges trong DB.\r\n3. **API Routing:** Viết API endpoint `/api/v1/map/route` nhận vị trí hiện tại và điểm đến, trả về đường dẫn (Array of coordinates) và Text chỉ dẫn dạng Turn-by-Turn.\r\n\r\n### Phase 2: Tích hợp Bản đồ vào Frontend\r\n1. Cài đặt thư viện `leaflet` và `react-leaflet`.\r\n2. Hiển thị Bản đồ nội bộ (Render custom vector/tiles) lên giao diện bằng một Component mới (ví dụ: `MapExplore.jsx`).\r\n3. Tích hợp Web Geolocation API để hiển thị vị trí người dùng theo thời gian thực.\r\n4. Viết hàm nội suy (Mapping function) để khớp tọa độ GPS thực tế với Bản đồ thiết kế (nếu cần xử lý độ lệch).\r\n\r\n### Phase 3: Luồng Dẫn đường (Navigation & Voice)\r\n1. Thêm tính năng chọn điểm đến trên bản đồ. Giao tiếp với API Routing.\r\n2. Vẽ đường đi (Polyline) trên bản đồ.\r\n3. Liên kết với `EdgeTTSProvider` hiện tại để đọc các bước chỉ đường mỗi khi GPS báo người dùng đi qua một node mới trên Graph.\r\n\r\n### Phase 4: Chế độ Thuyết minh Chuyên sâu (Storytelling Agent)\r\n1. **Trigger theo Vị trí (Geofencing):** Khi vị trí người dùng nằm trong bán kính (vd: < 5m) của điểm đến, Frontend báo Backend.\r\n2. **Nâng cấp LLM System Prompt:** Cập nhật `prompt_templates.py` bổ sung hệ thống Prompt mới cho vai trò \"Hướng dẫn viên thực thụ\" - giọng điệu kể chuyện hấp dẫn, gợi mở câu hỏi.\r\n3. **Tích hợp UI:** Hiển thị Popup/Panel Thuyết minh chuyên sâu khi đến nơi, cho phép phát Audio tự động, hiển thị ảnh chất lượng cao và giao diện Chat để đào sâu thông tin.\r\n\r\n## 5. Alternatives Considered (Các Lựa chọn Thay thế)\r\n- **Map hiển thị:** Thay vì Vector Map (như GeoJSON) có thể tốn thời gian dựng, có thể sử dụng **Image Overlay trên Leaflet** (Map một ảnh tĩnh sơ đồ nội bộ chất lượng cao khớp 4 góc với tọa độ GPS thực tế). Rất tốt cho proof-of-concept.\r\n- **Routing Engine:** Thay vì triển khai A* phức tạp trên Backend, có thể đóng gói file `graph.json` và dùng `turf.js` hoặc custom logic pathfinding ngay tại Frontend để giảm tải độ trễ (latency).\r\n\r\n## 6. Xác nhận & Kiểm tra (Verification)\r\n- **Test GPS Mapping:** Chạy Web trên điện thoại thực tế hoặc dùng công cụ giả lập GPS để kiểm tra hiển thị Blue dot.\r\n- **Test Pathfinding:** Kiểm tra xem các tuyến đường vẽ ra có tránh được vật cản và có hướng dẫn audio chính xác không.\r\n- **Test Workflow:** Mô phỏng đi bộ đến gần hiện vật xem trigger \"Thuyết minh chuyên sâu\" có nhảy đúng lúc không."
  }
}
```

---

## MODEL ✨

Dựa trên các lựa chọn của bạn (sử dụng Bản đồ tương tác, dùng GPS thật, và yêu cầu tính toán đường đi), tôi đã soạn thảo bản kế hoạch chi tiết dưới đây. 

Kế hoạch này vạch ra phương hướng tốt nhất để chuyển đổi ứng dụng hiện tại thành một ứng dụng điều hướng thực tế kết hợp thuyết minh thông minh.

Dưới đây là nội dung toàn bộ kế hoạch:

# Kế Hoạch Chuyển Đổi: AI Tour Guide -> Bản Đồ Tương Tác & Thuyết Minh Chuyên Sâu

## 1. Bối cảnh & Mục tiêu (Background & Motivation)
Ứng dụng hiện tại đang hoạt động dưới dạng một Chatbot thuần túy. Yêu cầu mới chuyển đổi ứng dụng thành một **Hướng dẫn viên du lịch tương tác dựa trên vị trí (Location-aware Interactive Guide)**. 

Hệ thống sẽ cung cấp:
- Danh sách các địa điểm (locations) có sẵn.
- **Bản đồ nội bộ tương tác (Vector/Tile Map)** kết hợp định vị GPS thực tế (Real On-site GPS).
- Hệ thống tìm đường (Pathfinding/Routing) giữa vị trí hiện tại và điểm đến được chọn.
- Luồng âm thanh chỉ đường tuần tự.
- Chế độ **Thuyết minh chuyên sâu (Deep-dive Storytelling)** khi đến nơi, hoạt động như một hướng dẫn viên thực thụ (đề xuất chủ đề, kể chuyện tương tác, trả lời câu hỏi).

## 2. Phạm vi & Tác động (Scope & Impact)

Sự thay đổi này tác động lớn đến cả Frontend và Backend:
- **Frontend:** Cần tích hợp thư viện bản đồ (như Leaflet.js hoặc Mapbox GL JS), xử lý Web Geolocation API, và thiết kế lại luồng UI/UX (Màn hình chính -> Bản đồ -> Chế độ dẫn đường -> Chế độ Thuyết minh).
- **Backend:** Cần thêm logic tìm đường (Routing Engine), quản lý tọa độ/polygon của bản đồ nội bộ, và nâng cấp Agent (Orchestrator) để hỗ trợ "State" dẫn đường và "State" thuyết minh sâu.
- **Dữ liệu (Database):** Mở rộng bảng `Location` và `Artifact` để lưu trữ tọa độ GeoJSON, các node/edge cho đồ thị tìm đường (Path Graph).

## 3. Kiến trúc Đề xuất (Proposed Solution)

### 3.1. Frontend (React + Vite)
- **Thư viện Bản đồ:** Sử dụng `React-Leaflet` (mã nguồn mở, dễ tích hợp custom vector/tiles) hoặc `Mapbox GL JS` (mượt mà, phù hợp vector map phức tạp).
- **Định vị (Geolocation):** Sử dụng `navigator.geolocation.watchPosition` để liên tục cập nhật vị trí người dùng.
- **Biến đổi Tọa độ (Coordinate Mapping):** Nếu bản đồ nội bộ không khớp hoàn hảo với GPS chuẩn, cần một hàm nội suy (Affine Transformation) ở Frontend hoặc Backend để map từ `[vĩ độ, kinh độ GPS]` sang `[x, y bản đồ nội bộ]`.
- **UI States:**
  - `LocationList`: Danh sách địa điểm tham quan.
  - `MapExplore`: Xem bản đồ, vị trí hiện tại (Blue dot), các điểm tham quan (Pins).
  - `Navigating`: Chế độ dẫn đường (hiển thị path, phát audio chỉ đường).
  - `StoryTelling`: Chế độ thuyết minh chuyên sâu khi đã tới nơi (hiển thị hình ảnh hiện vật, audio guide, chat bổ sung).

### 3.2. Backend & Dữ liệu (FastAPI + PostgreSQL)
- **Geospatial Data:** Sử dụng `PostGIS` (extension của PostgreSQL) hoặc lưu trữ tọa độ chuẩn dạng JSON (GeoJSON) nếu map nhỏ gọn.
- **Routing Engine (Tìm đường):**
  - Xây dựng một đồ thị (Graph) các đường đi nội bộ hợp lệ (Nodes & Edges). Có thể dùng script `build_graph.py` hiện tại làm nền tảng.
  - Áp dụng thuật toán Dijkstra hoặc A* để tìm đường ngắn nhất.
  - Chuyển đổi tuyến đường (Path) thành tập hợp các chỉ dẫn văn bản (ví dụ: "Đi thẳng 20 mét, rẽ trái tại khu vực A").
- **Voice Orchestrator (Nâng cấp):**
  - State 1: **Chỉ đường (Navigation Agent):** Đọc hướng dẫn tìm đường qua TTS.
  - State 2: **Đề xuất (Hooking Agent):** Khi GPS nhận diện người dùng đã đến gần (radius < 5m), kích hoạt câu hỏi: *"Bạn đã đến Cổng Ngọ Môn, bạn có muốn nghe tôi kể về lịch sử xây dựng của nó không?"*
  - State 3: **Thuyết minh (Storytelling Agent):** Lấy dữ liệu RAG sâu về hiện vật, chia nhỏ nội dung thành các đoạn hấp dẫn thay vì đọc một bài text dài, kết hợp hỏi đáp tương tác.

## 4. Các Bước Triển Khai (Phased Implementation Plan)

### Phase 1: Chuẩn bị Dữ liệu Bản đồ & Routing (Backend/Data)
1. **Thiết kế Cấu trúc Dữ liệu Bản đồ:** Mở rộng DB để lưu tọa độ `(lat, lng)` cho các `Location` và `Artifact`.
2. **Xây dựng Đồ thị Tìm đường:** Xác định các điểm nối (waypoints) trên bản đồ nội bộ để tạo Graph. Có thể lưu bằng bảng Nodes và Edges trong DB.
3. **API Routing:** Viết API endpoint `/api/v1/map/route` nhận vị trí hiện tại và điểm đến, trả về đường dẫn (Array of coordinates) và Text chỉ dẫn dạng Turn-by-Turn.

### Phase 2: Tích hợp Bản đồ vào Frontend
1. Cài đặt thư viện `leaflet` và `react-leaflet`.
2. Hiển thị Bản đồ nội bộ (Render custom vector/tiles) lên giao diện bằng một Component mới (ví dụ: `MapExplore.jsx`).
3. Tích hợp Web Geolocation API để hiển thị vị trí người dùng theo thời gian thực.
4. Viết hàm nội suy (Mapping function) để khớp tọa độ GPS thực tế với Bản đồ thiết kế (nếu cần xử lý độ lệch).

### Phase 3: Luồng Dẫn đường (Navigation & Voice)
1. Thêm tính năng chọn điểm đến trên bản đồ. Giao tiếp với API Routing.
2. Vẽ đường đi (Polyline) trên bản đồ.
3. Liên kết với `EdgeTTSProvider` hiện tại để đọc các bước chỉ đường mỗi khi GPS báo người dùng đi qua một node mới trên Graph.

### Phase 4: Chế độ Thuyết minh Chuyên sâu (Storytelling Agent)
1. **Trigger theo Vị trí (Geofencing):** Khi vị trí người dùng nằm trong bán kính (vd: < 5m) của điểm đến, Frontend báo Backend.
2. **Nâng cấp LLM System Prompt:** Cập nhật `prompt_templates.py` bổ sung hệ thống Prompt mới cho vai trò "Hướng dẫn viên thực thụ" - giọng điệu kể chuyện hấp dẫn, gợi mở câu hỏi.
3. **Tích hợp UI:** Hiển thị Popup/Panel Thuyết minh chuyên sâu khi đến nơi, cho phép phát Audio tự động, hiển thị ảnh chất lượng cao và giao diện Chat để đào sâu thông tin.

## 5. Alternatives Considered (Các Lựa chọn Thay thế)
- **Map hiển thị:** Thay vì Vector Map (như GeoJSON) có thể tốn thời gian dựng, có thể sử dụng **Image Overlay trên Leaflet** (Map một ảnh tĩnh sơ đồ nội bộ chất lượng cao khớp 4 góc với tọa độ GPS thực tế). Rất tốt cho proof-of-concept.
- **Routing Engine:** Thay vì triển khai A* phức tạp trên Backend, có thể đóng gói file `graph.json` và dùng `turf.js` hoặc custom logic pathfinding ngay tại Frontend để giảm tải độ trễ (latency).

## 6. Xác nhận & Kiểm tra (Verification)
- **Test GPS Mapping:** Chạy Web trên điện thoại thực tế hoặc dùng công cụ giả lập GPS để kiểm tra hiển thị Blue dot.
- **Test Pathfinding:** Kiểm tra xem các tuyến đường vẽ ra có tránh được vật cản và có hướng dẫn audio chính xác không.
- **Test Workflow:** Mô phỏng đi bộ đến gần hiện vật xem trigger "Thuyết minh chuyên sâu" có nhảy đúng lúc không.

---
Bạn có đồng ý với hướng tiếp cận và lộ trình như trên không? Nếu ok, tôi sẽ sử dụng `exit_plan_mode` để chúng ta có thể chuyển sang bước triển khai thực tế.

---

## USER 🧑‍💻

tôi muốn làm đơn giản lại là chỉ dùng gps để xác định điểm đầu, còn những điểm sau chỉ cần nhấn vào nó trên bản đồ thì nó sẽ thực hiện hướng dẫn đi và các thao tác sau, và song song cũng có nút set lại vị trí hiện tại để bấm vào đó thì ta có thể chọn vào vị trí hiện tại của ta trên bản đồ hiện tai trong TH gps sai hay ta di chuyển mà không thông báo cho phần mềm, nó có 2 lựa chọn, 1 là tự điều chỉnh lại vị trí hiện tại thông qua gps 2 là tự chọn. hãy bổ sung và sửa chữa kế hoạch đi

---

## MODEL ✨

**Tool Command**:
```json
{
  "name": "update_topic",
  "args": {
    "summary": "I will revise the map integration plan based on the user's feedback. The new approach simplifies GPS usage: it uses GPS for the initial position, but allows users to tap points on the map for subsequent routing. It also introduces a manual override for the current position (a \"set current location\" button with options to auto-update via GPS or manually tap on the map). I will update the `.md` plan file to reflect these changes in the UI state and routing logic.",
    "strategic_intent": "Updating the implementation plan to reflect a simplified hybrid approach for location tracking and navigation.",
    "title": "Refining the Map Integration Plan"
  },
  "id": "update_topic__update_topic_1780166868879_0"
}
```**Tool Command**:
```json
{
  "name": "replace",
  "args": {
    "file_path": "C:\\Users\\ADMIN\\.gemini\\tmp\\ai-tour-guide-2\\cecbaae4-0cf5-4f56-bf4d-854ca8131387\\plans/map_integration_plan.md",
    "allow_multiple": false,
    "instruction": "Update the UI states and navigation flow to reflect a hybrid GPS/manual location system. Remove continuous GPS tracking (watchPosition) and replace it with a get-current-location request + manual map tap fallback. Update the Storytelling trigger to be manual (button click) rather than purely automatic geofencing.",
    "new_string": "- **Bản đồ nội bộ tương tác (Vector/Tile Map hoặc Image Overlay).**\n- Lấy vị trí ban đầu bằng GPS, nhưng cho phép **người dùng tự chọn vị trí hiện tại** trên bản đồ (Hybrid Location System) để xử lý trường hợp GPS sai số hoặc di chuyển không báo trước.\n- Hệ thống tìm đường (Pathfinding/Routing) giữa vị trí hiện tại đã xác định và điểm đến được chọn.\n- Luồng âm thanh chỉ đường tuần tự.\n- Chế độ **Thuyết minh chuyên sâu (Deep-dive Storytelling)** khi đến nơi, hoạt động như một hướng dẫn viên thực thụ (đề xuất chủ đề, kể chuyện tương tác, trả lời câu hỏi).\n\n## 2. Phạm vi & Tác động (Scope & Impact)\n\nSự thay đổi này tác động lớn đến cả Frontend và Backend:\n- **Frontend:** Tích hợp bản đồ (Leaflet), thiết kế tính năng chọn/cập nhật vị trí bằng tay và GPS, và luồng UI mới (Màn hình chính -> Bản đồ -> Dẫn đường -> Thuyết minh).\n- **Backend:** Thêm API tìm đường (Routing Engine), quản lý tọa độ nội bộ. Nâng cấp Agent để hỗ trợ chuyển đổi từ \"State\" dẫn đường sang \"State\" thuyết minh sâu.\n- **Dữ liệu (Database):** Thêm tọa độ (lat/lng) cho các `Location` và `Artifact`, xây dựng đồ thị đường đi (Path Graph).\n\n## 3. Kiến trúc Đề xuất (Proposed Solution)\n\n### 3.1. Frontend (React + Vite)\n- **Thư viện Bản đồ:** Sử dụng `React-Leaflet`.\n- **Định vị (Hybrid Geolocation):**\n  - Khởi tạo: Lấy vị trí bằng `navigator.geolocation.getCurrentPosition()`.\n  - Nút \"Cập nhật vị trí\": Cung cấp 2 tùy chọn: (1) Tự động lấy lại GPS hiện tại, (2) Chạm vào bản đồ để \"Ghim\" vị trí thủ công.\n- **UI States:**\n  - `MapExplore`: Xem bản đồ, vị trí hiện tại (Blue dot/Pin có thể di chuyển), các điểm tham quan (Pins).\n  - `Navigating`: Chế độ dẫn đường. Người dùng chọn điểm B, hệ thống lấy điểm A (vị trí hiện tại), vẽ đường đi và hiện nút \"Bắt đầu đi\".\n  - `StoryTelling`: Khi người dùng nhấn nút \"Tôi đã đến nơi\" (hoặc chọn trực tiếp hiện vật), mở chế độ thuyết minh chuyên sâu.\n\n### 3.2. Backend & Dữ liệu (FastAPI + PostgreSQL)\n- **Geospatial Data:** Lưu tọa độ chuẩn hoặc tọa độ pixel/tương đối (nếu dùng Image Overlay) cho các địa điểm.\n- **Routing Engine (Tìm đường):**\n  - Xây dựng đồ thị (Graph) đường đi.\n  - Áp dụng thuật toán Dijkstra/A* (có thể implement ở Backend trả về API, hoặc dùng thư viện Frontend nếu data nhỏ).\n- **Voice Orchestrator (Nâng cấp):**\n  - **Dẫn đường:** Text-to-Speech đọc hướng dẫn tĩnh (vd: \"Hãy đi theo đường màu xanh, quẹo trái ở ngã tư...\").\n  - **Thuyết minh:** Agent tương tác. Khi Frontend báo đã đến nơi, Agent chủ động hỏi: *\"Bạn đã đến nơi, bạn có muốn nghe tôi kể về lịch sử của nó không?\"* và bắt đầu RAG chuyên sâu.\n\n## 4. Các Bước Triển Khai (Phased Implementation Plan)\n\n### Phase 1: Chuẩn bị Bản đồ & Routing (Data/Backend)\n1. **Thiết lập Bản đồ:** Xác định tọa độ các điểm trên sơ đồ.\n2. **Xây dựng Đồ thị Tìm đường:** Tạo danh sách Nodes/Edges các lối đi hợp lệ.\n3. **API (Tùy chọn):** Nếu xử lý routing ở Backend, viết API `/api/v1/map/route` nhận (A, B) và trả về Path. (Nếu làm ở Frontend thì bỏ qua bước này).\n\n### Phase 2: Tích hợp Bản đồ & Vị trí (Frontend)\n1. Tích hợp `react-leaflet`. Hiển thị sơ đồ (dùng Image Overlay hoặc GeoJSON).\n2. Xây dựng logic **Hybrid Location**:\n   - Nút lấy GPS (getCurrentPosition).\n   - Chế độ \"Chọn vị trí trên bản đồ\" (click để thả pin).\n3. Hiển thị các điểm tham quan (Markers) có thể click.\n\n### Phase 3: Luồng Dẫn đường (Routing & UI)\n1. Khi click vào một điểm tham quan, gọi hàm tìm đường từ (Vị trí hiện tại) đến (Điểm tham quan).\n2. Vẽ đường đi (Polyline).\n3. Đọc Audio chỉ đường tổng quan bằng `EdgeTTSProvider`.\n\n### Phase 4: Chế độ Thuyết minh Chuyên sâu (Storytelling Agent)\n1. Thêm nút **\"Tôi đã đến nơi / Nghe thuyết minh\"** tại điểm tham quan.\n2. Nâng cấp LLM System Prompt để đóng vai \"Hướng dẫn viên thực thụ\", chia nhỏ nội dung RAG thành các đoạn giao tiếp ngắn, gợi mở.\n3. Hiển thị giao diện Thuyết minh (phát audio tự động, hiển thị ảnh chất lượng cao, chat tương tác).",
    "old_string": "- **Bản đồ nội bộ tương tác (Vector/Tile Map)** kết hợp định vị GPS thực tế (Real On-site GPS).\n- Hệ thống tìm đường (Pathfinding/Routing) giữa vị trí hiện tại và điểm đến được chọn.\n- Luồng âm thanh chỉ đường tuần tự.\n- Chế độ **Thuyết minh chuyên sâu (Deep-dive Storytelling)** khi đến nơi, hoạt động như một hướng dẫn viên thực thụ (đề xuất chủ đề, kể chuyện tương tác, trả lời câu hỏi).\n\n## 2. Phạm vi & Tác động (Scope & Impact)\n\nSự thay đổi này tác động lớn đến cả Frontend và Backend:\n- **Frontend:** Cần tích hợp thư viện bản đồ (như Leaflet.js hoặc Mapbox GL JS), xử lý Web Geolocation API, và thiết kế lại luồng UI/UX (Màn hình chính -> Bản đồ -> Chế độ dẫn đường -> Chế độ Thuyết minh).\n- **Backend:** Cần thêm logic tìm đường (Routing Engine), quản lý tọa độ/polygon của bản đồ nội bộ, và nâng cấp Agent (Orchestrator) để hỗ trợ \"State\" dẫn đường và \"State\" thuyết minh sâu.\n- **Dữ liệu (Database):** Mở rộng bảng `Location` và `Artifact` để lưu trữ tọa độ GeoJSON, các node/edge cho đồ thị tìm đường (Path Graph).\n\n## 3. Kiến trúc Đề xuất (Proposed Solution)\n\n### 3.1. Frontend (React + Vite)\n- **Thư viện Bản đồ:** Sử dụng `React-Leaflet` (mã nguồn mở, dễ tích hợp custom vector/tiles) hoặc `Mapbox GL JS` (mượt mà, phù hợp vector map phức tạp).\n- **Định vị (Geolocation):** Sử dụng `navigator.geolocation.watchPosition` để liên tục cập nhật vị trí người dùng.\n- **Biến đổi Tọa độ (Coordinate Mapping):** Nếu bản đồ nội bộ không khớp hoàn hảo với GPS chuẩn, cần một hàm nội suy (Affine Transformation) ở Frontend hoặc Backend để map từ `[vĩ độ, kinh độ GPS]` sang `[x, y bản đồ nội bộ]`.\n- **UI States:**\n  - `LocationList`: Danh sách địa điểm tham quan.\n  - `MapExplore`: Xem bản đồ, vị trí hiện tại (Blue dot), các điểm tham quan (Pins).\n  - `Navigating`: Chế độ dẫn đường (hiển thị path, phát audio chỉ đường).\n  - `StoryTelling`: Chế độ thuyết minh chuyên sâu khi đã tới nơi (hiển thị hình ảnh hiện vật, audio guide, chat bổ sung).\n\n### 3.2. Backend & Dữ liệu (FastAPI + PostgreSQL)\n- **Geospatial Data:** Sử dụng `PostGIS` (extension của PostgreSQL) hoặc lưu trữ tọa độ chuẩn dạng JSON (GeoJSON) nếu map nhỏ gọn.\n- **Routing Engine (Tìm đường):**\n  - Xây dựng một đồ thị (Graph) các đường đi nội bộ hợp lệ (Nodes & Edges). Có thể dùng script `build_graph.py` hiện tại làm nền tảng.\n  - Áp dụng thuật toán Dijkstra hoặc A* để tìm đường ngắn nhất.\n  - Chuyển đổi tuyến đường (Path) thành tập hợp các chỉ dẫn văn bản (ví dụ: \"Đi thẳng 20 mét, rẽ trái tại khu vực A\").\n- **Voice Orchestrator (Nâng cấp):**\n  - State 1: **Chỉ đường (Navigation Agent):** Đọc hướng dẫn tìm đường qua TTS.\n  - State 2: **Đề xuất (Hooking Agent):** Khi GPS nhận diện người dùng đã đến gần (radius < 5m), kích hoạt câu hỏi: *\"Bạn đã đến Cổng Ngọ Môn, bạn có muốn nghe tôi kể về lịch sử xây dựng của nó không?\"*\n  - State 3: **Thuyết minh (Storytelling Agent):** Lấy dữ liệu RAG sâu về hiện vật, chia nhỏ nội dung thành các đoạn hấp dẫn thay vì đọc một bài text dài, kết hợp hỏi đáp tương tác.\n\n## 4. Các Bước Triển Khai (Phased Implementation Plan)\n\n### Phase 1: Chuẩn bị Dữ liệu Bản đồ & Routing (Backend/Data)\n1. **Thiết kế Cấu trúc Dữ liệu Bản đồ:** Mở rộng DB để lưu tọa độ `(lat, lng)` cho các `Location` và `Artifact`.\n2. **Xây dựng Đồ thị Tìm đường:** Xác định các điểm nối (waypoints) trên bản đồ nội bộ để tạo Graph. Có thể lưu bằng bảng Nodes và Edges trong DB.\n3. **API Routing:** Viết API endpoint `/api/v1/map/route` nhận vị trí hiện tại và điểm đến, trả về đường dẫn (Array of coordinates) và Text chỉ dẫn dạng Turn-by-Turn.\n\n### Phase 2: Tích hợp Bản đồ vào Frontend\n1. Cài đặt thư viện `leaflet` và `react-leaflet`.\n2. Hiển thị Bản đồ nội bộ (Render custom vector/tiles) lên giao diện bằng một Component mới (ví dụ: `MapExplore.jsx`).\n3. Tích hợp Web Geolocation API để hiển thị vị trí người dùng theo thời gian thực.\n4. Viết hàm nội suy (Mapping function) để khớp tọa độ GPS thực tế với Bản đồ thiết kế (nếu cần xử lý độ lệch).\n\n### Phase 3: Luồng Dẫn đường (Navigation & Voice)\n1. Thêm tính năng chọn điểm đến trên bản đồ. Giao tiếp với API Routing.\n2. Vẽ đường đi (Polyline) trên bản đồ.\n3. Liên kết với `EdgeTTSProvider` hiện tại để đọc các bước chỉ đường mỗi khi GPS báo người dùng đi qua một node mới trên Graph.\n\n### Phase 4: Chế độ Thuyết minh Chuyên sâu (Storytelling Agent)\n1. **Trigger theo Vị trí (Geofencing):** Khi vị trí người dùng nằm trong bán kính (vd: < 5m) của điểm đến, Frontend báo Backend.\n2. **Nâng cấp LLM System Prompt:** Cập nhật `prompt_templates.py` bổ sung hệ thống Prompt mới cho vai trò \"Hướng dẫn viên thực thụ\" - giọng điệu kể chuyện hấp dẫn, gợi mở câu hỏi.\n3. **Tích hợp UI:** Hiển thị Popup/Panel Thuyết minh chuyên sâu khi đến nơi, cho phép phát Audio tự động, hiển thị ảnh chất lượng cao và giao diện Chat để đào sâu thông tin."
  },
  "id": "replace__replace_1780166869980_1"
}
```

---

## USER 🧑‍💻

**Tool Response**:
```json
{
  "id": "update_topic__update_topic_1780166868879_0",
  "name": "update_topic",
  "response": {
    "output": "Current topic: \"Refining the Map Integration Plan\"\nTopic summary: I will revise the map integration plan based on the user's feedback. The new approach simplifies GPS usage: it uses GPS for the initial position, but allows users to tap points on the map for subsequent routing. It also introduces a manual override for the current position (a \"set current location\" button with options to auto-update via GPS or manually tap on the map). I will update the `.md` plan file to reflect these changes in the UI state and routing logic.\n\nStrategic Intent: Updating the implementation plan to reflect a simplified hybrid approach for location tracking and navigation."
  }
}
```**Tool Response**:
```json
{
  "id": "replace__replace_1780166869980_1",
  "name": "replace",
  "response": {
    "output": "Successfully modified file: C:\\Users\\ADMIN\\.gemini\\tmp\\ai-tour-guide-2\\cecbaae4-0cf5-4f56-bf4d-854ca8131387\\plans/map_integration_plan.md (1 replacements). Here is the updated code:\n# Kế Hoạch Chuyển Đổi: AI Tour Guide -> Bản Đồ Tương Tác & Thuyết Minh Chuyên Sâu\n\n## 1. Bối cảnh & Mục tiêu (Background & Motivation)\nỨng dụng hiện tại đang hoạt động dưới dạng một Chatbot thuần túy. Yêu cầu mới chuyển đổi ứng dụng thành một **Hướng dẫn viên du lịch tương tác dựa trên vị trí (Location-aware Interactive Guide)**. \n\nHệ thống sẽ cung cấp:\n- Danh sách các địa điểm (locations) có sẵn.\n- **Bản đồ nội bộ tương tác (Vector/Tile Map hoặc Image Overlay).**\n- Lấy vị trí ban đầu bằng GPS, nhưng cho phép **người dùng tự chọn vị trí hiện tại** trên bản đồ (Hybrid Location System) để xử lý trường hợp GPS sai số hoặc di chuyển không báo trước.\n- Hệ thống tìm đường (Pathfinding/Routing) giữa vị trí hiện tại đã xác định và điểm đến được chọn.\n- Luồng âm thanh chỉ đường tuần tự.\n- Chế độ **Thuyết minh chuyên sâu (Deep-dive Storytelling)** khi đến nơi, hoạt động như một hướng dẫn viên thực thụ (đề xuất chủ đề, kể chuyện tương tác, trả lời câu hỏi).\n\n## 2. Phạm vi & Tác động (Scope & Impact)\n\nSự thay đổi này tác động lớn đến cả Frontend và Backend:\n- **Frontend:** Tích hợp bản đồ (Leaflet), thiết kế tính năng chọn/cập nhật vị trí bằng tay và GPS, và luồng UI mới (Màn hình chính -> Bản đồ -> Dẫn đường -> Thuyết minh).\n- **Backend:** Thêm API tìm đường (Routing Engine), quản lý tọa độ nội bộ. Nâng cấp Agent để hỗ trợ chuyển đổi từ \"State\" dẫn đường sang \"State\" thuyết minh sâu.\n- **Dữ liệu (Database):** Thêm tọa độ (lat/lng) cho các `Location` và `Artifact`, xây dựng đồ thị đường đi (Path Graph).\n\n## 3. Kiến trúc Đề xuất (Proposed Solution)\n\n### 3.1. Frontend (React + Vite)\n- **Thư viện Bản đồ:** Sử dụng `React-Leaflet`.\n- **Định vị (Hybrid Geolocation):**\n  - Khởi tạo: Lấy vị trí bằng `navigator.geolocation.getCurrentPosition()`.\n  - Nút \"Cập nhật vị trí\": Cung cấp 2 tùy chọn: (1) Tự động lấy lại GPS hiện tại, (2) Chạm vào bản đồ để \"Ghim\" vị trí thủ công.\n- **UI States:**\n  - `MapExplore`: Xem bản đồ, vị trí hiện tại (Blue dot/Pin có thể di chuyển), các điểm tham quan (Pins).\n  - `Navigating`: Chế độ dẫn đường. Người dùng chọn điểm B, hệ thống lấy điểm A (vị trí hiện tại), vẽ đường đi và hiện nút \"Bắt đầu đi\".\n  - `StoryTelling`: Khi người dùng nhấn nút \"Tôi đã đến nơi\" (hoặc chọn trực tiếp hiện vật), mở chế độ thuyết minh chuyên sâu.\n\n### 3.2. Backend & Dữ liệu (FastAPI + PostgreSQL)\n- **Geospatial Data:** Lưu tọa độ chuẩn hoặc tọa độ pixel/tương đối (nếu dùng Image Overlay) cho các địa điểm.\n- **Routing Engine (Tìm đường):**\n  - Xây dựng đồ thị (Graph) đường đi.\n  - Áp dụng thuật toán Dijkstra/A* (có thể implement ở Backend trả về API, hoặc dùng thư viện Frontend nếu data nhỏ).\n- **Voice Orchestrator (Nâng cấp):**\n  - **Dẫn đường:** Text-to-Speech đọc hướng dẫn tĩnh (vd: \"Hãy đi theo đường màu xanh, quẹo trái ở ngã tư...\").\n  - **Thuyết minh:** Agent tương tác. Khi Frontend báo đã đến nơi, Agent chủ động hỏi: *\"Bạn đã đến nơi, bạn có muốn nghe tôi kể về lịch sử của nó không?\"* và bắt đầu RAG chuyên sâu.\n\n## 4. Các Bước Triển Khai (Phased Implementation Plan)\n\n### Phase 1: Chuẩn bị Bản đồ & Routing (Data/Backend)\n1. **Thiết lập Bản đồ:** Xác định tọa độ các điểm trên sơ đồ.\n2. **Xây dựng Đồ thị Tìm đường:** Tạo danh sách Nodes/Edges các lối đi hợp lệ.\n3. **API (Tùy chọn):** Nếu xử lý routing ở Backend, viết API `/api/v1/map/route` nhận (A, B) và trả về Path. (Nếu làm ở Frontend thì bỏ qua bước này).\n\n### Phase 2: Tích hợp Bản đồ & Vị trí (Frontend)\n1. Tích hợp `react-leaflet`. Hiển thị sơ đồ (dùng Image Overlay hoặc GeoJSON).\n2. Xây dựng logic **Hybrid Location**:\n   - Nút lấy GPS (getCurrentPosition).\n   - Chế độ \"Chọn vị trí trên bản đồ\" (click để thả pin).\n3. Hiển thị các điểm tham quan (Markers) có thể click.\n\n### Phase 3: Luồng Dẫn đường (Routing & UI)\n1. Khi click vào một điểm tham quan, gọi hàm tìm đường từ (Vị trí hiện tại) đến (Điểm tham quan).\n2. Vẽ đường đi (Polyline).\n3. Đọc Audio chỉ đường tổng quan bằng `EdgeTTSProvider`.\n\n### Phase 4: Chế độ Thuyết minh Chuyên sâu (Storytelling Agent)\n1. Thêm nút **\"Tôi đã đến nơi / Nghe thuyết minh\"** tại điểm tham quan.\n2. Nâng cấp LLM System Prompt để đóng vai \"Hướng dẫn viên thực thụ\", chia nhỏ nội dung RAG thành các đoạn giao tiếp ngắn, gợi mở.\n3. Hiển thị giao diện Thuyết minh (phát audio tự động, hiển thị ảnh chất lượng cao, chat tương tác).\n\n## 5. Alternatives Considered (Các Lựa chọn Thay thế)\n- **Map hiển thị:** Thay vì Vector Map (như GeoJSON) có thể tốn thời gian dựng, có thể sử dụng **Image Overlay trên Leaflet** (Map một ảnh tĩnh sơ đồ nội bộ chất lượng cao khớp 4 góc với tọa độ GPS thực tế). Rất tốt cho proof-of-concept.\n- **Routing Engine:** Thay vì triển khai A* phức tạp trên Backend, có thể đóng gói file `graph.json` và dùng `turf.js` hoặc custom logic pathfinding ngay tại Frontend để giảm tải độ trễ (latency).\n\n## 6. Xác nhận & Kiểm tra (Verification)\n- **Test GPS Mapping:** Chạy Web trên điện thoại thực tế hoặc dùng công cụ giả lập GPS để kiểm tra hiển thị Blue dot.\n- **Test Pathfinding:** Kiểm tra xem các tuyến đường vẽ ra có tránh được vật cản và có hướng dẫn audio chính xác không.\n- **Test Workflow:** Mô phỏng đi bộ đến gần hiện vật xem trigger \"Thuyết minh chuyên sâu\" có nhảy đúng lúc không."
  }
}
```

---

## MODEL ✨

Tôi đã cập nhật lại kế hoạch theo hướng đơn giản và chủ động hơn cho người dùng (Hybrid Location System). Dưới đây là nội dung mới của kế hoạch:

# Kế Hoạch Chuyển Đổi: AI Tour Guide -> Bản Đồ Tương Tác & Thuyết Minh Chuyên Sâu

## 1. Bối cảnh & Mục tiêu (Background & Motivation)
Ứng dụng hiện tại đang hoạt động dưới dạng một Chatbot thuần túy. Yêu cầu mới chuyển đổi ứng dụng thành một **Hướng dẫn viên du lịch tương tác dựa trên vị trí (Location-aware Interactive Guide)**. 

Hệ thống sẽ cung cấp:
- Danh sách các địa điểm (locations) có sẵn.
- **Bản đồ nội bộ tương tác (Vector/Tile Map hoặc Image Overlay).**
- Lấy vị trí ban đầu bằng GPS, nhưng cho phép **người dùng tự chọn vị trí hiện tại** trên bản đồ (Hybrid Location System) để xử lý trường hợp GPS sai số hoặc di chuyển không báo trước.
- Hệ thống tìm đường (Pathfinding/Routing) giữa vị trí hiện tại đã xác định và điểm đến được chọn.
- Luồng âm thanh chỉ đường tuần tự.
- Chế độ **Thuyết minh chuyên sâu (Deep-dive Storytelling)** khi đến nơi, hoạt động như một hướng dẫn viên thực thụ (đề xuất chủ đề, kể chuyện tương tác, trả lời câu hỏi).

## 2. Phạm vi & Tác động (Scope & Impact)

Sự thay đổi này tác động lớn đến cả Frontend và Backend:
- **Frontend:** Tích hợp bản đồ (Leaflet), thiết kế tính năng chọn/cập nhật vị trí bằng tay và GPS, và luồng UI mới (Màn hình chính -> Bản đồ -> Dẫn đường -> Thuyết minh).
- **Backend:** Thêm API tìm đường (Routing Engine), quản lý tọa độ nội bộ. Nâng cấp Agent để hỗ trợ chuyển đổi từ "State" dẫn đường sang "State" thuyết minh sâu.
- **Dữ liệu (Database):** Thêm tọa độ (lat/lng) cho các `Location` và `Artifact`, xây dựng đồ thị đường đi (Path Graph).

## 3. Kiến trúc Đề xuất (Proposed Solution)

### 3.1. Frontend (React + Vite)
- **Thư viện Bản đồ:** Sử dụng `React-Leaflet`.
- **Định vị (Hybrid Geolocation):**
  - Khởi tạo: Lấy vị trí bằng `navigator.geolocation.getCurrentPosition()`.
  - Nút "Cập nhật vị trí": Cung cấp 2 tùy chọn: (1) Tự động lấy lại GPS hiện tại, (2) Chạm vào bản đồ để "Ghim" vị trí thủ công.
- **UI States:**
  - `MapExplore`: Xem bản đồ, vị trí hiện tại (Blue dot/Pin có thể di chuyển), các điểm tham quan (Pins).
  - `Navigating`: Chế độ dẫn đường. Người dùng chọn điểm B, hệ thống lấy điểm A (vị trí hiện tại), vẽ đường đi và hiện nút "Bắt đầu đi".
  - `StoryTelling`: Khi người dùng nhấn nút "Tôi đã đến nơi" (hoặc chọn trực tiếp hiện vật), mở chế độ thuyết minh chuyên sâu.

### 3.2. Backend & Dữ liệu (FastAPI + PostgreSQL)
- **Geospatial Data:** Lưu tọa độ chuẩn hoặc tọa độ pixel/tương đối (nếu dùng Image Overlay) cho các địa điểm.
- **Routing Engine (Tìm đường):**
  - Xây dựng đồ thị (Graph) đường đi.
  - Áp dụng thuật toán Dijkstra/A* (có thể implement ở Backend trả về API, hoặc dùng thư viện Frontend nếu data nhỏ).
- **Voice Orchestrator (Nâng cấp):**
  - **Dẫn đường:** Text-to-Speech đọc hướng dẫn tĩnh (vd: "Hãy đi theo đường màu xanh, quẹo trái ở ngã tư...").
  - **Thuyết minh:** Agent tương tác. Khi Frontend báo đã đến nơi, Agent chủ động hỏi: *"Bạn đã đến nơi, bạn có muốn nghe tôi kể về lịch sử của nó không?"* và bắt đầu RAG chuyên sâu.

## 4. Các Bước Triển Khai (Phased Implementation Plan)

### Phase 1: Chuẩn bị Bản đồ & Routing (Data/Backend)
1. **Thiết thiết lập Bản đồ:** Xác định tọa độ các điểm trên sơ đồ.
2. **Xây dựng Đồ thị Tìm đường:** Tạo danh sách Nodes/Edges các lối đi hợp lệ.
3. **API (Tùy chọn):** Nếu xử lý routing ở Backend, viết API `/api/v1/map/route` nhận (A, B) và trả về Path. (Nếu làm ở Frontend thì bỏ qua bước này).

### Phase 2: Tích hợp Bản đồ & Vị trí (Frontend)
1. Tích hợp `react-leaflet`. Hiển thị sơ đồ (dùng Image Overlay hoặc GeoJSON).
2. Xây dựng logic **Hybrid Location**:
   - Nút lấy GPS (getCurrentPosition).
   - Chế độ "Chọn vị trí trên bản đồ" (click để thả pin).
3. Hiển thị các điểm tham quan (Markers) có thể click.

### Phase 3: Luồng Dẫn đường (Routing & UI)
1. Khi click vào một điểm tham quan, gọi hàm tìm đường từ (Vị trí hiện tại) đến (Điểm tham quan).
2. Vẽ đường đi (Polyline).
3. Đọc Audio chỉ đường tổng quan bằng `EdgeTTSProvider`.

### Phase 4: Chế độ Thuyết minh Chuyên sâu (Storytelling Agent)
1. Thêm nút **"Tôi đã đến nơi / Nghe thuyết minh"** tại điểm tham quan.
2. Nâng cấp LLM System Prompt để đóng vai "Hướng dẫn viên thực thụ", chia nhỏ nội dung RAG thành các đoạn giao tiếp ngắn, gợi mở.
3. Hiển thị giao diện Thuyết minh (phát audio tự động, hiển thị ảnh chất lượng cao, chat tương tác).

---
Bạn kiểm tra xem luồng "Hybrid Location" với nút "Ghim thủ công" và nút "Tôi đã đến nơi" này đã đúng ý bạn chưa? Nếu bạn đồng ý, tôi sẽ `exit_plan_mode` để kết thúc quá trình lên kế hoạch.