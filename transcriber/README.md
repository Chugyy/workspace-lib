# Transcriber

Transcrire des fichiers audio/video ou URLs via OpenAI Whisper.

## Setup

1. `cp .env.example .env`
2. Remplir la clé OpenAI
3. `./setup.sh`

Requiert `ffmpeg` installé sur le système (`sudo apt install ffmpeg`).

## Credentials

| Variable | Ou la trouver |
|----------|---------------|
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys |

La configuration est stockée dans `assets/config.json` (gitignored).

## Usage

```bash
cd ../../lib/transcriber && source .venv/bin/activate

# Fichier local
transcribe audio.ogg

# URL directe
transcribe https://example.com/audio.mp3

# URL YouTube
transcribe https://youtube.com/watch?v=xxx

# Options
transcribe audio.ogg --model whisper-1 --language fr --format markdown
transcribe audio.ogg --output result.md
```

## Pipeline automatique

1. Téléchargement si URL vers `downloads/`
2. Conversion vers mp3 si format non supporté (via ffmpeg)
3. Chunking si taille > 24 MB (tranches de 10 min)
4. Transcription via OpenAI (modèle paramétrable)
5. Réconciliation des timestamps entre chunks

## Modèles disponibles

| Modèle | Prix/min | Notes |
|--------|----------|-------|
| `gpt-4o-mini-transcribe` | $0.003 | Défaut — bon rapport qualité/prix |
| `gpt-4o-transcribe` | $0.006 | Meilleure précision |
| `whisper-1` | $0.006 | Modèle legacy, supporte SRT/VTT |

## Formats de sortie

`text`, `markdown`, `srt`, `vtt`, `json`

## Inputs / Outputs

- **downloads/** : fichiers téléchargés (contenu gitignored)
