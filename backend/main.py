"""
main.py — FastAPI application entry point.

Dev mode:  uvicorn backend.main:app --reload --port 8000
           (Vite dev server runs on :5173 and proxies /api → :8000)

Prod mode: npm run build  →  uvicorn backend.main:app --port 8000
           (FastAPI serves the React dist/ as static files)
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.routers import songs as songs_router

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="PlengGuessr API",
    description="Bandle-style song guessing game — stem separation with Demucs",
    version="1.0.0",
)

# CORS — allow Vite dev server (localhost:5173) in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
app.include_router(songs_router.router, prefix="/api", tags=["songs"])

# ---------------------------------------------------------------------------
# Static: audio files
# Vite serves frontend/public/** at its own origin in dev.
# In prod the FastAPI server exposes them at /audio/...
# ---------------------------------------------------------------------------
AUDIO_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "audio")
)
os.makedirs(AUDIO_DIR, exist_ok=True)
app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")

# ---------------------------------------------------------------------------
# Static: React production build (only if dist/ exists)
# ---------------------------------------------------------------------------
FRONTEND_DIST = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
)
if os.path.isdir(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
