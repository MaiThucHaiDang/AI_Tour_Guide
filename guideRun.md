# Hướng Dẫn Cài Đặt và Chạy Dự Án AI Tour Guide

Dự án AI Tour Guide là một ứng dụng hỗ trợ khách tham quan sử dụng AI để nhận diện hiện vật và trò chuyện bằng giọng nói. Hệ thống bao gồm:
- **Backend**: FastAPI (Python) - Xử lý Vision, Voice, LLM và Database.
- **Frontend**: React/Vite (JavaScript) - Giao diện người dùng di động.
- **Database**: PostgreSQL (Docker) - Lưu trữ thông tin hiện vật và lịch sử.

---

## 🛠 Yêu Cầu Hệ Thống (Prerequisites)

Đảm bảo máy tính của bạn đã cài đặt:
1. **Python 3.10+**: [Tải tại đây](https://www.python.org/). (Lưu ý: Tick vào **"Add Python to PATH"** khi cài đặt).
2. **Node.js 18+**: [Tải tại đây](https://nodejs.org/).
3. **Docker Desktop**: Để chạy Database PostgreSQL. [Tải tại đây](https://www.docker.com/).

---

## 🚀 Các Bước Triển Khai Chi Tiết

### Bước 1: Cấu Hình Biến Môi Trường (.env)

1. Tại thư mục gốc của dự án, tạo file `.env` (nếu chưa có) hoặc chỉnh sửa file `.env` hiện tại.
2. Đảm bảo các thông tin sau đã chính xác (đặc biệt là API Keys):

```env
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_tour_guide
ENVIRONMENT=development
LOG_LEVEL=INFO
```

---

### Bước 2: Khởi Chạy Cơ Sở Dữ Liệu (PostgreSQL)

1. Mở Docker Desktop.
2. Mở Terminal tại thư mục dự án và chạy:
```bash
cd docker
docker-compose up -d postgres
```
3. Kiểm tra trên Docker Desktop xem container `ai_tour_guide_db` đã ở trạng thái **Running** chưa.

---

### Bước 3: Cài Đặt và Chạy Backend

Backend hiện đã được hợp nhất (Unified), chạy tất cả tính năng trên cổng **8000**.
1. Mở một Terminal mới tại thư mục `backend`:
```bash
cd backend
```

2. Tạo và kích hoạt môi trường ảo:
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# MacOS/Linux:
source .venv/bin/activate
```

3. Cài đặt thư viện:
```bash
pip install -r requirements.txt
```
4. **Nạp dữ liệu mẫu (Seed Data)** - Chỉ cần chạy 1 lần duy nhất:
```bash
# Đứng tại thư mục backend
python ../scripts/seed_data.py
```
5. Khởi chạy Backend Server:
```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
> Server Backend chạy tại: **http://127.0.0.1:8000**

---

### Bước 4: Cài Đặt và Chạy Frontend

1. Mở một Terminal mới tại thư mục `frontend`:
```bash
cd frontend
```
2. Cài đặt các gói thư viện:
```bash
npm install
```
3. Khởi chạy Frontend:
```bash
npm run dev
```
> Giao diện Web chạy tại: **https://localhost:5173** (Sử dụng HTTPS để hỗ trợ Camera/Micro).

---

## 📱 Hướng Dẫn Kiểm Thử (Testing)

### 1. Trải nghiệm trên Máy tính (PC)
- Truy cập `https://localhost:5173`.
- Bấm **F12**, chọn biểu tượng **Mobile Device Mode** (Hình điện thoại) để xem giao diện chuẩn di động.
- Bạn có thể chọn file ảnh để tải lên thay vì dùng Camera trực tiếp nếu trình duyệt yêu cầu quyền.

### 2. Trải nghiệm trên Điện thoại thật
- Máy tính và điện thoại phải kết nối **cùng một mạng WiFi**.
- Chạy Frontend với lệnh: `npm run dev -- --host`
- Terminal sẽ hiện địa chỉ IP Network (ví dụ: `https://192.168.1.10:5173`).
- Dùng điện thoại truy cập vào địa chỉ IP đó.

---

## 📝 Lưu Ý Quan Trọng
- **API Keys**: Đảm bảo `GEMINI_API_KEY` và `GROQ_API_KEY` của bạn còn hạn mức.
- **Micro/Camera**: Trình duyệt yêu cầu HTTPS để sử dụng Micro/Camera. Dự án đã cấu hình plugin `basic-ssl`, hãy bấm "Advanced" -> "Proceed to localhost" khi gặp cảnh báo bảo mật.
- **Proxy**: Mọi yêu cầu từ Frontend đến `/api/*` sẽ tự động được chuyển hướng sang Backend cổng 8000 thông qua cấu hình trong `vite.config.js`.
