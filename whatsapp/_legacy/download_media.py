"""
WhatsApp Media Downloader

Download attachments (voice notes, images, videos, documents) from WhatsApp
conversations via the Unipile API.

Usage (CLI):
    python download_media.py --chat_id CHAT_ID [options]
    python download_media.py --chat_id CHAT_ID --type audio --output_dir ./downloads/
    python download_media.py --chat_id CHAT_ID --sender 142988252606566@lid --limit 20
    python download_media.py --chat_id CHAT_ID --message_id MSG_ID --attachment_id ATT_ID

Usage (import):
    from scripts.download_media import MediaDownloader
    downloader = MediaDownloader(config)
    files = await downloader.download_all_voice_notes(chat_id="...", output_dir="./out/")
"""

import asyncio
import json
import sys
import argparse
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

# Allow running from skill root or scripts/ directory
_SCRIPTS_DIR = Path(__file__).parent
_SKILL_DIR = _SCRIPTS_DIR.parent
sys.path.insert(0, str(_SCRIPTS_DIR))

from whatsapp_client import (
    UnipileWhatsAppClient,
    UnipileError,
    UnauthorizedError,
    AccountDisconnectedError,
    NotFoundError,
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

ATTACHMENT_TYPE_TO_EXT = {
    "audio": ".ogg",
    "image": ".jpg",
    "video": ".mp4",
    "document": ".bin",
}


def _resolve_extension(attachment: Dict[str, Any]) -> str:
    """Determine file extension from mimetype or attachment type."""
    mime = attachment.get("mimetype", "")
    # Try exact match first, then prefix match
    if mime in MIME_TO_EXT:
        return MIME_TO_EXT[mime]
    for key, ext in MIME_TO_EXT.items():
        if mime.startswith(key.split(";")[0]):
            return ext
    att_type = attachment.get("type", "")
    return ATTACHMENT_TYPE_TO_EXT.get(att_type, ".bin")


def _build_filename(message: Dict[str, Any], attachment: Dict[str, Any], index: int = 0) -> str:
    """
    Build a descriptive filename for an attachment.

    Format: {timestamp}_{sender_short}_{attachment_id}{ext}
    Example: 2026-02-16T14h51_Kilian_3EB0C98D.ogg
    """
    ts = message.get("timestamp", "unknown")
    # Normalize timestamp: replace : and . for filesystem safety
    ts_clean = ts.replace(":", "h", 1).replace(":", "m").split(".")[0].replace("T", "T")
    ts_clean = ts_clean[:16].replace(":", "").replace("T", "T")  # 2026-02-16T1451

    # Try to get sender name from original JSON
    sender_name = "unknown"
    original_raw = message.get("original", "{}")
    try:
        original = json.loads(original_raw) if isinstance(original_raw, str) else original_raw
        sender_name = original.get("pushName", "") or ""
        sender_name = sender_name.replace(" ", "_")[:15]
    except (json.JSONDecodeError, AttributeError):
        pass

    if not sender_name:
        sender_id = message.get("sender_id", "")
        sender_name = sender_id.split("@")[0][:10] if sender_id else f"msg{index}"

    att_id = attachment.get("id", "unknown")[:8]
    ext = _resolve_extension(attachment)

    return f"{ts_clean}_{sender_name}_{att_id}{ext}"


# ============================================================================
# TIME / SENDER HELPERS
# ============================================================================

# Paris timezone offset (CET = UTC+1, CEST = UTC+2)
# We use a fixed offset of +1 as default (CET) — caller can override via tz_offset_hours
_DEFAULT_TZ_OFFSET_HOURS = 1  # Europe/Paris CET


def parse_time_filter(time_str: str) -> Optional[tuple]:
    """
    Parse a time string into (hour, minute).

    Accepts: "15:51", "15h51", "1551", "15h", "15"

    Returns:
        (hour, minute) as ints, or (hour, None) if only hour given
    """
    time_str = time_str.strip()
    # 15:51 or 15h51
    m = re.match(r'^(\d{1,2})[h:](\d{2})$', time_str)
    if m:
        return int(m.group(1)), int(m.group(2))
    # 1551 (compact)
    m = re.match(r'^(\d{2})(\d{2})$', time_str)
    if m:
        return int(m.group(1)), int(m.group(2))
    # 15h or 15 (hour only)
    m = re.match(r'^(\d{1,2})h?$', time_str)
    if m:
        return int(m.group(1)), None
    raise ValueError(
        f"Cannot parse time '{time_str}'. Use format: 15:51, 15h51, or 1551"
    )


def normalize_sender(sender: str) -> str:
    """
    Normalize a sender identifier to Unipile LID or provider_id format.

    Accepts:
        - LID as-is:              "142988252606566@lid"
        - Phone with +/spaces:    "+33 6 76 13 37 08" → "33676133708"
        - Plain phone:            "33676133708"
        - WhatsApp provider_id:   "33676133708@s.whatsapp.net"

    Returns:
        Normalized string for matching against message sender_id or original JSON.
    """
    # Already a LID
    if sender.endswith("@lid"):
        return sender
    # Already a full provider_id
    if sender.endswith("@s.whatsapp.net"):
        return sender
    # Strip non-digits (spaces, dashes, +)
    digits = re.sub(r'\D', '', sender)
    return digits  # will be matched as substring


def message_matches_sender(message: Dict[str, Any], sender: str) -> bool:
    """
    Check if a message was sent by the given sender.

    Matches against:
    - message["sender_id"]  (LID format: "142988252606566@lid")
    - original["key"]["participantAlt"]  (phone: "33676133708@s.whatsapp.net")
    - original["pushName"]  (display name, case-insensitive)
    """
    sender_norm = normalize_sender(sender)

    # Match LID exactly
    sender_id = message.get("sender_id", "")
    if sender_norm == sender_id:
        return True

    # Match by phone digits as substring
    original_raw = message.get("original", "{}")
    try:
        original = json.loads(original_raw) if isinstance(original_raw, str) else original_raw
        key = original.get("key", {})
        participant_alt = key.get("participantAlt", "") or key.get("remoteJid", "")
        push_name = original.get("pushName", "")

        if sender_norm in participant_alt:
            return True
        # Name match (case-insensitive, for convenience)
        if sender_norm.lower() in push_name.lower():
            return True
    except (json.JSONDecodeError, AttributeError):
        pass

    return False


def message_matches_time(
    message: Dict[str, Any],
    hour: int,
    minute: Optional[int],
    window_minutes: int = 2,
    tz_offset_hours: int = _DEFAULT_TZ_OFFSET_HOURS,
) -> bool:
    """
    Check if a message was sent at the given local time (±window_minutes).

    Args:
        message: Message dict with "timestamp" in ISO format (UTC)
        hour: Local hour to match (0-23)
        minute: Local minute to match (0-59), or None to match any minute in that hour
        window_minutes: Tolerance in minutes (default ±2 min)
        tz_offset_hours: Local timezone offset from UTC (default +1 for Paris CET)
    """
    ts_str = message.get("timestamp", "")
    if not ts_str:
        return False

    try:
        # Parse UTC timestamp
        ts_utc = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        # Convert to local time
        local_dt = ts_utc + timedelta(hours=tz_offset_hours)
        local_h, local_m = local_dt.hour, local_dt.minute

        if minute is None:
            # Match whole hour
            return local_h == hour

        # Match with tolerance window
        target_minutes = hour * 60 + minute
        actual_minutes = local_h * 60 + local_m
        return abs(actual_minutes - target_minutes) <= window_minutes

    except (ValueError, TypeError):
        return False

class MediaDownloader:
    """
    High-level interface for downloading WhatsApp media attachments.

    Args:
        config: Dict with keys: unipile.dsn, unipile.api_key, unipile.account_id
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = UnipileWhatsAppClient(
            dsn=config["unipile"]["dsn"],
            api_key=config["unipile"]["api_key"],
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
        List messages that contain attachments in a chat.

        Args:
            chat_id: Unipile chat ID
            limit: Max messages to fetch (default: 50)
            attachment_type: Filter by type: "audio", "image", "video", "document"
            sender: Sender phone (+33676133708), LID (142988252606566@lid), or name
            time_str: Local time to filter on, e.g. "15:51", "15h51", "1551"
            time_window: Tolerance in minutes around time_str (default: ±2 min)
            tz_offset_hours: Local timezone UTC offset (default: +1 for Paris)

        Returns:
            List of attachment items (one per attachment, not per message).
        """
        response = await self.client.get_chat_messages(chat_id=chat_id, limit=limit)
        messages = response.get("items", [])

        # Pre-parse time filter
        time_filter = None
        if time_str:
            time_filter = parse_time_filter(time_str)

        result = []
        for msg in messages:
            attachments = msg.get("attachments") or []
            if not attachments:
                continue

            # Filter by sender (phone, LID, or name)
            if sender and not message_matches_sender(msg, sender):
                continue

            # Filter by time
            if time_filter is not None:
                hour, minute = time_filter
                if not message_matches_time(msg, hour, minute, time_window, tz_offset_hours):
                    continue

            # Filter by attachment type
            if attachment_type:
                attachments = [a for a in attachments if a.get("type") == attachment_type]
                if not attachments:
                    continue

            for i, att in enumerate(attachments):
                result.append({
                    "message": msg,
                    "attachment": att,
                    "filename": _build_filename(msg, att, i),
                    "message_id": msg["id"],
                    "attachment_id": att["id"],
                    "duration": att.get("duration"),
                    "mimetype": att.get("mimetype"),
                    "voice_note": att.get("voice_note", False),
                    "timestamp": msg.get("timestamp"),
                    "sender_id": msg.get("sender_id"),
                    "sender_name": _get_sender_name(msg),
                })

        return result

    async def download_single(
        self,
        message_id: str,
        attachment_id: str,
        output_path: str,
    ) -> Path:
        """
        Download a single attachment by its IDs.

        Args:
            message_id: Unipile message "id" field (not provider_id)
            attachment_id: Attachment "id" field
            output_path: Destination file path

        Returns:
            Path to the saved file

        Raises:
            NotFoundError: Message or attachment not found
            UnauthorizedError: Invalid API key
            AccountDisconnectedError: WhatsApp account disconnected
            RateLimitError: Too many requests
            InternalServerError: Unipile server error
        """
        await self.client.download_attachment(
            message_id=message_id,
            attachment_id=attachment_id,
            output_path=output_path,
        )
        return Path(output_path)

    async def download_all_voice_notes(
        self,
        chat_id: str,
        output_dir: str = "./downloads",
        limit: int = 50,
        sender: Optional[str] = None,
        time_str: Optional[str] = None,
        time_window: int = 2,
        tz_offset_hours: int = _DEFAULT_TZ_OFFSET_HOURS,
        skip_existing: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Download all voice notes from a chat.

        Args:
            chat_id: Unipile chat ID
            output_dir: Directory to save files
            limit: Max messages to scan
            sender: Phone number, LID, or name
            time_str: Local time filter e.g. "15:51"
            time_window: Tolerance in minutes (default ±2)
            tz_offset_hours: Timezone offset from UTC (default +1)
            skip_existing: Skip files already downloaded
        """
        return await self.download_attachments(
            chat_id=chat_id,
            output_dir=output_dir,
            limit=limit,
            attachment_type="audio",
            sender=sender,
            time_str=time_str,
            time_window=time_window,
            tz_offset_hours=tz_offset_hours,
            skip_existing=skip_existing,
        )

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
        Download attachments from a chat with optional filters.

        Args:
            chat_id: Unipile chat ID
            output_dir: Directory to save files
            limit: Max messages to scan
            attachment_type: "audio", "image", "video", "document" or None for all
            sender: Phone number (+33676133708), LID, or display name
            time_str: Local time filter e.g. "15:51", "15h51"
            time_window: Tolerance in minutes around time_str (default ±2)
            tz_offset_hours: Local timezone UTC offset (default +1 for Paris)
            skip_existing: Skip files already downloaded

        Returns:
            List of result dicts: {filename, path, status, error, timestamp, sender_name, duration, mimetype}
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
            result = {
                "filename": filename,
                "path": str(dest),
                "status": "ok",
                "error": None,
                "timestamp": item["timestamp"],
                "sender_name": item["sender_name"],
                "duration": item["duration"],
                "mimetype": item["mimetype"],
            }

            if skip_existing and dest.exists():
                result["status"] = "skipped"
                results.append(result)
                continue

            try:
                await self.client.download_attachment(
                    message_id=item["message_id"],
                    attachment_id=item["attachment_id"],
                    output_path=str(dest),
                )
            except NotFoundError as e:
                result["status"] = "error"
                result["error"] = f"Not found: {e}"
            except UnauthorizedError as e:
                result["status"] = "error"
                result["error"] = f"Unauthorized: {e}"
            except AccountDisconnectedError as e:
                result["status"] = "error"
                result["error"] = f"Account disconnected: {e}"
            except RateLimitError as e:
                result["status"] = "error"
                result["error"] = f"Rate limited (retry after {e.retry_after}s): {e}"
            except InternalServerError as e:
                result["status"] = "error"
                result["error"] = f"Server error: {e}"
            except UnipileError as e:
                result["status"] = "error"
                result["error"] = f"API error: {e}"
            except Exception as e:
                result["status"] = "error"
                result["error"] = f"Unexpected error: {e}"

            results.append(result)

        return results


# ============================================================================
# HELPERS
# ============================================================================

def _get_sender_name(message: Dict[str, Any]) -> str:
    """Extract pushName from original WhatsApp message JSON."""
    original_raw = message.get("original", "{}")
    try:
        original = json.loads(original_raw) if isinstance(original_raw, str) else original_raw
        return original.get("pushName", "") or message.get("sender_id", "unknown")
    except (json.JSONDecodeError, AttributeError):
        return message.get("sender_id", "unknown")


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load config from JSON file. Defaults to assets/config.json relative to skill root."""
    if config_path:
        path = Path(config_path)
    else:
        path = _SKILL_DIR / "assets" / "config.json"

    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}. Run setup.sh first.")

    with open(path) as f:
        return json.load(f)


# ============================================================================
# CLI
# ============================================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download WhatsApp attachments via Unipile API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List voice notes in a chat
  python download_media.py --chat_id Q7z9wLVuWEKXJ505iLYh9w --list --type audio

  # Download all voice notes from a chat
  python download_media.py --chat_id Q7z9wLVuWEKXJ505iLYh9w --type audio --output_dir ./downloads/

  # Download from a specific sender
  python download_media.py --chat_id Q7z9wLVuWEKXJ505iLYh9w --sender 142988252606566@lid --type audio

  # Download a specific message attachment by IDs
  python download_media.py --message_id kLR2ZebfWIy3Y6WeOPzIuw --attachment_id 3EB0C98DE493248B2CC757 --output_path ./voice.ogg
        """
    )

    # Mode
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--list", action="store_true", help="List attachments without downloading")
    mode.add_argument("--message_id", help="Download specific message by Unipile message ID")

    # Target
    parser.add_argument("--chat_id", help="Unipile chat ID")
    parser.add_argument("--attachment_id", help="Attachment ID (required with --message_id)")
    parser.add_argument("--output_path", help="Output file path (for single download)")

    # Filters
    parser.add_argument("--type", dest="attachment_type",
                        choices=["audio", "image", "video", "document"],
                        help="Filter by attachment type")
    parser.add_argument("--sender",
                        help="Filter by sender: phone (+33676133708), LID (142988252606566@lid), or name (Kilian)")
    parser.add_argument("--time",
                        help="Filter by local time: '15:51', '15h51', '1551'")
    parser.add_argument("--time_window", type=int, default=2,
                        help="Time match tolerance in minutes (default: 2)")
    parser.add_argument("--tz", dest="tz_offset", type=int, default=1,
                        help="Timezone offset from UTC (default: 1 for Paris CET)")
    parser.add_argument("--limit", type=int, default=50,
                        help="Max messages to scan (default: 50)")

    # Output
    parser.add_argument("--output_dir", default="./downloads",
                        help="Output directory for batch download (default: ./downloads)")
    parser.add_argument("--no_skip", action="store_true",
                        help="Re-download even if file already exists")
    parser.add_argument("--config", help="Path to config.json (default: assets/config.json)")

    return parser


async def main_async(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    downloader = MediaDownloader(config)

    # Mode 1: Download single attachment by message_id + attachment_id
    if args.message_id:
        if not args.attachment_id:
            print("Error: --attachment_id is required with --message_id", file=sys.stderr)
            return 1
        output = args.output_path or f"./downloads/{args.attachment_id}.bin"
        try:
            path = await downloader.download_single(
                message_id=args.message_id,
                attachment_id=args.attachment_id,
                output_path=output,
            )
            print(f"Downloaded: {path}")
            return 0
        except NotFoundError:
            print(f"Error: Message or attachment not found", file=sys.stderr)
            return 1
        except UnauthorizedError:
            print("Error: Invalid API key", file=sys.stderr)
            return 1
        except AccountDisconnectedError:
            print("Error: WhatsApp account disconnected", file=sys.stderr)
            return 1
        except UnipileError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    # Mode 2: List or batch download from chat
    if not args.chat_id:
        print("Error: --chat_id is required", file=sys.stderr)
        return 1

    if args.list:
        items = await downloader.list_messages_with_attachments(
            chat_id=args.chat_id,
            limit=args.limit,
            attachment_type=args.attachment_type,
            sender=args.sender,
            time_str=args.time,
            time_window=args.time_window,
            tz_offset_hours=args.tz_offset,
        )
        if not items:
            print("No attachments found.")
            return 0
        print(f"Found {len(items)} attachment(s):\n")
        for item in items:
            duration_str = f" [{item['duration']}s]" if item["duration"] else ""
            print(f"  {item['timestamp']}  {item['sender_name']:<15}  "
                  f"{item['attachment']['type']:<8}{duration_str:<8}  "
                  f"msg_id={item['message_id']}  att_id={item['attachment_id']}")
        return 0

    # Batch download
    results = await downloader.download_attachments(
        chat_id=args.chat_id,
        output_dir=args.output_dir,
        limit=args.limit,
        attachment_type=args.attachment_type,
        sender=args.sender,
        time_str=args.time,
        time_window=args.time_window,
        tz_offset_hours=args.tz_offset,
        skip_existing=not args.no_skip,
    )

    ok = [r for r in results if r["status"] == "ok"]
    skipped = [r for r in results if r["status"] == "skipped"]
    errors = [r for r in results if r["status"] == "error"]

    print(f"\nResults: {len(ok)} downloaded, {len(skipped)} skipped, {len(errors)} errors\n")

    for r in ok:
        print(f"  [OK]      {r['filename']}")
    for r in skipped:
        print(f"  [SKIP]    {r['filename']}")
    for r in errors:
        print(f"  [ERROR]   {r['filename']} — {r['error']}")

    return 0 if not errors else 1


def main():
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()
