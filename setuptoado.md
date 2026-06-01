# Hướng dẫn Căn chỉnh Tọa độ Bản đồ Kinh thành Huế (Đại Nội)

Tài liệu này hướng dẫn cách truy cập trang căn chỉnh bản đồ độc lập (Standalone Map Calibration Page) để kéo thả điều chỉnh tọa độ các di tích, co giãn ảnh sơ đồ bản đồ, và lưu cấu hình cố định vĩnh viễn vào cơ sở dữ liệu.

---

## Bước 1: Khởi động hệ thống
Đảm bảo cả Backend và Frontend của bạn đang chạy bình thường:
1.  **Backend:**
    ```bash
    cd backend
    uvicorn main:app --host 127.0.0.1 --port 8000 --reload
    ```
2.  **Frontend:**
    ```bash
    cd frontend
    npm run dev
    ```

---

## Bước 2: Chọn Cách Truy Cập Giao Diện Căn Chỉnh
Hệ thống cung cấp **2 cách** để bạn căn chỉnh và lưu tọa độ:

### 👉 Cách A: Dùng trang Căn chỉnh riêng biệt (Khuyên dùng cho màn hình lớn)
Truy cập trực tiếp đường dẫn: **[http://localhost:5173/?view=calibrate](http://localhost:5173/?view=calibrate)**
*Lưu ý: URL này tải trang cấu hình chuyên dụng với thanh tiêu đề riêng biệt và nút "LƯU VÀO DATABASE" ở góc trên cùng bên phải.*

### 👉 Cách B: Dùng chế độ Căn chỉnh trực tiếp (Trong giao diện Khám phá)
Tại trang chính (`http://localhost:5173`), nhấn **"Kinh thành Huế - Bắt đầu khám phá"**. Trên bản đồ, nhấn biểu tượng cờ-lê **🔧 (Căn chỉnh)** ở góc trên cùng bên phải để mở trực tiếp bảng điều khiển căn chỉnh.

---

## Bước 3: Thực hiện Căn chỉnh trên Giao diện
Giao diện căn chỉnh bao gồm bản đồ sơ đồ và bảng điều khiển:

1.  **Kéo thả di tích:** 
    *   Các công trình được biểu diễn bằng các Marker chấm đỏ trên bản đồ.
    *   Dùng chuột nhấp giữ và **kéo thả (drag-and-drop)** các chấm đỏ này đến đúng vị trí hình ảnh của chúng trên tấm ảnh sơ đồ `map.png`.
2.  **Co giãn và Dịch chuyển Ảnh bản đồ:**
    *   Trong bảng điều khiển, có 4 ô nhập liệu tương ứng với tọa độ vĩ độ/kinh độ của 2 góc biên ảnh:
        *   **SW (Southwest - Tây Nam):** Góc dưới cùng bên trái của ảnh.
        *   **NE (Northeast - Đông Bắc):** Góc trên cùng bên phải của ảnh.
    *   Bạn có thể thay đổi các giá trị này (tăng/giảm nhẹ) để co giãn, kéo rộng hoặc thu nhỏ sơ đồ bản đồ trên lưới GPS thực tế cho đến khi khớp hoàn hảo. Ảnh sơ đồ sẽ di chuyển trực quan ngay lập tức khi bạn thay đổi số.
3.  **Xem cấu hình xuất ra (Để tham khảo):**
    *   Bảng điều khiển hiển thị trực tiếp danh sách tọa độ mới định dạng file `toado.md` và code JS để bạn tham khảo hoặc copy thủ công nếu cần.

---

## Bước 4: Lưu cấu hình vĩnh viễn vào Database
Sau khi đã căn chỉnh tất cả 16 điểm di tích và biên ảnh trùng khớp hoàn hảo:
1.  **Thực hiện Lưu:**
    *   Nếu dùng **Cách A**: Nhấp nút màu xanh lá **"LƯU VÀO DATABASE"** ở góc trên bên phải màn hình.
    *   Nếu dùng **Cách B**: Nhấp nút màu xanh lá **"LƯU VÀO DATABASE"** nằm ngay trong bảng điều khiển căn chỉnh bên trái.
2.  **Hệ thống sẽ tự động:**
    *   Gửi tọa độ mới lên backend và cập nhật trực tiếp vào bảng `artifacts` và bảng `locations` trong cơ sở dữ liệu PostgreSQL.
    *   Ghi đè cấu hình mới này vào tệp cấu hình đĩa cứng **`backend/data/map_calibrated.json`** để sao lưu dự phòng lâu dài.

---

## Bước 5: Kiểm tra kết quả
1.  **Tải lại trang:** F5 lại trang trình duyệt và kiểm tra xem vị trí các di tích có giữ nguyên ở vị trí bạn vừa kéo thả hay không.
2.  **Trang trải nghiệm du lịch:** Quay lại trang chủ (`http://localhost:5173`) và bấm vào **"Kinh thành Huế - Bắt đầu khám phá"**. Bản đồ du lịch lúc này sẽ tự động tải tọa độ mới nhất vừa lưu từ Database.
3.  **Tương thích khi chạy lại Seed data:**
    *   Ngay cả khi bạn chạy lại lệnh làm sạch và nạp dữ liệu mặc định:
        ```bash
        python scripts/seed_data.py
        ```
    *   Hệ thống sẽ tự động phát hiện file dự phòng `backend/data/map_calibrated.json` và nạp các tọa độ đã căn chỉnh của bạn làm mặc định thay vì ghi đè tọa độ thô ban đầu. Bản đồ sẽ luôn được giữ cố định như bạn đã thiết lập!
