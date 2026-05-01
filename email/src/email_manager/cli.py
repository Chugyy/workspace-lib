#!/usr/bin/env python3
"""Email Manager CLI - Gmail API + IMAP/SMTP."""
import json
import sys
import typer
from pathlib import Path
from typing import Optional

app = typer.Typer(help="Manage emails via Gmail API or IMAP/SMTP.")

SKILL_DIR = Path(__file__).parent.parent.parent
CONFIG_PATH = SKILL_DIR / "assets" / "config.json"

# Profile resolver
sys.path.insert(0, str(SKILL_DIR.parent / ".profiles"))
_profile_name: Optional[str] = None


@app.callback()
def main(profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile name")):
    global _profile_name
    _profile_name = profile


def load_config():
    """Load config from profile resolver, with legacy fallback."""
    try:
        from resolver import resolve
        return resolve("email", _profile_name)
    except Exception:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                return json.load(f)
        raise


# ──────────────────────────────────────────────
# Gmail subcommands
# ──────────────────────────────────────────────

gmail_app = typer.Typer(help="Gmail API commands (OAuth).")
app.add_typer(gmail_app, name="gmail")


def _get_gmail():
    from email_manager.gmail_client import authenticate
    config = load_config()
    creds = config["gmail"]["credentials"]
    return authenticate(creds)


@gmail_app.command("list")
def gmail_list(
    max: int = typer.Option(10, help="Max results"),
    unread: bool = typer.Option(False, "--unread", help="Unread only"),
    sender: Optional[str] = typer.Option(None, "--sender", help="Filter by sender"),
    subject: Optional[str] = typer.Option(None, "--subject", help="Filter by subject"),
):
    """List emails."""
    from email_manager.gmail_client import list_emails
    gmail = _get_gmail()
    emails = list_emails(gmail, max_results=max, unread_only=unread, sender=sender, subject=subject)
    for e in emails:
        typer.echo(f"[{e['id']}] {e['date']} | From: {e['from']} | {e['subject']}")


@gmail_app.command("read")
def gmail_read(message_id: str = typer.Argument(..., help="Gmail message ID")):
    """Read full email by ID."""
    from email_manager.gmail_client import read_email
    gmail = _get_gmail()
    e = read_email(gmail, message_id)
    typer.echo(f"From: {e['from']}\nTo: {e['to']}\nSubject: {e['subject']}\nDate: {e['date']}\n\n{e['plain_text']}")


@gmail_app.command("send")
def gmail_send(
    to: str = typer.Option(..., "--to", help="Recipient"),
    subject: str = typer.Option(..., "--subject", help="Subject"),
    body: str = typer.Option(..., "--body", help="Body"),
    html: bool = typer.Option(False, "--html", help="Body is HTML"),
):
    """Send email via Gmail."""
    from email_manager.gmail_client import send_email
    gmail = _get_gmail()
    ok = send_email(gmail, to, subject, body, html=html)
    typer.echo("Sent" if ok else "Failed")
    if not ok:
        raise typer.Exit(1)


@gmail_app.command("draft")
def gmail_draft(
    to: str = typer.Option(..., "--to", help="Recipient"),
    subject: str = typer.Option(..., "--subject", help="Subject"),
    body: str = typer.Option(..., "--body", help="Body"),
    html: bool = typer.Option(False, "--html", help="Body is HTML"),
):
    """Create draft email."""
    from email_manager.gmail_client import create_draft
    gmail = _get_gmail()
    ok = create_draft(gmail, to, subject, body, html=html)
    typer.echo("Draft created" if ok else "Failed")
    if not ok:
        raise typer.Exit(1)


@gmail_app.command("search")
def gmail_search(
    query: str = typer.Argument(..., help="Gmail query (e.g. 'from:user@example.com newer_than:7d')"),
    max: int = typer.Option(10, help="Max results"),
):
    """Search emails using Gmail query syntax."""
    from email_manager.gmail_client import search_emails
    gmail = _get_gmail()
    emails = search_emails(gmail, query, max_results=max)
    for e in emails:
        typer.echo(f"[{e['id']}] {e['date']} | From: {e['from']} | {e['subject']}")


# ──────────────────────────────────────────────
# IMAP subcommands
# ──────────────────────────────────────────────

imap_app = typer.Typer(help="IMAP/SMTP commands (any provider).")
app.add_typer(imap_app, name="imap")


def _get_imap_config():
    return load_config()["imap_smtp"]


@imap_app.command("list")
def imap_list(
    limit: int = typer.Option(10, help="Max results"),
    unread: bool = typer.Option(False, "--unread", help="Unread only"),
    folder: str = typer.Option("INBOX", "--folder", help="Folder"),
):
    """List emails via IMAP."""
    from email_manager.imap_smtp_client import list_emails
    cfg = _get_imap_config()
    emails = list_emails(cfg["imap_host"], cfg["email"], cfg["password"],
                         folder=folder, limit=limit, unread_only=unread)
    for e in emails:
        typer.echo(f"[{e['id']}] {e['date']} | From: {e['from']} | {e['subject']}")


@imap_app.command("read")
def imap_read(
    email_id: str = typer.Argument(..., help="Email ID"),
    folder: str = typer.Option("INBOX", "--folder", help="Folder"),
):
    """Read full email by ID via IMAP."""
    from email_manager.imap_smtp_client import read_email
    cfg = _get_imap_config()
    e = read_email(cfg["imap_host"], cfg["email"], cfg["password"], email_id, folder=folder)
    typer.echo(f"From: {e['from']}\nTo: {e['to']}\nSubject: {e['subject']}\nDate: {e['date']}\n\n{e['body']}")


@imap_app.command("send")
def imap_send(
    to: str = typer.Option(..., "--to", help="Recipient"),
    subject: str = typer.Option(..., "--subject", help="Subject"),
    body: str = typer.Option(..., "--body", help="Body"),
    html: bool = typer.Option(False, "--html", help="Body is HTML"),
):
    """Send email via SMTP."""
    from email_manager.imap_smtp_client import send_email
    cfg = _get_imap_config()
    ok = send_email(cfg["smtp_host"], cfg["email"], cfg["password"], to, subject, body, html=html)
    typer.echo("Sent" if ok else "Failed")
    if not ok:
        raise typer.Exit(1)


@imap_app.command("search")
def imap_search(
    sender: Optional[str] = typer.Option(None, "--sender", help="Filter by sender"),
    subject: Optional[str] = typer.Option(None, "--subject", help="Filter by subject"),
    limit: int = typer.Option(10, help="Max results"),
):
    """Search emails via IMAP."""
    from email_manager.imap_smtp_client import search_emails
    cfg = _get_imap_config()
    emails = search_emails(cfg["imap_host"], cfg["email"], cfg["password"],
                           sender=sender, subject=subject, limit=limit)
    for e in emails:
        typer.echo(f"[{e['id']}] {e['date']} | From: {e['from']} | {e['subject']}")


if __name__ == "__main__":
    app()
