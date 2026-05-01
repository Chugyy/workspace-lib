---
name: tools-divers
description: Generic reusable utilities for audio/video transcription. Use when the user wants to transcribe an audio or video file, a direct URL, or a YouTube URL. Supports local files (mp3, mp4, ogg, wav, m4a, webm, flac) and remote URLs via yt-dlp.
---

# Tools Divers

Utilitaires génériques réutilisables par tous les skills et agents.

## Utilitaires disponibles

### `utils/transcribe.py` — Transcription audio/vidéo

Transcrit n'importe quel fichier audio/vidéo ou URL via l'API OpenAI.

**Entrée acceptée :**
- Fichier local : `mp3, mp4, ogg, wav, m4a, webm, flac, mpeg, mpga`
- URL directe (fichier audio/vidéo)
- URL YouTube ou autre plateforme (via yt-dlp)

**Pipeline automatique :**
1. Téléchargement si URL → `downloads/`
2. Conversion vers `mp3` si format non supporté (via ffmpeg)
3. Chunking si taille > 24 MB (tranches de 10 min)
4. Transcription via OpenAI (modèle paramétrable)
5. Réconciliation des timestamps entre chunks

**Usage CLI :**
```bash
# Fichier local
python utils/transcribe.py audio.ogg

# URL directe
python utils/transcribe.py https://example.com/audio.mp3

# URL YouTube
python utils/transcribe.py https://youtube.com/watch?v=xxx

# Options
python utils/transcribe.py audio.ogg --model whisper-1 --language fr --format markdown
python utils/transcribe.py audio.ogg --output result.md
```

**Usage import (depuis un autre script) :**
```python
from utils.transcribe import Transcriber
import asyncio

transcriber = Transcriber(config)
result = await transcriber.transcribe("audio.ogg")
print(result.text)
print(result.markdown)
```

**Formats de sortie :**
- `text` — texte brut
- `markdown` — texte formaté avec métadonnées
- `srt` — sous-titres SRT avec timestamps
- `vtt` — sous-titres WebVTT
- `json` — JSON complet avec segments et timestamps

## Setup

```bash
./setup.sh
source .venv/bin/activate
```

Requiert `ffmpeg` installé sur le système.

## Configuration

`assets/config.json` :
```json
{
  "openai": {
    "api_key": "...",
    "default_model": "gpt-4o-mini-transcribe",
    "default_language": "fr"
  },
  "transcription": {
    "chunk_duration_minutes": 10,
    "max_file_size_mb": 24,
    "downloads_dir": "downloads"
  }
}
```

## Modèles disponibles

| Modèle | Prix/min | Notes |
|--------|----------|-------|
| `gpt-4o-mini-transcribe` | $0.003 | Défaut — bon rapport qualité/prix |
| `gpt-4o-transcribe` | $0.006 | Meilleure précision |
| `whisper-1` | $0.006 | Modèle legacy, supporte SRT/VTT |

## Commande /cleanup

La commande `/cleanup` permet de gérer les fichiers téléchargés dans `downloads/`.
