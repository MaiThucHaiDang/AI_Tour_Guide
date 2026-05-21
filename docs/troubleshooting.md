# AI Tour Guide - Troubleshooting local

Tai lieu nay gom cac loi hay gap khi chay demo local va cach khoanh vung nhanh.

## Backend khong ket noi duoc

Dau hieu:

- Chat hien thong bao backend khong reachable.
- Browser console co `Failed to fetch`.
- Frontend mo duoc nhung gui cau hoi that bai.

Kiem tra:

```powershell
Invoke-WebRequest -Uri http://localhost:8000/api/v1/health/live -UseBasicParsing
Invoke-WebRequest -Uri http://localhost:8000/api/v1/health/ready -UseBasicParsing
```

Xu ly:

- Dam bao backend FastAPI dang chay dung port.
- Kiem tra `.env` va `DATABASE_URL`.
- Neu ready fail vi DB, chay Postgres va migration/seed.

## Frontend khong goi dung backend

Dau hieu:

- Frontend chay nhung API 404/connection refused.
- Network tab goi sai host/port.

Kiem tra:

- Xem config trong `frontend/src/services/apiService.js`.
- Dam bao Vite proxy hoac URL API khop backend port.

Xu ly:

- Restart frontend sau khi doi env/config.
- Dung cung protocol localhost local, tranh tron HTTP/HTTPS neu browser chan media/API.

## Database loi

Dau hieu:

- `/api/v1/health/ready` fail.
- Backend log co loi asyncpg/connection refused/authentication failed.

Kiem tra:

```powershell
alembic current
alembic upgrade head
python scripts\seed_data.py
```

Xu ly:

- Kiem tra Postgres dang chay.
- Kiem tra user/password/database trong `DATABASE_URL`.
- Chay migration truoc seed.

## API key hoac provider AI loi

Dau hieu:

- Recognition/LLM/STT loi nhung backend van live.
- Chat bao voice/recognition chua san sang.
- Backend log co provider error.

Kiem tra:

- `GEMINI_API_KEY`
- `GROQ_API_KEY`
- Model names trong `.env`

Xu ly:

- Dat key hop le trong `.env`.
- Restart backend sau khi doi key.
- Neu provider loi tam thoi, demo text direct fact/DB answer truoc.

## Camera bi chan

Dau hieu:

- Modal camera hien thong bao permission denied hoac browser khong ho tro.

Xu ly:

- Cap quyen camera trong browser site settings.
- Chay frontend qua `localhost` hoac HTTPS.
- Dung nut upload anh neu camera khong dung duoc.

## Microphone bi chan

Dau hieu:

- Chat hien thong bao micro bi chan/khong tim thay.
- Nut mic khong bat dau recording.

Xu ly:

- Cap quyen microphone trong browser site settings.
- Kiem tra thiet bi input cua he dieu hanh.
- Nhap cau hoi bang text neu mic khong kha dung.

## Timeout khi gui anh/audio

Dau hieu:

- Chat bao request qua lau.
- Anh/audio lon hoac provider phan hoi cham.

Xu ly:

- Thu anh nho hon/ro hon.
- Ghi am ngan hon.
- Kiem tra backend log xem cham o Vision, STT, LLM hay TTS.
- Neu can demo tiep, dung text-only flow.

## Feedback khong luu duoc

Dau hieu:

- Frontend khong crash nhung backend log co `feedback persist failed`.
- `python scripts\feedback_report.py` khong thay event moi.

Kiem tra:

```powershell
alembic upgrade head
python scripts\feedback_report.py
```

Xu ly:

- Dam bao migration `0002_feedback_events` da chay.
- Kiem tra ket noi DB.
- Xem backend log theo request id.

## Lenh verify nhanh

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests
cd frontend
npm run lint
npm run build
```
