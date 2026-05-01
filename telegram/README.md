# Telegram

Envoyer des notifications et alertes via Telegram Bot.

## Setup

1. `cp .env.example .env`
2. Remplir les variables (voir ci-dessous)
3. `./setup.sh`

## Credentials

| Variable | Ou la trouver |
|----------|---------------|
| `TELEGRAM_BOT_TOKEN` | @BotFather sur Telegram > /newbot |
| `TELEGRAM_CHAT_ID` | Envoyer un message au bot, puis `GET https://api.telegram.org/bot<token>/getUpdates` |

La configuration est stockée dans `assets/config.json` (gitignored).

## Usage

```bash
cd ../../lib/telegram && source .venv/bin/activate

# Envoyer du texte
telegram send --text "Task completed"
telegram send --text "Silent update" --silent

# Notification formatée
telegram notify --title "Alert" --text "Something happened"
telegram notify --title "Deploy" --text "v1.2.3 deployed" --emoji "rocket"

# Alerte avec niveau
telegram alert --text "All good" --level success
telegram alert --text "Disk 90% full" --level warning
telegram alert --text "API down!" --level error

# Tester la connexion
telegram test
```

## Alert Levels

| Niveau | Emoji |
|--------|-------|
| `info` | info |
| `warning` | warning |
| `error` | error |
| `success` | success |
