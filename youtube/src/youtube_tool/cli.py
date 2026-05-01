"""YouTube Tool CLI."""

import json
import typer
from typing import Optional
from pathlib import Path

app = typer.Typer(help="YouTube tool: download, transcript, search, upload.")

TOOL_DIR = Path(__file__).parent.parent.parent
DEFAULT_OUTPUT = TOOL_DIR / "output"


@app.command("download")
def download_cmd(
    url: str = typer.Argument(..., help="YouTube video URL"),
    audio_only: bool = typer.Option(False, "--audio-only", "-a", help="Extract audio only (mp3)"),
    output: Path = typer.Option(DEFAULT_OUTPUT, "--output", "-o", help="Output directory"),
    filename: Optional[str] = typer.Option(None, "--name", "-n", help="Output filename (without extension)"),
):
    """Download a YouTube video or extract its audio."""
    from youtube_tool.download import download

    typer.echo(f"Downloading {'audio' if audio_only else 'video'} from {url}...")
    result = download(url, audio_only=audio_only, output_dir=output, filename=filename)
    typer.echo(f"Title: {result['title']}")
    typer.echo(f"Saved: {result['path']}")
    typer.echo(json.dumps(result, indent=2))


@app.command("transcript")
def transcript_cmd(
    url: str = typer.Argument(..., help="YouTube video URL"),
    lang: str = typer.Option("fr", "--lang", "-l", help="Preferred language (fr, en, ...)"),
    timestamps: bool = typer.Option(False, "--timestamps", "-t", help="Include timestamps"),
    save: bool = typer.Option(False, "--save", "-s", help="Save to output/ as .txt"),
):
    """Get the transcript of a YouTube video."""
    from youtube_tool.transcript import get_transcript

    typer.echo(f"Fetching transcript for {url} (lang: {lang})...")
    result = get_transcript(url, lang=lang)

    if timestamps:
        for seg in result["segments"]:
            m, s = divmod(int(seg["start"]), 60)
            typer.echo(f"[{m:02d}:{s:02d}] {seg['text']}")
    else:
        typer.echo(result["text"])

    if save:
        DEFAULT_OUTPUT.mkdir(parents=True, exist_ok=True)
        out_path = DEFAULT_OUTPUT / f"transcript-{result['video_id']}.txt"
        out_path.write_text(result["text"], encoding="utf-8")
        typer.echo(f"\nSaved: {out_path}")

    typer.echo(f"\nSource: {result['source']} | Lang: {result['lang']} | Segments: {len(result['segments'])}")


@app.command("search")
def search_cmd(
    query: str = typer.Argument(..., help="Search query"),
    max_results: int = typer.Option(10, "--max", "-m", help="Max results (1-50)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
):
    """Search YouTube videos."""
    from youtube_tool.search import search, format_results

    typer.echo(f"Searching: {query}...")
    results = search(query, max_results=max_results)

    if json_output:
        typer.echo(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        typer.echo(format_results(results))

    typer.echo(f"Found {len(results)} results.")


@app.command("upload")
def upload_cmd(
    file: Path = typer.Argument(..., help="Video file path"),
    title: str = typer.Option(..., "--title", "-t", help="Video title"),
    description: str = typer.Option("", "--description", "-d", help="Video description"),
    tags: Optional[str] = typer.Option(None, "--tags", help="Comma-separated tags"),
    category: str = typer.Option("22", "--category", "-c", help="YouTube category ID (22=People & Blogs)"),
    privacy: str = typer.Option("private", "--privacy", "-p", help="Privacy: private, unlisted, public"),
    thumbnail: Optional[Path] = typer.Option(None, "--thumbnail", help="Thumbnail image path"),
    publish_at: Optional[str] = typer.Option(None, "--publish-at", help="Schedule publish time (ISO 8601 UTC, e.g. 2026-04-18T16:00:00Z). Forces privacy=private until then, then becomes public."),
):
    """Upload a video to YouTube (requires OAuth2 auth)."""
    from youtube_tool.upload import upload_video

    if not file.exists():
        typer.echo(f"Error: file not found: {file}", err=True)
        raise typer.Exit(1)

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    thumb = str(thumbnail) if thumbnail and thumbnail.exists() else None

    typer.echo(f"Uploading: {file.name}")
    typer.echo(f"Title: {title} | Privacy: {privacy}")

    result = upload_video(
        file_path=str(file),
        title=title,
        description=description,
        tags=tag_list,
        category=category,
        privacy=privacy,
        thumbnail_path=thumb,
        publish_at=publish_at,
    )

    typer.echo(f"Uploaded: {result['url']}")
    typer.echo(json.dumps(result, indent=2))


@app.command("thumbnail")
def thumbnail_cmd(
    video_id: str = typer.Argument(..., help="YouTube video ID"),
    image: Path = typer.Argument(..., help="Thumbnail image path"),
):
    """Set a custom thumbnail on an existing video (requires OAuth2 auth)."""
    from youtube_tool.upload import set_thumbnail

    if not image.exists():
        typer.echo(f"Error: image not found: {image}", err=True)
        raise typer.Exit(1)

    typer.echo(f"Setting thumbnail for {video_id}...")
    result = set_thumbnail(video_id, str(image))
    typer.echo("Thumbnail set.")
    typer.echo(json.dumps(result, indent=2))


@app.command("get-info")
def get_info_cmd(
    video_id: str = typer.Argument(..., help="YouTube video ID"),
):
    """Get a video's current metadata (title, description, tags)."""
    from youtube_tool.upload import get_video_details

    typer.echo(f"Fetching info for {video_id}...")
    result = get_video_details(video_id)
    typer.echo(json.dumps(result, indent=2, ensure_ascii=False))


@app.command("update")
def update_cmd(
    video_id: str = typer.Argument(..., help="YouTube video ID"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="New title"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="New description"),
    tags: Optional[str] = typer.Option(None, "--tags", help="Comma-separated tags"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="YouTube category ID"),
):
    """Update an existing video's metadata (requires OAuth2 auth)."""
    from youtube_tool.upload import update_video

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None

    typer.echo(f"Updating video {video_id}...")
    result = update_video(
        video_id=video_id,
        title=title,
        description=description,
        tags=tag_list,
        category=category,
    )
    typer.echo(f"Updated: {result['url']}")
    typer.echo(json.dumps(result, indent=2, ensure_ascii=False))


@app.command("auth")
def auth_cmd():
    """Authenticate with Google (opens browser for OAuth2 consent)."""
    from youtube_tool.auth import get_credentials, TOKEN_FILE

    typer.echo("Authenticating with Google YouTube API...")
    creds = get_credentials()
    if creds and creds.valid:
        typer.echo(f"Authenticated. Token saved: {TOKEN_FILE}")
    else:
        typer.echo("Authentication failed.", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
