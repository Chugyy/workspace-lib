# Fathom

Recuperer les transcripts d'appels Fathom via l'API.

## Setup

1. `cp .env.example .env`
2. Remplir les variables (voir Credentials ci-dessous)
3. `./setup.sh`

Configurer `assets/config.json` avec l'API key et le webhook secret.

## Credentials

| Variable | Ou la trouver |
|----------|---------------|
| `FATHOM_API_KEY` | Fathom → Settings → API → Generate API Key |
| `FATHOM_WEBHOOK_SECRET` | Fathom → Settings → Webhooks → Secret |
| `FATHOM_BASE_URL` | `https://api.fathom.ai/external/v1` (defaut) |

## Usage

```bash
cd ../../lib/fathom && .venv/bin/fathom --help
```

### Fetch transcript

```bash
# Par URL de partage
.venv/bin/fathom transcript "https://fathom.video/share/<token>"

# Par URL d'appel
.venv/bin/fathom transcript "https://fathom.video/calls/124392814"

# Par ID numerique
.venv/bin/fathom transcript 124392814

# Sauvegarder dans un fichier
.venv/bin/fathom transcript "https://fathom.video/share/<token>" --output /tmp/transcript.txt
```

## Output

- Transcript imprime sur stdout
- Chemin du fichier temporaire sur stderr : `TEMP_FILE:/tmp/fathom_...txt`
- Format : `[timestamp] Speaker: text`
