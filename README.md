# AI Tour Guide

AI Tour Guide là web app hướng dẫn du lịch thông minh. Ứng dụng chạy trên trình duyệt, dùng React/Vite ở frontend và FastAPI ở backend để xử lý hội thoại, nhận diện ảnh, giọng nói, RAG theo dữ liệu hiện vật và đọc câu trả lời.

## Tính năng chính

- Trải nghiệm hướng dẫn tham quan tập trung vào người dùng.
- Hỏi đáp bằng text, ảnh upload/webcam và giọng nói.
- Nhận diện hiện vật bằng Gemini Vision.
- Tìm dữ liệu hiện vật trong PostgreSQL và trả lời nhanh từ DB/cache khi đủ thông tin.
- Gọi LLM Gemini/Groq khi cần diễn giải tự nhiên.
- Đọc câu trả lời bằng Web Speech API ở trình duyệt; backend chỉ cần STT cho input giọng nói.
- Ghi nhận phản hồi hữu ích/chưa đúng để cải thiện chất lượng câu trả lời.

## Cấu trúc

```text
backend/       FastAPI unified backend
frontend/      React + Vite web app
scripts/       Seed data PostgreSQL
docker/        PostgreSQL + backend compose
migrations/    Alembic config
docs/          Architecture và improvement plan
```

## Yêu cầu

- Python 3.10+
- Node.js 18+
- Docker Desktop nếu dùng PostgreSQL qua Docker
- API keys:
  - `GEMINI_API_KEY`
  - `GROQ_API_KEY`

## Chạy trên máy local

### 1. Tạo file môi trường

Tạo `.env` ở thư mục root:

```env
ENVIRONMENT=development
LOG_LEVEL=INFO
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_tour_guide
LLM_PROVIDER_ORDER=gemini,groq
GEMINI_TEXT_MODEL=gemini-2.5-flash
GEMINI_VISION_MODEL=gemini-2.5-flash
GROQ_LLM_MODEL=llama-3.3-70b-versatile
GROQ_STT_MODEL=whisper-large-v3
LLM_TEMPERATURE=0.6
LLM_MAX_TOKENS=2048
LLM_MAX_TOKENS_FOLLOWUP=800
```

### 2. Chạy PostgreSQL

```bash
cd docker
docker-compose up -d postgres
cd ..
```

### 3. Cài và chạy backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
cd ..
backend\.venv\Scripts\alembic upgrade head
backend\.venv\Scripts\python scripts\seed_data.py
cd backend
.venv\Scripts\python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Nếu backend log báo `function word_similarity(...) does not exist`, database chưa bật extension `pg_trgm`; chạy lại `backend\.venv\Scripts\alembic upgrade head` bằng user PostgreSQL có quyền tạo extension.

Backend chạy tại:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/api/v1/health
http://127.0.0.1:8000/api/v1/health/ready
```

### 4. Cài và chạy frontend

Mở terminal mới:

```bash
cd frontend
npm install
npm run dev
```

Frontend chạy tại:

```text
https://localhost:5173
```

Vite dùng HTTPS self-signed để trình duyệt cho phép camera/microphone. Nếu trình duyệt cảnh báo bảo mật, chọn Advanced/Proceed để vào ứng dụng local.

## Cách sử dụng nhanh

1. Mở `https://localhost:5173`.
2. Chọn `Bắt đầu tham quan`.
3. Dùng một trong các cách:
   - nhập câu hỏi về hiện vật;
   - tải ảnh từ thiết bị;
   - chụp ảnh bằng camera;
   - ghi âm bằng microphone.
4. Xem câu trả lời ở panel giữa và thông tin hiện vật ở panel bên phải.

## Lệnh kiểm tra

Backend:

```bash
cd backend
python -m pytest tests
```

Frontend:

```bash
cd frontend
npm run build
npm run test:web-speech
npm run lint
```

## Ghi chú hiện tại

- Web hiện tối ưu cho máy tính và laptop. Mobile web/PWA là hướng phát triển sau.
- Nếu backend chưa chạy, frontend vẫn mở được nhưng các request AI sẽ báo lỗi.
- Nếu thiếu API key hoặc hết quota, các bước Vision/STT/LLM có thể thất bại.
- Web Speech API phụ thuộc trình duyệt và giọng đọc cài trên thiết bị. Chrome/Edge hiện là lựa chọn ổn định nhất cho tính năng pause/play.
- Nếu chưa chạy PostgreSQL/migration/seed data, hệ thống vẫn có thể chat general nhưng RAG hiện vật sẽ thiếu dữ liệu.
