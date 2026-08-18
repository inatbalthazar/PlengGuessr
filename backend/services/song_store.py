"""
song_store.py — Read/write songs.json flat-file database.
"""
import json
import os
from typing import List, Dict, Any

SONGS_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "songs.json")
)


def load_songs() -> List[Dict[str, Any]]:
    """Load all songs from songs.json. Returns empty list if file missing."""
    if not os.path.exists(SONGS_FILE):
        return []
    with open(SONGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_songs(songs: List[Dict[str, Any]]) -> None:
    """Overwrite songs.json with provided list."""
    with open(SONGS_FILE, "w", encoding="utf-8") as f:
        json.dump(songs, f, ensure_ascii=False, indent=2)


import re

def normalize_key(artist: str, title: str) -> tuple[str, str]:
    norm_a = re.sub(r"[^a-zA-Z0-9ก-๙]", "", artist or "").lower()
    norm_t = re.sub(r"[^a-zA-Z0-9ก-๙]", "", title or "").lower()
    return (norm_a, norm_t)


def add_song(song: Dict[str, Any]) -> None:
    """Add or update a song entry in songs.json (prevents duplicates)."""
    songs = load_songs()
    target_key = normalize_key(song.get("artist", ""), song.get("title", ""))
    target_id = song.get("id")

    updated = False
    for i, s in enumerate(songs):
        s_key = normalize_key(s.get("artist", ""), s.get("title", ""))
        if s.get("id") == target_id or (s_key[0] and s_key[1] and s_key == target_key):
            songs[i] = song
            updated = True
            break

    if not updated:
        songs.append(song)

    save_songs(songs)




def delete_song(song_id: str) -> bool:
    """Remove song by id. Returns True if removed, False if not found."""
    songs = load_songs()
    filtered = [s for s in songs if s["id"] != song_id]
    if len(filtered) == len(songs):
        return False
    save_songs(filtered)
    return True
