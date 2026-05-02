---
name: whatsapp-manager
description: Send and receive WhatsApp messages via WAHA (self-hosted). Use when the user needs to send messages, check conversations, read messages, or start new WhatsApp conversations. Supports text, images, videos, audio, and documents.
---

# WhatsApp Manager

## Setup

```bash
cd ../../lib/whatsapp && ./setup.sh
```

## CLI Usage

```bash
# Activate venv
source ../../lib/whatsapp/.venv/bin/activate

# Help
whatsapp --help
```

## Commands

```bash
# Check session status
whatsapp session-status

# Check if a phone number is on WhatsApp
whatsapp check-phone --phone "+33612345678"

# Send text to existing chat
whatsapp send-text --chat-id "33612345678@c.us" --text "Hello!"

# Send image
whatsapp send-image --chat-id "33612345678@c.us" --image "/path/img.png" --caption "Look at this"

# Send video
whatsapp send-video --chat-id "33612345678@c.us" --video "/path/video.mp4"

# Send audio
whatsapp send-audio --chat-id "33612345678@c.us" --audio "/path/voice.ogg"

# Send file/document
whatsapp send-file --chat-id "33612345678@c.us" --file "/path/doc.pdf" --caption "Document"

# Start new conversation (validates phone is on WhatsApp)
whatsapp new-conversation --phone "+33612345678" --text "Hello!"
whatsapp new-conversation --phone "+33612345678" --text "See attachment" --files "/path/doc.pdf"

# List all conversations
whatsapp get-chats

# Get messages from a chat
whatsapp get-messages --chat-id "33612345678@c.us" --limit 20

# Download media from chat (batch)
whatsapp download-media --chat-id "33612345678@c.us" --type audio --output-dir ./downloads
whatsapp download-media --chat-id "33612345678@c.us" --list --type audio
whatsapp download-media --chat-id "33612345678@c.us" --sender "Kilian" --time "15:51"
```

## Chat ID Format

- Contact: `{phone}@c.us` (e.g., `33612345678@c.us`)
- Group: `{groupId}@g.us`
- Phone number without `+`, international format

## Config

Profile-based credentials via `profile add whatsapp default`.

## Notes

- WAHA (self-hosted Docker container) — no external API dependency
- Phone numbers must be E.164 format: `+33612345678`
- `new-conversation` verifies the phone is on WhatsApp before sending
- Formats: JPG, PNG, GIF, WEBP, MP4, AVI, MOV, OGG, MP3, WAV, PDF, DOC, XLS
- Session status: `whatsapp session-status` to check connection
