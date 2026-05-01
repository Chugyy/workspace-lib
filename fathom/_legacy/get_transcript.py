#!/usr/bin/env python3
"""
Fetch transcript from a Fathom call recording.

Usage:
  python get_transcript.py <fathom_url_or_recording_id>

Accepts:
  - Share URL:    https://fathom.video/share/<token>
  - Calls URL:    https://fathom.video/calls/<id>
  - Recording ID: 124392814

Output:
  - Prints formatted transcript to stdout
  - Writes transcript to /tmp/fathom_<title>_<id>.txt
  - Prints temp file path to stderr
"""

import sys
import json
import re
import urllib.request
import urllib.error
import urllib.parse
import os
from pathlib import Path


def load_config() -> dict:
    config_path = Path(__file__).parent.parent / "config.json"
    with open(config_path) as f:
        return json.load(f)


def api_get(url: str, api_key: str) -> dict:
    req = urllib.request.Request(url, headers={"X-Api-Key": api_key})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"API Error {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)


def find_meeting(input_str: str, api_key: str, base_url: str) -> dict | None:
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


def get_transcript_by_id(recording_id: str, api_key: str, base_url: str) -> list[dict]:
    url = f"{base_url}/recordings/{recording_id}/transcript"
    return api_get(url, api_key).get("transcript", [])


def format_transcript(transcript: list[dict], title: str | None = None) -> str:
    lines = []
    if title:
        lines.append(f"# {title}\n")
    for entry in transcript:
        speaker = entry.get("speaker", {}).get("display_name", "Unknown")
        timestamp = entry.get("timestamp", "")
        text = entry.get("text", "")
        lines.append(f"[{timestamp}] {speaker}: {text}")
    return "\n".join(lines)


def save_to_temp(content: str, recording_id: int, title: str | None) -> str:
    safe_title = re.sub(r'[^\w\-]', '_', title or "call")[:40]
    path = f"/tmp/fathom_{safe_title}_{recording_id}.txt"
    with open(path, "w") as f:
        f.write(content)
    return path


def main():
    if len(sys.argv) < 2:
        print("Usage: get_transcript.py <fathom_url_or_recording_id>", file=sys.stderr)
        sys.exit(1)

    config = load_config()
    api_key = config["api_key"]
    base_url = config["base_url"]
    input_str = sys.argv[1].strip().rstrip("/")

    transcript = None
    title = None
    recording_id = None

    if re.fullmatch(r"\d+", input_str):
        # Direct numeric recording ID
        recording_id = int(input_str)
        transcript = get_transcript_by_id(input_str, api_key, base_url)
    else:
        meeting = find_meeting(input_str, api_key, base_url)
        if not meeting:
            print(f"No meeting found matching: {input_str}", file=sys.stderr)
            sys.exit(1)
        transcript = meeting.get("transcript", [])
        title = meeting.get("title")
        recording_id = meeting.get("recording_id")

    if not transcript:
        print("No transcript available for this recording.")
        return

    formatted = format_transcript(transcript, title=title)
    temp_path = save_to_temp(formatted, recording_id, title)

    print(formatted)
    print(f"\nTEMP_FILE:{temp_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
