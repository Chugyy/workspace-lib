"""Search YouTube videos via yt-dlp."""

import json


def search(query: str, max_results: int = 10) -> list[dict]:
    """Search YouTube and return video metadata.

    Returns list of dicts with: title, url, channel, views, duration, date, thumbnail.
    """
    import yt_dlp

    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
    }

    search_url = f"ytsearch{max_results}:{query}"

    with yt_dlp.YoutubeDL(opts) as ydl:
        result = ydl.extract_info(search_url, download=False)

    entries = result.get("entries", [])
    results = []

    for entry in entries:
        if not entry:
            continue
        results.append({
            "title": entry.get("title", ""),
            "url": f"https://www.youtube.com/watch?v={entry.get('id', '')}",
            "id": entry.get("id", ""),
            "channel": entry.get("channel", entry.get("uploader", "")),
            "views": entry.get("view_count", 0),
            "duration": entry.get("duration", 0),
            "date": entry.get("upload_date", ""),
            "thumbnail": entry.get("thumbnail", entry.get("thumbnails", [{}])[0].get("url", "") if entry.get("thumbnails") else ""),
            "description": (entry.get("description", "") or "")[:200],
        })

    return results


def format_results(results: list[dict]) -> str:
    """Format search results for display."""
    lines = []
    for i, r in enumerate(results, 1):
        duration_str = _format_duration(r.get("duration", 0))
        views_str = _format_views(r.get("views", 0))
        lines.append(f"{i}. {r['title']}")
        lines.append(f"   {r['channel']} | {views_str} views | {duration_str}")
        lines.append(f"   {r['url']}")
        lines.append("")
    return "\n".join(lines)


def _format_duration(seconds) -> str:
    if not seconds:
        return "?"
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _format_views(count: int) -> str:
    if not count:
        return "?"
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    if count >= 1_000:
        return f"{count / 1_000:.1f}K"
    return str(count)
