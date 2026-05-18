# AI Tour Guide — Documentation

## Architecture

- **Frontend**: React 18 + Vite (in `frontend/`)
- **Backend**: FastAPI unified backend (in `backend/`)
- **Database**: PostgreSQL 16 via async SQLAlchemy

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/health` | GET | Health check |
| `/api/v1/recognize` | POST | Image recognition |
| `/api/v1/voice/chat` | POST | Voice chat |

## Running

See `guideRun.md` in the project root.
