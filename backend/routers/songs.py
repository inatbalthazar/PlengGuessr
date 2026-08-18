"""
songs.py — FastAPI router for all /api/* endpoints.

Endpoints:
  POST   /api/process-song      Start background pipeline (download + trim + demucs)
  GET    /api/status/{task_id}  Poll task progress (every 1-2 s from frontend)
  GET    /api/songs             List all songs in songs.json
  DELETE /api/songs/{song_id}   Remove a song + its audio files
"""
from __future__ import annotations

import os
import shutil
import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile

from backend.services import downloader, playlist_store, separator, song_store


router = APIRouter()

# ---------------------------------------------------------------------------
# In-memory task registry (lives as long as the server process)
# ---------------------------------------------------------------------------
tasks: dict[str, dict] = {}

# Absolute path to frontend/public/audio  (Vite dev serves it directly)
AUDIO_BASE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "public", "audio")
)


# ---------------------------------------------------------------------------
# Background pipeline
# ---------------------------------------------------------------------------

def _update(task_id: str, **kwargs) -> None:
    tasks[task_id].update(kwargs)


def _run_pipeline(
    task_id: str,
    youtube_url: Optional[str],
    title: str,
    artist: str,
    start_time: float,
    duration: float,
    upload_path: Optional[str],
) -> None:
    """
    Long-running task: download / trim → Demucs → save metadata.
    Runs in a BackgroundTasks thread so it doesn't block the event loop.
    """
    song_id = str(uuid.uuid4())[:8]
    work_dir = os.path.join(AUDIO_BASE, f"_work_{song_id}")
    os.makedirs(work_dir, exist_ok=True)

    try:
        # ---- Step 1: Download or trim ------------------------------------ #
        _update(task_id, status="downloading", progress=10,
                message="⬇️  กำลังดาวน์โหลดและตัดเสียง...")

        input_wav = os.path.join(work_dir, "input.wav")

        if youtube_url:
            downloader.download_and_trim(youtube_url, start_time, duration, input_wav)
        elif upload_path:
            downloader.trim_file(upload_path, start_time, duration, input_wav)

        # ---- Step 2: Stem separation ------------------------------------- #
        _update(task_id, status="separating", progress=35,
                message="🎛️  กำลังแยกเสียง (Demucs htdemucs)… อาจใช้เวลา 2–10 นาที")

        stem_paths = separator.separate_stems(input_wav, AUDIO_BASE, song_id)

        # ---- Step 3: Persist -------------------------------------------- #
        _update(task_id, status="saving", progress=95,
                message="💾  กำลังบันทึกข้อมูลเพลง...")

        song: dict = {
            "id": song_id,
            "title": title,
            "artist": artist,
            "stems": stem_paths,
        }
        song_store.add_song(song)

        _update(task_id, status="done", progress=100,
                message="🎉  เพิ่มเพลงสำเร็จแล้ว!", song=song, error=None)

    except Exception as exc:  # noqa: BLE001
        _update(task_id, status="error", progress=0,
                message="❌  เกิดข้อผิดพลาด", error=str(exc))
        # Clean up partial audio output (keep work_dir cleanup in finally)
        shutil.rmtree(os.path.join(AUDIO_BASE, song_id), ignore_errors=True)

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
        if upload_path and os.path.exists(upload_path):
            os.remove(upload_path)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/process-song", summary="Start song processing pipeline")
async def process_song(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    artist: str = Form(...),
    start_time: float = Form(0.0),
    duration: float = Form(30.0),
    youtube_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    if not youtube_url and not file:
        raise HTTPException(
            status_code=400,
            detail="กรุณาส่ง YouTube URL หรืออัปโหลดไฟล์เสียงอย่างใดอย่างหนึ่ง",
        )

    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "progress": 0,
        "message": "⏳  รอดำเนินการ...",
        "song": None,
        "error": None,
    }

    # Save uploaded file to disk before handing off to background task
    upload_path: Optional[str] = None
    if file:
        upload_dir = os.path.join(AUDIO_BASE, "_uploads")
        os.makedirs(upload_dir, exist_ok=True)
        ext = os.path.splitext(file.filename or "audio.mp3")[1] or ".mp3"
        upload_path = os.path.join(upload_dir, f"{task_id}{ext}")
        content = await file.read()
        with open(upload_path, "wb") as fh:
            fh.write(content)

    background_tasks.add_task(
        _run_pipeline,
        task_id, youtube_url, title, artist,
        start_time, duration, upload_path,
    )

    return {"task_id": task_id}


@router.get("/status/{task_id}", summary="Poll task status")
async def get_status(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="ไม่พบ task_id นี้")
    return tasks[task_id]


PLAYLIST_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "playlist.txt")
)


def _run_playlist_pipeline(task_id: str) -> None:
    if not os.path.exists(PLAYLIST_FILE):
        _update(task_id, status="error", progress=0, message="❌ ไม่พบไฟล์ playlist.txt", error="ไม่พบไฟล์ playlist.txt ในโฟลเดอร์หลัก")
        return

    items = []
    with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if " - " in line:
                parts = line.split(" - ", 1)
                artist, title = parts[0].strip(), parts[1].strip()
            elif "-" in line:
                parts = line.split("-", 1)
                artist, title = parts[0].strip(), parts[1].strip()
            else:
                artist, title = "Unknown Artist", line
            items.append((artist, title))

    if not items:
        _update(task_id, status="error", progress=0, message="⚠️ ไม่มีรายการเพลงใน playlist.txt", error="ไม่มีรายการเพลงใน playlist.txt")
        return

    existing_songs = song_store.load_songs()
    existing_keys = {
        song_store.normalize_key(s.get("artist", ""), s.get("title", ""))
        for s in existing_songs
    }

    total = len(items)
    success = 0
    skipped = 0
    failed = 0

    for idx, (artist, title) in enumerate(items, 1):
        pct = int(((idx - 1) / total) * 100)
        key = song_store.normalize_key(artist, title)
        query = f"{artist} - {title}"

        if key in existing_keys:
            skipped += 1
            _update(task_id, progress=pct, message=f"⏭️ [{idx}/{total}] เพลง {title} มีในระบบแล้ว ข้าม...")
            continue

        _update(task_id, progress=pct, message=f"🔎 [{idx}/{total}] ค้นหาบน YouTube: {query}...")

        song_id = str(uuid.uuid4())[:8]
        work_dir = os.path.join(AUDIO_BASE, f"_work_{song_id}")
        os.makedirs(work_dir, exist_ok=True)

        try:
            search_res = downloader.search_youtube_most_viewed(query, clip_duration=20.0)
            yt_url = search_res["youtube_url"]
            start_time = search_res["start_time"]
            duration = search_res["duration"]

            _update(task_id, progress=pct + 1, message=f"⬇️ [{idx}/{total}] ตัดคลิปท่อนท้ายเพลง 20s (เริ่ม {start_time}s): {title}")
            input_wav = os.path.join(work_dir, "input.wav")
            downloader.download_and_trim(yt_url, start_time, duration, input_wav)

            _update(task_id, progress=pct + 2, message=f"🎛️ [{idx}/{total}] แยกเสียง Demucs: {title}...")
            stem_paths = separator.separate_stems(input_wav, AUDIO_BASE, song_id)

            song_obj = {
                "id": song_id,
                "title": title,
                "artist": artist,
                "stems": stem_paths,
            }
            song_store.add_song(song_obj)
            existing_keys.add(key)
            success += 1

        except Exception as exc:
            failed += 1
            shutil.rmtree(os.path.join(AUDIO_BASE, song_id), ignore_errors=True)
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    _update(
        task_id,
        status="done",
        progress=100,
        message=f"🎉 สำเร็จ! เพิ่ม {success} เพลง (ข้าม {skipped}, ล้มเหลว {failed})",
        error=None,
    )


@router.post("/process-playlist", summary="Process playlist.txt in batch")
async def process_playlist(background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "progress": 0,
        "message": "⏳ กำลังเริ่มประมวลผล playlist.txt...",
        "song": None,
        "error": None,
    }
    background_tasks.add_task(_run_playlist_pipeline, task_id)
    return {"task_id": task_id}


@router.get("/playlist", summary="Get playlist.txt content")
async def get_playlist():
    if not os.path.exists(PLAYLIST_FILE):
        return {"songs": []}
    items = []
    with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                items.append(line)
    return {"songs": items}


@router.get("/songs", summary="Get all songs")
async def get_songs():
    return song_store.load_songs()


@router.delete("/songs/{song_id}", summary="Delete a song")
async def delete_song(song_id: str):
    if not song_store.delete_song(song_id):
        raise HTTPException(status_code=404, detail=f"ไม่พบเพลง id={song_id}")

    # Remove audio files
    audio_dir = os.path.join(AUDIO_BASE, song_id)
    shutil.rmtree(audio_dir, ignore_errors=True)

    return {"message": f"ลบเพลง {song_id} เรียบร้อยแล้ว"}


# ---------------------------------------------------------------------------
# Custom Playlists / Quizzes
# ---------------------------------------------------------------------------

@router.get("/custom-playlists", summary="Get all custom playlists/quizzes")
async def get_custom_playlists():
    return playlist_store.load_playlists()


@router.post("/custom-playlists", summary="Create or update custom playlist/quiz")
async def create_custom_playlist(playlist: dict):
    if not playlist.get("name"):
        raise HTTPException(status_code=400, detail="กรุณาระบุชื่อ Playlist / Quiz")
    saved = playlist_store.add_or_update_playlist(playlist)
    return saved


@router.delete("/custom-playlists/{playlist_id}", summary="Delete custom playlist/quiz")
async def delete_custom_playlist(playlist_id: str):
    if not playlist_store.delete_playlist(playlist_id):
        raise HTTPException(status_code=400, detail="ไม่สามารถลบ Playlist นี้ได้")
    return {"message": "ลบ Playlist เรียบร้อยแล้ว"}


