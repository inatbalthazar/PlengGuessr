"""
create_playlists.py — Categorize songs.json into 3 new Playlists:
  1. เพลงสากล (International)
  2. เพลงไทย (Thai)
  3. K-Pop (Korean)
"""
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

SONGS_FILE = os.path.join(os.path.dirname(__file__), "songs.json")
PLAYLISTS_FILE = os.path.join(os.path.dirname(__file__), "playlists.json")

KPOP_ARTISTS = [
    "bts", "blackpink", "twice", "newjeans", "exo", "exo-k", "red velvet", "bigbang",
    "girls' generation", "super junior", "apink", "g-dragon", "gd x taeyang", "taeyang",
    "aoa", "exid", "2ne1", "gfriend", "monsta x", "taeyeon", "i.o.i", "iu", "bol4",
    "ikon", "treasure", "cortis", "wonder girls", "got7", "sistar", "katseye", "rosé"
]


def contains_thai(text: str) -> bool:
    return bool(re.search(r"[\u0e00-\u0e7f]", text))


def contains_korean(text: str) -> bool:
    return bool(re.search(r"[\uac00-\ud7af\u1100-\u11ff]", text))


def main():
    if not os.path.exists(SONGS_FILE):
        print("songs.json not found")
        return

    with open(SONGS_FILE, "r", encoding="utf-8") as f:
        songs = json.load(f)

    thai_ids = []
    kpop_ids = []
    inter_ids = []

    for s in songs:
        s_id = s.get("id")
        artist = s.get("artist", "")
        title = s.get("title", "")
        combined = f"{artist} {title}".lower()

        if contains_thai(combined):
            thai_ids.append(s_id)
        elif contains_korean(combined) or any(k in combined for k in KPOP_ARTISTS):
            kpop_ids.append(s_id)
        else:
            inter_ids.append(s_id)

    playlists = [
        {
            "id": "all-songs",
            "name": "🎵 รวมเพลงทั้งหมด",
            "description": "คลังเพลงทั้งหมดที่มีในระบบ",
            "song_ids": []
        },
        {
            "id": "inter-songs",
            "name": "🌎 เพลงสากล (International)",
            "description": "รวมฮิตเพลงสากลยอดนิยมระดับโลก",
            "song_ids": inter_ids
        },
        {
            "id": "thai-songs",
            "name": "🇹🇭 เพลงไทย (Thai Hits)",
            "description": "รวมฮิตเพลงไทยยอดนิยม",
            "song_ids": thai_ids
        },
        {
            "id": "kpop-songs",
            "name": "🇰🇷 K-Pop (Korean Hits)",
            "description": "รวมฮิตเพลง K-Pop ศิลปินเกาหลีระดับโลก",
            "song_ids": kpop_ids
        }
    ]

    with open(PLAYLISTS_FILE, "w", encoding="utf-8") as f:
        json.dump(playlists, f, ensure_ascii=False, indent=2)

    print(f"✅ Successfully created 3 new Playlists / Quizzes:")
    print(f"   1. 🌎 เพลงสากล ({len(inter_ids)} เพลง)")
    print(f"   2. 🇹🇭 เพลงไทย ({len(thai_ids)} เพลง)")
    print(f"   3. 🇰🇷 K-Pop ({len(kpop_ids)} เพลง)")
    print(f"   (รวมทั้งหมด {len(songs)} เพลง)")


if __name__ == "__main__":
    main()
