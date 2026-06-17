# Photo Booth Frame Prompt

Use this prompt when creating a new check-in frame for an artifact.

```text
Tạo một khung photo booth cho địa điểm [TÊN ĐỊA ĐIỂM] trong phong cách poster/nhật báo du lịch Huế.

Yêu cầu quan trọng:
- Giữ một vùng chữ nhật lớn màu đen thuần (#000000) ở giữa để làm vùng thay thế bằng camera người dùng.
- Vùng đen phải liền mạch, không có chữ, không có họa tiết, không có ảnh, không có texture, không có gradient và không đổ bóng quá mạnh.
- Vùng đen nên chiếm khoảng 35-60% diện tích khung để người dùng hiện rõ.
- Các phần trang trí, tiêu đề, ảnh nền, viền poster, chú thích, logo và họa tiết nằm bên ngoài vùng đen.
- Không đặt nhân vật, vật thể quan trọng hoặc chữ đè lên vùng đen.
- Xuất PNG chất lượng cao.

Cách app sẽ xử lý:
- App tự động tìm vùng pixel gần đen (#000000) lớn nhất trong ảnh.
- Vùng đen đó sẽ bị làm trong suốt ở lớp khung.
- Camera người dùng sẽ được vẽ vào vùng đó theo kiểu cover/crop để lấp đầy khung mà không méo hình.
- Toàn bộ phần viền, tiêu đề và trang trí xung quanh được giữ nguyên.

Tên file nên dùng không dấu, viết liền hoặc gạch dưới, khớp với `key` trong registry, ví dụ:
- cuangomon.png
- dienthaihoa.png
- cungtruongsanh.png
```

Quy trình bổ sung frame:
1. Đặt ảnh gốc vào `anh_photo`.
2. Copy PNG dùng trong app sang `frontend/public/assets/photo-booth`.
3. Đăng ký frame trong `frontend/src/data/photoBoothFrames.js` với đúng `artifactId`, `key`, `nameVi`, `nameEn`, và `src`.
4. Nếu là ảnh bìa tổng thể, cập nhật `PHOTO_BOOTH_COVER_FRAME`.

Thông số hiện tại:
- App chỉ mở nút check-in cho địa điểm có frame trong `PHOTO_BOOTH_FRAMES`.
- Ảnh check-in lưu vào album phải có `type: 'checkin'` và `source: 'photo_booth'`.
- Ảnh upload trong chat/scan được lưu là `type: 'scan'` và không xuất hiện trong album check-in.
- Album export chỉ gồm tiêu đề `Về với kinh thành`, ảnh bìa nếu có, và các ảnh check-in photo booth, mỗi khung một ảnh.
