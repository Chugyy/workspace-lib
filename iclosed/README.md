# iClosed — Research

## Setup

1. `cp .env.example .env`
2. Remplir `ICLOSED_API_KEY` (voir Credentials)

## Credentials

| Variable | Ou la trouver |
|----------|---------------|
| `ICLOSED_API_KEY` | Dashboard iClosed > Settings > API. Format: `iclosed-<token>` |

## Resume

iClosed est une plateforme de sales scheduling / closing. L'API REST v1 publique donne acces aux contacts, event calls (appels planifies), deals, transactions et outcomes. Usage principal pour Closer Prep AI : lister les appels planifies d'un closer par son email, resoudre un lead depuis un `previewId` ou un lien Meet, pousser l'outcome d'un call en fin de conversation (WON / NO_SALE avec raison).

## Integration

- **SDK/Librairie** : aucun SDK Python officiel — wrapper direct via `httpx` async
- **Auth** : API key, header `Authorization: Bearer iclosed-<token>` (prefixe "Bearer" + prefixe "iclosed-" obligatoires)
- **Base URL** : `https://public.api.iclosed.io`
- **Version** : toutes les routes sont prefixees `/v1/`
- **OpenAPI spec** : `https://api-docs-iclosed.redocly.app/_bundle/openapi/v1/openapi.yaml`
- **Docs developpeur** : `https://developer.iclosed.io/`

## Endpoints utiles

### GET /v1/eventCalls — Search/list calls (endpoint cle)

Filtrage tres riche, supporte listes comma-separees.

**Query parameters** :

| Param | Type | Description |
|-------|------|-------------|
| `ids` | string | Comma-separated event call IDs |
| `contactId` | integer | Filter by contact |
| `eventType` | enum | `PAST`, `UPCOMING`, `ALL` |
| `search` | string | Free-text (invitee name/email/phone) |
| `dateFrom` / `dateTo` | ISO date | Range filter |
| `limit` | integer | Max 100, default 20 |
| `page` | integer | Zero-based page |
| `userIds` | string | Comma-separated closer/assigned user IDs |
| `eventIds` | string | Comma-separated event template IDs |
| `types` | string | `rescheduled_events`, `cancelled_events`, `scheduled_events` |
| `inviteeEmails` | string | Comma-separated |
| `outcomes` | string | `WON`, `NO_SALE`, `QUALIFIED`, `UNQUALIFIED`, `PENDING`, `APPROVED`, `REJECTED`, `PENDING_OUTCOME` |
| `noSaleReason` | string | `FOLLOW_UP_SCHEDULE`, `UNQUALIFIED`, `NO_SHOW`, `CONTACT_CANCELLED`, `ADMIN_CANCELLED`, `NOT_INTERESTED`, `BAD_FIT`, `OTHER` |
| `callTypes` | string | `STRATEGY_EVENT`, `DISCOVERY_EVENT` |
| `setterIds` | string | Comma-separated setter IDs |
| `previewId` | string | (observe en prod, non documente formellement) |

**Response** : status `201` (!), shape `{ data: { eventCalls: [...], count: N } }`.

**Champs cles d'un eventCall** (observes en production) :

```json
{
  "id": 1725546,
  "callId": 1725546,
  "previewId": "contact_Ll2PXG6CAOsj",
  "contactId": 2852639,
  "userId": 26629,
  "firstName": "Adrien",          // closer first name
  "lastName": "Perrier",          // closer last name
  "email": "closer@domain.com",   // closer email
  "inviteeEmail": "prospect@...", // prospect email
  "inviteeName": "Johanna Fonteneau",
  "phoneNumber": "+330664929387",
  "location": "GOOGLE_MEET",
  "locationLink": "https://meet.google.com/ffc-yqwz-hmy",
  "locationLinkInvitee": "https://meet.google.com/ffc-yqwz-hmy",
  "dateTime": "2026-04-18 10:00:00.000",
  "dateTimeUTC": "2026-04-18T09:00:00.000Z",
  "duration": 1,
  "durationUnit": "HOURS",
  "callType": "STRATEGY_EVENT",
  "eventType": "UPCOMING",
  "isCalendarConnected": true,
  "allowReschedule": true,
  "rescheduledBy": null,
  "rescheduleReason": null,
  "cancelledBy": null,
  "cancelReason": null,
  "name": "Candidature - Ecole HTR",
  "linkPrefix": "hittherecord/candidature-ecole-htr",
  "notes": null,
  "inviteTimeZone": "Europe/Paris",
  "userAvailabilityTimezone": "Africa/Casablanca",

  "SettedClaim": {
    "id": 3620840,
    "claimStatus": "USER_SCHEDULED",   // PENDING | SCHEDULED | NO_CALL | EXISTING_CALL | RESCHEDULED | CANCELLED | DISCOVERY_OUTCOME_PENDING | USER_SCHEDULED
    "outcome": "APPROVED",
    "user": null
  },
  "task": [{
    "id": 1740988,
    "completed": false,
    "outcome": null,
    "noSaleReason": null,
    "objection": null,
    "notes": null
  }],
  "taskId": 1740988,
  "deals": [],
  "questions": [
    { "statement": "Phone Number", "answer": "+33..." },
    { "statement": "First Name", "answer": "Johanna" }
  ],
  "secondaryAnswers": [
    {
      "statement": "Quelle est ta situation actuelle ?",
      "isSecondaryQuestion": true,
      "answer": [{
        "inputType": "SINGLE_SELECT",
        "answer": "Salarie(e) en CDI - Je veux quitter mon job"
      }]
    }
  ],
  "utm": [
    { "utmKey": "_fbp", "utmValue": "fb.1...." }
  ]
}
```

**Notes critiques** :
- `locationLink` contient le **code Meet** extrayable via regex `meet\.google\.com/([a-z]{3}-[a-z]{4}-[a-z]{3})` — cle de matching principale pour Closer Prep AI
- `email` = email du **closer** (pas du prospect !)
- `inviteeEmail` = email du **prospect**
- `previewId` = ID preview que l'URL iClosed expose (`?preview=contact_XXXX`)
- `secondaryAnswers` contient le questionnaire pre-rempli par le prospect (gold pour le brief)

### GET /v1/contacts/detail — Get contact by ID

- **Operation** : `getContactById`
- **Query param** : `id` (integer, requis) OU `previewId`
- **Response** : objet contact complet avec custom fields

### GET /v1/contacts — List contacts

- **Operation** : `getContacts`
- **Query params** : `userId` (assigned), `limit`, `page`, `joinedTimeFrom`, etc.

### POST /v1/outcomes — Upsert Call Outcome (endpoint finalize)

Pousse le resultat d'un call en fin de conversation.

**Body** :

```json
{
  "eventCallId": 1001,
  "outcome": "WON",             // WON | NO_SALE (STRATEGY) | APPROVED | REJECTED (DISCOVERY)
  "notes": "Closed on first strategy call.",
  "objection": "NO_OBJECTION",  // MONEY | LOGISTIC | PARTNER | FEAR | SMOKE_SCREEN | NO_OBJECTION
  "noSaleReason": "FOLLOW_UP_SCHEDULE",  // required if outcome=NO_SALE or REJECTED
  "newDeal": {
    "value": 5000,
    "transactionType": "WON",   // WON | RECURRING | DEPOSIT
    "productId": 42,
    "date": "2026-04-14T15:30:00.000Z"
  }
}
```

**Regles de validation croisees** :
- `outcome=WON` → `objection` requis
- `outcome=NO_SALE` → `noSaleReason` requis
- `outcome=NO_SALE` avec `noSaleReason` in (`FOLLOW_UP_SCHEDULE`, `UNQUALIFIED`) → `objection` aussi requis
- `outcome=REJECTED` → `noSaleReason` requis (DISCOVERY uniquement : `NO_SHOW`, `BAD_FIT`, `OTHER`, `NOT_INTERESTED`, `CONTACT_CANCELLED`, `ADMIN_CANCELLED`)

**Contraintes par callType** :
- `STRATEGY_EVENT` : outcome doit etre `WON` ou `NO_SALE`. Si `NO_SALE`, noSaleReason parmi `FOLLOW_UP_SCHEDULE`, `UNQUALIFIED`, `NO_SHOW`, `CONTACT_CANCELLED`, `ADMIN_CANCELLED`, `NOT_INTERESTED`.
- `DISCOVERY_EVENT` : outcome doit etre `APPROVED` ou `REJECTED`.

### PUT /v1/eventCalls/cancel — Cancel a call
### PUT /v1/eventCalls/reschedule — Reschedule
### POST /v1/contacts — Create/upsert contact
### PUT /v1/contacts — Update contact
### POST /v1/contacts/notes — Add note to contact

## Mapping outcomes → branches Closer Prep AI

| Branche UI | iClosed outcome | noSaleReason | objection | newDeal |
|---|---|---|---|---|
| Closing (Closing) | `WON` | — | required (`NO_OBJECTION` si rien) | required (value + productId + transactionType + date) |
| Suivi prevu | `NO_SALE` | `FOLLOW_UP_SCHEDULE` | required | — |
| No-show | `NO_SALE` | `NO_SHOW` | — | — |
| Pas interesse | `NO_SALE` | `NOT_INTERESTED` | — | — |

## Limites & Couts

### Rate limits

| Tier | Limite |
|------|--------|
| Startup | 20 req / endpoint / 10s / account |
| Business | 100 req / endpoint / 10s / account |

- Depassement : `429 Too Many Requests` avec header `Retry-After`
- Reponse inclut headers : `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

### HTTP Status codes

| Code | Signification |
|------|---------------|
| 200 | Success (GET) |
| 201 | Created / Success (POST, et meme GET /v1/eventCalls !) |
| 400 | Validation (Zod errors in body) |
| 401 | API key manquante/invalide |
| 403 | Permissions insuffisantes |
| 404 | Ressource introuvable |
| 429 | Rate limit (cf. headers) |
| 5xx | Retry avec backoff |

### Couts

Tarif iClosed (abonnement SaaS), pas de facturation a l'appel API. API comprise dans le plan.

## Patterns recommandes

1. **Client httpx centralise** avec `base_url`, `headers={"Authorization": f"Bearer {API_KEY}"}` (la cle inclut deja le prefixe `iclosed-`)
2. **Resolution lead multi-angle** : pour matcher un lead depuis le contexte extension :
   - Prio 1 : `previewId` si on l'a (URL iClosed)
   - Prio 2 : `meetCode` extrait du Meet → filter les calls `UPCOMING` + regex sur `locationLink`
   - Prio 3 : `inviteeEmails` + `dateFrom/dateTo` fenetre (+/- 15min autour de maintenant)
   - Prio 4 : `userIds` (closer) + `eventType=UPCOMING` + date proche
3. **Retry sur 429** : respecter `Retry-After` ; backoff exponentiel sur 5xx (max 3 retries)
4. **Pas de retry sur 4xx** (400, 401, 403, 404)
5. **Timeouts** : 10s pour GET, 15s pour POST outcome (validation lourde cote serveur)
6. **Cache leger** : liste des calls UPCOMING d'un closer peut etre cachee 30s cote backend pour eviter de hammer l'API sur chaque polling
7. **Logs** : toujours logger `eventCallId` + `outcome` lors d'un POST outcome (audit trail)
8. **Gestion `questions` + `secondaryAnswers`** : extraire en dict key-value pour alimenter le brief Claude (profil psychologique du prospect)

## Exemples de code

### Client service minimal

```python
import httpx
from config.config import settings

_client = httpx.AsyncClient(
    base_url="https://public.api.iclosed.io",
    headers={"Authorization": f"Bearer {settings.iclosed_api_key}"},
    timeout=10.0,
)

class IClosedError(Exception): ...
class IClosedNotFound(IClosedError): ...
class IClosedRateLimited(IClosedError): ...

async def list_calls(
    closer_user_ids: list[int] | None = None,
    event_type: str = "UPCOMING",
    date_from: str | None = None,
    date_to: str | None = None,
    preview_id: str | None = None,
    invitee_emails: list[str] | None = None,
    contact_id: int | None = None,
    limit: int = 20,
) -> dict:
    params = {"eventType": event_type, "limit": limit}
    if closer_user_ids:
        params["userIds"] = ",".join(str(i) for i in closer_user_ids)
    if date_from: params["dateFrom"] = date_from
    if date_to: params["dateTo"] = date_to
    if preview_id: params["previewId"] = preview_id
    if invitee_emails: params["inviteeEmails"] = ",".join(invitee_emails)
    if contact_id: params["contactId"] = contact_id

    response = await _client.get("/v1/eventCalls", params=params)
    if response.status_code == 429:
        raise IClosedRateLimited(response.headers.get("Retry-After", "1"))
    if response.status_code == 404:
        raise IClosedNotFound(f"No calls found: {params}")
    response.raise_for_status()
    return response.json()["data"]  # {"eventCalls": [...], "count": N}
```

### Resolve lead par meet_code

```python
import re

MEET_CODE_RE = re.compile(r"meet\.google\.com/([a-z]{3}-[a-z]{4}-[a-z]{3})", re.I)

async def resolve_by_meet_code(meet_code: str, closer_email: str) -> dict | None:
    """Find upcoming call matching a Google Meet code."""
    data = await list_calls(event_type="UPCOMING", limit=100)
    for call in data["eventCalls"]:
        link = call.get("locationLink") or ""
        match = MEET_CODE_RE.search(link)
        if match and match.group(1).lower() == meet_code.lower():
            if call.get("email", "").lower() == closer_email.lower():
                return call
    return None
```

### Push outcome (finalize)

```python
async def push_outcome(
    event_call_id: int,
    outcome: str,                  # WON | NO_SALE | APPROVED | REJECTED
    objection: str | None = None,  # MONEY | LOGISTIC | PARTNER | FEAR | SMOKE_SCREEN | NO_OBJECTION
    no_sale_reason: str | None = None,
    notes: str | None = None,
    deal_value: float | None = None,
    product_id: int | None = None,
    deal_date: str | None = None,
) -> dict:
    body = {"eventCallId": event_call_id, "outcome": outcome}
    if objection: body["objection"] = objection
    if no_sale_reason: body["noSaleReason"] = no_sale_reason
    if notes: body["notes"] = notes
    if outcome == "WON" and deal_value is not None:
        body["newDeal"] = {
            "value": deal_value,
            "transactionType": "WON",
            "productId": product_id,
            "date": deal_date,  # ISO 8601
        }
    response = await _client.post("/v1/outcomes", json=body, timeout=15.0)
    response.raise_for_status()
    return response.json()
```

## Variables d'environnement necessaires

| Variable | Description |
|----------|-------------|
| `ICLOSED_API_KEY` | Cle API iClosed, format `iclosed-<token>` (genere dans Settings > API). Le wrapper ajoute automatiquement `Bearer ` devant. |

## Notes importantes pour le projet HTR

- **Closer identification** : les closers HTR ont un email fixe. L'extension envoie `closer_email` au backend, qui resout le `userId` iClosed (via un cache email → userId rafraichi periodiquement, ou en filtrant les calls par `inviteeEmails` si le closer est aussi invitee).
- **Questionnaire HTR** : les reponses sont dans `secondaryAnswers`. Keys critiques pour le brief : situation actuelle, niveau montage video, revenu cible, heures dispo, delai objectif, blocage, budget, engagement presence.
- **Objections iClosed limitees** : enum stricte `MONEY | LOGISTIC | PARTNER | FEAR | SMOKE_SCREEN | NO_OBJECTION`. Pour des objections plus fines cote Closer Prep AI, les stocker en DB locale ET pousser l'enum mapping dans iClosed.
- **Status `PENDING_OUTCOME`** : indique qu'un call strategy attend que le closer push l'outcome — exactement notre UX post-call.
