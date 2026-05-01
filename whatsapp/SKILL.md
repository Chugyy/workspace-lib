---
name: whatsapp-manager
description: Send and receive WhatsApp messages via Unipile API. Use when the user needs to send messages, check conversations, read messages, or start new WhatsApp conversations. Supports text, images, videos, audio, and documents.
---

# WhatsApp Manager

## Setup

```bash
cd .claude/skills/whatsapp-manager && ./setup.sh
```

## CLI Usage

```bash
# Activate venv
source .claude/skills/whatsapp-manager/.venv/bin/activate

# Help
whatsapp --help
```

## Commands

```bash
# Send text to existing chat
whatsapp send-text --chat-id "Q7z9wLVuWEKXJ505iLYh9w" --text "Hello!"

# Send image
whatsapp send-image --chat-id "Q7z9wLVuWEKXJ505iLYh9w" --image "/path/img.png" --caption "Look at this"

# Send video
whatsapp send-video --chat-id "Q7z9wLVuWEKXJ505iLYh9w" --video "/path/video.mp4"

# Send audio
whatsapp send-audio --chat-id "Q7z9wLVuWEKXJ505iLYh9w" --audio "/path/voice.ogg"

# Start new conversation (validates phone is on WhatsApp)
whatsapp new-conversation --phone "+33612345678" --text "Hello!"
whatsapp new-conversation --phone "+33612345678" --text "See attachment" --files "/path/doc.pdf"

# List all conversations
whatsapp get-chats

# Get messages from a chat
whatsapp get-messages --chat-id "Q7z9wLVuWEKXJ505iLYh9w" --limit 20

# Download attachment
whatsapp download-attachment --message-id "kLR2ZebfWIy3Y6WeOPzIuw" --attachment-id "3EB0C98D..." --output ./voice.ogg

# Download media from chat (batch)
whatsapp download-media --chat-id "Q7z9wLVuWEKXJ505iLYh9w" --type audio --output-dir ./downloads
whatsapp download-media --chat-id "Q7z9wLVuWEKXJ505iLYh9w" --list --type audio
whatsapp download-media --chat-id "Q7z9wLVuWEKXJ505iLYh9w" --sender "Kilian" --time "15:51"
```

## Config

`assets/config.json` — Unipile DSN, API key, account_id, user info.

## Notes

- Phone numbers must be E.164 format: `+33612345678`
- `new-conversation` verifies the phone is on WhatsApp before sending
- Max attachment size: 15 MB
- Supported formats: JPG, PNG, GIF, WEBP, MP4, AVI, MOV, OGG, MP3, WAV, PDF, DOC, XLS
