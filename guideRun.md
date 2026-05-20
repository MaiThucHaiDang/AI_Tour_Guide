# Hướng dẫn chạy AI Tour Guide trên máy tính local

Dự án hiện là web app hướng dẫn tham quan chạy local:

- Frontend: React/Vite tại `frontend/`, chạy `https://localhost:5173`
- Backend: FastAPI unified tại `backend/`, chạy `http://127.0.0.1:8000`
- Database: PostgreSQL qua Docker

## 1. Chuẩn bị `.env`

Tạo file `.env` ở thư mục root:

```env
ENVIRONMENT=development
LOG_LEVEL=INFO
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_tour_guide
LLM_PROVIDER_ORDER=gemini,groq
```

## 2. Chạy database

```bash
cd docker
docker-compose up -d postgres
cd ..
```

## 3. Chạy backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cd ..
alembic upgrade head
python scripts\seed_data.py
cd backend
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Kiểm tra backend:

```text
http://127.0.0.1:8000/api/v1/health
http://127.0.0.1:8000/api/v1/health/ready
```

## 4. Chạy frontend

Mở terminal mới:

```bash
cd frontend
npm install
npm run dev
```

Mở trình duyệt:

```text
https://localhost:5173
```

Nếu thấy cảnh báo HTTPS self-signed, chọn Advanced/Proceed để vào trang local.

## 5. Sử dụng

1. Bấm `Bắt đầu tham quan`.
2. Nhập câu hỏi hoặc tải ảnh hiện vật.
3. Có thể dùng webcam/microphone của máy tính nếu trình duyệt đã cấp quyền.
4. Xem câu trả lời ở khung chat và thông tin hiện vật ở panel bên phải.

## 6. Lỗi thường gặp

- `Failed to fetch`: backend chưa chạy hoặc cổng 8000 bị chặn.
- Không mở được webcam/microphone: kiểm tra quyền trình duyệt và dùng HTTPS local của Vite.
- Không có dữ liệu hiện vật: kiểm tra PostgreSQL, chạy `alembic upgrade head`, rồi chạy lại `python scripts\seed_data.py`.
- AI không trả lời: kiểm tra `GEMINI_API_KEY`, `GROQ_API_KEY` và quota provider.
