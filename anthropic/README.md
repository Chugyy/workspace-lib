# Anthropic (Claude API) — Research

## Setup

1. `cp .env.example .env`
2. Remplir `ANTHROPIC_API_KEY`
3. `pip install anthropic`

## Credentials

| Variable | Ou la trouver |
|----------|---------------|
| `ANTHROPIC_API_KEY` | https://console.anthropic.com → API Keys |

## Resume
SDK Python officiel (`anthropic >= 0.94.1`) pour acceder aux modeles Claude. Supporte async, streaming SSE, structured JSON output (GA via `output_config`), prompt caching, et retries automatiques. Deux modeles cibles : Opus 4.6 pour les taches complexes et Sonnet 4.6 pour le streaming rapide.

## Integration
- **SDK/Librairie** : `anthropic`, version 0.94.1+
- **Auth** : API key via env var `ANTHROPIC_API_KEY`
- **Base URL** : `https://api.anthropic.com`

```bash
pip install anthropic
```

## Models utilises

### Claude Opus 4.6
- **Model ID** : `claude-opus-4-6`
- **Usage** : Brief pre-call, resume post-call (JSON structure)
- **Context window** : 1M tokens
- **Max output** : 128k tokens
- **Pricing** : $5/MTok input, $25/MTok output
- **Cache hit** : $0.50/MTok

### Claude Sonnet 4.6
- **Model ID** : `claude-sonnet-4-6`
- **Usage** : Suggestions live (streaming, ~300 tokens)
- **Context window** : 1M tokens
- **Max output** : 64k tokens
- **Pricing** : $3/MTok input, $15/MTok output
- **Cache hit** : $0.30/MTok

## Patterns cles

### JSON Output (Structured Outputs — GA)
```python
response = await client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1000,
    messages=[{"role": "user", "content": "..."}],
    output_config={
        "format": {
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {...},
                "required": [...],
                "additionalProperties": False,
            },
        }
    },
)
data = json.loads(response.content[0].text)  # garanti valide
```

### Streaming
```python
async with client.messages.stream(
    model="claude-sonnet-4-6",
    max_tokens=300,
    messages=[{"role": "user", "content": "..."}],
) as stream:
    async for text in stream.text_stream:
        await websocket.send(text)
```

### Prompt Caching
```python
response = await client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1000,
    system=[{
        "type": "text",
        "text": SYSTEM_PROMPT,
        "cache_control": {"type": "ephemeral"},  # cache 5 min
    }],
    messages=[{"role": "user", "content": query}],
)
```

## Limites & Couts
- **Rate limits Tier 2** : 1000 RPM, 450k input TPM
- **Cached tokens ne comptent pas dans l'ITPM**
- **Cout estime par appel** : ~$0.10 (brief + 5 suggestions + summary)
- **Retries** : SDK fait 2 retries auto avec backoff sur 429, >=500

## Patterns recommandes
1. Prompt caching sur le system prompt (ROI des le 2e appel)
2. Streaming pour les suggestions live, pas create()
3. JSON structured output via output_config (garanti valide)
4. Timeout adapte : 30s pour briefs/summaries, 15s pour suggestions
5. AsyncAnthropic pour le contexte FastAPI async

## Exemples de code
```python
import json
from anthropic import AsyncAnthropic

client = AsyncAnthropic()

async def generate_brief(lead_data: str, system_prompt: str) -> dict:
    response = await client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1000,
        system=[{
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": lead_data}],
        output_config={
            "format": {
                "type": "json_schema",
                "schema": BRIEF_SCHEMA,
            }
        },
    )
    return json.loads(response.content[0].text)

async def stream_suggestion(context: str, on_text):
    async with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": context}],
    ) as stream:
        async for text in stream.text_stream:
            await on_text(text)
```

## Variables d'environnement necessaires
| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Cle API Anthropic (console.anthropic.com) |
