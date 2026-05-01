# Slack (Incoming Webhook) — Research

## Setup

1. `cp .env.example .env`
2. Remplir `SLACK_WEBHOOK_URL` (voir Credentials ci-dessous)
3. `pip install httpx`

## Credentials

| Variable | Ou la trouver |
|----------|---------------|
| `SLACK_WEBHOOK_URL` | https://api.slack.com/apps → Your App → Incoming Webhooks → Add New Webhook to Workspace |

---

## Resume
Slack Incoming Webhooks permettent de poster des messages dans un channel via un simple POST HTTP avec un payload JSON. Pas de SDK necessaire — un appel httpx async suffit. Block Kit permet des messages structures riches avec sections, headers, dividers et context blocks.

## Integration
- **SDK/Librairie** : httpx (async HTTP, pas de Slack SDK necessaire)
- **Auth** : Webhook URL (secret, agit comme bearer token)
- **Base URL** : `https://hooks.slack.com/services/T.../B.../XXX...` (fourni par la config Slack app)

## Setup (creation du webhook)

1. Aller sur https://api.slack.com/apps et creer une nouvelle app
2. Dans Features > Incoming Webhooks, activer le toggle
3. Cliquer "Add New Webhook to Workspace", selectionner le channel cible
4. Copier l'URL generee et la stocker en variable d'environnement

## Endpoints utiles

### POST Webhook
- **Methode** : POST
- **URL** : `YOUR_SLACK_WEBHOOK_URL`
- **Headers** : `Content-Type: application/json`
- **Input avec Block Kit** :
  ```json
  {
    "text": "Fallback text for notifications",
    "blocks": [
      {
        "type": "header",
        "text": {"type": "plain_text", "text": "Call Complete"}
      },
      {
        "type": "section",
        "fields": [
          {"type": "mrkdwn", "text": "*Lead:* John Doe"},
          {"type": "mrkdwn", "text": "*Score:* 8/10"},
          {"type": "mrkdwn", "text": "*Status:* Closing"},
          {"type": "mrkdwn", "text": "*Duration:* 25min"}
        ]
      },
      {"type": "divider"},
      {
        "type": "section",
        "text": {"type": "mrkdwn", "text": "*Next Action:* Envoyer le contrat"}
      }
    ]
  }
  ```
- **Output succes** : `"ok"` (HTTP 200)
- **Erreurs** : 400 (invalid_payload, no_text), 403 (invalid_token), 404 (channel_not_found), 429 (rate limited)

## Limites & Couts
- **Rate limit** : 1 message/seconde par webhook
- **429 response** : header `Retry-After: N`
- **Max blocks** : 50 par message
- **Cout** : Gratuit

## Patterns recommandes
1. Toujours inclure `text` meme avec `blocks` (fallback notifications push)
2. Retry avec backoff sur 429, respecter Retry-After
3. Webhook URL = secret, stocker en env var
4. Ne jamais crash si le webhook echoue, logger et continuer

## Exemples de code
```python
import httpx

async def send_slack_notification(
    webhook_url: str,
    text: str,
    blocks: list[dict] | None = None,
) -> bool:
    payload = {"text": text}
    if blocks:
        payload["blocks"] = blocks

    async with httpx.AsyncClient(timeout=10.0) as client:
        for attempt in range(3):
            response = await client.post(webhook_url, json=payload)
            if response.status_code == 200:
                return True
            if response.status_code == 429:
                import asyncio
                retry_after = int(response.headers.get("Retry-After", 1))
                await asyncio.sleep(retry_after)
                continue
            return False
    return False
```

## Variables d'environnement necessaires
| Variable | Description |
|----------|-------------|
| `SLACK_WEBHOOK_URL` | Incoming Webhook URL |
