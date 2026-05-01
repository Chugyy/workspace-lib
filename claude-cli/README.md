# Claude CLI

Appeler Claude (Haiku/Sonnet/Opus) depuis des scripts shell via l'API Anthropic. Utile quand un script d'action a besoin d'inference LLM (categorisation, analyse, extraction, resume).

## Setup

1. `cp .env.example .env`
2. Remplir `ANTHROPIC_API_KEY`
3. `./setup.sh`

## Credentials

| Variable | Ou la trouver |
|----------|---------------|
| `ANTHROPIC_API_KEY` | https://console.anthropic.com → API Keys |

## Usage

```bash
# Activate venv
source ../../lib/claude-cli/.venv/bin/activate

# Help
claude-cli --help
```

## Commands

```bash
# Ask with default model (haiku)
claude-cli ask "What category is this event?"

# Ask with specific model
claude-cli ask --model haiku "Categorize this text"
claude-cli ask --model sonnet "Analyze these feedbacks..."
claude-cli ask --model opus "Complex reasoning task"

# With system prompt
claude-cli ask --model sonnet --system "You are a data analyst" "Summarize this data"

# JSON output (adds JSON instruction + validates response)
claude-cli ask --model haiku --json "Return {category: string} for: Meeting with client"

# Pipe-friendly — prints raw response to stdout
CATEGORY=$(claude-cli ask --model haiku --json "Categorize: $EVENT")
```

## Models

| Alias | Model ID |
|-------|----------|
| haiku | claude-haiku-4-5-20251001 |
| sonnet | claude-sonnet-4-6-20250514 |
| opus | claude-opus-4-6-20250514 |
