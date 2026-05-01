# mp4-transcriber

CLI pour soumettre des fichiers vidéo ou audio au service de transcription/derush local (port 8765).

Formats supportés — **Vidéo** : `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm` | **Audio** : `.mp3`, `.wav`, `.m4a`, `.aac`, `.ogg`, `.flac`, `.opus`

## Setup

1. `cp .env.example .env` (optionnel si les defaults conviennent)
2. `./setup.sh` (necessite que le service mp4-transcriber soit deploye sur le VPS)

## Credentials

| Variable | Ou la trouver | Default |
|----------|---------------|---------|
| `MP4_TRANSCRIBER_URL` | URL du service de transcription | `http://localhost:8765` |
| `MP4_TRANSCRIBER_AUTHORIZATION` | Header auth pour telechargements personal cloud | _(vide)_ |

## Usage

```bash
cd ../../lib/mp4-transcriber

# Transcrire un fichier vidéo
bin/mp4-transcriber run video.mp4

# Transcrire un fichier audio
bin/mp4-transcriber run podcast.mp3
bin/mp4-transcriber run enregistrement.m4a

# Depuis une URL
bin/mp4-transcriber run https://personal-cloud-api.example.com/public/video.mp4

# Derush seulement
bin/mp4-transcriber run video.mp4 --actions derush

# Sortie brute (pour agents)
bin/mp4-transcriber run audio.wav --quiet

# Consulter un job
bin/mp4-transcriber status 42

# Telecharger le fichier derushe
bin/mp4-transcriber download 42 output.mp4
```

Pour le detail complet, voir `SKILL.md`.
