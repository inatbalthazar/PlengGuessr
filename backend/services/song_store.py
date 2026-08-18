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
import urllib.request
import urllib.parse

def _query_itunes(query: str) -> str | None:
    if not query.strip():
        return None
    url = f"https://itunes.apple.com/search?term={urllib.parse.quote(query)}&entity=song&limit=1"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    try:
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("results", [])
            if results and "artworkUrl100" in results[0]:
                art = results[0]["artworkUrl100"]
                return art.replace("100x100bb", "600x600bb")
    except Exception:
        pass
    return None


def fetch_itunes_cover(artist: str, title: str) -> str:
    """Fetch high-res album cover URL from iTunes Search API with smart query fallbacks."""
    main_artist = artist.split(",")[0].split("&")[0].split("feat")[0].strip()
    clean_title = re.sub(r"\(.*?\)|\[.*?\]|- Radio Edit|- Remix", "", title, flags=re.IGNORECASE).strip()

    queries = [
        f"{artist} {title}",
        f"{main_artist} {clean_title}",
        f"{main_artist} {title}",
        f"{clean_title}",
    ]

    for q in queries:
        art = _query_itunes(q)
        if art:
            return art
    return ""


def normalize_key(artist: str, title: str) -> tuple[str, str]:
    norm_a = re.sub(r"[^a-zA-Z0-9ก-๙]", "", artist or "").lower()
    norm_t = re.sub(r"[^a-zA-Z0-9ก-๙]", "", title or "").lower()
    return (norm_a, norm_t)


def add_song(song: Dict[str, Any]) -> None:
    """Add or update a song entry in songs.json (prevents duplicates)."""
    songs = load_songs()
    target_key = normalize_key(song.get("artist", ""), song.get("title", ""))
    target_id = song.get("id")

    # Auto fetch cover URL if missing
    if not song.get("cover_url"):
        song["cover_url"] = fetch_itunes_cover(song.get("artist", ""), song.get("title", ""))

    updated = False
    for i, s in enumerate(songs):
        s_key = normalize_key(s.get("artist", ""), s.get("title", ""))
        if s.get("id") == target_id or (s_key[0] and s_key[1] and s_key == target_key):
            # Preserve existing cover if not provided
            if not song.get("cover_url") and s.get("cover_url"):
                song["cover_url"] = s["cover_url"]
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
