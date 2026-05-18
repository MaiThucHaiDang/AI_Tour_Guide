# Hướng Dẫn Cài Đặt và Chạy Dự Án AI Tour Guide

Dự án này sử dụng kiến trúc **Clean Architecture**, bao gồm một **FastAPI Backend** (Python), một **React/Vite Frontend** (JavaScript/Node.js), và cơ sở dữ liệu **PostgreSQL** (chạy thông qua Docker).

---

## 🛠 Yêu Cầu Cần Thiết (Prerequisites)

Trước khi bắt đầu, hãy đảm bảo máy tính của bạn đã cài đặt các phần mềm sau:
1. **Python 3.10 trở lên**: Tải tại [python.org](https://www.python.org/) (nhớ tick chọn "Add Python to PATH" khi cài đặt).
2. **Node.js (LTS 18.x trở lên)**: Tải tại [nodejs.org](https://nodejs.org/).
3. **Docker Desktop**: Cần thiết để chạy database PostgreSQL. Tải tại [docker.com](https://www.docker.com/products/docker-desktop).

---

## 🚀 Bước 1: Khởi Tạo Cơ Sở Dữ Liệu (PostgreSQL)

Hệ thống sử dụng Docker để khởi tạo nhanh PostgreSQL. Đảm bảo **Docker Desktop đang chạy**.

1. Mở Terminal (Command Prompt / PowerShell).
2. Di chuyển vào thư mục dự án và khởi chạy Docker:
```bash
# Đi vào thư mục chứa dự án
cd C:\TranNhatTruong_2026\HK1\Tu_duy_tinh_toan\Project\AI_Tour_Guide

# Vào thư mục docker và chạy lệnh khởi tạo
cd docker
docker-compose up -d postgres
```
*(Nếu là lần đầu chạy, Docker sẽ tốn khoảng vài phút để tải Image PostgreSQL về máy).*

---

## ⚙️ Bước 2: Cài Đặt và Khởi Chạy Backend

Backend xử lý toàn bộ logic AI (Vision, Voice) và kết nối với Database.

1. Mở một cửa sổ Terminal **mới** ở thư mục gốc của dự án.
2. Di chuyển vào thư mục `backend`:
```bash
cd backend
```

3. (Khuyến nghị) Tạo và kích hoạt môi trường ảo (Virtual Environment):
```bash
# Tạo môi trường ảo có tên là .venv
python -m venv .venv

# Kích hoạt môi trường (trên Windows):
.venv\Scripts\activate

# (Nếu dùng MacOS/Linux, dùng lệnh: source .venv/bin/activate)
```

4. Cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
```

5. Khởi tạo dữ liệu mẫu (Seed Data) vào Database:
```bash
# Lệnh này sẽ nạp toàn bộ dữ liệu hiện vật, locations, FAQ từ hệ thống cũ vào PostgreSQL
python ../scripts/seed_data.py
```
*(Lưu ý: Nếu thấy báo "Seeded...", tức là dữ liệu đã được nạp thành công).*

6. Khởi chạy Backend Server:
```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
> Server Backend sẽ chạy tại: **http://127.0.0.1:8000**

---

## 🎨 Bước 3: Cài Đặt và Khởi Chạy Frontend

Frontend là giao diện người dùng viết bằng React.

1. Mở một cửa sổ Terminal **mới** ở thư mục gốc của dự án.
2. Di chuyển vào thư mục `frontend`:
```bash
cd frontend
```

3. Cài đặt các gói thư viện Node.js:
```bash
npm install
```

4. Khởi chạy Frontend Server:
```bash
npm run dev
```
> Giao diện web sẽ chạy tại: **https://localhost:5173** (hoặc http://localhost:5173 tùy vào console log).

---

## 🔑 Bước 4: Cấu Hình API Keys (.env)

Hệ thống yêu cầu các API Key của Google Gemini và Groq để nhận diện hình ảnh và xử lý giọng nói.

1. Tại thư mục gốc dự án, tìm file `.env`.
2. Mở file `.env` bằng Notepad hoặc VSCode, đảm bảo bạn đã điền các Key hợp lệ:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_tour_guide
ENVIRONMENT=development
LOG_LEVEL=INFO
```
*(API Keys hiện tại đã được cấu hình trong file của bạn. Nếu chúng hết hạn, bạn hãy tự thay bằng Key mới).*

---

## 📝 Tóm Tắt Luồng Chạy (Làm Hằng Ngày)

Sau khi cài đặt xong lần đầu, mỗi lần muốn chạy lại dự án, bạn chỉ cần mở 3 tab Terminal:

- **Tab 1 (Database):** `cd docker` -> `docker-compose up -d postgres`
- **Tab 2 (Backend):** `cd backend` -> `.venv\Scripts\activate` -> `uvicorn main:app --port 8000 --reload`
- **Tab 3 (Frontend):** `cd frontend` -> `npm run dev`

Mở trình duyệt vào trang `https://localhost:5173` và trải nghiệm AI Tour Guide!
