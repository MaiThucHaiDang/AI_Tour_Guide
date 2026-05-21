# AI Tour Guide - Demo script 5 phut

Muc tieu: demo nhanh cac luong chinh cua san pham local web: text, image upload, camera, voice, doi ngon ngu va feedback.

## Chuan bi

- Backend FastAPI dang chay.
- Frontend Vite dang chay.
- Database da migrate va seed.
- Browser cho phep microphone/camera neu demo voice/camera.
- Co san 1-2 anh hien vat trong dataset, uu tien Ngo Mon/Thai Hoa Palace/Independence Palace.

## Kich ban

### 1. Mo workspace

1. Mo frontend trong browser.
2. Chon vao AI Tour Guide workspace.
3. Gioi thieu nhanh 3 vung: dia diem/goi y, chat, artifact detail.

Ket qua mong doi: welcome message xuat hien, input text va nut upload/camera/mic san sang.

### 2. Text chat

Hoi bang tieng Viet:

```text
Ngọ Môn được xây năm nào?
```

Ket qua mong doi:

- App tra loi ngan gon ve nam xay dung.
- Neu match artifact, panel hien thong tin hien vat.
- Cac nut helpful/not helpful xuat hien.

### 3. Doi ngon ngu khong mat lich su

1. Bam `EN`.
2. Xac nhan cac message cu van con.
3. Hoi:

```text
Who built Thai Hoa Palace?
```

Ket qua mong doi: chat history khong reset; message moi dung tieng Anh.

### 4. Upload anh

1. Bam upload.
2. Chon anh mau cua hien vat.
3. Gui kem cau hoi ngan neu can:

```text
Tell me briefly about this artifact.
```

Ket qua mong doi:

- Anh hien thanh pending image truoc khi gui.
- Processing timeline thay doi.
- Artifact panel duoc cap nhat neu nhan dien/tim thay hien vat.

### 5. Camera fallback

1. Bam camera.
2. Neu browser cho quyen, chup anh va bam su dung.
3. Neu browser chan quyen, chi ra thong bao recovery va nut upload fallback.

Ket qua mong doi: user co duong tiep tuc bang upload anh, khong bi ket o modal loi.

### 6. Voice

1. Giu nut mic va noi:

```text
Kể ngắn về Cửu Đỉnh trong 30 giây
```

2. Tha/dung ghi am.

Ket qua mong doi:

- App chuyen voice thanh text.
- Neu micro bi chan, chat hien thong bao cap quyen hoac nhap text thay the.
- Text answer xuat hien; audio co the phat neu TTS san sang.

### 7. Feedback

1. Bam helpful cho mot cau tra loi dung.
2. Bam not helpful cho mot cau tra loi khac neu can.
3. Sau demo, chay:

```powershell
python scripts\feedback_report.py
```

Ket qua mong doi: report hien tong feedback va nhom feedback theo artifact/source.

## Smoke checklist

- [ ] Text chat tra loi duoc.
- [ ] Doi VI/EN khong mat lich su.
- [ ] Upload anh khong crash.
- [ ] Camera co fallback upload neu bi chan.
- [ ] Voice co fallback text neu mic bi chan.
- [ ] Feedback luu duoc va report doc duoc.
- [ ] Reset conversation tao session moi.
