"""
downloader.py — Download audio from YouTube (yt-dlp) and trim clips with FFmpeg.
"""
import os
import subprocess
import sys

import yt_dlp


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

import shutil


def get_ffmpeg_cmd() -> str:
    """Find ffmpeg binary from system PATH or imageio_ffmpeg package."""
    if shutil.which("ffmpeg"):
        return "ffmpeg"
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        pass
    return "ffmpeg"


def _run_ffmpeg(args: list) -> None:
    """Run ffmpeg subprocess and raise on failure."""
    ffmpeg_exe = get_ffmpeg_cmd()
    try:
        result = subprocess.run(
            [ffmpeg_exe, *args],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        raise RuntimeError(
            "ไม่พบ FFmpeg ในระบบ! กรุณาติดตั้ง imageio-ffmpeg ด้วยคำสั่ง: pip install imageio-ffmpeg "
            "หรือติดตั้ง FFmpeg บน Windows แล้วรีสตาร์ทเครื่อง/เปิด Terminal ใหม่"
        )
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error:\n{result.stderr}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def download_and_trim(
    youtube_url: str,
    start_time: float,
    duration: float,
    output_path: str,
) -> str:
    """
    Download best audio from YouTube URL, trim to [start_time, start_time+duration],
    and save as 44.1 kHz stereo WAV at *output_path*.
    """
    out_dir = os.path.dirname(output_path)
    os.makedirs(out_dir, exist_ok=True)

    # Use a predictable temp filename in the same directory
    temp_template = os.path.join(out_dir, "_yt_raw.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": temp_template,
        "quiet": True,
        "no_warnings": True,
        "logger": QuietLogger(),
        "socket_timeout": 30,
        "nocheckcertificate": True,
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web", "mweb"],
            }
        },
        # Download only, no post-processing — we trim with ffmpeg ourselves
        "postprocessors": [],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)
        ext = info.get("ext", "webm")

    # Resolve the downloaded file (try exact ext first, then common ones)
    raw_file = os.path.join(out_dir, f"_yt_raw.{ext}")
    if not os.path.exists(raw_file):
        for fallback_ext in ("webm", "m4a", "opus", "ogg", "mp3"):
            candidate = os.path.join(out_dir, f"_yt_raw.{fallback_ext}")
            if os.path.exists(candidate):
                raw_file = candidate
                break

    if not os.path.exists(raw_file):
        raise FileNotFoundError("yt-dlp ดาวน์โหลดเสียงไม่สำเร็จ ไม่พบไฟล์ชั่วคราว")

    try:
        trim_file(raw_file, start_time, duration, output_path)
    finally:
        if os.path.exists(raw_file):
            os.remove(raw_file)

    return output_path


class QuietLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass


def _find_hook_from_heatmap(heatmap: list, clip_duration: float = 20.0, total_duration: float = 180.0) -> Optional[float]:
    """
    Find start_time of the 20-second window with the highest Most Replayed density on YouTube.
    """
    if not heatmap or not isinstance(heatmap, list):
        return None

    best_start = 0.0
    max_score = -1.0

    for entry in heatmap:
        w_start = float(entry.get("start_time", 0.0))
        w_end = w_start + clip_duration
        if w_end > total_duration:
            w_start = max(0.0, total_duration - clip_duration)
            w_end = total_duration

        score = sum(
            float(item.get("value", 0.0))
            for item in heatmap
            if float(item.get("start_time", 0.0)) >= w_start and float(item.get("end_time", 0.0)) <= w_end
        )

        if score > max_score:
            max_score = score
            best_start = w_start

    return round(best_start, 1)


def search_youtube_most_viewed(query: str, clip_duration: float = 20.0, start_ratio: float = 0.80) -> dict:
    """
    Search YouTube for *query*, trying Audio/Lyric variations and candidate entries
    to bypass YouTube's 'Sign in to confirm you're not a bot' blocks on official MVs.
    Automatically detects the main chorus hook using YouTube's Most Replayed Heatmap.
    """
    winget_path = r"C:\Users\Charyn Kylers\AppData\Local\Microsoft\WinGet\Links"
    if os.path.exists(winget_path) and winget_path not in os.environ.get("PATH", ""):
        os.environ["PATH"] += f";{winget_path}"

    ydl_flat = yt_dlp.YoutubeDL({
        "quiet": True,
        "no_warnings": True,
        "logger": QuietLogger(),
        "nocheckcertificate": True,
        "socket_timeout": 15,
        "extract_flat": "in_playlist",
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
    })

    ydl_info = yt_dlp.YoutubeDL({
        "quiet": True,
        "no_warnings": True,
        "logger": QuietLogger(),
        "ignoreerrors": True,
        "nocheckcertificate": True,
        "socket_timeout": 15,
        "skip_download": True,
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "extractor_args": {
            "youtube": {
                "player_client": ["mweb", "android", "web"],
            }
        },
    })


    best_match = None
    search_queries = [
        f"{query} Lyric",
        f"{query} Lyrics",
        f"{query} Color Coded Lyrics",
        f"{query} Audio",
        query,
    ]

    for q in search_queries:
        try:
            res = ydl_flat.extract_info(f"ytsearch10:{q}", download=False)
            entries = res.get("entries", [])
        except Exception:
            continue

        for entry in entries:
            video_id = entry.get("id")
            if not video_id:
                continue
            url = f"https://www.youtube.com/watch?v={video_id}"

            try:
                vinfo = ydl_info.extract_info(url, download=False)
                if vinfo and float(vinfo.get("duration") or 0) > 10:
                    best_match = vinfo
                    break
            except Exception:
                continue

        if best_match:
            break

    # Fallback to SoundCloud if YouTube blocks extraction
    if not best_match:
        try:
            ydl_sc = yt_dlp.YoutubeDL({
                "quiet": True,
                "no_warnings": True,
                "logger": QuietLogger(),
                "nocheckcertificate": True,
                "socket_timeout": 15,
            })
            res_sc = ydl_sc.extract_info(f"scsearch1:{query}", download=False)
            sc_entries = res_sc.get("entries", [])
            if sc_entries and sc_entries[0].get("duration"):
                best_match = sc_entries[0]
        except Exception:
            pass

    if not best_match:
        raise RuntimeError(f"ไม่สามารถดึงข้อมูลวิดีโอ/เพลงสำหรับ: {query}")

    url = best_match.get("webpage_url") or f"https://www.youtube.com/watch?v={best_match['id']}"
    total_duration = float(best_match.get("duration") or 180.0)


    # 1. Try YouTube Heatmap (Most Replayed) automatic hook detection
    heatmap = best_match.get("heatmap")
    detected_start = _find_hook_from_heatmap(heatmap, clip_duration, total_duration)

    if detected_start is not None:
        start_time = detected_start
    elif total_duration <= clip_duration:
        start_time = 0.0
    else:
        # Fallback to ratio
        target_start = total_duration * start_ratio
        start_time = round(max(0.0, min(target_start, total_duration - clip_duration)), 1)

    actual_duration = min(clip_duration, total_duration)

    return {
        "youtube_url": url,
        "video_title": best_match.get("title", query),
        "view_count": best_match.get("view_count", 0),
        "total_duration": total_duration,
        "start_time": start_time,
        "duration": actual_duration,
    }




def trim_file(
    input_path: str,
    start_time: float,
    duration: float,
    output_path: str,
) -> str:
    """
    Trim an existing audio file to [start_time, start_time+duration]
    and write a 44.1 kHz stereo WAV to *output_path*.
    """
    out_dir = os.path.dirname(output_path)
    os.makedirs(out_dir, exist_ok=True)

    _run_ffmpeg([
        "-y",
        "-i", input_path,
        "-ss", str(start_time),
        "-t", str(duration),
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        output_path,
    ])

    return output_path


