"""
WhatsApp Media Downloader (WAHA)

Download attachments (voice notes, images, videos, documents) from WhatsApp
conversations via the WAHA self-hosted API.

In WAHA, media is accessible via the `media.url` field in message objects.
We fetch messages with `downloadMedia=true`, filter, then download.

Usage (CLI):
    whatsapp download-media --chat-id CHAT_ID --type audio --output-dir ./downloads
    whatsapp download-media --chat-id CHAT_ID --list --type audio
    whatsapp download-media --chat-id CHAT_ID --sender "Kilian" --time "15:51"
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

from whatsapp_manager.client import (
    WAHAClient,
    WAHAError,
    NotFoundError,
    UnauthorizedError,
    RateLimitError,
    InternalServerError,
)


# ============================================================================
# MIME TYPE → EXTENSION MAPPING
# ============================================================================

MIME_TO_EXT = {
    "audio/ogg": ".ogg",
    "audio/ogg; codecs=opus": ".ogg",
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
    "audio/aac": ".aac",
    "audio/wav": ".wav",
    "audio/webm": ".webm",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "video/mp4": ".mp4",
    "video/avi": ".avi",
    "video/quicktime": ".mov",
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
}

# Map broad types to fallback extensions
TYPE_TO_EXT = {
    "audio": ".ogg",
    "image": ".jpg",
    "video": ".mp4",
    "document": ".bin",
}


def _resolve_extension(mimetype: str, media_type: str = "") -> str:
    """Determine file extension from mimetype or media type."""
    if mimetype in MIME_TO_EXT:
        return MIME_TO_EXT[mimetype]
    for key, ext in MIME_TO_EXT.items():
        if mimetype.startswith(key.split(";")[0]):
            return ext
    return TYPE_TO_EXT.get(media_type, ".bin")


def _get_media_type(mimetype: str) -> str:
    """Determine broad media type from MIME type."""
    if not mimetype:
        return "unknown"
    if mimetype.startswith("audio/"):
        return "audio"
    if mimetype.startswith("image/"):
        return "image"
    if mimetype.startswith("video/"):
        return "video"
    return "document"


def _build_filename(msg: Dict[str, Any], index: int = 0) -> str:
    """
    Build a descriptive filename for a media attachment.

    Format: {timestamp}_{sender_short}_{msg_id_short}{ext}
    Example: 2026-02-16T14h51_Kilian_ABCDE123.ogg
    """
    # Timestamp
    ts = str(msg.get("timestamp", "unknown"))
    # If it's an epoch number, convert
    if ts.isdigit():
        try:
            dt = datetime.fromtimestamp(int(ts))
            ts = dt.strftime("%Y-%m-%dT%Hh%M")
        except (ValueError, OSError):
            pass
    else:
        ts_clean = ts.replace(":", "h", 1).replace(":", "m").split(".")[0]
        ts = ts_clean[:16].replace(":", "")

    # Sender
    sender_name = _get_sender_name(msg)
    sender_name = sender_name.replace(" ", "_")[:15]

    # Message ID (short)
    msg_id = str(msg.get("id", "unknown"))[:12]

    # Extension from media
    media = msg.get("media", {}) or {}
    mimetype = media.get("mimetype", msg.get("mimetype", ""))
    ext = _resolve_extension(mimetype, _get_media_type(mimetype))

    return f"{ts}_{sender_name}_{msg_id}{ext}"


# ============================================================================
# TIME / SENDER HELPERS
# ============================================================================

_DEFAULT_TZ_OFFSET_HOURS = 1  # Europe/Paris CET


def parse_time_filter(time_str: str) -> Optional[tuple]:
    """
    Parse a time string into (hour, minute).

    Accepts: "15:51", "15h51", "1551", "15h", "15"
    """
    time_str = time_str.strip()
    m = re.match(r'^(\d{1,2})[h:](\d{2})$', time_str)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.match(r'^(\d{2})(\d{2})$', time_str)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.match(r'^(\d{1,2})h?$', time_str)
    if m:
        return int(m.group(1)), None
    raise ValueError(f"Cannot parse time '{time_str}'. Use format: 15:51, 15h51, or 1551")


def _get_sender_name(msg: Dict[str, Any]) -> str:
    """Extract sender name from WAHA message."""
    # WAHA provides _data.pushName or from field
    data = msg.get("_data", {}) or {}
    push_name = data.get("pushName", "")
    if push_name:
        return push_name

    # Fallback to 'from' field
    from_id = msg.get("from", "") or ""
    if from_id:
        return from_id.split("@")[0][:15]

    return "unknown"


def message_matches_sender(msg: Dict[str, Any], sender: str) -> bool:
    """
    Check if a message was sent by the given sender.

    Matches against:
    - msg["from"] (JID format: 33612345678@c.us)
    - msg["_data"]["pushName"] (display name)
    - Phone digits as substring
    """
    sender_lower = sender.lower().strip()
    sender_digits = re.sub(r'\D', '', sender)

    # Match by 'from' JID
    from_id = (msg.get("from") or "").lower()
    if sender_lower == from_id:
        return True
    if sender_digits and sender_digits in from_id:
        return True

    # Match by participant (in groups)
    participant = (msg.get("participant") or "").lower()
    if participant:
        if sender_lower == participant or (sender_digits and sender_digits in participant):
            return True

    # Match by pushName (display name)
    data = msg.get("_data", {}) or {}
    push_name = (data.get("pushName", "") or "").lower()
    if push_name and sender_lower in push_name:
        return True

    return False


def message_matches_time(
    msg: Dict[str, Any],
    hour: int,
    minute: Optional[int],
    window_minutes: int = 2,
    tz_offset_hours: int = _DEFAULT_TZ_OFFSET_HOURS,
) -> bool:
    """Check if a message was sent at the given local time (±window_minutes)."""
    ts = msg.get("timestamp")
    if not ts:
        return False

    try:
        # WAHA timestamps can be epoch seconds or ISO strings
        if isinstance(ts, (int, float)):
            dt_utc = datetime.utcfromtimestamp(ts)
        else:
            dt_utc = datetime.fromisoformat(str(ts).replace("Z", "+00:00")).replace(tzinfo=None)

        local_dt = dt_utc + timedelta(hours=tz_offset_hours)
        local_h, local_m = local_dt.hour, local_dt.minute

        if minute is None:
            return local_h == hour

        target_minutes = hour * 60 + minute
        actual_minutes = local_h * 60 + local_m
        return abs(actual_minutes - target_minutes) <= window_minutes

    except (ValueError, TypeError, OSError):
        return False


# ============================================================================
# MEDIA DOWNLOADER
# ============================================================================

class MediaDownloader:
    """
    High-level interface for downloading WhatsApp media attachments via WAHA.

    Args:
        config: Dict with keys: waha.base_url, waha.api_key, waha.session
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        waha = config.get("waha", config)
        # Support both env-style keys (WAHA_BASE_URL) and camelCase (base_url)
        base_url = waha.get("base_url") or waha.get("WAHA_BASE_URL")
        api_key = waha.get("api_key") or waha.get("WAHA_API_KEY")
        session = waha.get("session") or waha.get("WAHA_SESSION") or "default"
        self.client = WAHAClient(
            base_url=base_url,
            api_key=api_key,
            session=session,
        )

    async def list_messages_with_attachments(
        self,
        chat_id: str,
        limit: int = 50,
        attachment_type: Optional[str] = None,
        sender: Optional[str] = None,
        time_str: Optional[str] = None,
        time_window: int = 2,
        tz_offset_hours: int = _DEFAULT_TZ_OFFSET_HOURS,
    ) -> List[Dict[str, Any]]:
        """
        List messages that contain media in a chat.

        Args:
            chat_id: WAHA chat ID
            limit: Max messages to fetch
            attachment_type: Filter: "audio", "image", "video", "document"
            sender: Sender phone, JID, or name
            time_str: Local time to filter on
            time_window: Tolerance in minutes
            tz_offset_hours: UTC offset

        Returns:
            List of attachment items
        """
        response = await self.client.get_chat_messages(
            chat_id=chat_id, limit=limit, download_media=True
        )
        messages = response.get("items", response if isinstance(response, list) else [])

        time_filter = None
        if time_str:
            time_filter = parse_time_filter(time_str)

        result = []
        for msg in messages:
            # WAHA messages with media have hasMedia=true and media.url
            if not msg.get("hasMedia"):
                continue

            media = msg.get("media") or {}
            mimetype = media.get("mimetype", "")
            media_type = _get_media_type(mimetype)
            media_url = media.get("url", "")

            if not media_url:
                continue

            # Filter by sender
            if sender and not message_matches_sender(msg, sender):
                continue

            # Filter by time
            if time_filter is not None:
                hour, minute = time_filter
                if not message_matches_time(msg, hour, minute, time_window, tz_offset_hours):
                    continue

            # Filter by attachment type
            if attachment_type and media_type != attachment_type:
                continue

            # Extract duration for audio/video
            duration = media.get("duration") or msg.get("_data", {}).get("duration")

            result.append({
                "message": msg,
                "filename": _build_filename(msg),
                "message_id": msg.get("id", ""),
                "media_url": media_url,
                "media_type": media_type,
                "mimetype": mimetype,
                "duration": duration,
                "timestamp": msg.get("timestamp"),
                "sender_name": _get_sender_name(msg),
            })

        return result

    async def download_attachments(
        self,
        chat_id: str,
        output_dir: str = "./downloads",
        limit: int = 50,
        attachment_type: Optional[str] = None,
        sender: Optional[str] = None,
        time_str: Optional[str] = None,
        time_window: int = 2,
        tz_offset_hours: int = _DEFAULT_TZ_OFFSET_HOURS,
        skip_existing: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Download media attachments from a chat with optional filters.

        Args:
            chat_id: WAHA chat ID
            output_dir: Directory to save files
            limit: Max messages to scan
            attachment_type: "audio", "image", "video", "document" or None
            sender: Sender phone, JID, or name
            time_str: Local time filter
            time_window: Tolerance in minutes
            tz_offset_hours: UTC offset
            skip_existing: Skip already-downloaded files

        Returns:
            List of result dicts
        """
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        items = await self.list_messages_with_attachments(
            chat_id=chat_id,
            limit=limit,
            attachment_type=attachment_type,
            sender=sender,
            time_str=time_str,
            time_window=time_window,
            tz_offset_hours=tz_offset_hours,
        )

        results = []
        for item in items:
            filename = item["filename"]
            dest = out_dir / filename
            result_entry = {
                "filename": filename,
                "path": str(dest),
                "status": "ok",
                "error": None,
                "timestamp": item["timestamp"],
                "sender_name": item["sender_name"],
                "duration": item.get("duration"),
                "mimetype": item["mimetype"],
            }

            if skip_existing and dest.exists():
                result_entry["status"] = "skipped"
                results.append(result_entry)
                continue

            try:
                data = await self.client._download_file(item["media_url"])
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
            except NotFoundError as e:
                result_entry["status"] = "error"
                result_entry["error"] = f"Not found: {e}"
            except UnauthorizedError as e:
                result_entry["status"] = "error"
                result_entry["error"] = f"Unauthorized: {e}"
            except RateLimitError as e:
                result_entry["status"] = "error"
                result_entry["error"] = f"Rate limited (retry after {e.retry_after}s): {e}"
            except InternalServerError as e:
                result_entry["status"] = "error"
                result_entry["error"] = f"Server error: {e}"
            except WAHAError as e:
                result_entry["status"] = "error"
                result_entry["error"] = f"API error: {e}"
            except Exception as e:
                result_entry["status"] = "error"
                result_entry["error"] = f"Unexpected error: {e}"

            results.append(result_entry)

        return results
