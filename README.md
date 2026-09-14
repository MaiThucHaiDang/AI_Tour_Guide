# AI Tour Guide for Hue Imperial City

AI Tour Guide is a bilingual, multimodal web application for exploring 17 landmarks inside Hue Imperial City. Visitors can ask questions in Vietnamese or English, identify landmarks from photos, use voice input, receive grounded historical answers, and navigate an interactive walking map.

The project combines a FastAPI orchestration layer, PostgreSQL-backed conversation memory, graph-augmented retrieval, Google Gemini models, speech recognition through the Groq API, and a React Leaflet interface.

## Highlights

- Unified text, image, and voice chat with persistent conversation context.
- DB-first RAG over curated Vietnamese and English heritage content.
- Landmark recognition with image preprocessing, candidate reranking, confidence rejection, and API-key fallback.
- Speech-to-text with Whisper Large V3 through the Groq API; browser narration with the Web Speech API.
- GPS-aware map, OSRM walking directions, Dijkstra fallback routing, and time-constrained tour planning.
- Supporting experiences for blog posts, ratings, feedback, passport check-ins, quizzes, photo booth frames, and VNPay Sandbox checkout.
- Reproducible RAG, Vision, and system evaluation with per-case results.

## System Architecture

```text
React 18 + Vite
  ├─ text / camera / image upload / microphone
  ├─ React Leaflet map + browser Web Speech
  └─ blog / rating / game / payment / passport
                    │
                    ▼
FastAPI routers
  ├─ input validation, rate limiting, request IDs
  └─ UnifiedOrchestrator
       ├─ Groq API → Whisper Large V3 speech-to-text
       ├─ Google Gemini → image understanding
       ├─ PostgreSQL conversation memory
       ├─ DB lookup + pgvector retrieval + graph expansion
       └─ Gemini/Groq text-generation fallback
                    │
                    ▼
PostgreSQL 16
  ├─ pgvector embedding index
  ├─ pg_trgm fuzzy matching
  └─ artifacts, bilingual content, graph, chat and product data
```

The orchestrator starts speech recognition and image recognition concurrently when both inputs are present. It then resolves the landmark context, retrieves grounded content, generates a response only when necessary, stores the conversation turn, and returns structured processing metadata to the frontend.

More detail is available in [docs/architecture.md](docs/architecture.md).

## AI and Retrieval Pipeline

### RAG

The source dataset contains 122 curated Vietnamese and English content records for 17 Hue landmarks. The indexing script converts this content into deterministic, sentence-aware documents and stores 768-dimensional Gemini embeddings in PostgreSQL.

Retrieval combines:

1. Exact and normalized landmark lookup.
2. `pg_trgm` fuzzy matching for Vietnamese and English names.
3. `pgvector` cosine-distance search over 393 indexed documents.
4. One-hop knowledge-graph expansion ordered by relation weight.
5. Conversation and selected-landmark context from PostgreSQL.

`scripts/build_rag_index.py` is idempotent: existing `artifact_id + document` records are reused, and only missing embeddings trigger external requests.

### Image understanding

The Vision pipeline validates and resizes images before sending them to Google Gemini. It requests ranked landmark candidates, reranks them against a local feature catalogue, rejects low-confidence or out-of-domain images, and rotates through configured Gemini keys when a provider request fails.

### Voice

Recorded audio is transcribed by Whisper Large V3 through the Groq API. The backend filters silence, noise, and common speech-recognition hallucinations before the transcript enters the chat pipeline. The primary web experience reads answers with chunked Web Speech playback; Edge TTS remains available for the legacy voice endpoint.

### Provider resilience

Gemini and Groq credentials can be supplied as ordered key pools. Text generation follows `LLM_PROVIDER_ORDER`; embedding and Vision use Gemini key fallback, while speech recognition uses Groq key fallback. Provider failures are isolated so the system can still return deterministic DB-backed responses when sufficient local context exists.

## Technology Stack

| Layer | Technologies |
|---|---|
| Backend | Python, FastAPI, Pydantic, async SQLAlchemy |
| AI | Google Gemini text, Vision and embeddings; Groq API; Whisper Large V3 |
| Retrieval | PostgreSQL 16, pgvector, pg_trgm, knowledge graph |
| Frontend | React 18, Vite, React Leaflet, Web Speech API |
| Maps | OpenStreetMap, OSRM, NetworkX/Dijkstra |
| Infrastructure | Docker Compose, Alembic |
| Testing | pytest, pytest-asyncio, Node.js contract tests, ESLint |

## Repository Layout

```text
backend/
  api/              FastAPI route handlers
  core/             configuration, database, cache, security and metrics
  orchestrators/    multimodal request coordination
  repositories/     database retrieval and graph expansion
  services/         AI, Vision, Voice, map, memory and payment services
  tests/            unit, API, security and integration tests
frontend/
  src/              React application
  public/           canonical landmark, map and photo-booth assets
  scripts/          frontend behavior and contract tests
scripts/            data seed, RAG indexing, graph and feedback utilities
migrations/         Alembic database migrations
evaluation/         datasets, benchmark runners and auditable results
docs/               architecture, demo and troubleshooting notes
docker/             PostgreSQL/pgvector and backend containers
```

## Prerequisites

- Python 3.12 recommended
- Node.js 18 or later
- Docker Desktop or another Docker Compose installation
- Google Gemini and Groq API keys for the complete AI workflow

OpenStreetMap and OSRM do not require a Google Maps API key.

## Local Setup

### 1. Clone and configure

```bash
git clone https://github.com/MaiThucHaiDang/AI_Tour_Guide.git
cd AI_Tour_Guide
cp .env.example .env
```

On Windows PowerShell, use `Copy-Item .env.example .env` instead of `cp`.

At minimum, configure these values in `.env`:

```env
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_tour_guide
```

Additional keys may be supplied through `GEMINI_API_KEY_2` through `GEMINI_API_KEY_4`, `GEMINI_API_KEYS`, and `GROQ_API_KEYS`. Never commit the local `.env` file.

### 2. Start PostgreSQL

```bash
docker compose -f docker/docker-compose.yml up -d postgres
```

The container uses `pgvector/pgvector:pg16` and exposes PostgreSQL on port `5432`.

### 3. Install and initialize the backend

```bash
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS/Linux
source .venv/bin/activate
```

Install dependencies, apply migrations, and load the curated data:

```bash
python -m pip install -r backend/requirements.txt
alembic upgrade head
python scripts/seed_data.py
python scripts/build_rag_index.py
```

Build the knowledge graph after configuring a working text-generation provider:

```bash
python scripts/build_graph.py
```

To inspect document coverage without writing embeddings:

```bash
python scripts/build_rag_index.py --dry-run
```

Start FastAPI:

```bash
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Useful URLs:

- API documentation: <http://127.0.0.1:8000/docs>
- Liveness: <http://127.0.0.1:8000/api/v1/health/live>
- Readiness: <http://127.0.0.1:8000/api/v1/health/ready>

### 4. Start the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

The application is served at <https://localhost:5173>. Vite uses a local self-signed certificate so the browser can grant camera, microphone, and geolocation permissions. A browser warning is expected on the first local visit.

## Main API Surface

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/v1/chat/unified` | Text, image, voice, location and conversation input |
| `POST` | `/api/v1/recognize` | Standalone landmark image recognition |
| `POST` | `/api/v1/voice/chat` | Legacy voice-chat pipeline |
| `GET` | `/api/v1/map/route` | Walking route with OSRM/local fallback |
| `GET` | `/api/v1/map/plan-tour` | Time-constrained landmark itinerary |
| `POST` | `/api/v1/feedback` | Persist answer feedback |
| `GET` | `/api/v1/metrics` | In-process counters and latency snapshot |

Blog, game, payment, rating, map configuration, and health endpoints are documented interactively at `/docs`.

## Evaluation

The repository includes project-level validation sets and stores raw per-case predictions so reported metrics can be audited. These are internal project benchmarks, not external research benchmarks.

### RAG retrieval

| Metric | Held-out result |
|---|---:|
| Test queries | 68 |
| Hit@1 | 88.2% |
| Hit@3 | 94.1% |
| Mean reciprocal rank | 0.9069 |
| Graph-expanded context recall | 97.1% |
| OOD detection F1 | 80.0% |
| OOD rejection | 100.0% (10/10) |
| Database retrieval latency p50 / p95 | 8.08 / 10.34 ms |

The distance threshold was selected on the development split and applied unchanged to the held-out test split.

### Landmark image recognition

| Metric | Internal 43-image benchmark |
|---|---:|
| Top-1 landmark accuracy | 52.6% |
| Top-3 landmark recall | 63.2% |
| In-domain/OOD classification F1 | 98.7% |
| OOD rejection | 100.0% (5/5) |
| Provider failures | 0 |
| End-to-end latency p50 / p95 | 3.77 / 8.00 s |

The 98.7% figure measures in-domain versus out-of-domain classification, not landmark identity accuracy.

See [evaluation/README.md](evaluation/README.md) for the isolated Docker workflow and [evaluation/results/evaluation_report.md](evaluation/results/evaluation_report.md) for the complete report.

## Tests and Quality Checks

Run backend tests from the repository root:

```bash
python -m pytest backend/tests -q
```

Run frontend checks:

```bash
cd frontend
npm run lint
npm run build
npm test
```

Provider credentials and model access can be checked without printing secret values:

```bash
python evaluation/check_provider_access.py
```

Use `--smoke` only when you intentionally want to send minimal requests to the configured providers.

## Operational Notes

- Camera, microphone, geolocation, provider access, and OSRM routing depend on browser permissions or external services.
- The Vision set contains visually similar imperial structures; top-1 recognition remains the main improvement target.
- Web Speech voice availability differs by browser and operating system. Current Chrome and Edge releases provide the most reliable playback behavior.
- Uploaded blog covers and RAG debug logs are runtime files and are intentionally excluded from Git.
- VNPay support targets the Sandbox environment and requires separate merchant credentials.

## Additional Documentation

- [Architecture](docs/architecture.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Demo script](docs/demo_script.md)
- [Photo-booth frame prompt](docs/photo_booth_frame_prompt.md)
- [Evaluation methodology](evaluation/README.md)
