# Context Hub CLI

CLI pour publier, s'abonner et synchroniser des entites de contexte via le Context Hub API.

## Setup

```bash
./setup.sh
profile add context-hub default
```

## Credentials

| Variable | Description |
|----------|-------------|
| `CONTEXT_HUB_URL` | URL du Context Hub (ex: https://context.multimodal-house.fr) |
| `CONTEXT_HUB_EMAIL` | Email du compte |
| `CONTEXT_HUB_PASSWORD` | Mot de passe du compte |

## Usage

```bash
# Authentification
context-hub login

# Publier une entite locale
context-hub publish context/store/identity.md
context-hub publish context/store/strategy.md --visibility public

# Lister les entites publiees
context-hub list

# Generer un share link
context-hub share identity --permissions read_write --review-mode manual

# S'abonner a une entite distante
context-hub subscribe https://context.multimodal-house.fr/s/xK9mQ2vR8n

# Voir le statut des abonnements
context-hub status

# Synchroniser toutes les entites abonnees
context-hub sync

# Depublier
context-hub unpublish identity
```

## Flow de partage

```
Owner                                    Subscriber
──────                                   ──────────
context-hub publish file.md
context-hub share entity-id ──────────→  context-hub subscribe <url>
                                         context-hub sync
  (modif locale)                         context-hub sync  ← pull changes
context-hub sync  ← push changes ────→  context-hub sync  ← pull changes
```

## Fichiers locaux abonnes

Quand on subscribe, un champ `source:` est ajoute au frontmatter :

```yaml
---
id: strategy-partner
source: "https://context.multimodal-house.fr/s/xK9mQ2vR8n"
source_mode: read-write:manual
source_synced_at: 2026-05-01T08:00:00Z
---
```

Le `sync` utilise ces champs pour detecter les changements et synchroniser.
