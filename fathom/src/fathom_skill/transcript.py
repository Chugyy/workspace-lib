"""Fathom API client for fetching call transcripts."""

import json
import re
import sys
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from typing import Optional, List, Dict

SKILL_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(SKILL_DIR.parent / ".profiles"))


def load_config(config_path: Optional[str] = None, profile: Optional[str] = None) -> dict:
    """Load config from profile resolver, with legacy fallback."""
    if config_path:
        with open(Path(config_path)) as f:
            return json.load(f)
    try:
        from resolver import resolve
        return resolve("fathom", profile)
    except Exception:
        legacy = SKILL_DIR / "assets" / "config.json"
        if legacy.exists():
            with open(legacy) as f:
                return json.load(f)
        raise


def api_get(url: str, api_key: str) -> dict:
    req = urllib.request.Request(url, headers={"X-Api-Key": api_key})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise Exception(f"API Error {e.code}: {e.read().decode()}")


def find_meeting(input_str: str, api_key: str, base_url: str) -> Optional[dict]:
    """Paginate meetings to find one matching share_url or url."""
    cursor = None
    while True:
        params = {"include_transcript": "true"}
        if cursor:
            params["cursor"] = cursor
        url = f"{base_url}/meetings?" + urllib.parse.urlencode(params)
        data = api_get(url, api_key)
        for meeting in data.get("items", []):
            if meeting.get("share_url") == input_str or meeting.get("url") == input_str:
                return meeting
        cursor = data.get("next_cursor")
        if not cursor:
            break
    return None


def get_transcript_by_id(recording_id: str, api_key: str, base_url: str) -> List[dict]:
    url = f"{base_url}/recordings/{recording_id}/transcript"
    return api_get(url, api_key).get("transcript", [])


def format_transcript(transcript: List[dict], title: Optional[str] = None) -> str:
    lines = []
    if title:
        lines.append(f"# {title}\n")
    for entry in transcript:
        speaker = entry.get("speaker", {}).get("display_name", "Unknown")
        timestamp = entry.get("timestamp", "")
        text = entry.get("text", "")
        lines.append(f"[{timestamp}] {speaker}: {text}")
    return "\n".join(lines)


def save_to_file(content: str, recording_id: int, title: Optional[str], output_dir: str = "/tmp") -> str:
    safe_title = re.sub(r"[^\w\-]", "_", title or "call")[:40]
    path = f"{output_dir}/fathom_{safe_title}_{recording_id}.txt"
    with open(path, "w") as f:
        f.write(content)
    return path


def fetch_transcript(input_str: str, config: dict) -> tuple:
    """
    Fetch transcript for a Fathom URL or recording ID.

    Returns:
        (formatted_str, file_path)
    """
    api_key = config["api_key"]
    base_url = config["base_url"]
    input_str = input_str.strip().rstrip("/")

    transcript = None
    title = None
    recording_id = None

    if re.fullmatch(r"\d+", input_str):
        recording_id = int(input_str)
        transcript = get_transcript_by_id(input_str, api_key, base_url)
    else:
        meeting = find_meeting(input_str, api_key, base_url)
        if not meeting:
            raise ValueError(f"No meeting found matching: {input_str}")
        transcript = meeting.get("transcript", [])
        title = meeting.get("title")
        recording_id = meeting.get("recording_id")

    if not transcript:
        return "No transcript available for this recording.", None

    formatted = format_transcript(transcript, title=title)
    file_path = save_to_file(formatted, recording_id, title)
    return formatted, file_path
