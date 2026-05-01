#!/usr/bin/env python3
"""
mp4-transcriber CLI — soumet des fichiers vidéo/audio au service de transcription local.

Usage:
    mp4-transcriber run video.mp4                        # upload + attends + retourne la transcription
    mp4-transcriber run audio.mp3                        # fonctionne aussi avec les fichiers audio
    mp4-transcriber run https://cloud.fr/video.mp4       # via URL directe
    mp4-transcriber run video.mp4 --actions derush       # derush uniquement
    mp4-transcriber run video.mp4 --actions transcribe,derush  # les deux
    mp4-transcriber status 42                            # état d'un job
    mp4-transcriber result 42                            # texte de transcription du job
    mp4-transcriber list                                 # liste des jobs récents
    mp4-transcriber download 42 output.mp4               # télécharger le résultat derushed

Formats supportés:
    Vidéo : .mp4, .mov, .avi, .mkv, .webm
    Audio : .mp3, .wav, .m4a, .aac, .ogg, .flac, .opus

Env vars:
    MP4_TRANSCRIBER_URL            URL du service (défaut: http://localhost:8765)
    MP4_TRANSCRIBER_AUTHORIZATION  Header Authorization pour personal-cloud (ex: Bearer sk_live_...)
"""

import os
import sys
import time
from pathlib import Path

import httpx
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="mp4-transcriber",
    help="CLI pour le service de transcription/derush vidéo et audio local.",
    no_args_is_help=True,
)
console = Console()

BASE_URL = os.environ.get("MP4_TRANSCRIBER_URL", "http://localhost:8765").rstrip("/")
DEFAULT_AUTH = os.environ.get("MP4_TRANSCRIBER_AUTHORIZATION", "")
POLL_INTERVAL = 3  # secondes entre chaque poll
TERMINAL_STATUSES = {"completed", "error"}

# MIME types par extension
MIME_TYPES: dict[str, str] = {
    # Vidéo
    ".mp4":  "video/mp4",
    ".mov":  "video/quicktime",
    ".avi":  "video/x-msvideo",
    ".mkv":  "video/x-matroska",
    ".webm": "video/webm",
    # Audio
    ".mp3":  "audio/mpeg",
    ".wav":  "audio/wav",
    ".m4a":  "audio/mp4",
    ".aac":  "audio/aac",
    ".ogg":  "audio/ogg",
    ".flac": "audio/flac",
    ".opus": "audio/opus",
}


def _client() -> httpx.Client:
    return httpx.Client(base_url=BASE_URL, timeout=60)


def _poll_until_done(jid: int, quiet: bool = False) -> dict:
    """Poll le job jusqu'à completion. Retourne le job final."""
    with _client() as c:
        while True:
            r = c.get(f"/api/jobs/{jid}")
            r.raise_for_status()
            job = r.json()
            status = job.get("status", "")
            if not quiet:
                console.print(f"  [dim]#{jid} {status}[/dim]", end="\r")
            if status in TERMINAL_STATUSES:
                if not quiet:
                    console.print()
                return job
            time.sleep(POLL_INTERVAL)


# ─── Commands ──────────────────────────────────────────────────────────────────

@app.command()
def run(
    source: str = typer.Argument(..., help="Fichier vidéo/audio local (.mp4, .mp3, .wav, .m4a, .aac, .ogg, .flac, .opus, .mov, .avi, .mkv, .webm) OU URL directe"),
    actions: str = typer.Option("transcribe", help="Actions: transcribe | derush | transcribe,derush"),
    authorization: str = typer.Option(None, "--auth", help="Authorization header (ex: Bearer sk_live_...). Défaut: $MP4_TRANSCRIBER_AUTHORIZATION"),
    noise_threshold: float = typer.Option(-30.0, help="Seuil silence en dB (derush seulement)"),
    min_duration: float = typer.Option(0.5, help="Durée min silence en secondes (derush seulement)"),
    padding: float = typer.Option(0.2, help="Padding autour des segments (derush seulement)"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Sortie minimale (transcription uniquement)"),
    wait: bool = typer.Option(True, help="Attendre la fin du job (défaut: True)"),
):
    """Soumettre un fichier vidéo ou audio (local ou URL) et attendre le résultat."""
    auth = authorization or DEFAULT_AUTH

    is_url = source.startswith(("http://", "https://"))

    with _client() as c:
        if is_url:
            data = {
                "url": source,
                "actions": actions,
                "noise_threshold": str(noise_threshold),
                "min_duration": str(min_duration),
                "padding": str(padding),
            }
            if auth:
                data["authorization"] = auth
            if not quiet:
                console.print(f"[bold]Soumission URL[/bold] {source[:80]}...")
            r = c.post("/api/jobs-url", data=data)
        else:
            filepath = Path(source)
            if not filepath.exists():
                console.print(f"[red]Fichier introuvable: {source}[/red]")
                raise typer.Exit(1)
            ext = filepath.suffix.lower()
            mime_type = MIME_TYPES.get(ext)
            if mime_type is None:
                console.print(f"[yellow]Extension '{ext}' non reconnue, envoi en application/octet-stream[/yellow]")
                mime_type = "application/octet-stream"
            if not quiet:
                size_mb = filepath.stat().st_size / 1024 / 1024
                console.print(f"[bold]Upload[/bold] {filepath.name} ({size_mb:.1f} MB)...")
            with open(filepath, "rb") as f:
                r = c.post(
                    "/api/jobs",
                    data={
                        "actions": actions,
                        "noise_threshold": str(noise_threshold),
                        "min_duration": str(min_duration),
                        "padding": str(padding),
                    },
                    files={"file": (filepath.name, f, mime_type)},
                    timeout=300,
                )

        r.raise_for_status()
        jid = r.json()["id"]
        if not quiet:
            console.print(f"[green]Job #{jid} créé[/green] — actions: {actions}")

    if not wait:
        print(jid)
        return

    job = _poll_until_done(jid, quiet=quiet)

    if job["status"] == "error":
        console.print(f"[red]Erreur:[/red] {job.get('error_message', 'inconnue')}")
        raise typer.Exit(1)

    # Output
    if "transcribe" in actions and job.get("t_full_text"):
        if quiet:
            print(job["t_full_text"])
        else:
            console.print(f"\n[bold cyan]Transcription[/bold cyan] ({job.get('t_language', '?')}, {job.get('t_duration', 0):.0f}s, {job.get('t_processing_time_s', 0):.1f}s de traitement)")
            console.print(job["t_full_text"])

    if "derush" in actions and job.get("d_status") == "completed":
        if not quiet:
            console.print(f"\n[bold cyan]Derush[/bold cyan] {job.get('d_duration_before', 0):.0f}s → {job.get('d_duration_after', 0):.0f}s (-{job.get('d_reduction_pct', 0):.1f}%)")
            console.print(f"  Télécharger: mp4-transcriber download {jid} output.mp4")


@app.command()
def status(
    jid: int = typer.Argument(..., help="ID du job"),
):
    """Afficher l'état d'un job."""
    with _client() as c:
        r = c.get(f"/api/jobs/{jid}")
        if r.status_code == 404:
            console.print(f"[red]Job #{jid} introuvable[/red]")
            raise typer.Exit(1)
        r.raise_for_status()
        job = r.json()

    console.print(f"[bold]Job #{jid}[/bold] — {job['filename']}")
    console.print(f"  Status   : {job['status']}")
    console.print(f"  Actions  : {job['actions']}")
    if job.get("error_message"):
        console.print(f"  [red]Erreur   : {job['error_message']}[/red]")
    if job.get("t_status") == "completed":
        console.print(f"  Transcript: {job.get('t_language', '?')} — {job.get('t_duration', 0):.0f}s")
    if job.get("d_status") == "completed":
        console.print(f"  Derush   : -{job.get('d_reduction_pct', 0):.1f}% ({job.get('d_duration_before', 0):.0f}s → {job.get('d_duration_after', 0):.0f}s)")


@app.command()
def result(
    jid: int = typer.Argument(..., help="ID du job"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Texte brut uniquement"),
):
    """Récupérer la transcription d'un job terminé."""
    with _client() as c:
        r = c.get(f"/api/jobs/{jid}")
        if r.status_code == 404:
            console.print(f"[red]Job #{jid} introuvable[/red]")
            raise typer.Exit(1)
        r.raise_for_status()
        job = r.json()

    if job["status"] != "completed":
        console.print(f"[yellow]Job #{jid} pas encore terminé (status: {job['status']})[/yellow]")
        raise typer.Exit(1)

    text = job.get("t_full_text", "")
    if not text:
        console.print(f"[yellow]Pas de transcription pour le job #{jid}[/yellow]")
        raise typer.Exit(1)

    if quiet:
        print(text)
    else:
        console.print(f"[bold cyan]Job #{jid}[/bold cyan] — {job['filename']}")
        console.print(text)


@app.command(name="list")
def list_jobs(
    limit: int = typer.Option(20, help="Nombre de jobs à afficher"),
    action: str = typer.Option(None, "--action", help="Filtrer par action (transcribe|derush)"),
    search: str = typer.Option(None, "--search", help="Recherche dans les noms / transcriptions"),
):
    """Lister les jobs récents."""
    params = {"limit": limit}
    if action:
        params["filter"] = action
    if search:
        params["search"] = search

    with _client() as c:
        r = c.get("/api/jobs", params=params)
        r.raise_for_status()
        data = r.json()

    items = data["items"]
    total = data["total"]

    if not items:
        console.print("[dim]Aucun job.[/dim]")
        return

    table = Table(title=f"Jobs ({len(items)}/{total})")
    table.add_column("ID", style="bold")
    table.add_column("Fichier")
    table.add_column("Actions")
    table.add_column("Status")
    table.add_column("Durée")
    table.add_column("Créé")

    for j in items:
        dur = f"{j.get('t_duration', 0):.0f}s" if j.get("t_duration") else "—"
        created = (j.get("created_at") or "")[:16].replace("T", " ")
        table.add_row(
            str(j["id"]),
            j["filename"][:40],
            j["actions"],
            j["status"],
            dur,
            created,
        )

    console.print(table)


@app.command()
def download(
    jid: int = typer.Argument(..., help="ID du job"),
    output: str = typer.Argument(..., help="Fichier de sortie (.mp4)"),
):
    """Télécharger le fichier derushed d'un job terminé."""
    with _client() as c:
        r = c.get(f"/api/jobs/{jid}/download", follow_redirects=True)
        if r.status_code == 404:
            console.print(f"[red]Fichier introuvable pour le job #{jid} (job non terminé ou pas de derush)[/red]")
            raise typer.Exit(1)
        r.raise_for_status()
        Path(output).write_bytes(r.content)

    size_mb = Path(output).stat().st_size / 1024 / 1024
    console.print(f"[green]✓[/green] Sauvegardé: {output} ({size_mb:.1f} MB)")


@app.command()
def wait(
    jid: int = typer.Argument(..., help="ID du job"),
    quiet: bool = typer.Option(False, "--quiet", "-q"),
):
    """Attendre la fin d'un job existant."""
    job = _poll_until_done(jid, quiet=quiet)
    if job["status"] == "error":
        console.print(f"[red]Erreur:[/red] {job.get('error_message', 'inconnue')}")
        raise typer.Exit(1)
    if not quiet:
        console.print(f"[green]✓ Job #{jid} terminé[/green]")
    else:
        print(job["status"])


if __name__ == "__main__":
    app()
