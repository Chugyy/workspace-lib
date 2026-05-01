"""Download YouTube videos/audio via yt-dlp."""

from pathlib import Path
from typing import Optional

TOOL_DIR = Path(__file__).parent.parent.parent
DEFAULT_OUTPUT = TOOL_DIR / "output"


def download(
    url: str,
    audio_only: bool = False,
    output_dir: Optional[Path] = None,
    filename: Optional[str] = None,
) -> dict:
    """Download a YouTube video or extract audio.

    Returns dict with: path, title, duration, channel, id.
    """
    import yt_dlp

    out = output_dir or DEFAULT_OUTPUT
    out.mkdir(parents=True, exist_ok=True)

    template = str(out / (filename or "%(title)s")) + ".%(ext)s"

    opts = {
        "outtmpl": template,
        "quiet": True,
        "no_warnings": True,
    }

    if audio_only:
        opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        })
    else:
        opts["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        opts["merge_output_format"] = "mp4"

    info = None
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)

    ext = "mp3" if audio_only else "mp4"
    actual_filename = filename or info.get("title", "video")
    downloaded_path = out / f"{actual_filename}.{ext}"

    # yt-dlp may sanitize the filename — find the actual file
    if not downloaded_path.exists():
        candidates = sorted(out.glob(f"*.{ext}"), key=lambda p: p.stat().st_mtime, reverse=True)
        downloaded_path = candidates[0] if candidates else downloaded_path

    return {
        "path": str(downloaded_path),
        "title": info.get("title", ""),
        "duration": info.get("duration", 0),
        "channel": info.get("channel", info.get("uploader", "")),
        "id": info.get("id", ""),
        "url": url,
    }
