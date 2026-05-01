#!/usr/bin/env python3
"""Transcribe CLI - Audio/Video transcription via OpenAI Whisper."""
import asyncio
import typer
from pathlib import Path
from typing import Optional
from enum import Enum

app = typer.Typer(help="Transcribe audio/video files or URLs via OpenAI Whisper.")

_profile_name: Optional[str] = None


@app.callback()
def main(profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile name")):
    global _profile_name
    _profile_name = profile


class OutputFormat(str, Enum):
    text = "text"
    markdown = "markdown"
    srt = "srt"
    vtt = "vtt"
    json = "json"


@app.command("run")
def run(
    source: str = typer.Argument(..., help="Local file path or URL (direct/YouTube)"),
    model: Optional[str] = typer.Option(None, "--model", help="OpenAI model (default from config)"),
    language: Optional[str] = typer.Option(None, "--language", help="ISO 639-1 code (default: fr)"),
    format: OutputFormat = typer.Option(OutputFormat.text, "--format", help="Output format"),
    output: Optional[str] = typer.Option(None, "--output", help="Output file path (auto if not set)"),
    no_keep: bool = typer.Option(False, "--no-keep", help="Don't keep downloaded files"),
    config: Optional[str] = typer.Option(None, "--config", help="Config file path"),
):
    """Transcribe an audio/video file or URL."""
    from transcribe_skill.core import Transcriber, load_config, _auto_output_path

    cfg = load_config(config, profile=_profile_name)
    transcriber = Transcriber(cfg)

    output_path = output
    if not output_path:
        output_path = str(_auto_output_path(source, format.value, transcriber.downloads_dir))

    async def _run():
        result = await transcriber.transcribe(
            source=source,
            model=model,
            language=language,
            output_format=format.value,
            output_path=output_path,
            keep_download=not no_keep,
        )
        typer.echo(f"\n--- Transcription ({result.duration:.0f}s, {result.chunks_count} chunk(s)) ---")
        typer.echo(result.text)
        typer.echo(f"\nSaved: {output_path}")

    try:
        asyncio.run(_run())
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except RuntimeError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command("cleanup")
def cleanup(
    list_only: bool = typer.Option(False, "--list", help="List files without deleting"),
    older_than: Optional[int] = typer.Option(None, "--older-than", metavar="DAYS", help="Delete files older than N days"),
    delete_all: bool = typer.Option(False, "--all", help="Delete all files"),
    pattern: Optional[str] = typer.Option(None, "--pattern", help="Glob pattern filter"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate without deleting"),
    config: Optional[str] = typer.Option(None, "--config", help="Config file path"),
):
    """Manage downloads/ directory."""
    from transcribe_skill.core import Transcriber, load_config, cleanup_downloads, get_downloads_stats

    cfg = load_config(config, profile=_profile_name)
    transcriber = Transcriber(cfg)
    downloads_dir = transcriber.downloads_dir

    stats = get_downloads_stats(downloads_dir)
    if not stats["exists"] or stats["files"] == 0:
        typer.echo("downloads/ is empty.")
        return

    typer.echo(f"downloads/: {stats['files']} files, {stats['total_size_mb']} MB\n")

    if list_only or (not delete_all and not older_than):
        files = cleanup_downloads(downloads_dir, dry_run=True, pattern=pattern)
        for f in files:
            typer.echo(f"  {f['name']:<50} {f['size_kb']:>6} KB  {f['age_days']}d")
        return

    older = older_than if not delete_all else None
    files = cleanup_downloads(downloads_dir, older_than_days=older, dry_run=dry_run, pattern=pattern)
    deleted = [f for f in files if f["deleted"]]
    freed_kb = sum(f["size_kb"] for f in deleted)
    label = "[DRY RUN] Would delete" if dry_run else "Deleted"
    typer.echo(f"{label} {len(deleted)} files ({freed_kb} KB freed):")
    for f in deleted:
        typer.echo(f"  {f['name']}")


if __name__ == "__main__":
    app()
