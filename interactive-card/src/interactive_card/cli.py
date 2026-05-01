#!/usr/bin/env python3
"""Interactive Card CLI — create structured notifications in AI Manager."""

import json
import sys
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(
    help="Create interactive cards (notifications, forms, tickets) in the AI Manager.",
    no_args_is_help=True,
)


def _client():
    from interactive_card.client import create_conversation, test_connection
    return create_conversation, test_connection


def _builder():
    from interactive_card.builder import CardBuilder
    return CardBuilder


# ---------------------------------------------------------------------------
# notify — simple notification with text + resolve button
# ---------------------------------------------------------------------------

@app.command("notify")
def notify(
    title: str = typer.Argument(..., help="Notification title"),
    text: str = typer.Argument(..., help="Notification body (markdown)"),
    pid: str = typer.Option("system", "--pid", help="PID for the conversation"),
    button_label: str = typer.Option("OK", "--button", help="Resolve button label"),
):
    """Send a simple notification. Auto-creates a resolve button.

    Example:
        interactive-card notify "New booking" "**Client**: John Doe, tomorrow 2pm"
    """
    CardBuilder = _builder()
    card = (CardBuilder()
        .text(title, bold=True)
        .text(text)
        .button("resolve", button_label, "primary", action_type="resolve")
        .build())

    create, _ = _client()
    result = create(card, title=title, pid=pid)
    typer.echo(json.dumps({"ok": True, "conversation_id": result["id"]}, indent=2))


# ---------------------------------------------------------------------------
# prompt — card with text, optional inputs, and action buttons
# ---------------------------------------------------------------------------

@app.command("prompt")
def prompt(
    title: str = typer.Argument(..., help="Card title"),
    text: str = typer.Option("", "--text", "-t", help="Body text (markdown)"),
    fact: list[str] = typer.Option([], "--fact", "-f", help="Key=Value fact (repeatable)"),
    input_field: list[str] = typer.Option(
        [], "--input", "-i",
        help="id:type:label[:placeholder] (repeatable). Types: text,textarea,select,number,date,toggle",
    ),
    select_options: list[str] = typer.Option(
        [], "--options",
        help="input_id:value1=Label1,value2=Label2 (for select inputs)",
    ),
    approve: str = typer.Option("", "--approve", help="Label for approve button (event+resolve)"),
    reject: str = typer.Option("", "--reject", help="Label for reject/dismiss button (resolve)"),
    event_source: str = typer.Option("", "--event-source", help="Source for event action"),
    event_type: str = typer.Option("action.approved", "--event-type", help="Event type for approve action"),
    related_to: str = typer.Option("", "--related-to", help="Related event ID"),
    pid: str = typer.Option("system", "--pid", help="PID for the conversation"),
):
    """Create an interactive prompt with optional form fields and buttons.

    Examples:
        interactive-card prompt "Approve booking?" \\
            --text "John Doe wants tomorrow at 2pm" \\
            --fact "Client=John Doe" --fact "Date=2026-04-23" \\
            --input "reply:textarea:Your response" \\
            --approve "Approve" --reject "Reject" \\
            --event-source "interactive:booking" --event-type "booking.approved"

        interactive-card prompt "Choose priority" \\
            --input "level:select:Priority" \\
            --options "level:low=Low,medium=Medium,high=High" \\
            --approve "Set" --event-source "interactive:triage"
    """
    CardBuilder = _builder()
    builder = CardBuilder()

    builder.text(title, bold=True)
    if text:
        builder.text(text)

    # Parse facts
    if fact:
        facts = {}
        for f in fact:
            if "=" in f:
                k, v = f.split("=", 1)
                facts[k.strip()] = v.strip()
        if facts:
            builder.fact_set(facts)

    # Parse select options lookup
    options_map: dict[str, dict[str, str]] = {}
    for opt_str in select_options:
        if ":" in opt_str:
            input_id, pairs = opt_str.split(":", 1)
            opts = {}
            for pair in pairs.split(","):
                if "=" in pair:
                    val, label = pair.split("=", 1)
                    opts[val.strip()] = label.strip()
            options_map[input_id.strip()] = opts

    # Parse inputs
    for inp in input_field:
        parts = inp.split(":")
        inp_id = parts[0]
        inp_type = parts[1] if len(parts) > 1 else "text"
        inp_label = parts[2] if len(parts) > 2 else ""
        inp_placeholder = parts[3] if len(parts) > 3 else ""
        opts = options_map.get(inp_id)
        builder.input(inp_id, inp_type, label=inp_label, placeholder=inp_placeholder, options=opts)

    # Buttons
    has_inputs = len(input_field) > 0
    if approve:
        builder.button(
            "approve", approve, "primary",
            action_type="event" if event_source else "resolve",
            source=event_source,
            event_type=event_type,
            related_to=related_to,
            inputs="all" if has_inputs else "none",
            resolves=True,
        )
    if reject:
        builder.button("reject", reject, "ghost", action_type="resolve")

    # If no buttons specified, add a default resolve
    if not approve and not reject:
        builder.button("ok", "OK", "primary", action_type="resolve")

    card = builder.build()
    create, _ = _client()
    result = create(card, title=title, pid=pid)
    typer.echo(json.dumps({"ok": True, "conversation_id": result["id"]}, indent=2))


# ---------------------------------------------------------------------------
# create — full JSON control
# ---------------------------------------------------------------------------

@app.command("create")
def create(
    card_json: str = typer.Argument(None, help="Card JSON string (body + actions)"),
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="Read card JSON from file"),
    title: str = typer.Option("", "--title", help="Text shown above the card"),
    pid: str = typer.Option("system", "--pid", help="PID for the conversation"),
):
    """Create a conversation with a full interactive card from JSON.

    The JSON must have 'body' (list of elements) and 'actions' (list of buttons).

    Examples:
        interactive-card create '{"body":[{"type":"text","text":"Hello"}],"actions":[{"id":"ok","label":"OK","style":"primary","action":{"type":"resolve"}}]}'

        interactive-card create --file /tmp/card.json --title "Review needed"

        echo '{"body": [...], "actions": [...]}' | interactive-card create -
    """
    if card_json == "-":
        raw = sys.stdin.read()
    elif file:
        raw = file.read_text()
    elif card_json:
        raw = card_json
    else:
        typer.echo("Error: provide JSON as argument, --file, or pipe via stdin", err=True)
        raise typer.Exit(1)

    try:
        card = json.loads(raw)
    except json.JSONDecodeError as e:
        typer.echo(f"Error: invalid JSON — {e}", err=True)
        raise typer.Exit(1)

    if "body" not in card or "actions" not in card:
        typer.echo("Error: JSON must have 'body' and 'actions' keys", err=True)
        raise typer.Exit(1)

    create_fn, _ = _client()
    result = create_fn(card, title=title or None, pid=pid)
    typer.echo(json.dumps({"ok": True, "conversation_id": result["id"]}, indent=2))


# ---------------------------------------------------------------------------
# test — verify connectivity
# ---------------------------------------------------------------------------

@app.command("test")
def test():
    """Test connection to the AI Manager backend."""
    _, test_fn = _client()
    try:
        result = test_fn()
        typer.echo(f"Connected: {json.dumps(result)}")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
