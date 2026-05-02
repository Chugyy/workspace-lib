# WhatsApp

Envoyer et recevoir des messages WhatsApp via WAHA (self-hosted, open-source).

## Architecture

```
CLI Python (whatsapp) → HTTP → WAHA (Docker) → WebSocket → WhatsApp Servers
```

WAHA est un container Docker qui wrappe le protocole WhatsApp Web en API REST.
Moteur par défaut : NOWEB (Baileys, WebSocket direct, pas de Chrome).

## Setup

### 1. Lancer WAHA (Docker)

```bash
docker run -d \
  --name waha \
  --restart unless-stopped \
  -p 3000:3000 \
  -v waha_sessions:/app/.sessions \
  -e WHATSAPP_DEFAULT_ENGINE=NOWEB \
  -e WHATSAPP_API_KEY=waha-internal-key \
  devlikeapro/waha
```

### 2. Scanner le QR code

Ouvrir le dashboard : http://localhost:3000/dashboard
Ou via le CLI :

```bash
whatsapp session-status
```

### 3. Configurer le profil

```bash
profile add whatsapp default
# Ou manuellement :
cp .env.example .env
```

### 4. Installer le CLI

```bash
./setup.sh
```

## Credentials

| Variable | Description |
|----------|-------------|
| `WAHA_BASE_URL` | URL du serveur WAHA (ex: `http://localhost:3000`) |
| `WAHA_API_KEY` | Clé API passée au container Docker via `WHATSAPP_API_KEY` |
| `WAHA_SESSION` | Nom de la session (default: `default`) |

## Usage

```bash
# Statut de la session
whatsapp session-status

# Vérifier un numéro
whatsapp check-phone --phone "+33612345678"

# Envoyer du texte
whatsapp send-text --chat-id "33612345678@c.us" --text "Hello!"

# Envoyer une image / vidéo / audio / fichier
whatsapp send-image --chat-id "33612345678@c.us" --image "/path/img.png" --caption "Look"
whatsapp send-video --chat-id "33612345678@c.us" --video "/path/video.mp4"
whatsapp send-audio --chat-id "33612345678@c.us" --audio "/path/voice.ogg"
whatsapp send-file  --chat-id "33612345678@c.us" --file "/path/doc.pdf" --caption "Doc"

# Nouvelle conversation
whatsapp new-conversation --phone "+33612345678" --text "Hello!"

# Lister les conversations
whatsapp get-chats

# Récupérer les messages
whatsapp get-messages --chat-id "33612345678@c.us" --limit 20

# Télécharger des médias
whatsapp download-media --chat-id "33612345678@c.us" --type audio --output-dir ./downloads
whatsapp download-media --chat-id "33612345678@c.us" --list --type audio
whatsapp download-media --chat-id "33612345678@c.us" --sender "Kilian" --time "15:51"
```

## Format des Chat IDs

| Type | Format | Exemple |
|------|--------|---------|
| Contact | `{phone}@c.us` | `33612345678@c.us` |
| Groupe | `{groupId}@g.us` | `120363047817217729@g.us` |

Le numéro est au format international sans le `+` : `33612345678` (pas `+33612345678`).

## Notes

- **Moteur NOWEB** : WebSocket direct (pas de Chrome/Puppeteer), léger et rapide
- **Session persistante** : le volume Docker `waha_sessions` garde la session active entre redémarrages
- **Formats supportés** : JPG, PNG, GIF, WEBP, MP4, AVI, MOV, OGG, MP3, WAV, PDF, DOC, XLS
- **QR code** : à re-scanner si la session expire (déconnexion WhatsApp Web)
- **Dashboard** : http://localhost:3000/dashboard pour voir le statut, QR, logs
