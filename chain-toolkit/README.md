# Chain Toolkit

Helpers bash pour les scripts d'action des PIDs. A sourcer en debut de script pour parser l'event entrant, configurer les traps d'erreur, emettre de la progression, et verifier l'idempotency.

## Setup

Aucune installation necessaire. Le fichier est source directement dans les scripts d'action.

## Credentials

| Variable | Ou la trouver |
|----------|---------------|
| `AGGREGATOR_URL` | URL de l'aggregator (ex: `https://events.multimodal-house.fr`) |
| `AGG_API_KEY` | Cle API aggregator |

## Variables d'environnement

Ces variables sont utilisees par les fonctions du toolkit. Elles sont soit injectees par le handler runner, soit renseignees par `parse_event` :

| Variable | Source | Description |
|----------|--------|-------------|
| `AGGREGATOR_URL` | handler / .env | URL de l'aggregator |
| `AGG_API_KEY` | handler / .env | Cle API aggregator |
| `TASK_ID` | handler / `parse_event` | ID de la tache en cours |
| `ROADMAP_ID` | handler / `parse_event` | ID de la roadmap |
| `ROADMAP_SOURCE` | handler / `parse_event` | Source pour les events (ex: `roadmap:rm-123`) |
| `EVENT_ID` | `parse_event` | ID de l'event trigger (utilise comme `related_to`) |
| `TMPDIR` | script | Si set, nettoy par `roadmap_trap` en cas d'erreur |

## Usage — Structure type d'un script d'action

```bash
#!/bin/bash
set -euo pipefail
source "/data/workspace/lib/chain-toolkit/chain-toolkit.sh"

# 1. Parser l'event et exporter TASK_ID, ROADMAP_ID, etc.
parse_event "$1"

# 2. Configurer le trap d'erreur (emet roadmap.task.failed si le script crashe)
roadmap_trap

# --- Logique metier ---

# Idempotency : ne re-executer une etape que si elle n'a pas deja reussi
if ! has_event "step.schema.done"; then
  emit_progress 1 3 "Generating schema"
  # ... travail ...
  emit_business_event "step.schema.done"
fi

if ! has_event "step.api.done"; then
  emit_progress 2 3 "Building API"
  # ... travail ...
  emit_business_event "step.api.done" '{"routes": 12}'
fi

emit_progress 3 3 "Done"

# verify_file pour valider les outputs
verify_file "./docs/schema.md"
```

## Fonctions

### `parse_event <json>`

Parse le JSON event d'entree (passe en `$1` par le handler) et exporte les variables standard.

```bash
parse_event "$1"
# Exporte : EVENT_ID, EVENT_SOURCE, EVENT_TYPE, TASK_ID, ROADMAP_ID, ROADMAP_SOURCE
```

- Exit 1 si jq manque, si le JSON est invalide, ou si l'argument est vide
- `ROADMAP_SOURCE` est derive de `EVENT_SOURCE` si non deja set

---

### `roadmap_trap`

Configure un `trap ERR` qui emet `roadmap.task.failed` avant que le process ne meure.

```bash
roadmap_trap
# A appeler apres parse_event
```

- Emet `roadmap.task.failed` avec `exit_code` et `line`
- Nettoie `$TMPDIR` si set
- Complement au handler runner (qui emet aussi `failed` si exit != 0)

---

### `emit_progress <step> <total> [message]`

Emet un event `roadmap.task.progress` avec la progression.

```bash
emit_progress 2 5 "Building API routes"
```

- `related_to` utilise automatiquement `$EVENT_ID`
- Silencieux si le curl echoue (warning sur stderr)

---

### `emit_business_event <event_type> [extra_payload_json]`

Emet un event business pour le chainage, avec `task_id` et `roadmap_id` inclus automatiquement.

```bash
emit_business_event "deploy.completed" '{"url":"https://myapp.example.com"}'
emit_business_event "step.schema.done"
```

- Merge `extra_payload` avec `{task_id, roadmap_id}` (extra gagne en cas de conflit)

---

### `has_event <event_type> [task_id]`

Verifie si un event du type donne a deja ete emis pour cette tache (idempotency).

```bash
if ! has_event "step.schema.done"; then
  # executer l'etape
  emit_business_event "step.schema.done"
fi
```

- Query `GET /events?source=...&type=...&limit=50` puis filtre sur `payload.task_id`
- Exit 0 si trouve, exit 1 sinon
- Retourne exit 1 (graceful) si l'aggregator est injoignable

---

### `emit_event <type> [payload_json] [related_to]`

Emet un event arbitraire vers l'aggregator.

```bash
emit_event "roadmap.task.completed" '{"task_id":"t-1","roadmap_id":"rm-1"}' "$EVENT_ID"
```

---

### `verify_file <path> [message]`

Verifie qu'un fichier existe et n'est pas vide. Return 1 si echec.

```bash
verify_file "./docs/prd.md" "PRD not generated"
```

## Dependances

- `bash` 4+
- `jq` (pour parse_event, emit_event, has_event, emit_progress, emit_business_event)
- `curl` (pour emit_event, has_event)
- `python3` (pour l'encodage URL dans has_event)
