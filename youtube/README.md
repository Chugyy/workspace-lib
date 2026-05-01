# YouTube

Download, transcript, search, upload video & thumbnail sur YouTube.

## Setup

1. Placer `client_secret.json` (OAuth2) dans `credentials/`
2. `./setup.sh auth` (ouvre le navigateur pour l'auth OAuth2)
3. Le token est sauvegardé dans `credentials/token.json` (auto-refresh)

## Credentials

| Fichier | Ou l'obtenir |
|---------|--------------|
| `credentials/client_secret.json` | Google Cloud Console > APIs & Services > Credentials > OAuth 2.0 Client ID (Desktop App) > Download JSON |

## Usage

```bash
LIB_TOOL="../../lib/youtube"

# Télécharger une vidéo
$LIB_TOOL/setup.sh download "https://youtube.com/watch?v=..." [--audio-only] [--output ./dir]

# Récupérer la transcription
$LIB_TOOL/setup.sh transcript "https://youtube.com/watch?v=..." [--lang fr] [--timestamps]

# Rechercher
$LIB_TOOL/setup.sh search "query" [--max 10] [--json]

# Uploader (requiert auth OAuth2)
$LIB_TOOL/setup.sh upload ./video.mp4 --title "Title" --description "Desc" --privacy private

# Définir une thumbnail
$LIB_TOOL/setup.sh thumbnail VIDEO_ID ./thumbnail.png

# Authentification OAuth2
$LIB_TOOL/setup.sh auth
```

## Inputs / Outputs

- **credentials/** : OAuth2 client secret et token (gitignored)
- **output/** : vidéos téléchargées et transcriptions (contenu gitignored)
