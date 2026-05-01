#!/usr/bin/env python3
"""ERP Manager CLI - Personal Dashboard API."""
import json
import sys
import typer
from pathlib import Path
from typing import Optional

app = typer.Typer(help="Manage ERP leads and notes.")

# Profile resolver
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / ".profiles"))
_profile_name: Optional[str] = None


@app.callback()
def main(profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile name")):
    global _profile_name
    _profile_name = profile


def _client():
    from erp_manager.client import create_client
    return create_client()


# ──────────────────────────────────────────────
# Leads
# ──────────────────────────────────────────────

leads_app = typer.Typer(help="Lead management.")
app.add_typer(leads_app, name="lead")


@leads_app.command("list")
def lead_list(
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status"),
    heat: Optional[str] = typer.Option(None, "--heat", help="Filter by heat level"),
    search: Optional[str] = typer.Option(None, "--search", help="Full-text search"),
    limit: int = typer.Option(20, "--limit", help="Max results"),
    page: int = typer.Option(1, "--page", help="Page number"),
):
    """List leads with optional filters."""
    from erp_manager.client import format_lead
    client = _client()
    result = client.list_leads(page=page, limit=limit, status=status, heat_level=heat, search=search)
    leads = result.get("leads", [])
    for lead in leads:
        typer.echo(format_lead(lead))
        typer.echo("---")
    typer.echo(f"Total: {result.get('total', len(leads))}")


@leads_app.command("get")
def lead_get(lead_id: int = typer.Argument(..., help="Lead ID")):
    """Get lead details."""
    from erp_manager.client import format_lead
    typer.echo(format_lead(_client().get_lead(lead_id)))


@leads_app.command("create")
def lead_create(
    name: str = typer.Option(..., "--name", help="Last name"),
    email: str = typer.Option(..., "--email", help="Email address"),
    first_name: Optional[str] = typer.Option(None, "--first-name", help="First name"),
    phone: Optional[str] = typer.Option(None, "--phone", help="Phone"),
    company: Optional[str] = typer.Option(None, "--company", help="Company"),
    status: str = typer.Option("to_contact", "--status", help="Status"),
    heat: str = typer.Option("cold", "--heat", help="Heat level"),
):
    """Create a new lead."""
    result = _client().create_lead(
        name=name, email=email, first_name=first_name,
        phone=phone, company=company, status=status, heat_level=heat,
    )
    typer.echo(f"Created lead ID: {result.get('id')}")


@leads_app.command("update")
def lead_update(
    lead_id: int = typer.Argument(..., help="Lead ID"),
    name: Optional[str] = typer.Option(None, "--name"),
    first_name: Optional[str] = typer.Option(None, "--first-name"),
    email: Optional[str] = typer.Option(None, "--email"),
    phone: Optional[str] = typer.Option(None, "--phone"),
    company: Optional[str] = typer.Option(None, "--company"),
    status: Optional[str] = typer.Option(None, "--status"),
    heat: Optional[str] = typer.Option(None, "--heat"),
):
    """Update lead fields."""
    from erp_manager.client import format_lead
    updates = {k: v for k, v in {
        "name": name, "first_name": first_name, "email": email,
        "phone": phone, "company": company, "status": status, "heat_level": heat,
    }.items() if v is not None}
    typer.echo(format_lead(_client().update_lead(lead_id, **updates)))


@leads_app.command("delete")
def lead_delete(lead_id: int = typer.Argument(..., help="Lead ID")):
    """Delete lead permanently."""
    typer.echo(_client().delete_lead(lead_id))


@leads_app.command("search")
def lead_search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(20, "--limit"),
):
    """Search leads by name, email, company."""
    from erp_manager.client import format_lead
    result = _client().search_leads(query, limit=limit)
    for lead in result.get("leads", []):
        typer.echo(format_lead(lead))
        typer.echo("---")


# ──────────────────────────────────────────────
# Notes
# ──────────────────────────────────────────────

notes_app = typer.Typer(help="Note management.")
app.add_typer(notes_app, name="note")


@notes_app.command("list")
def note_list(lead_id: int = typer.Argument(..., help="Lead ID")):
    """List all notes for a lead."""
    from erp_manager.client import format_note
    for note in _client().list_lead_notes(lead_id):
        typer.echo(format_note(note))
        typer.echo("---")


@notes_app.command("get")
def note_get(note_id: int = typer.Argument(..., help="Note ID")):
    """Get note details."""
    from erp_manager.client import format_note
    typer.echo(format_note(_client().get_note(note_id)))


@notes_app.command("create")
def note_create(
    lead_id: int = typer.Option(..., "--lead-id", help="Lead ID"),
    title: str = typer.Option(..., "--title", help="Note title"),
    content: str = typer.Option(..., "--content", help="Note content"),
    description: Optional[str] = typer.Option(None, "--description", help="Short description"),
):
    """Create a note for a lead."""
    result = _client().create_note(lead_id, title, content, description)
    typer.echo(f"Created note ID: {result.get('id')}")


@notes_app.command("delete")
def note_delete(note_id: int = typer.Argument(..., help="Note ID")):
    """Delete note permanently."""
    typer.echo(_client().delete_note(note_id))


if __name__ == "__main__":
    app()
