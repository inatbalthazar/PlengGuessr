"""
separator.py — Stem separation using Facebook Demucs (htdemucs model).

Pipeline:
  input.wav  →  Demucs (htdemucs)  →  {stem}.wav (×4)  →  ffmpeg  →  {stem}.mp3

Output paths:  /audio/{song_id}/{stem}.mp3
"""
import os
import shutil
import subprocess
import sys

STEMS = ["drums", "bass", "other", "vocals"]


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


def _ffmpeg_wav_to_mp3(src_wav: str, dst_mp3: str) -> None:
    """Convert a WAV file to MP3 (VBR quality 2 ≈ ~190 kbps) via ffmpeg."""
    ffmpeg_exe = get_ffmpeg_cmd()
    try:
        result = subprocess.run(
            [
                ffmpeg_exe, "-y",
                "-i", src_wav,
                "-codec:a", "libmp3lame",
                "-qscale:a", "2",
                dst_mp3,
            ],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        raise RuntimeError("ไม่พบ FFmpeg ในระบบ! กรุณาติดตั้ง imageio-ffmpeg หรือ ffmpeg")
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg MP3 conversion failed for {src_wav}:\n{result.stderr}")


def separate_stems(
    input_wav: str,
    audio_base_dir: str,
    song_id: str,
) -> dict:
    """
    Run Demucs htdemucs on *input_wav*, convert each stem to MP3,
    and place them at:  {audio_base_dir}/{song_id}/{stem}.mp3

    Returns a dict mapping stem name → URL path ("/audio/{song_id}/{stem}.mp3").
    """
    temp_out = os.path.join(audio_base_dir, f"_demucs_tmp_{song_id}")
    os.makedirs(temp_out, exist_ok=True)

    try:
        # --- 1. Run Demucs ------------------------------------------------
        # sys.executable ensures we use the same Python / venv as the server
        cmd = [
            sys.executable, "-m", "demucs",
            "--name", "htdemucs",
            "--out", temp_out,
            input_wav,
        ]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=300,
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Demucs ใช้เวลานานเกินไป (Timeout 5 นาที)")

        if result.returncode != 0:
            raise RuntimeError(
                f"Demucs failed (exit {result.returncode}):\n{result.stderr}"
            )


        # --- 2. Locate Demucs output ---------------------------------------
        # Demucs writes to:  {temp_out}/htdemucs/{input_basename}/{stem}.wav
        input_basename = os.path.splitext(os.path.basename(input_wav))[0]
        stems_dir = os.path.join(temp_out, "htdemucs", input_basename)

        if not os.path.isdir(stems_dir):
            raise RuntimeError(
                f"Demucs output directory not found: {stems_dir}\n"
                f"stdout: {result.stdout}\nstderr: {result.stderr}"
            )

        # --- 3. Convert each stem WAV → MP3 -------------------------------
        final_dir = os.path.join(audio_base_dir, song_id)
        os.makedirs(final_dir, exist_ok=True)

        stem_paths: dict = {}
        for stem in STEMS:
            src_wav = os.path.join(stems_dir, f"{stem}.wav")
            dst_mp3 = os.path.join(final_dir, f"{stem}.mp3")

            if not os.path.exists(src_wav):
                raise RuntimeError(
                    f"Stem file not found after Demucs: {src_wav}"
                )

            _ffmpeg_wav_to_mp3(src_wav, dst_mp3)
            stem_paths[stem] = f"/audio/{song_id}/{stem}.mp3"

        return stem_paths

    finally:
        # Always clean up temp Demucs output
        shutil.rmtree(temp_out, ignore_errors=True)
