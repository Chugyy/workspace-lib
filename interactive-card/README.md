# Interactive Card

Cree des conversations interactives (notifications, formulaires, tickets) dans l'AI Manager.

## Setup

1. `cp .env.example .env` (optionnel si les defaults conviennent)
2. `./setup.sh`

## Credentials

| Variable | Ou la trouver | Default |
|----------|---------------|---------|
| `BACKEND_URL` | URL du backend AI Manager | `http://127.0.0.1:4810` |
| `BACKEND_INTERNAL_KEY` | Cle API interne du backend | `proxy-internal-key` |

Les scripts d'action du handler ont deja ces variables dans leur environnement.

## Usage

```bash
cd ../../lib/interactive-card

# Notification simple
.venv/bin/interactive-card notify "Titre" "**Details** en markdown"

# Formulaire interactif
.venv/bin/interactive-card prompt "Approuver ?" \
    --text "Un client souhaite reserver" \
    --fact "Client=John Doe" --fact "Montant=500 EUR" \
    --input "reply:textarea:Votre reponse" \
    --approve "Approuver" --reject "Refuser"

# JSON complet
.venv/bin/interactive-card create '{"body":[...],"actions":[...]}'

# Test de connexion
.venv/bin/interactive-card test
```

Pour le detail complet (builder Python, exemples scripts d'action), voir `SKILL.md`.
