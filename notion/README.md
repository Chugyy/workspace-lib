# Notion API — Research

Documentation de l'API Notion pour l'integration (queries, webhooks, SDK Python).

## Setup

1. `cp .env.example .env`
2. Remplir `NOTION_TOKEN` et `NOTION_DATABASE_ID`
3. `pip install notion-client`

## Credentials

| Variable | Ou la trouver |
|----------|---------------|
| `NOTION_TOKEN` | https://www.notion.com/my-integrations → New integration → Configuration → Secret |
| `NOTION_DATABASE_ID` | URL de la database Notion (32-char hex dans l'URL) |

---

## 1. Lire une database

### Endpoint

```
POST https://api.notion.com/v1/databases/{database_id}/query
Notion-Version: 2022-06-28
Authorization: Bearer {NOTION_TOKEN}
```

Note : un nouveau endpoint existe (`/v1/data_sources/{id}/query`, API v2025-09-03) mais l'ancien fonctionne et est plus simple. Migrer plus tard si besoin.

### Filtres pertinents pour HTR

**Par statut (missions en cours)** :
```json
{
  "filter": {
    "property": "Status",
    "status": { "equals": "En cours" }
  }
}
```

**Par monteur assigne** :
```json
{
  "filter": {
    "property": "Monteur",
    "people": { "contains": "user-uuid" }
  }
}
```

**Compose (missions actives d'un monteur)** :
```json
{
  "filter": {
    "and": [
      { "property": "Status", "status": { "equals": "En cours" } },
      { "property": "Monteur", "people": { "contains": "user-uuid" } }
    ]
  }
}
```

Attention : `status` et `select` sont des types differents. Verifier le type reel de la propriete.

### Pagination

- `page_size` : max 100 resultats par requete
- Response : `has_more` (bool) + `next_cursor` (string)
- Passer `start_cursor` pour les pages suivantes

### Structure d'une entree (page)

```json
{
  "object": "page",
  "id": "uuid",
  "last_edited_time": "2024-01-20T14:22:00.000Z",
  "properties": {
    "Status": {
      "type": "status",
      "status": { "name": "En cours", "color": "blue" }
    },
    "Monteur": {
      "type": "people",
      "people": [{ "id": "user-uuid", "name": "John Doe" }]
    },
    "Date de livraison": {
      "type": "date",
      "date": { "start": "2026-04-10", "end": null }
    },
    "Nom mission": {
      "type": "title",
      "title": [{ "plain_text": "Video Client X" }]
    }
  }
}
```

### Comment obtenir le Database ID

1. Ouvrir la database en page complete dans Notion
2. Share → Copy link
3. URL : `https://www.notion.so/{workspace}/{database_id}?v={view_id}`
4. Le `database_id` = 32 caracteres hex (sans tirets) ou 36 (avec)

---

## 2. Webhooks / Mises a jour temps reel

### Webhooks natifs — OUI (depuis API v2025-09-03)

Notion supporte les webhooks natifs. Pas besoin de Zapier/Make.

**Setup** :
1. notion.com/my-integrations → tab Webhooks
2. Creer un abonnement avec URL HTTPS (pas localhost)
3. Notion envoie un `verification_token` via POST
4. Soumettre le token dans l'UI pour activer

**Evenements supportes** :
- `page.content_updated` — changement de contenu (batche, leger delai)
- `page.locked` — page verrouillee
- `comment.created` — nouveau commentaire
- `data_source.schema_updated` — changement schema DB

**Limitations** :
- Payload = notification legere (type event + page ID). Il faut re-querier l'API pour le contenu reel.
- `page.content_updated` a un delai volontaire (batching des edits rapides)
- Pas d'event specifique "property changed" — un changement de statut = `page.content_updated`
- URL non modifiable apres verification (supprimer et recreer)

**Validation** : header `X-Notion-Signature` (HMAC-SHA256).

### Approche recommandee pour HTR

| Option | Avantage | Inconvenient |
|--------|----------|--------------|
| **Polling** (toutes les 2-3 min) | Simple, pas besoin d'endpoint public | Delai de 2-3 min |
| **Webhooks** | Quasi temps reel | Besoin d'endpoint HTTPS public |

Pour la Phase 2 (BP engagee), le **polling toutes les 2-3 min est largement suffisant**. La dispo des monteurs ne change pas a la seconde pres.

---

## 3. Details pratiques

### Lib Python : `notion-client` (SDK officiel)

```
pip install notion-client
```

- Repo : `ramnes/notion-sdk-py`
- Supporte sync (`Client`) et async (`AsyncClient`) — utiliser `AsyncClient` avec FastAPI
- Auto-retry sur 429 et 5xx (backoff exponentiel, max 2 retries)
- Helpers pagination : `iterate_paginated_api()`, `collect_paginated_api()`

### Creer une integration

1. https://www.notion.com/my-integrations → New integration
2. Nommer, selectionner le workspace
3. Tab Configuration → copier le secret (commence par `ntn_` ou `secret_`)
4. Stocker dans `NOTION_TOKEN`

### Partager la database avec l'integration

**OBLIGATOIRE** — sinon l'API retourne 404.

1. Ouvrir la database dans Notion
2. Menu "..." (en haut a droite) → Add connections
3. Chercher et selectionner l'integration

### Rate limits

- **3 req/s** en moyenne par token
- **2700 req / 15 min** par token
- HTTP 429 avec header `Retry-After`
- Payload max : 500KB/requete
- `notion-client` gere les retries automatiquement

### Gotchas

1. **Status vs Select** : types differents, filtres differents
2. **People property** : retourne des user objects (id + name), pas des emails. Il faudra mapper Notion user ID → discord_id
3. **Linked databases** : pas supportees par l'API (seulement les originales)
4. **Rich text** : tableaux d'objets texte, utiliser `.plain_text`
5. **Formulas avec 25+ relations** : seules les 25 premieres sont evaluees

---

## 4. Decouverte du schema

`GET /v1/databases/{database_id}` retourne toutes les proprietes avec noms, types et configurations.

Utile pour verifier que les noms de proprietes correspondent a ce qu'on attend (Status, Monteur, Date, etc.).

---

## Variables d'env

| Variable | Source |
|----------|--------|
| `NOTION_TOKEN` | Notion Integrations → Internal Integration Secret |
| `NOTION_DATABASE_ID` | URL de la database Notion |
