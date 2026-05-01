#!/usr/bin/env python3
"""Telegram Notifier CLI."""
import sys
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(help="Send Telegram notifications via Bot API.")

# Profile resolver
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / ".profiles"))
_profile_name: Optional[str] = None


@app.callback()
def main(profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile name")):
    global _profile_name
    _profile_name = profile


def _client():
    from telegram_notifier.client import create_client
    return create_client(profile=_profile_name)


@app.command("send")
def send(
    text: str = typer.Option(..., "--text", help="Message text"),
    chat_id: Optional[int] = typer.Option(None, "--chat-id", help="Override chat ID"),
    silent: bool = typer.Option(False, "--silent", help="Send silently"),
):
    """Send a plain text message."""
    result = _client().send_message(text, chat_id=chat_id, disable_notification=silent)
    typer.echo("OK" if result.get("ok") else f"Error: {result}")
    if not result.get("ok"):
        raise typer.Exit(1)


@app.command("notify")
def notify(
    title: str = typer.Option(..., "--title", help="Notification title"),
    text: str = typer.Option(..., "--text", help="Notification body"),
    chat_id: Optional[int] = typer.Option(None, "--chat-id", help="Override chat ID"),
    emoji: str = typer.Option("🔔", "--emoji", help="Title emoji"),
):
    """Send a formatted notification."""
    result = _client().send_notification(title, text, chat_id=chat_id, emoji=emoji)
    typer.echo("OK" if result.get("ok") else f"Error: {result}")
    if not result.get("ok"):
        raise typer.Exit(1)


@app.command("alert")
def alert(
    text: str = typer.Option(..., "--text", help="Alert message"),
    level: str = typer.Option("info", "--level", help="info|warning|error|success"),
    chat_id: Optional[int] = typer.Option(None, "--chat-id", help="Override chat ID"),
):
    """Send an alert with level emoji."""
    result = _client().send_alert(text, level=level, chat_id=chat_id)
    typer.echo("OK" if result.get("ok") else f"Error: {result}")
    if not result.get("ok"):
        raise typer.Exit(1)


@app.command("test")
def test():
    """Test bot connection."""
    client = _client()
    bot_info = client.get_me()
    name = bot_info.get("result", {}).get("first_name", "unknown")
    typer.echo(f"Connected: {name}")
    result = client.send_notification("Test", "Bot operational")
    typer.echo("OK" if result.get("ok") else f"Error: {result}")


if __name__ == "__main__":
    app()
