"""
enrich_covers.py — Batch fetch album cover URLs from iTunes Search API for songs.json
"""
import json
import os
import sys
import time
import urllib.request
import urllib.parse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

SONGS_FILE = os.path.join(os.path.dirname(__file__), "songs.json")


def fetch_itunes_cover(artist: str, title: str) -> str | None:
    query = f"{artist} {title}".strip()
    url = f"https://itunes.apple.com/search?term={urllib.parse.quote(query)}&entity=song&limit=1"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("results", [])
            if results and "artworkUrl100" in results[0]:
                art = results[0]["artworkUrl100"]
                return art.replace("100x100bb", "600x600bb")
    except Exception:
        pass

    # Try title only as fallback
    query_title = title.strip()
    url_title = f"https://itunes.apple.com/search?term={urllib.parse.quote(query_title)}&entity=song&limit=1"
    req_title = urllib.request.Request(url_title, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    try:
        with urllib.request.urlopen(req_title, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("results", [])
            if results and "artworkUrl100" in results[0]:
                art = results[0]["artworkUrl100"]
                return art.replace("100x100bb", "600x600bb")
    except Exception:
        pass

    return None


def main():
    if not os.path.exists(SONGS_FILE):
        print(f"File not found: {SONGS_FILE}")
        return

    with open(SONGS_FILE, "r", encoding="utf-8") as f:
        songs = json.load(f)

    print(f"Starting iTunes Album Cover enrichment for {len(songs)} songs...")

    updated_count = 0
    skipped_count = 0
    failed_count = 0

    for idx, song in enumerate(songs, 1):
        artist = song.get("artist", "")
        title = song.get("title", "")
        existing_cover = song.get("cover_url")

        if existing_cover:
            skipped_count += 1
            continue

        print(f"[{idx}/{len(songs)}] Fetching cover for: {artist} - {title}...", end=" ")
        cover_url = fetch_itunes_cover(artist, title)

        if cover_url:
            song["cover_url"] = cover_url
            updated_count += 1
            print("OK")
        else:
            song["cover_url"] = ""
            failed_count += 1
            print("Not found")

        time.sleep(0.12)

        if idx % 15 == 0:
            with open(SONGS_FILE, "w", encoding="utf-8") as f:
                json.dump(songs, f, ensure_ascii=False, indent=2)

    with open(SONGS_FILE, "w", encoding="utf-8") as f:
        json.dump(songs, f, ensure_ascii=False, indent=2)

    print(f"Completed! Updated: {updated_count}, Skipped: {skipped_count}, Failed: {failed_count}")


if __name__ == "__main__":
    main()
