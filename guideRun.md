# Hướng dẫn chạy AI Tour Guide – Kinh thành Huế (Đại Nội)

## 1. Cấu hình Môi trường (`.env`)

Tạo file `.env` tại thư mục root (nếu chưa có) và cập nhật các cấu hình sau để khớp với logic mặc định của hệ thống:

```env
ENVIRONMENT=development
LOG_LEVEL=INFO

# AI API Keys (Bắt buộc để chạy Chatbot & Storytelling)
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here

# Database (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_tour_guide

# ─── Cấu hình AI & LLM ────────────────────────────────────────────────────────
LLM_PROVIDER_ORDER=gemini,groq
GEMINI_TEXT_MODEL=gemini-2.5-flash-lite
GEMINI_VISION_MODEL=gemini-2.5-flash-lite
GROQ_LLM_MODEL=llama-3.3-70b-versatile
GROQ_STT_MODEL=whisper-large-v3

# Cấu hình độ sáng tạo (mặc định 0.7) và số lượng token cho các loại câu hỏi
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048
LLM_MAX_TOKENS_FOLLOWUP=800
```

> Ghi chú voice: frontend dùng Web Speech API của trình duyệt để đọc câu trả lời. Backend vẫn dùng `GROQ_API_KEY` cho Speech-to-Text khi người dùng ghi âm, nhưng không cần Edge TTS cho thanh phát chính trong web app.

## 2. Khởi động Cơ sở dữ liệu

Sử dụng Docker để chạy PostgreSQL (hỗ trợ pgvector cho tìm kiếm ngữ nghĩa):

```bash
cd docker
docker-compose up -d postgres
cd ..
```

## 3. Thiết lập Backend

```bash
# Tạo môi trường ảo (tại thư mục root)
python -m venv .venv

# Cài đặt thư viện
.venv\Scripts\python -m pip install -r backend/requirements.txt

# Cập nhật Database Schema và nạp dữ liệu 17 công trình Kinh thành Huế (từ thư mục root)
.venv\Scripts\alembic upgrade head
.venv\Scripts\python scripts/seed_data.py

# (Tùy chọn) Xây dựng Knowledge Graph - Đồ thị tri thức (yêu cầu GROQ_API_KEY)
.venv\Scripts\python scripts/build_graph.py

# Chạy server Backend (Giữ terminal này chạy)
cd backend
..\.venv\Scripts\python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

## 4. Thiết lập Frontend

```bash
cd frontend
npm install
# Lưu ý: Ứng dụng dùng HTTPS (self-signed) để hỗ trợ Camera/Microphone trên trình duyệt
npm run dev
```

## 5. Hướng dẫn Sử dụng Tính năng Bản đồ (Kinh thành Huế)

1.  **Truy cập:** Mở trình duyệt vào `https://localhost:5173`, nhấn vào card **"Đại Nội Huế"** (có ghi chú 17 điểm tham quan).
2.  **Xác định vị trí khởi đầu:** 
    *   Một modal sẽ hiện ra cho phép bạn chọn:
        *   **"Định vị GPS tự động"** – hệ thống lấy tọa độ GPS thật từ thiết bị.
        *   **"Chọn vị trí trên bản đồ"** – chạm vào bản đồ để đặt vị trí hiện tại của bạn.
    *   Bạn có thể thay đổi vị trí hiện tại bất kỳ lúc nào bằng các nút ở góc phải:
        *   🔵 Nút GPS (định vị lại GPS thực tế)
        *   📍 Nút Pin (chọn lại trên bản đồ)
        *   🔧 Nút Căn chỉnh (Bật/tắt chế độ căn chỉnh tọa độ thủ công)
3.  **Chọn điểm tham quan & Chỉ đường:**
    *   Nhấn vào các Marker (màu đỏ) đại diện cho 17 công trình trên bản đồ.
    *   Mỗi popup có các nút hành động:
        *   **"Chỉ đường đến đây"** – tính toán lộ trình đi bộ thực tế qua OSRM, vẽ đường đi uốn lượn theo lối mòn, tự động đọc chỉ dẫn bằng Web Speech API.
        *   **"Giới thiệu công trình"** – chuyển sang khung Chat để AI kể chuyện sâu sắc về công trình đó.
4.  **Sử dụng Thanh hướng dẫn:**
    *   Khi đang dẫn đường, thanh dưới đáy hiển thị hướng dẫn bước hiện tại.
    *   Dùng nút phát/tạm dừng để nghe chỉ dẫn bằng giọng đọc trên thiết bị, hoặc dùng mũi tên `<-` `->` để xem các bước tiếp theo.
    *   Bấm **"Toàn bộ bước"** để xem danh sách lộ trình đầy đủ.
5.  **Đến nơi:**
    *   Khi đã đến đích, nhấn nút **"ĐÃ ĐẾN NƠI – Giới thiệu địa điểm"**.
    *   Hệ thống sẽ cập nhật vị trí của bạn và kích hoạt AI thuyết minh về địa điểm đó.

## 6. Danh sách 17 Công trình trong Bản đồ

| # | Tên công trình | Tên tiếng Anh |
|---|---------------|--------------|
| 1 | Cửa Hòa Bình | Hoa Binh Gate |
| 2 | Điện Kiến Trung | Kien Trung Palace |
| 3 | Cung Trường Sanh | Truong Sanh Palace |
| 4 | Cung Diên Thọ | Dien Tho Palace |
| 5 | Cửa Chương Đức | Chuong Duc Gate |
| 6 | Hưng Miếu | Hung Mieu Temple |
| 7 | Thế Miếu | The Mieu Temple |
| 8 | Điện Thái Hòa | Thai Hoa Palace |
| 9 | Nền điện Cần Chánh | Can Chanh Palace Foundation |
| 10 | Duyệt Thị Đường | Duyet Thi Duong Theater |
| 11 | Phủ Nội Vụ | Phu Noi Vu |
| 12 | Vườn Cơ Hạ | Co Ha Garden |
| 13 | Triệu Miếu | Trieu Mieu Temple |
| 14 | Thái Miếu | Thai Mieu Temple |
| 15 | Cửa Hiển Nhơn | Hien Nhon Gate |
| 16 | Điện Long An (Bảo tàng Cổ vật) | Long An Palace (Museum) |
| 17 | Ngọ Môn | Ngo Mon Gate (Meridian Gate) |

## 7. Căn chỉnh Tọa độ (Map Calibration Mode)

Nếu vị trí các di tích hiển thị chưa khớp trên ảnh bản đồ `map.jpg`, bạn có thể căn chỉnh:
1.  Bấm vào nút **🔧 (Căn chỉnh)**.
2.  **Kéo thả Marker:** Di chuyển các Marker đỏ đến vị trí chính xác trên sơ đồ.
3.  **Co giãn bản đồ:** Điều chỉnh tọa độ GPS góc SW và NE để khớp chấm GPS của bạn với hình ảnh bản đồ.
4.  **Lưu thay đổi:** 
    *   Copy mã mảng `HUE_ARTIFACTS` được xuất ra ở bảng bên trái.
    *   Ghi đè vào biến `HUE_ARTIFACTS` trong file `frontend/src/components/map/MapExplore.jsx`.
    *   Cập nhật tọa độ trong `scripts/seed_data.py` và chạy lại lệnh seed để đồng bộ Database.

## 8. Nhật ký trích xuất dữ liệu RAG (RAG Debug Logging)

Kiểm tra dữ liệu AI sử dụng để trả lời tại:
- **Đường dẫn:** `backend/data/rag_debug_log.txt`
- Giúp bạn biết chính xác đoạn văn bản nào từ Database đã được nạp vào Prompt của AI cho mỗi câu hỏi.
- Đây là file log runtime; không dùng nội dung log này như dữ liệu nguồn của hệ thống.

## 9. Kiểm thử nhanh

```bash
cd frontend
npm run test:web-speech
npm run build
```

`test:web-speech` kiểm tra queue Web Speech, đọc hết đoạn dài, pause/play nhiều lần và hủy phát ổn định.
