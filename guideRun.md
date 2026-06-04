# Hướng dẫn chạy AI Tour Guide – Kinh thành Huế (Đại Nội)

Tài liệu này cung cấp hướng dẫn chi tiết từng bước để thiết lập, khởi chạy và vận hành toàn bộ hệ thống **AI Tour Guide** (bao gồm Bản đồ tương tác, Trợ lý AI kể chuyện đa phương thức RAG, và Trò chơi Đấu Trí Nhóm thời gian thực) sau khi pull mã nguồn về.

---

## 1. Yêu cầu chuẩn bị (Prerequisites)
Trước khi bắt đầu, hãy đảm bảo máy tính đã cài đặt sẵn:
1. **Python 3.10 - 3.13**
2. **Node.js (phiên bản 18 trở lên)** và **npm**
3. **Docker Desktop** (dành cho chạy Cơ sở dữ liệu PostgreSQL)
4. **Git** (để quản lý mã nguồn)

---

## 2. Cấu hình Môi trường (`.env`)

Tạo tệp `.env` tại thư mục gốc (root) của dự án và điền cấu hình dưới đây.

```env
# ─── Môi trường ──────────────────────────────────────────────────────────────
ENVIRONMENT=development
LOG_LEVEL=INFO

# ─── AI API Keys (Bắt buộc để chạy Chatbot & Nhận diện ảnh) ───────────────────
# Lấy tại Google AI Studio: https://aistudio.google.com/
GEMINI_API_KEY=your_gemini_api_key_here

# Lấy tại Groq Console: https://console.groq.com/
GROQ_API_KEY=your_groq_api_key_here

# ─── Cơ sở dữ liệu (PostgreSQL) ──────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_tour_guide

# ─── Cấu hình Model AI (Tối ưu hóa tránh khóa Quota và tăng độ sáng tạo) ─────
LLM_PROVIDER_ORDER=gemini,groq
GEMINI_TEXT_MODEL=gemini-1.5-flash
GEMINI_VISION_MODEL=gemini-2.5-flash
GROQ_LLM_MODEL=llama-3.1-8b-instant
GROQ_STT_MODEL=whisper-large-v3

# Cấu hình kiểm soát chất lượng câu thoại
LLM_TEMPERATURE=0.6
LLM_MAX_TOKENS=800
VISION_CONFIDENCE_THRESHOLD=0.6

# ─── Cấu hình Cache (Redis hoặc Bộ nhớ cục bộ) ───────────────────────────────
# Nếu máy bạn KHÔNG có Redis chạy ở cổng 6379, hãy sửa giá trị này thành rỗng ("")
# Hệ thống sẽ tự động chuyển sang SimpleMemoryCache cục bộ để tránh lỗi khởi động.
REDIS_URL=redis://localhost:6379/0

# ─── CORS Origins ─────────────────────────────────────────────────────────────
CORS_ORIGINS=["http://localhost:5173", "http://127.0.0.1:5173"]

# ─── Tốc độ giọng nói (EDGE-TTS) ──────────────────────────────────────────────
EDGE_TTS_RATE=+0%
```

---

## 3. Khởi động Cơ sở dữ liệu (Docker)

Hệ thống sử dụng cơ sở dữ liệu **PostgreSQL** kết hợp tiện ích mở rộng **pgvector** cho tìm kiếm ngữ nghĩa. Sử dụng Docker để khởi động nhanh chóng:

```bash
# Di chuyển vào thư mục docker và khởi chạy dịch vụ
cd docker
docker-compose up -d postgres
cd ..
```

---

## 4. Thiết lập Backend (FastAPI)

### Bước 4.1: Tạo môi trường ảo và cài đặt thư viện
Dự án hỗ trợ môi trường ảo tại thư mục gốc hoặc thư mục `backend`. Dưới đây là cách cài đặt độc lập cho Backend:

```bash
cd backend
# Tạo môi trường ảo
python -m venv .venv

# Kích hoạt môi trường ảo (Windows)
.venv\Scripts\activate
# Hoặc trên macOS/Linux: source .venv/bin/activate

# Cài đặt các thư viện cần thiết
pip install -r requirements.txt
```

### Bước 4.2: Chạy Migrations và Nạp dữ liệu (Seeding)
Sau khi database PostgreSQL đã sẵn sàng, bạn cần cập nhật cấu trúc bảng và điền dữ liệu di tích Đại Nội Huế:

```bash
# Quay lại thư mục gốc để chạy các script dữ liệu
cd ..

# 1. Chạy cập nhật cấu trúc database (migrations)
.venv\Scripts\alembic upgrade head

# 2. Nạp dữ liệu thuyết minh lịch sử & Đồ thị tri thức (Knowledge Graph)
# (Lệnh này sẽ nạp thông tin 17 di tích, tọa độ hiệu chỉnh, 186 facts và 92 relations có sẵn)
.venv\Scripts\python scripts/seed_enriched_data.py
```

> [!NOTE]
> **Dữ liệu thuyết minh tạo sẵn (Pre-generated Cache):**
> Bộ nhớ đệm thuyết minh 17 di tích song ngữ (`backend/data/pre_generated_intros.json`) đã được tối ưu hóa độ dài (khoảng 120-140 từ) và commit sẵn trên Git. Backend sẽ tự động nạp tệp này vào bộ nhớ mà **không cần gọi đến API Gemini/Groq** khi khởi động.
> Chỉ chạy lệnh sau nếu bạn muốn cập nhật hoặc sinh lại toàn bộ tệp thuyết minh mẫu:
> `.venv\Scripts\python scripts/pregenerate_intros.py`

### Bước 4.3: Chạy server Backend
```bash
cd backend
# Khởi chạy server phát triển với chế độ tự động reload
.venv\Scripts\python main.py
```
Server backend sẽ chạy tại: `http://127.0.0.1:8000`.

---

## 5. Thiết lập Frontend (React + Vite)

Mở một terminal mới (không tắt terminal backend):

```bash
cd frontend
# Cài đặt thư viện React/Leaflet
npm install

# Khởi chạy server frontend phát triển
npm run dev
```

Mở trình duyệt truy cập vào đường dẫn được hiển thị (thường là `http://localhost:5173`).

---

## 6. Chạy Kiểm thử tự động (Unit Tests)

Để xác nhận toàn bộ hệ thống backend, kết nối database, chatbot RAG, và các chức năng giọng nói hoạt động đúng:

```bash
# Kích hoạt môi trường ảo tại thư mục gốc và chạy pytest
.venv\Scripts\python -m pytest backend/tests
```
Hệ thống sẽ chạy qua **28 tests** (bao gồm API Contract, Game Service, RAG Pipeline, Tour Service, Unified Chatbot và Voice Features).

---

## 7. Các tính năng cốt lõi và Hướng dẫn sử dụng

### 7.1. Bản đồ & Chỉ đường thông minh (Smart Walk Route)
*   **Vị trí xuất phát:** Chọn sử dụng định vị GPS thực tế hoặc bấm trực tiếp trên bản đồ để giả lập vị trí đứng hiện tại.
*   **Dẫn đường:** Click vào bất kỳ biểu tượng di tích nào và chọn **"Chỉ đường đến đây"**. Hệ thống vẽ tuyến đường đi bộ thực tế men theo các lối đi trong Đại Nội (qua dịch vụ định tuyến OSRM miễn phí) và hiển thị bảng chỉ dẫn đi từng bước.
*   **Sự kiện đã đến nơi:** Khi bấm **"Đã đến & Giới thiệu"**, hệ thống sẽ kết thúc tuyến đường và tự động chuyển sang màn hình Hỏi AI để thuyết minh di tích bằng giọng nói (độ trễ 0 giây nhờ cache).

### 7.2. Trợ lý AI Hỏi đáp grounded (RAG Chatbot)
*   **Query Rewriting (Viết lại câu hỏi):** Khi bạn hỏi các câu nối tiếp chứa đại từ thay thế (ví dụ: *"Ai xây dựng nó?"*, *"Nó ở đâu?"*), hệ thống tự động trích xuất ngữ cảnh từ bộ nhớ và viết lại câu hỏi đầy đủ (ví dụ: *"Ai xây dựng Ngọ Môn?"*) trước khi gửi vào cơ sở dữ liệu Vector RAG để đạt độ chính xác 100%.
*   **Storytelling Mode:** Chatbot được cấu hình để phản hồi bằng phong cách hướng dẫn viên lịch sử truyền cảm, kể chuyện sinh động (từ 120-200 từ), lồng ghép giai thoại triều Nguyễn.
*   **Cắt câu thông minh (Sentence Truncation):** Khắc phục lỗi ngắt câu giữa chừng của Groq bằng thuật toán tìm kiếm ranh giới câu (`.`, `!`, `?`), đảm bảo câu trả lời luôn trọn vẹn nghĩa.

### 7.3. Trò chơi Đấu Trí Cung Đình (Multiplayer Quiz Room)
*   **Khởi tạo:** Khi người dùng đi qua ít nhất **2 địa điểm** trên bản đồ, nút **"Đấu Trí Nhóm"** sẽ sáng lên. Chủ phòng (Host) bấm nút này để tạo phòng game.
*   **Tham gia chơi:** Các thành viên trong nhóm kết nối chung mạng Wifi (LAN) với Host, quét mã QR hiển thị trên màn hình Host bằng điện thoại để vào giao diện tay cầm chơi game di động mà không cần tải app.
*   **Cơ chế trò chơi:**
    *   Hệ thống gọi Gemini để sinh ngẫu nhiên 5 câu hỏi dựa trên chính lịch sử các điểm mà nhóm của bạn vừa đi qua.
    *   Cộng điểm thưởng theo tốc độ trả lời (Speed Bonus).
    *   Kết thúc trò chơi, AI sẽ tự động sinh và phát loa một bài chúc mừng trạng nguyên bằng giọng cung đình Huế hài hước.

---

## 8. Giải quyết sự cố thường gặp (Troubleshooting)

### 1. Lỗi kết nối Redis (`ConnectionError` / Lỗi khởi động cache)
*   **Hiện tượng:** Terminal Backend báo lỗi không thể kết nối tới `127.0.0.1:6379` và dừng tiến trình.
*   **Khắc phục:** Mở file `.env` ở thư mục gốc, sửa dòng `REDIS_URL=redis://localhost:6379/0` thành `REDIS_URL=` (để trống). Backend sẽ tự động nhận diện và chuyển sang chế độ `SimpleMemoryCache` lưu trữ tạm thời trong RAM, giúp chạy mượt mà không cần cài đặt Redis.

### 2. Tay cầm điện thoại không kết nối được màn hình Host của máy tính
*   **Hiện tượng:** Điện thoại báo lỗi kết nối hoặc không tải được trang sau khi quét mã QR.
*   **Khắc phục:**
    *   Đảm bảo cả máy tính (Host) và điện thoại đều đang kết nối **chung một mạng Wifi**.
    *   Nếu máy tính chạy tường lửa (Windows Firewall), hãy tạm thời cho phép Node.js và Python đi qua mạng Private/Public.
    *   Nếu trình duyệt hiển thị cảnh báo HTTPS/SSL không an toàn (do truy cập IP LAN nội bộ dạng HTTP), hãy chọn **Nâng cao (Advanced)** $\rightarrow$ **Tiếp tục truy cập (Proceed to IP)**.

### 3. Lỗi trùng cổng cơ sở dữ liệu (Postgres Port Conflicted)
*   **Hiện tượng:** Khởi chạy `docker-compose up` báo lỗi cổng `5432` đã được sử dụng.
*   **Khắc phục:** Do máy bạn đang chạy sẵn một phiên bản PostgreSQL cài trực tiếp trên Windows. Hãy tắt dịch vụ Postgres cục bộ đó đi bằng cách: Mở cửa sổ **Services** của Windows $\rightarrow$ tìm `postgresql-x64-...` $\rightarrow$ click chuột phải chọn **Stop**, sau đó chạy lại lệnh Docker Compose.
