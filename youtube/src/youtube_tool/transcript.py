"""Fetch YouTube video transcripts."""

from typing import Optional


def get_transcript(url: str, lang: str = "fr") -> dict:
    """Get transcript for a YouTube video.

    Uses youtube-transcript-api v2 (instance-based API).

    Returns dict with: text, segments (list of {start, duration, text}), lang, source.
    """
    video_id = _extract_video_id(url)
    if not video_id:
        raise ValueError(f"Cannot extract video ID from: {url}")

    # Try with preferred language first
    try:
        return _fetch_via_api(video_id, lang)
    except Exception:
        pass

    # Fallback: try any available language
    try:
        return _fetch_via_api(video_id, lang=None)
    except Exception as e:
        raise RuntimeError(f"No transcript available for {url}. Error: {e}")


def _fetch_via_api(video_id: str, lang: Optional[str]) -> dict:
    """Fetch via youtube-transcript-api v2."""
    from youtube_transcript_api import YouTubeTranscriptApi

    api = YouTubeTranscriptApi()

    if lang:
        result = api.fetch(video_id, languages=[lang, "en"])
        segments = [{"start": s.start, "duration": s.duration, "text": s.text} for s in result]
        actual_lang = lang
    else:
        transcript_list = api.list(video_id)
        first = next(iter(transcript_list))
        result = first.fetch()
        segments = [{"start": s.start, "duration": s.duration, "text": s.text} for s in result]
        actual_lang = first.language_code

    full_text = " ".join(s["text"] for s in segments)

    return {
        "text": full_text,
        "segments": segments,
        "lang": actual_lang,
        "source": "youtube-transcript-api",
        "video_id": video_id,
    }


def _extract_video_id(url: str) -> Optional[str]:
    """Extract video ID from various YouTube URL formats."""
    import re

    patterns = [
        r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'(?:embed/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None
