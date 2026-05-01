"""
Transcription Audio/Vidéo — Utilitaire OpenAI Whisper

Transcrit n'importe quel fichier audio/vidéo ou URL.

Features:
- Téléchargement auto depuis URL (direct ou YouTube via yt-dlp)
- Conversion de format via ffmpeg si nécessaire
- Chunking automatique si fichier > 24 MB (tranches de 10 min)
- Reconciliation des timestamps entre chunks
- Formats de sortie : text, markdown, json, srt, vtt

Usage CLI:
    python utils/transcribe.py audio.ogg
    python utils/transcribe.py https://youtube.com/watch?v=xxx
    python utils/transcribe.py audio.ogg --format markdown --output result.md
    python utils/transcribe.py cleanup --older-than 7

Usage import:
    from utils.transcribe import Transcriber
    transcriber = Transcriber(config)
    result = await transcriber.transcribe("audio.ogg")
"""

import asyncio
import json
import sys
import os
import shutil
import argparse
import hashlib
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

# ============================================================================
# CONSTANTS
# ============================================================================

SKILL_DIR = Path(__file__).parent.parent
DOWNLOADS_DIR = SKILL_DIR / "downloads"

# Formats acceptés nativement par l'API OpenAI Whisper
OPENAI_SUPPORTED_FORMATS = {".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm", ".ogg", ".flac"}

# Taille max par upload (en bytes) — on garde 1 MB de marge
MAX_UPLOAD_BYTES = 24 * 1024 * 1024  # 24 MB

# Durée max d'un chunk en secondes (10 minutes)
DEFAULT_CHUNK_DURATION_SEC = 10 * 60


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class TranscriptionSegment:
    start: float   # secondes depuis le début du fichier original
    end: float
    text: str


@dataclass
class TranscriptionResult:
    text: str                              # Transcription complète
    segments: List[TranscriptionSegment]   # Segments avec timestamps
    language: str
    duration: float                        # Durée totale en secondes
    source_file: str                       # Fichier source original
    model: str
    chunks_count: int                      # Nombre de chunks utilisés

    @property
    def markdown(self) -> str:
        """Rendu Markdown avec métadonnées."""
        duration_str = _format_duration(self.duration)
        lines = [
            f"# Transcription",
            f"",
            f"**Source** : {Path(self.source_file).name}  ",
            f"**Durée** : {duration_str}  ",
            f"**Langue** : {self.language}  ",
            f"**Modèle** : {self.model}  ",
            f"**Date** : {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"",
            f"---",
            f"",
            self.text,
        ]
        return "\n".join(lines)

    @property
    def srt(self) -> str:
        """Format SRT pour sous-titres."""
        lines = []
        for i, seg in enumerate(self.segments, 1):
            start = _seconds_to_srt_time(seg.start)
            end = _seconds_to_srt_time(seg.end)
            lines.append(f"{i}\n{start} --> {end}\n{seg.text.strip()}\n")
        return "\n".join(lines)

    @property
    def vtt(self) -> str:
        """Format WebVTT pour sous-titres."""
        lines = ["WEBVTT", ""]
        for seg in self.segments:
            start = _seconds_to_vtt_time(seg.start)
            end = _seconds_to_vtt_time(seg.end)
            lines.append(f"{start} --> {end}\n{seg.text.strip()}\n")
        return "\n".join(lines)

    def to_json(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "language": self.language,
            "duration": self.duration,
            "source_file": self.source_file,
            "model": self.model,
            "chunks_count": self.chunks_count,
            "segments": [
                {"start": s.start, "end": s.end, "text": s.text}
                for s in self.segments
            ],
        }


# ============================================================================
# TRANSCRIBER
# ============================================================================

class Transcriber:
    """
    Transcrit audio/vidéo via l'API OpenAI.

    Args:
        config: Dict avec openai.api_key, openai.default_model, etc.
        downloads_dir: Répertoire pour stocker les fichiers téléchargés
    """

    def __init__(self, config: Dict[str, Any], downloads_dir: Optional[Path] = None):
        self.config = config
        self.api_key = config["openai"]["api_key"]
        self.default_model = config["openai"].get("default_model", "gpt-4o-mini-transcribe")
        self.default_language = config["openai"].get("default_language", "fr")
        self.max_size = int(config.get("transcription", {}).get("max_file_size_mb", 24)) * 1024 * 1024
        self.chunk_duration = int(config.get("transcription", {}).get("chunk_duration_minutes", 10)) * 60
        self.downloads_dir = downloads_dir or DOWNLOADS_DIR
        self.downloads_dir.mkdir(parents=True, exist_ok=True)

    async def transcribe(
        self,
        source: str,
        model: Optional[str] = None,
        language: Optional[str] = None,
        output_format: str = "text",
        output_path: Optional[str] = None,
        keep_download: bool = True,
    ) -> TranscriptionResult:
        """
        Transcrit un fichier audio/vidéo ou une URL.

        Args:
            source: Chemin local ou URL (directe ou YouTube)
            model: Modèle OpenAI (défaut: config default_model)
            language: Code langue ISO 639-1 (ex: "fr", "en")
            output_format: "text", "markdown", "json", "srt", "vtt"
            output_path: Si fourni, sauvegarde le résultat
            keep_download: Garder les fichiers téléchargés dans downloads/

        Returns:
            TranscriptionResult
        """
        model = model or self.default_model
        language = language or self.default_language

        # Étape 1 : Résoudre la source → fichier local
        local_path, downloaded = await self._resolve_source(source, keep_download)

        try:
            # Étape 2 : Convertir si format non supporté
            workfile, converted = self._ensure_supported_format(local_path)

            try:
                # Étape 3 : Chunker si trop gros
                chunks = self._split_if_needed(workfile)

                # Étape 4 : Transcrire chunk par chunk
                result = await self._transcribe_chunks(
                    chunks=chunks,
                    source_file=str(local_path),
                    model=model,
                    language=language,
                )

                # Étape 5 : Sauvegarder si output_path demandé
                if output_path:
                    self._save_output(result, output_format, output_path)
                    print(f"Saved: {output_path}")

                return result

            finally:
                # Cleanup fichiers temporaires de chunks (pas le workfile)
                for chunk in chunks:
                    if chunk != workfile and chunk.exists():
                        chunk.unlink()

                # Cleanup fichier converti
                if converted and workfile.exists():
                    workfile.unlink()

        finally:
            # Si pas keep_download, supprimer le fichier téléchargé
            if downloaded and not keep_download and local_path.exists():
                local_path.unlink()

    # -----------------------------------------------------------------------
    # Source resolution
    # -----------------------------------------------------------------------

    async def _resolve_source(self, source: str, keep: bool) -> tuple:
        """
        Retourne (local_path, was_downloaded).
        Télécharge si URL, sinon vérifie que le fichier existe.
        """
        source = source.strip()

        # Fichier local
        if not source.startswith(("http://", "https://", "ftp://")):
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {source}")
            return path, False

        # URL → téléchargement
        print(f"Downloading: {source}")
        local_path = await self._download_url(source)
        print(f"Downloaded: {local_path.name} ({local_path.stat().st_size // 1024} KB)")
        return local_path, True

    async def _download_url(self, url: str) -> Path:
        """
        Télécharge une URL dans downloads/.
        Utilise yt-dlp pour YouTube/plateformes, httpx pour fichiers directs.
        """
        # Générer un nom de fichier basé sur le hash de l'URL
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Détecter si c'est une URL YouTube/plateforme connue
        is_platform_url = any(domain in url for domain in [
            "youtube.com", "youtu.be", "vimeo.com", "dailymotion.com",
            "twitch.tv", "soundcloud.com", "twitter.com", "instagram.com",
            "facebook.com", "tiktok.com",
        ])

        if is_platform_url:
            return await self._download_with_ytdlp(url, url_hash, timestamp)
        else:
            return await self._download_direct(url, url_hash, timestamp)

    async def _download_with_ytdlp(self, url: str, url_hash: str, timestamp: str) -> Path:
        """Télécharge via yt-dlp (YouTube et autres plateformes)."""
        output_template = str(self.downloads_dir / f"{timestamp}_{url_hash}.%(ext)s")

        cmd = [
            "yt-dlp",
            "--extract-audio",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            "--output", output_template,
            "--no-playlist",
            "--quiet",
            url,
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"yt-dlp failed: {stderr.decode()}")

        # Trouver le fichier créé
        matches = list(self.downloads_dir.glob(f"{timestamp}_{url_hash}.*"))
        if not matches:
            raise RuntimeError(f"yt-dlp: output file not found")
        return matches[0]

    async def _download_direct(self, url: str, url_hash: str, timestamp: str) -> Path:
        """Télécharge un fichier direct via httpx."""
        try:
            import httpx
        except ImportError:
            raise ImportError("httpx required: pip install httpx")

        # Deviner l'extension depuis l'URL
        url_path = url.split("?")[0]
        ext = Path(url_path).suffix or ".bin"
        dest = self.downloads_dir / f"{timestamp}_{url_hash}{ext}"

        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                with open(dest, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=65536):
                        f.write(chunk)

        # Sauvegarder métadonnées
        meta = {
            "url": url,
            "downloaded_at": datetime.now().isoformat(),
            "filename": dest.name,
            "size_bytes": dest.stat().st_size,
        }
        dest.with_suffix(".json").write_text(json.dumps(meta, indent=2))

        return dest

    # -----------------------------------------------------------------------
    # Format conversion
    # -----------------------------------------------------------------------

    def _ensure_supported_format(self, path: Path) -> tuple:
        """
        Convertit en mp3 si le format n'est pas supporté par l'API.
        Retourne (workfile, was_converted).
        """
        if path.suffix.lower() in OPENAI_SUPPORTED_FORMATS:
            return path, False

        print(f"Converting {path.suffix} → mp3...")
        mp3_path = path.with_suffix(".converted.mp3")
        _run_ffmpeg([
            "-i", str(path),
            "-vn",                  # Pas de vidéo
            "-acodec", "libmp3lame",
            "-q:a", "2",            # Qualité ~190 kbps
            "-y",
            str(mp3_path),
        ])
        return mp3_path, True

    # -----------------------------------------------------------------------
    # Chunking
    # -----------------------------------------------------------------------

    def _split_if_needed(self, path: Path) -> List[Path]:
        """
        Si le fichier dépasse MAX_UPLOAD_BYTES, le découpe en chunks.
        Retourne la liste des fichiers à transcrire (chunks ou [path] si pas besoin).
        """
        size = path.stat().st_size
        if size <= self.max_size:
            return [path]

        print(f"File is {size // (1024*1024)} MB > 24 MB, splitting into chunks...")
        return self._split_by_duration(path)

    def _split_by_duration(self, path: Path) -> List[Path]:
        """
        Découpe le fichier en tranches de chunk_duration secondes via ffmpeg.
        """
        # Obtenir la durée totale
        duration = _get_audio_duration(path)
        chunk_count = int(duration / self.chunk_duration) + 1
        print(f"Duration: {_format_duration(duration)}, creating {chunk_count} chunks of {self.chunk_duration//60} min")

        chunks = []
        for i in range(chunk_count):
            start = i * self.chunk_duration
            if start >= duration:
                break
            chunk_path = path.parent / f"{path.stem}_chunk{i:03d}{path.suffix}"
            _run_ffmpeg([
                "-i", str(path),
                "-ss", str(start),
                "-t", str(self.chunk_duration),
                "-acodec", "copy",
                "-y",
                str(chunk_path),
            ])
            if chunk_path.exists() and chunk_path.stat().st_size > 0:
                chunks.append(chunk_path)

        return chunks

    # -----------------------------------------------------------------------
    # API calls
    # -----------------------------------------------------------------------

    async def _transcribe_chunks(
        self,
        chunks: List[Path],
        source_file: str,
        model: str,
        language: str,
    ) -> TranscriptionResult:
        """
        Transcrit chaque chunk et assemble le résultat avec timestamps corrigés.
        """
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("openai package required: pip install openai")

        client = AsyncOpenAI(api_key=self.api_key)

        all_segments: List[TranscriptionSegment] = []
        all_text_parts: List[str] = []
        total_offset = 0.0
        chunk_count = len(chunks)

        for i, chunk_path in enumerate(chunks):
            if chunk_count > 1:
                print(f"Transcribing chunk {i+1}/{chunk_count}: {chunk_path.name}")

            # Contexte du chunk précédent pour améliorer la précision
            prompt = None
            if all_text_parts:
                # Passer les ~200 derniers caractères comme contexte
                prompt = "..." + " ".join(all_text_parts)[-200:]

            segments, text, chunk_duration = await self._call_api(
                client=client,
                audio_path=chunk_path,
                model=model,
                language=language,
                prompt=prompt,
            )

            # Corriger les timestamps avec l'offset du chunk
            for seg in segments:
                all_segments.append(TranscriptionSegment(
                    start=seg.start + total_offset,
                    end=seg.end + total_offset,
                    text=seg.text,
                ))

            all_text_parts.append(text)
            total_offset += chunk_duration

        full_text = " ".join(all_text_parts).strip()
        total_duration = total_offset

        return TranscriptionResult(
            text=full_text,
            segments=all_segments,
            language=language,
            duration=total_duration,
            source_file=source_file,
            model=model,
            chunks_count=chunk_count,
        )

    async def _call_api(
        self,
        client,
        audio_path: Path,
        model: str,
        language: str,
        prompt: Optional[str],
    ) -> tuple:
        """
        Appelle l'API OpenAI et retourne (segments, text, duration).
        """
        # whisper-1 supporte verbose_json avec segments
        # gpt-4o-*-transcribe supporte json ou text seulement
        use_verbose = model == "whisper-1"

        kwargs = {
            "model": model,
            "language": language,
            "response_format": "verbose_json" if use_verbose else "json",
        }
        if prompt:
            kwargs["prompt"] = prompt
        if use_verbose:
            kwargs["timestamp_granularities"] = ["segment"]

        with open(audio_path, "rb") as f:
            response = await client.audio.transcriptions.create(
                file=(audio_path.name, f),
                **kwargs,
            )

        # Extraire segments et durée
        if use_verbose and hasattr(response, "segments") and response.segments:
            segments = [
                TranscriptionSegment(
                    start=float(s.get("start", 0) if isinstance(s, dict) else s.start),
                    end=float(s.get("end", 0) if isinstance(s, dict) else s.end),
                    text=s.get("text", "") if isinstance(s, dict) else s.text,
                )
                for s in response.segments
            ]
            duration = float(getattr(response, "duration", 0) or 0)
            text = response.text
        else:
            # Pas de segments disponibles : on crée un segment unique
            text = response.text if hasattr(response, "text") else str(response)
            duration = _get_audio_duration(audio_path)
            segments = [TranscriptionSegment(start=0.0, end=duration, text=text)]

        return segments, text, duration

    # -----------------------------------------------------------------------
    # Output
    # -----------------------------------------------------------------------

    def _save_output(self, result: TranscriptionResult, fmt: str, path: str) -> None:
        """Sauvegarde le résultat dans le format demandé."""
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)

        if fmt == "text":
            output.write_text(result.text, encoding="utf-8")
        elif fmt == "markdown":
            output.write_text(result.markdown, encoding="utf-8")
        elif fmt == "srt":
            output.write_text(result.srt, encoding="utf-8")
        elif fmt == "vtt":
            output.write_text(result.vtt, encoding="utf-8")
        elif fmt == "json":
            output.write_text(json.dumps(result.to_json(), indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            output.write_text(result.text, encoding="utf-8")


# ============================================================================
# CLEANUP
# ============================================================================

def cleanup_downloads(
    downloads_dir: Path,
    older_than_days: Optional[int] = None,
    dry_run: bool = False,
    pattern: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Liste et/ou supprime les fichiers dans downloads/.

    Args:
        downloads_dir: Répertoire à nettoyer
        older_than_days: Supprimer uniquement les fichiers plus vieux que N jours
        dry_run: Si True, liste sans supprimer
        pattern: Glob pattern pour filtrer (ex: "*.ogg")

    Returns:
        Liste de dicts {name, size_kb, age_days, deleted}
    """
    if not downloads_dir.exists():
        return []

    now = datetime.now()
    cutoff = now - timedelta(days=older_than_days) if older_than_days else None
    glob = pattern or "*"

    files = sorted(
        [f for f in downloads_dir.glob(glob) if f.is_file()],
        key=lambda f: f.stat().st_mtime,
    )

    results = []
    for f in files:
        stat = f.stat()
        age_days = (now - datetime.fromtimestamp(stat.st_mtime)).days
        size_kb = stat.st_size // 1024

        should_delete = (cutoff is None) or (datetime.fromtimestamp(stat.st_mtime) < cutoff)
        deleted = False

        if should_delete and not dry_run:
            f.unlink()
            deleted = True

        results.append({
            "name": f.name,
            "size_kb": size_kb,
            "age_days": age_days,
            "path": str(f),
            "deleted": deleted,
        })

    return results


def get_downloads_stats(downloads_dir: Path) -> Dict[str, Any]:
    """Retourne les stats du dossier downloads/."""
    if not downloads_dir.exists():
        return {"exists": False, "files": 0, "total_size_mb": 0}

    files = [f for f in downloads_dir.iterdir() if f.is_file()]
    total_size = sum(f.stat().st_size for f in files)

    return {
        "exists": True,
        "path": str(downloads_dir),
        "files": len(files),
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "oldest": min((f.stat().st_mtime for f in files), default=None),
        "newest": max((f.stat().st_mtime for f in files), default=None),
    }


# ============================================================================
# HELPERS
# ============================================================================

def _run_ffmpeg(args: List[str]) -> None:
    """Execute une commande ffmpeg, lève RuntimeError en cas d'échec."""
    cmd = ["ffmpeg", "-loglevel", "error"] + args
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg error: {result.stderr.decode()}")


def _get_audio_duration(path: Path) -> float:
    """Retourne la durée d'un fichier audio en secondes via ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        return 0.0
    try:
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    except (KeyError, ValueError, json.JSONDecodeError):
        return 0.0


def _format_duration(seconds: float) -> str:
    """Convertit des secondes en format lisible H:MM:SS ou M:SS."""
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m}:{sec:02d}"


def _seconds_to_srt_time(seconds: float) -> str:
    """Convertit des secondes en format SRT : 00:01:23,456"""
    ms = int((seconds % 1) * 1000)
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


def _seconds_to_vtt_time(seconds: float) -> str:
    """Convertit des secondes en format VTT : 00:01:23.456"""
    return _seconds_to_srt_time(seconds).replace(",", ".")


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Charge la config depuis assets/config.json."""
    if config_path:
        path = Path(config_path)
    else:
        path = SKILL_DIR / "assets" / "config.json"
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}. Run setup.sh first.")
    with open(path) as f:
        return json.load(f)


# ============================================================================
# CLI
# ============================================================================

def _auto_output_path(source: str, output_format: str, downloads_dir: Path) -> Path:
    """
    Génère un nom de fichier de sortie automatique.
    Format : {downloads_dir}/{timestamp}_{source_basename}.txt
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Extraire le nom de base de la source (fichier ou URL)
    if source.startswith(("http://", "https://")):
        basename = source.rstrip("/").split("/")[-1].split("?")[0]
        basename = basename or "audio"
        # Retirer l'extension existante
        basename = Path(basename).stem
    else:
        basename = Path(source).stem

    # Nettoyer les caractères problématiques
    basename = "".join(c if c.isalnum() or c in "-_" else "_" for c in basename)[:50]
    ext = {"srt": ".srt", "vtt": ".vtt", "json": ".json", "markdown": ".md"}.get(output_format, ".txt")
    return downloads_dir / f"{ts}_{basename}{ext}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Transcription audio/vidéo via OpenAI Whisper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Transcrire un fichier local (sortie auto dans downloads/)
  python utils/transcribe.py audio.ogg

  # Depuis une URL directe
  python utils/transcribe.py https://example.com/audio.mp3

  # Depuis YouTube
  python utils/transcribe.py "https://youtube.com/watch?v=xxx"

  # Avec options
  python utils/transcribe.py audio.ogg --model whisper-1 --language en --format srt

  # Spécifier un fichier de sortie
  python utils/transcribe.py audio.ogg --output result.txt

  # Voir les stats downloads
  python utils/transcribe.py cleanup --list

  # Supprimer les fichiers > 7 jours
  python utils/transcribe.py cleanup --older-than 7

  # Supprimer tout
  python utils/transcribe.py cleanup --all
        """
    )

    # Détecter si le premier argument est "cleanup" → sous-commande
    # Sinon → mode transcription directe
    parser.add_argument("source", nargs="?", help="Fichier local ou URL à transcrire")
    parser.add_argument("--model", help="Modèle OpenAI (défaut: config)")
    parser.add_argument("--language", help="Code langue ISO 639-1 (défaut: fr)")
    parser.add_argument("--format", dest="output_format",
                        choices=["text", "markdown", "srt", "vtt", "json"],
                        default="text", help="Format de sortie (défaut: text → .txt)")
    parser.add_argument("--output", dest="output_path",
                        help="Fichier de sortie (défaut: auto dans downloads/)")
    parser.add_argument("--no-keep", action="store_true",
                        help="Ne pas garder les fichiers téléchargés")
    parser.add_argument("--config", help="Chemin vers config.json")

    # Sous-commande cleanup (détectée si source == "cleanup")
    parser.add_argument("--list", action="store_true", help="(cleanup) Lister les fichiers")
    parser.add_argument("--older-than", type=int, metavar="DAYS",
                        help="(cleanup) Supprimer les fichiers plus vieux que N jours")
    parser.add_argument("--all", action="store_true", dest="delete_all",
                        help="(cleanup) Supprimer tous les fichiers")
    parser.add_argument("--pattern", help="(cleanup) Glob pattern à filtrer")
    parser.add_argument("--dry-run", action="store_true",
                        help="(cleanup) Simuler sans supprimer")

    return parser


async def main_async(args: argparse.Namespace) -> int:
    config = load_config(getattr(args, "config", None))
    transcriber = Transcriber(config)

    # --- Mode cleanup : source == "cleanup" ou flags cleanup présents ---
    is_cleanup = (args.source == "cleanup") or args.list or args.delete_all or args.older_than
    if is_cleanup:
        stats = get_downloads_stats(transcriber.downloads_dir)
        if not stats["exists"] or stats["files"] == 0:
            print("downloads/ est vide.")
            return 0

        print(f"downloads/: {stats['files']} fichiers, {stats['total_size_mb']} MB\n")

        if args.list or (not args.delete_all and not args.older_than):
            files = cleanup_downloads(transcriber.downloads_dir, dry_run=True, pattern=args.pattern)
            for f in files:
                print(f"  {f['name']:<50} {f['size_kb']:>6} KB  {f['age_days']}j")
            return 0

        older_than = args.older_than if not args.delete_all else None
        files = cleanup_downloads(
            transcriber.downloads_dir,
            older_than_days=older_than,
            dry_run=args.dry_run,
            pattern=args.pattern,
        )
        deleted = [f for f in files if f["deleted"]]
        freed_kb = sum(f["size_kb"] for f in deleted)

        label = "[DRY RUN] Would delete" if args.dry_run else "Deleted"
        print(f"{label} {len(deleted)} files ({freed_kb} KB freed):")
        for f in deleted:
            print(f"  {f['name']}")
        return 0

    # --- Mode transcription ---
    source = args.source
    if not source:
        print("Usage: python utils/transcribe.py <fichier_ou_url>", file=sys.stderr)
        print("       python utils/transcribe.py cleanup --list", file=sys.stderr)
        return 1

    fmt = args.output_format or "text"

    # Générer un output_path automatique si non fourni
    output_path = args.output_path
    if not output_path:
        output_path = str(_auto_output_path(source, fmt, transcriber.downloads_dir))

    try:
        result = await transcriber.transcribe(
            source=source,
            model=args.model,
            language=args.language,
            output_format=fmt,
            output_path=output_path,
            keep_download=not args.no_keep,
        )
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        raise

    # Afficher aussi en console
    print(f"\n--- Transcription ({result.duration:.0f}s, {result.chunks_count} chunk(s)) ---")
    print(result.text)
    print(f"\nSaved: {output_path}")
    return 0


def main():
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()
