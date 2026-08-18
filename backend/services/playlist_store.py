"""
playlist_store.py — Read/write playlists.json flat-file database.
"""
import json
import os
import uuid
from typing import List, Dict, Any, Optional

PLAYLISTS_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "playlists.json")
)

DEFAULT_PLAYLISTS = [
    {
        "id": "all-songs",
        "name": "🎵 รวมเพลงทั้งหมด",
        "description": "คลังเพลงทั้งหมดที่มีในระบบ",
        "song_ids": [],
    }
]


def load_playlists() -> List[Dict[str, Any]]:
    """Load all playlists. Creates default playlists.json if missing."""
    if not os.path.exists(PLAYLISTS_FILE):
        save_playlists(DEFAULT_PLAYLISTS)
        return DEFAULT_PLAYLISTS

    try:
        with open(PLAYLISTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not data:
                return DEFAULT_PLAYLISTS
            return data
    except Exception:
        return DEFAULT_PLAYLISTS


def save_playlists(playlists: List[Dict[str, Any]]) -> None:
    """Save playlists list to playlists.json."""
    with open(PLAYLISTS_FILE, "w", encoding="utf-8") as f:
        json.dump(playlists, f, ensure_ascii=False, indent=2)


def get_playlist(playlist_id: str) -> Optional[Dict[str, Any]]:
    playlists = load_playlists()
    for p in playlists:
        if p["id"] == playlist_id:
            return p
    return None


def add_or_update_playlist(playlist_data: Dict[str, Any]) -> Dict[str, Any]:
    playlists = load_playlists()
    p_id = playlist_data.get("id") or str(uuid.uuid4())[:8]
    playlist_data["id"] = p_id

    updated = False
    for i, p in enumerate(playlists):
        if p["id"] == p_id:
            playlists[i] = playlist_data
            updated = True
            break

    if not updated:
        playlists.append(playlist_data)

    save_playlists(playlists)
    return playlist_data


def delete_playlist(playlist_id: str) -> bool:
    if playlist_id == "all-songs":
        return False
    playlists = load_playlists()
    filtered = [p for p in playlists if p["id"] != playlist_id]
    if len(filtered) == len(playlists):
        return False
    save_playlists(filtered)
    return True
