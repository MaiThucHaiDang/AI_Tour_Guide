"""FastAPI application entrypoint for the backend."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

_LOGGER = logging.getLogger(__name__)

# Load .env from backend folder first, then repo root as fallback
BACKEND_ROOT = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_ROOT.parents[1]

load_dotenv(BACKEND_ROOT / ".env")
load_dotenv(REPO_ROOT / ".env", override=False)

if not os.getenv("GROQ_API_KEY"):
    _LOGGER.warning("GROQ_API_KEY is not set. Voice STT/LLM will fail.")

from routers.voice_router import voice_router


app = FastAPI(title="AI Tour Guide Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(voice_router, tags=["Voice Feature"])


@app.get("/")
async def root() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "ok"}