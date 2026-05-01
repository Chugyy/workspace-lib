---
name: telegram-notifier
description: Send notifications, alerts, and messages via Telegram Bot. Use when you need to send real-time notifications to the user (email alerts, task completions, system events, error notifications, status updates). The bot is already configured with token and chat ID.
---

# Telegram Notifier

## Setup

```bash
cd .claude/skills/telegram-notifier && ./setup.sh
```

## CLI Usage

```bash
# Activate venv
source .claude/skills/telegram-notifier/.venv/bin/activate

# Help
telegram --help
```

## Commands

```bash
# Send plain text
telegram send --text "Task completed"
telegram send --text "Silent update" --silent

# Send formatted notification
telegram notify --title "Alert" --text "Something happened"
telegram notify --title "Deploy" --text "v1.2.3 deployed" --emoji "🚀"

# Send alert with level
telegram alert --text "All good" --level success
telegram alert --text "Disk 90% full" --level warning
telegram alert --text "API down!" --level error
telegram alert --text "Job started" --level info

# Test connection
telegram test
```

## Config

`assets/config.json` — bot_token + chat_id (already configured).

## Alert Levels

- `info` — ℹ️
- `warning` — ⚠️
- `error` — ❌
- `success` — ✅
