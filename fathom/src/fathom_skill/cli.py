#!/usr/bin/env python3
"""Fathom CLI - Fetch call transcripts."""
import sys
import typer
from pathlib import Path
from typing import Optional

app = typer.Typer(help="Fetch transcripts from Fathom call recordings.")

SKILL_DIR = Path(__file__).parent.parent.parent

# Profile resolver
sys.path.insert(0, str(SKILL_DIR.parent / ".profiles"))
_profile_name: Optional[str] = None


@app.callback()
def main(profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile name")):
    global _profile_name
    _profile_name = profile


@app.command("transcript")
def transcript(
    source: str = typer.Argument(..., help="Fathom URL or recording ID"),
    output: Optional[str] = typer.Option(None, "--output", help="Output file path"),
    config: Optional[str] = typer.Option(None, "--config", help="Config file path"),
):
    """Fetch and display transcript for a Fathom recording."""
    from fathom_skill.transcript import load_config, fetch_transcript

    cfg = load_config(config)

    try:
        formatted, file_path = fetch_transcript(source, cfg)
    except ValueError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    typer.echo(formatted)

    if output:
        Path(output).write_text(formatted)
        typer.echo(f"\nSaved: {output}", err=True)
    elif file_path:
        typer.echo(f"\nTEMP_FILE:{file_path}", err=True)


if __name__ == "__main__":
    app()
