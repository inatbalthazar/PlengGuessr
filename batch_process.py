"""
batch_process.py — Batch song processing script from playlist.txt

Usage:
    python batch_process.py              # process playlist.txt in workspace root
    python batch_process.py path/to/file.txt
"""
import os
import sys
import uuid
import shutil

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from backend.services import downloader, separator, song_store

AUDIO_BASE = os.path.join(PROJECT_ROOT, "frontend", "public", "audio")
PLAYLIST_FILE = os.path.join(PROJECT_ROOT, "playlist.txt")


def parse_playlist(file_path: str) -> list[tuple[str, str]]:
    """Parse artist and title from playlist file (format: Artist - Title)."""
    items = []
    if not os.path.exists(file_path):
        print(f"❌ ไม่พบไฟล์ {file_path}")
        return items

    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
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

    return items


def main():
    playlist_path = sys.argv[1] if len(sys.argv) > 1 else PLAYLIST_FILE
    print(f"🎵 กำลังอ่านรายการเพลงจาก: {playlist_path}")

    items = parse_playlist(playlist_path)
    if not items:
        print("⚠️  ไม่มีรายการเพลงให้ดำเนินการ")
        return

    existing_songs = song_store.load_songs()
    existing_keys = {
        song_store.normalize_key(s.get("artist", ""), s.get("title", ""))
        for s in existing_songs
    }

    print(f"📋 พบทั้งหมด {len(items)} เพลง (ในระบบมีอยู่แล้ว {len(existing_keys)} เพลง)\n" + "=" * 60)

    success_count = 0
    skip_count = 0
    fail_count = 0

    for idx, (artist, title) in enumerate(items, 1):
        key = song_store.normalize_key(artist, title)
        query = f"{artist} - {title}"

        print(f"\n[{idx}/{len(items)}] 🎧 {query}")

        # Check duplicate
        if key in existing_keys:
            print(f"  ⏭️  เพลงนี้มีในระบบแล้ว ข้าม...")
            skip_count += 1
            continue

        song_id = str(uuid.uuid4())[:8]
        work_dir = os.path.join(AUDIO_BASE, f"_work_{song_id}")
        os.makedirs(work_dir, exist_ok=True)

        try:
            # 1. Search YouTube
            print(f"  🔎 กำลังค้นหาคลิปที่มียอดวิวสูงสุดบน YouTube...")
            search_res = downloader.search_youtube_most_viewed(query, clip_duration=20.0)

            yt_url = search_res["youtube_url"]
            start_time = search_res["start_time"]
            duration = search_res["duration"]
            views = search_res["view_count"]
            tot_dur = search_res["total_duration"]

            print(f"  📺 พบวิดีโอ: {search_res['video_title']}")
            print(f"  👁️  ยอดวิว: {views:,} | ความยาว: {tot_dur}s")
            print(f"  ✂️  เลือกช่วงท้ายเพลง (~80%): {start_time}s - {start_time + duration}s ({duration}s)")

            # 2. Download & trim
            print(f"  ⬇️  กำลังดาวน์โหลดและตัดคลิป...")
            input_wav = os.path.join(work_dir, "input.wav")
            downloader.download_and_trim(yt_url, start_time, duration, input_wav)

            # 3. Demucs stem separation
            print(f"  🎛️  กำลังแยกเสียง 4 Stems ด้วย Demucs (htdemucs)...")
            stem_paths = separator.separate_stems(input_wav, AUDIO_BASE, song_id)

            # 4. Save to songs.json
            song_obj = {
                "id": song_id,
                "title": title,
                "artist": artist,
                "stems": stem_paths,
            }
            song_store.add_song(song_obj)
            existing_keys.add(key)

            success_count += 1
            print(f"  🎉 สำเร็จ! เพิ่มเพลง '{title}' โดย {artist} เรียบร้อยแล้ว")

        except Exception as exc:
            fail_count += 1
            print(f"  ❌ ไม่สามารถประมวลผลได้: {exc}")
            shutil.rmtree(os.path.join(AUDIO_BASE, song_id), ignore_errors=True)

        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    print("\n" + "=" * 60)
    print(f"🏁 ประมวลผลเสร็จสิ้น!")
    print(f"  ✅ สำเร็จ: {success_count} เพลง")
    print(f"  ⏭️  ข้าม (มีอยู่แล้ว): {skip_count} เพลง")
    print(f"  ❌ ล้มเหลว: {fail_count} เพลง")


if __name__ == "__main__":
    main()
