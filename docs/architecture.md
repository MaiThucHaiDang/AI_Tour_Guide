# AI Tour Guide Architecture

## Product Surface

AI Tour Guide is a web application for visitors exploring cultural and historical artifacts. The primary experience is a guided workspace with destination selection, chat, image capture/upload, voice input, artifact details, audio playback, and answer feedback.

## Runtime Components

- Frontend: React 18 + Vite in `frontend/`.
- Backend: FastAPI unified backend in `backend/`.
- Database: PostgreSQL 16 with async SQLAlchemy.
- Migration: Alembic in `migrations/`.
- AI providers: Gemini Vision/Text via `google-genai`, Groq STT/LLM fallback.
- Browser narration: Web Speech API in the frontend, with chunked playback plus pause/resume/stop controls.

## Main User Flow

```text
Visitor opens the web app
-> chooses a destination or asks directly
-> sends text, photo, camera capture, or voice
-> backend validates size/rate limits
-> STT/Vision runs only when needed
-> retrieval searches artifact data
-> direct DB/template/cache answer is preferred
-> LLM is used only when natural reasoning is needed
-> frontend shows the answer, artifact details, browser narration, and feedback actions
```

## API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/v1/health` | GET | Backward-compatible health check |
| `/api/v1/health/live` | GET | Process liveness |
| `/api/v1/health/ready` | GET | DB and provider readiness |
| `/api/v1/recognize` | POST | Image recognition |
| `/api/v1/chat/unified` | POST | Text/image/voice unified chat |
| `/api/v1/voice/chat` | POST | Legacy voice-only chat |
| `/api/v1/feedback` | POST | User feedback on answers |
| `/api/v1/metrics` | GET | In-memory operational counters and latency |

## Reliability Controls

- Request id is attached to each response and access log.
- AI endpoints are rate-limited.
- Text, image, and audio payloads are size-checked before provider calls.
- Frontend requests have timeout/abort handling.
- Common answers use in-memory cache for repeated requests.
- Frontend Web Speech playback splits long text into smaller chunks so browser voices can pause/resume reliably.
- Errors shown to visitors are action-oriented; raw provider exceptions stay in logs.

## Data Flow

PostgreSQL stores locations, artifacts, bilingual content, and precomputed audio metadata. Seed data is loaded by `scripts/seed_data.py` after `alembic upgrade head`.

Artifact retrieval currently uses exact name matching, normalized Vietnamese/English matching, and token-overlap scoring. This keeps the local system fast without requiring a vector database for the current dataset.

## Running

See `guideRun.md` in the project root.
