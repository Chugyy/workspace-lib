#!/usr/bin/env python3
"""WhatsApp Manager CLI - WAHA (WhatsApp HTTP API)."""
import asyncio
import json
import sys
import typer
from pathlib import Path
from typing import Optional

app = typer.Typer(help="Send and receive WhatsApp messages via WAHA (self-hosted).")

SKILL_DIR = Path(__file__).parent.parent.parent

# Profile resolver
sys.path.insert(0, str(SKILL_DIR.parent / ".profiles"))
_profile_name: Optional[str] = None


@app.callback()
def main(profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile name")):
    global _profile_name
    _profile_name = profile


AI_PREFIX = "\n\n_Written by AI_"


def load_config():
    """Load config from profile resolver, with legacy fallback."""
    try:
        from resolver import resolve
        return resolve("whatsapp", _profile_name)
    except Exception:
        # Fallback: try .env-style config
        config_path = SKILL_DIR / "assets" / "config.json"
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        raise


def _client():
    from whatsapp_manager.client import WAHAClient
    config = load_config()
    waha = config.get("waha", config)
    return WAHAClient(
        base_url=waha["base_url"],
        api_key=waha["api_key"],
        session=waha.get("session", "default"),
    )


def _tag(text: str) -> str:
    """Append AI authorship tag to outgoing messages."""
    return text + AI_PREFIX


@app.command("send-text")
def send_text(
    chat_id: str = typer.Option(..., "--chat-id", help="Chat ID (e.g., 33612345678@c.us)"),
    text: str = typer.Option(..., "--text", help="Message text"),
):
    """Send a text message to an existing chat."""
    async def _run():
        client = _client()
        result = await client.send_text_message(chat_id, _tag(text))
        typer.echo(json.dumps(result, indent=2, default=str))
    asyncio.run(_run())


@app.command("send-image")
def send_image(
    chat_id: str = typer.Option(..., "--chat-id", help="Chat ID"),
    image: str = typer.Option(..., "--image", help="Image file path"),
    caption: str = typer.Option("", "--caption", help="Caption"),
):
    """Send an image to an existing chat."""
    async def _run():
        client = _client()
        result = await client.send_image(chat_id, image, caption)
        typer.echo(json.dumps(result, indent=2, default=str))
    asyncio.run(_run())


@app.command("send-video")
def send_video(
    chat_id: str = typer.Option(..., "--chat-id", help="Chat ID"),
    video: str = typer.Option(..., "--video", help="Video file path"),
    caption: str = typer.Option("", "--caption", help="Caption"),
):
    """Send a video to an existing chat."""
    async def _run():
        client = _client()
        result = await client.send_video(chat_id, video, caption)
        typer.echo(json.dumps(result, indent=2, default=str))
    asyncio.run(_run())


@app.command("send-audio")
def send_audio(
    chat_id: str = typer.Option(..., "--chat-id", help="Chat ID"),
    audio: str = typer.Option(..., "--audio", help="Audio file path"),
):
    """Send an audio file to an existing chat."""
    async def _run():
        client = _client()
        result = await client.send_audio(chat_id, audio)
        typer.echo(json.dumps(result, indent=2, default=str))
    asyncio.run(_run())


@app.command("send-file")
def send_file(
    chat_id: str = typer.Option(..., "--chat-id", help="Chat ID"),
    file: str = typer.Option(..., "--file", help="File path"),
    caption: str = typer.Option("", "--caption", help="Caption"),
):
    """Send a document/file to an existing chat."""
    async def _run():
        client = _client()
        result = await client.send_file(chat_id, file, caption)
        typer.echo(json.dumps(result, indent=2, default=str))
    asyncio.run(_run())


@app.command("new-conversation")
def new_conversation(
    phone: str = typer.Option(..., "--phone", help="Phone number E.164 format (+33...)"),
    text: str = typer.Option(..., "--text", help="Initial message"),
    files: Optional[str] = typer.Option(None, "--files", help="Comma-separated file paths"),
):
    """Start a new conversation with a phone number."""
    async def _run():
        client = _client()
        file_paths = files.split(",") if files else None
        result = await client.start_new_conversation(phone, _tag(text), file_paths)
        typer.echo(json.dumps(result, indent=2, default=str))
    asyncio.run(_run())


@app.command("get-chats")
def get_chats(
    limit: int = typer.Option(50, "--limit", help="Max chats"),
    offset: int = typer.Option(0, "--offset", help="Pagination offset"),
):
    """List all conversations."""
    async def _run():
        client = _client()
        result = await client.get_chats(limit=limit, offset=offset)
        items = result.get("items", result if isinstance(result, list) else [])
        for chat in items:
            chat_id = chat.get("id", "")
            name = chat.get("name", "") or chat.get("title", "")
            is_group = "[group]" if chat_id.endswith("@g.us") else ""
            typer.echo(f"{chat_id}  {name}  {is_group}")
        typer.echo(f"\n{len(items)} chats")
    asyncio.run(_run())


@app.command("get-messages")
def get_messages(
    chat_id: str = typer.Option(..., "--chat-id", help="Chat ID"),
    limit: int = typer.Option(50, "--limit", help="Max messages"),
):
    """Get message history for a chat."""
    async def _run():
        client = _client()
        result = await client.get_chat_messages(chat_id, limit=limit)
        typer.echo(json.dumps(result, indent=2, default=str))
    asyncio.run(_run())


@app.command("download-media")
def download_media(
    chat_id: str = typer.Option(..., "--chat-id", help="Chat ID"),
    output_dir: str = typer.Option("./downloads", "--output-dir", help="Output directory"),
    attachment_type: Optional[str] = typer.Option(None, "--type", help="audio|image|video|document"),
    sender: Optional[str] = typer.Option(None, "--sender", help="Phone, name, or JID"),
    time: Optional[str] = typer.Option(None, "--time", help="Local time filter e.g. 15:51"),
    limit: int = typer.Option(50, "--limit", help="Max messages to scan"),
    list_only: bool = typer.Option(False, "--list", help="List without downloading"),
):
    """Download media attachments from a chat."""
    async def _run():
        from whatsapp_manager.download_media import MediaDownloader
        config = load_config()
        downloader = MediaDownloader(config)

        if list_only:
            items = await downloader.list_messages_with_attachments(
                chat_id=chat_id, limit=limit,
                attachment_type=attachment_type, sender=sender, time_str=time,
            )
            if not items:
                typer.echo("No attachments found.")
                return
            typer.echo(f"Found {len(items)} attachment(s):\n")
            for item in items:
                dur = f" [{item['duration']}s]" if item.get("duration") else ""
                typer.echo(f"  {item['timestamp']}  {item['sender_name']:<15}  "
                           f"{item['media_type']:<8}{dur}  "
                           f"msg_id={item['message_id']}")
        else:
            results = await downloader.download_attachments(
                chat_id=chat_id, output_dir=output_dir, limit=limit,
                attachment_type=attachment_type, sender=sender, time_str=time,
            )
            ok = [r for r in results if r["status"] == "ok"]
            skipped = [r for r in results if r["status"] == "skipped"]
            errors = [r for r in results if r["status"] == "error"]
            typer.echo(f"\nResults: {len(ok)} downloaded, {len(skipped)} skipped, {len(errors)} errors")
            for r in ok:
                typer.echo(f"  [OK]      {r['filename']}")
            for r in errors:
                typer.echo(f"  [ERROR]   {r['filename']} — {r['error']}")

    asyncio.run(_run())


@app.command("session-status")
def session_status():
    """Check WhatsApp session status."""
    async def _run():
        client = _client()
        result = await client.get_session_status()
        status = result.get("status", "UNKNOWN")
        me = result.get("me")
        typer.echo(f"Session: {client.session}")
        typer.echo(f"Status:  {status}")
        if me:
            typer.echo(f"Account: {me.get('id', '')} ({me.get('pushName', '')})")
        if status == "SCAN_QR_CODE":
            typer.echo(f"\n→ Scan QR code at: {client.base_url}/dashboard")
    asyncio.run(_run())


@app.command("check-phone")
def check_phone(
    phone: str = typer.Option(..., "--phone", help="Phone number E.164 format (+33...)"),
):
    """Check if a phone number is on WhatsApp."""
    async def _run():
        client = _client()
        from whatsapp_manager.client import PhoneNotOnWhatsAppError
        try:
            result = await client.check_phone_exists_on_whatsapp(phone)
            typer.echo(f"✓ {phone} is on WhatsApp → chatId: {result.get('chatId', 'unknown')}")
        except PhoneNotOnWhatsAppError:
            typer.echo(f"✗ {phone} is NOT on WhatsApp")
    asyncio.run(_run())


if __name__ == "__main__":
    app()
