# Hướng dẫn chạy AI Tour Guide – Kinh thành Huế (Đại Nội)

## 1. Cấu hình Môi trường (`.env`)

Tạo file `.env` tại thư mục root (nếu chưa có) và cập nhật các API Keys:

```env
ENVIRONMENT=development
LOG_LEVEL=INFO

# AI API Keys (Bắt buộc để chạy Chatbot & Storytelling)
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here

# Database (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_tour_guide

# Cấu hình Model ưu tiên cho Storytelling (Giai đoạn Test)
LLM_PROVIDER_ORDER=gemini,groq
STORYTELLING_MODEL=gemini-1.5-flash # Hoặc llama3-70b-8192 (Groq)
```

## 2. Khởi động Cơ sở dữ liệu

Sử dụng Docker để chạy PostgreSQL:

```bash
cd docker
docker-compose up -d postgres
cd ..
```

## 3. Thiết lập Backend

```bash
cd backend
# Tạo và kích hoạt môi trường ảo
python -m venv .venv
.venv\Scripts\activate # Windows

# Cài đặt thư viện (bao gồm networkx cho bản đồ)
pip install -r requirements.txt

# Cập nhật Database Schema và nạp dữ liệu 16 công trình Kinh thành Huế
cd ..
alembic upgrade head
python scripts/seed_data.py

# Chạy server Backend (Giữ terminal này chạy)
cd backend
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

## 4. Thiết lập Frontend

```bash
cd frontend
npm install
# Lưu ý: map.png (bản đồ Kinh thành Huế) phải nằm trong thư mục frontend/public/
npm run dev
```

## 5. Hướng dẫn Sử dụng Tính năng Bản đồ (Kinh thành Huế)

1.  **Truy cập:** Mở trình duyệt vào `https://localhost:5173`, nhấn nút **"Kinh thành Huế – Bắt đầu khám phá"**.
2.  **Xác định vị trí khởi đầu:** 
    *   Một modal sẽ hiện ra cho phép bạn chọn 1 trong 2 cách:
        *   **"Định vị GPS tự động"** – hệ thống lấy tọa độ GPS thật từ thiết bị.
        *   **"Chọn vị trí trên bản đồ"** – chạm vào bản đồ để đặt vị trí hiện tại.
    *   Bạn có thể thay đổi vị trí hiện tại bất kỳ lúc nào bằng các nút ở góc phải:
        *   🔵 Nút GPS (định vị lại GPS thực tế)
        *   📍 Nút Pin (chọn lại trên bản đồ)
        *   🔧 Nút Căn chỉnh (Bật/tắt chế độ căn chỉnh tọa độ thủ công)
3.  **Chọn điểm tham quan & Chỉ đường:**
    *   Nhấn vào các Marker (màu đỏ) đại diện cho 16 công trình trên bản đồ.
    *   Mỗi popup có 2 nút:
        *   **"Chỉ đường đến đây"** – tính toán lộ trình đi bộ thực tế qua OSRM, vẽ đường đi, tự động phát âm thanh đọc chỉ dẫn bằng giọng nói (TTS) và hiển thị thanh hướng dẫn đi dưới đáy.
        *   **"Giới thiệu công trình"** – chuyển sang khung Chat để AI kể chuyện về công trình (đã sửa lỗi đồng bộ ID và tên di tích).
4.  **Sử dụng Thanh chỉ đường từng bước:**
    *   Khi đang dẫn đường, thanh ngang dưới đáy sẽ hiển thị hướng dẫn của bước hiện tại (VD: *Bước 1/4: Bắt đầu di chuyển...*).
    *   Sử dụng nút lùi `<-` hoặc tiến `->` để xem và nghe đọc lại (nút `🔊`) chỉ dẫn từng bước.
    *   Bấm **"Toàn bộ bước"** để mở rộng danh sách timeline đứng hiển thị tất cả các bước đi. Bấm vào bước bất kỳ để xem và nghe đọc bước đó.
5.  **Đến nơi:**
    *   Khi đã đi đến đích, nhấn nút **"ĐÃ ĐẾN NƠI – Giới thiệu địa điểm"**.
    *   Hệ thống sẽ di chuyển chấm xanh của bạn đến đích và tự động kích hoạt AI thuyết minh về địa điểm đó trong phần Chat.

## 6. Danh sách 16 Công trình trong Bản đồ

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

## 7. Căn chỉnh Tọa độ & Bounds thủ công (Map Calibration Mode)

Nếu vị trí GPS của bạn hoặc các di tích hiển thị chưa chính xác trên ảnh `map.png`, bạn có thể tự căn chỉnh bằng tay cực kỳ dễ dàng:
1.  Bấm vào nút **🔧 (Căn chỉnh)** ở góc trên bên phải bản đồ. Giao diện **Căn Chỉnh Bản Đồ** sẽ xuất hiện ở bên trái.
2.  **Căn chỉnh vị trí di tích:** Dùng chuột kéo thả trực tiếp các Marker di tích (chấm màu đỏ) trên bản đồ đến đúng vị trí hình ảnh của nó trên sơ đồ.
3.  **Co giãn/Dịch chuyển ảnh bản đồ:** Điều chỉnh các thông số toạ độ GPS của góc Tây Nam (SW) và Đông Bắc (NE) trong các ô nhập liệu. Sơ đồ `map.png` sẽ tự động co giãn và di chuyển theo thời gian thực để bạn đối chiếu với chấm GPS của mình.
4.  **Xuất cấu hình:** 
    *   Bảng bên trái tự động hiển thị dữ liệu tọa độ đã căn chỉnh dưới dạng file `toado.md` và mã mảng JS `HUE_ARTIFACTS`.
    *   Chỉ cần copy nội dung trong ô văn bản và ghi đè vào file `toado.md` ở thư mục root, code trong `MapExplore.jsx`, và chạy lại seed database để cập nhật.
5.  **Lưu ý kỹ thuật:** 
    *   Ảnh bản đồ có độ xoay góc khoảng 37 độ so với hướng Bắc thật. Định vị GPS sẽ sử dụng thuật toán chiếu của Leaflet lên góc bounds để hiển thị chính xác tương đối.
    *   Routing sử dụng dịch vụ đi bộ OSRM dựa trên dữ liệu đường đi của OpenStreetMap. Nếu xuất phát quá xa, hệ thống sẽ tự động vẽ đường thẳng (đường chim bay) và hiển thị cảnh báo hướng dẫn ghim vị trí bắt đầu gần Đại Nội.
