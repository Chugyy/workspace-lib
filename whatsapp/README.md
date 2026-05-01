# WhatsApp

Envoyer et recevoir des messages WhatsApp via Unipile API.

## Setup

1. `cp .env.example .env`
2. Remplir les variables (voir ci-dessous)
3. `./setup.sh`

## Credentials

| Variable | Ou la trouver |
|----------|---------------|
| `UNIPILE_DSN` | URL du serveur Unipile (ex: `https://api15.unipile.com:14510`) |
| `UNIPILE_API_KEY` | https://app.unipile.com/ > Settings > API Keys |
| `UNIPILE_ACCOUNT_ID` | ID du compte WhatsApp connecté dans Unipile |

La configuration est stockée dans `assets/config.json` (gitignored).

## Usage

```bash
cd ../../lib/whatsapp && source .venv/bin/activate

# Envoyer du texte
whatsapp send-text --chat-id "CHAT_ID" --text "Hello!"

# Envoyer une image / vidéo / audio
whatsapp send-image --chat-id "CHAT_ID" --image "/path/img.png" --caption "Look at this"
whatsapp send-video --chat-id "CHAT_ID" --video "/path/video.mp4"
whatsapp send-audio --chat-id "CHAT_ID" --audio "/path/voice.ogg"

# Nouvelle conversation
whatsapp new-conversation --phone "+33612345678" --text "Hello!"

# Lister les conversations
whatsapp get-chats

# Récupérer les messages
whatsapp get-messages --chat-id "CHAT_ID" --limit 20

# Télécharger un média
whatsapp download-media --chat-id "CHAT_ID" --type audio --output-dir ./downloads
```

## Notes

- Numéros au format E.164 : `+33612345678`
- `new-conversation` vérifie que le numéro est sur WhatsApp avant d'envoyer
- Taille max pièce jointe : 15 MB
- Formats supportés : JPG, PNG, GIF, WEBP, MP4, AVI, MOV, OGG, MP3, WAV, PDF, DOC, XLS
