"""
enrich_deezer.py — High-Res 1000x1000 Album Cover fetcher via Deezer API
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


def clean_term(t: str) -> str:
    return re.sub(r"\(.*?\)|\[.*?\]|- Radio Edit|- Remix", "", t, flags=re.IGNORECASE).strip()


def fetch_deezer_cover(artist: str, title: str) -> str:
    main_artist = artist.split(",")[0].split("&")[0].split("feat")[0].strip()
    clean_t = clean_term(title)
    queries = [f"{artist} {title}", f"{main_artist} {clean_t}", clean_t]

    for q in queries:
        if not q.strip():
            continue
        try:
            url = f"https://api.deezer.com/search?q={urllib.parse.quote(q)}&limit=1"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                res = data.get("data", [])
                if res and "album" in res[0]:
                    art = res[0]["album"].get("cover_xl") or res[0]["album"].get("cover_big")
                    if art:
                        return art
        except Exception:
            pass
        time.sleep(0.04)
    return ""


def main():
    if not os.path.exists(SONGS_FILE):
        print("songs.json not found")
        return

    with open(SONGS_FILE, "r", encoding="utf-8") as f:
        songs = json.load(f)

    print(f"Starting Deezer Cover enrichment for {len(songs)} songs...")

    filled = 0
    for idx, s in enumerate(songs, 1):
        if not s.get("cover_url"):
            art = fetch_deezer_cover(s.get("artist", ""), s.get("title", ""))
            if art:
                s["cover_url"] = art
                filled += 1
                print(f"[{idx}/{len(songs)}] ✅ {s.get('artist')} - {s.get('title')}")
            else:
                print(f"[{idx}/{len(songs)}] ❌ {s.get('artist')} - {s.get('title')}")

        if idx % 15 == 0:
            with open(SONGS_FILE, "w", encoding="utf-8") as f:
                json.dump(songs, f, ensure_ascii=False, indent=2)

    with open(SONGS_FILE, "w", encoding="utf-8") as f:
        json.dump(songs, f, ensure_ascii=False, indent=2)

    with_covers = [s for s in songs if s.get('cover_url')]
    print(f"🎉 Complete! {len(with_covers)} / {len(songs)} songs have album cover URLs!")


if __name__ == "__main__":
    main()
