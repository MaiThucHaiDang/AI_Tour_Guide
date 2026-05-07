# AI Tour Guide
Nhóm 2 - Tư duy tính toán - 24CTT6

## Tính năng 1: Quét ảnh -> Nhận diện -> Thuyết minh bằng giọng nói

### 🛠 Yêu cầu hệ thống (Prerequisites)

Để chạy được mã nguồn này trên máy tính của bạn, bắt buộc phải cài đặt môi trường **Node.js**.

**Hướng dẫn cài đặt Node.js (Nếu máy chưa có):**
1. Truy cập trang web chính thức: [https://nodejs.org/](https://nodejs.org/)
2. Bấm tải xuống phiên bản **LTS (Long Term Support)** dành cho Windows/Mac.
3. Mở file vừa tải về và cứ bấm `Next` liên tục cho đến khi cài đặt xong (Finish).
4. Để kiểm tra xem đã cài thành công chưa:
   - Mở **Terminal** (trên VS Code) hoặc **Command Prompt (cmd)**.
   - Gõ lệnh `node -v` và ấn Enter. Nếu hiện ra version (ví dụ: `v18.17.0`) là bạn đã cài thành công.

---

### 🚀 Hướng dẫn Cài đặt & Chạy dự án chi tiết

#### Bước 1: Mở Terminal tại thư mục dự án
1. Mở phần mềm **Visual Studio Code (VS Code)**.
2. Chọn `File` > `Open Folder...` và chọn thư mục chứa đồ án.
3. Bấm tổ hợp phím `` Ctrl + ` `` (hoặc trên menu chọn `Terminal` > `New Terminal`) để mở cửa sổ dòng lệnh.

#### Bước 2: Cài đặt thư viện (Dependencies)
Trong Terminal, hãy gõ lệnh sau và ấn Enter:
```bash
npm install
```
*Lưu ý: Bạn chỉ cần chạy lệnh này 1 lần duy nhất để tải các thư viện React, Lucide Icons,... về thư mục `node_modules`. Quá trình này có thể mất 1-2 phút tùy tốc độ mạng.*

#### Bước 3: Khởi động Server (Development Server)
Tiếp tục gõ lệnh sau để chạy App:
```bash
npm run dev
```
Khi chạy thành công, Terminal sẽ hiện ra một dòng chữ màu xanh lá cây tương tự như:
`➜  Local:   http://localhost:5173/`

#### Bước 4: Xem App trên trình duyệt
1. Giữ phím `Ctrl` và click chuột trái vào đường link `http://localhost:5173/` để mở web.
2. **QUAN TRỌNG:** Vì đây là Mobile App, bạn CẦN xem ở giao diện điện thoại:
   - Bấm phím **F12** (hoặc chuột phải chọn `Inspect` / `Kiểm tra`).
   - Tìm icon **Hình chiếc điện thoại / Máy tính bảng** (hoặc bấm `Ctrl + Shift + M`).
   - Chọn loại thiết bị (Ví dụ: iPhone 12 Pro) và F5 tải lại trang.

---

### 📱 Hướng dẫn Test App trực tiếp trên Điện thoại thật (Cùng mạng WiFi)

Nếu bạn muốn dùng chính điện thoại của mình để soi camera thay vì dùng Webcam máy tính:
1. Đảm bảo điện thoại và máy tính kết nối **cùng một mạng WiFi**.
2. Ở Terminal VS Code đang chạy `npm run dev`, hãy tắt đi bằng `Ctrl + C` (Chọn Y).
3. Chạy lại server với lệnh:
   ```bash
   npm run dev -- --host
   ```
4. Terminal sẽ hiện thêm đường link **Network**, ví dụ: `http://192.168.1.11:5173/`.
5. Lấy điện thoại mở trình duyệt và gõ đúng đường link Network đó vào. Cấp quyền Camera và trải nghiệm!

---

### 🧪 Hướng dẫn Kiểm thử (Testing) cho báo cáo Đồ án

Để hỗ trợ bạn quay video/chụp ảnh làm báo cáo Báo cáo Đồ án, hệ thống đã được tích hợp sẵn công cụ **Mock Testing** (Giả lập).

Trên màn hình Camera (Góc trên cùng bên trái) có 3 nút bấm tương ứng với 3 Kịch bản (Scenarios):

1. **[Thành công] (Màu xanh): Kịch bản Happy Path**
   - Bấm nút này $\rightarrow$ Chụp ảnh $\rightarrow$ App nén ảnh $\rightarrow$ Giả lập delay 1.5s $\rightarrow$ Hiện màn hình kết quả $\rightarrow$ **Tự động đọc Audio** (Text-to-Speech).
2. **[Lỗi mờ] (Màu cam): Kịch bản Edge Case 1**
   - Bấm nút này $\rightarrow$ Chụp ảnh $\rightarrow$ Giả lập API trả về `Confidence Score < 0.5`.
   - Hiển thị Pop-up thân thiện yêu cầu *"Góc này hơi tối, bạn chụp lại nhé"*.
3. **[Mất mạng] (Màu đỏ): Kịch bản Edge Case 2**
   - Bấm nút này $\rightarrow$ Chụp ảnh $\rightarrow$ Giả lập gọi API thất bại.
   - Hiển thị Pop-up *"Chà, mất mạng rồi! Bạn kiểm tra lại wifi/4G nhé."*

---

### 📂 Giải thích Cấu trúc Source Code (Dùng cho viết Báo cáo)

Dưới đây là sơ đồ kiến trúc dành cho phần Frontend (Người 1):

* **`src/App.jsx`**: File Controller chính. Nơi quản lý State (`camera`, `scanning`, `result`) và luồng chạy của ứng dụng.
* **`src/components/`**: Các mảnh ghép giao diện:
  * `CameraScanner.jsx`: Dùng `navigator.mediaDevices.getUserMedia` để lấy quyền và stream Camera.
  * `ScanningLoader.jsx`: UI màn hình chờ API (Che giấu độ trễ).
  * `ResultView.jsx`: Hiển thị thông tin hiện vật & tích hợp trình phát Audio.
  * `ErrorPopup.jsx`: Giao diện xử lý ngoại lệ (Edge cases).
* **`src/services/apiService.js`**: File Mock API (Giả lập Backend khi Người 2 chưa làm xong) và tích hợp **Web Speech API** (Công nghệ chuyển đổi Văn bản thành Giọng nói của Browser).
* **`src/utils/imageUtils.js`**: Core Logic Tiền xử lý. Tự động vẽ ảnh lên HTML5 `<canvas>`, resize chiều dài về 800px và nén JPEG `quality=0.7` giúp giảm ảnh từ 5MB xuống Base64 dưới 1MB.
* **`src/index.css`**: Code giao diện (Vanilla CSS), áp dụng phong cách Dark Mode, Glassmorphism và CSS Animations.