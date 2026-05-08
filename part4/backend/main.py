"""FastAPI application entrypoint for the backend."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path

# Load .env from backend folder so provider constructors see API keys
load_dotenv(Path(__file__).resolve().parent / ".env")

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