# mp4-transcriber — CLI tool

CLI local pour soumettre des fichiers vidéo ou audio au service de transcription/derush tournant sur le VPS (port 8765).

**Formats supportés :**
- Vidéo : `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`
- Audio : `.mp3`, `.wav`, `.m4a`, `.aac`, `.ogg`, `.flac`, `.opus`

## Setup

```bash
cd /data/workspace/lib/mp4-transcriber
./setup.sh
```

## Commandes

```bash
# Transcrire un fichier vidéo
mp4-transcriber run video.mp4

# Transcrire un fichier audio
mp4-transcriber run podcast.mp3
mp4-transcriber run enregistrement.m4a
mp4-transcriber run interview.wav

# Depuis une URL directe (personal cloud public ou presigned)
mp4-transcriber run https://personal-cloud-api.multimodal-house.fr/public/mon-service/video.mp4

# Depuis personal cloud privé (avec auth)
mp4-transcriber run https://personal-cloud-api.multimodal-house.fr/v1/objects/audio.mp3 \
  --auth "Bearer sk_live_..."

# Derush seulement (vidéo uniquement)
mp4-transcriber run video.mp4 --actions derush

# Transcription + Derush
mp4-transcriber run video.mp4 --actions transcribe,derush

# Sortie brute (pour agents : texte uniquement sur stdout)
mp4-transcriber run audio.mp3 --quiet

# Soumettre sans attendre (retourne l'ID du job)
mp4-transcriber run video.mp4 --no-wait

# Consulter un job existant
mp4-transcriber status 42
mp4-transcriber result 42 --quiet   # texte brut

# Lister les jobs
mp4-transcriber list

# Télécharger le fichier derushed
mp4-transcriber download 42 output.mp4

# Attendre un job soumis précédemment
mp4-transcriber wait 42
```

## Env vars

| Variable | Défaut | Description |
|----------|--------|-------------|
| `MP4_TRANSCRIBER_URL` | `http://localhost:8765` | URL du service |
| `MP4_TRANSCRIBER_AUTHORIZATION` | _(vide)_ | Header auth pour téléchargements personal cloud |

## Utilisation par un agent

```python
import subprocess

# Transcrire un fichier vidéo
result = subprocess.run(
    ["mp4-transcriber", "run", "/path/to/video.mp4", "--quiet"],
    capture_output=True, text=True, check=True
)
transcription = result.stdout.strip()

# Transcrire un fichier audio
result = subprocess.run(
    ["mp4-transcriber", "run", "/path/to/podcast.mp3", "--quiet"],
    capture_output=True, text=True, check=True
)
transcription = result.stdout.strip()

# Depuis personal cloud
result = subprocess.run(
    ["mp4-transcriber", "run",
     "https://personal-cloud-api.multimodal-house.fr/v1/objects/audio/interview.m4a",
     "--auth", "Bearer sk_live_...",
     "--quiet"],
    capture_output=True, text=True, check=True
)
```

## Service

Le service tourne sur `http://localhost:8765` (PM2 : `mp4-transcriber`).
- Modèle Whisper : `base` (configurable via `WHISPER_MODEL`)
- Storage : `/data/mp4-transcriber/data/`
- ffmpeg statique : `/data/mp4-transcriber/bin/`
