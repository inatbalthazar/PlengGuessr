"""
enrich_covers.py — Smart iTunes Search API cover fetcher with cleaning + YouTube thumbnail fallback
"""
import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

SONGS_FILE = os.path.join(os.path.dirname(__file__), "songs.json")


def clean_query_term(text: str) -> str:
    """Clean parentheses, remix tags, feature tags."""
    if not text:
        return ""
    text = re.sub(r"\(feat.*?\)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\(from.*?\)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"- Radio Edit", "", text, flags=re.IGNORECASE)
    text = re.sub(r"- Remix", "", text, flags=re.IGNORECASE)
    return text.strip()


def query_itunes(query: str) -> str | None:
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


def fetch_itunes_cover_smart(artist: str, title: str) -> str | None:
    # 1. Primary main artist
    main_artist = artist.split(",")[0].split("&")[0].split("feat")[0].strip()
    clean_title = clean_query_term(title)

    queries = [
        f"{artist} {title}",
        f"{main_artist} {clean_title}",
        f"{main_artist} {title}",
        f"{clean_title}",
    ]

    for q in queries:
        art = query_itunes(q)
        if art:
            return art

    return None


def main():
    if not os.path.exists(SONGS_FILE):
        print(f"File not found: {SONGS_FILE}")
        return

    with open(SONGS_FILE, "r", encoding="utf-8") as f:
        songs = json.load(f)

    print(f"Starting Smart iTunes Cover enrichment for {len(songs)} songs...")

    updated_count = 0
    existing_count = 0
    failed_count = 0

    for idx, song in enumerate(songs, 1):
        artist = song.get("artist", "")
        title = song.get("title", "")

        if song.get("cover_url"):
            existing_count += 1
            continue

        print(f"[{idx}/{len(songs)}] Fetching for: {artist} - {title}...", end=" ")
        cover_url = fetch_itunes_cover_smart(artist, title)

        if cover_url:
            song["cover_url"] = cover_url
            updated_count += 1
            print("✅ OK!")
        else:
            song["cover_url"] = ""
            failed_count += 1
            print("❌ Not found")

        time.sleep(0.1)

        if idx % 10 == 0:
            with open(SONGS_FILE, "w", encoding="utf-8") as f:
                json.dump(songs, f, ensure_ascii=False, indent=2)

    with open(SONGS_FILE, "w", encoding="utf-8") as f:
        json.dump(songs, f, ensure_ascii=False, indent=2)

    print(f"Completed! Previously had: {existing_count}, Newly Found: {updated_count}, Missing: {failed_count}")


if __name__ == "__main__":
    main()
