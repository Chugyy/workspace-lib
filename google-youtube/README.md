# Google / YouTube — Research

## TL;DR

YouTube OAuth passe par Google OAuth 2.0 standard. Deux APIs :
- **YouTube Data API v3** : metadata videos + trending (API Key suffit pour les donnees publiques)
- **YouTube Analytics API v2** : metriques privees du createur (OAuth obligatoire)

---

## Prerequis

1. **Projet Google Cloud** sur [console.cloud.google.com](https://console.cloud.google.com)
2. **APIs activees** dans le projet :
   - YouTube Data API v3
   - YouTube Analytics API
3. **Ecran de consentement OAuth** configure
4. **Identifiants OAuth 2.0** crees (Client ID + Secret)

---

## Setup Google Cloud (etape par etape)

### Creation du projet

1. [console.cloud.google.com](https://console.cloud.google.com) → **New Project** → nom (ex: "ContentOS") → Create
2. Selectionner le projet dans le dropdown en haut

### Activer les APIs

3. **APIs & Services** → **Library**
4. Chercher **"YouTube Data API v3"** → **Enable**
5. Chercher **"YouTube Analytics API"** → **Enable**

### Ecran de consentement OAuth

6. **APIs & Services** → **OAuth consent screen**
7. **User Type** : External → Create
8. App name, user support email, developer email → Save
9. **Scopes** : ajouter `youtube.readonly` et `yt-analytics.readonly` → Save
10. **Test users** → **Add users** → ajouter ton email Google
    - ATTENTION : sans ca, erreur "access_denied" 403
11. Save

### Identifiants OAuth

12. **APIs & Services** → **Credentials** → **Create credentials** → **OAuth client ID**
13. Application type : **Web application**
14. Name : "ContentOS"
15. **Authorized redirect URIs** → Add :
    - `http://localhost:3000/api/oauth/youtube/callback` (dev)
    - `https://contentos.multimodal-house.fr/api/oauth/youtube/callback` (prod)
    - Google accepte localhost en HTTP (contrairement a Meta)
16. Create → copier **Client ID** et **Client Secret**

### API Key (pour trending, pas OAuth)

17. **APIs & Services** → **Credentials** → **Create credentials** → **API Key**
18. (Recommande) **Restrict key** → limiter a "YouTube Data API v3" uniquement

---

## Flow OAuth 2.0

### 1. Authorize

```
GET https://accounts.google.com/o/oauth2/v2/auth
  ?client_id={CLIENT_ID}
  &redirect_uri={REDIRECT_URI}
  &response_type=code
  &scope=https://www.googleapis.com/auth/youtube.readonly https://www.googleapis.com/auth/yt-analytics.readonly
  &access_type=offline
  &prompt=consent
  &include_granted_scopes=true
  &state={STATE}
```

**IMPORTANT** :
- `access_type=offline` : obligatoire pour obtenir un refresh_token
- `prompt=consent` : obligatoire pour obtenir le refresh_token a chaque fois (sinon Google ne le renvoie qu'a la premiere auth)
- Les scopes sont separes par des **espaces** (pas des virgules)

### 2. Callback

Google redirige vers : `{REDIRECT_URI}?code={CODE}&state={STATE}&scope={SCOPES}`

### 3. Token exchange

```
POST https://oauth2.googleapis.com/token
Content-Type: application/x-www-form-urlencoded

client_id={CLIENT_ID}
&client_secret={CLIENT_SECRET}
&code={CODE}
&grant_type=authorization_code
&redirect_uri={REDIRECT_URI}
```

Reponse :
```json
{
  "access_token": "ya29.a0AfH...",
  "expires_in": 3600,
  "refresh_token": "1//0eXx...",
  "scope": "https://www.googleapis.com/auth/youtube.readonly https://www.googleapis.com/auth/yt-analytics.readonly",
  "token_type": "Bearer"
}
```

### 4. Refresh token

```
POST https://oauth2.googleapis.com/token
Content-Type: application/x-www-form-urlencoded

client_id={CLIENT_ID}
&client_secret={CLIENT_SECRET}
&refresh_token={REFRESH_TOKEN}
&grant_type=refresh_token
```

Reponse (PAS de nouveau refresh_token, reutiliser l'ancien) :
```json
{
  "access_token": "ya29.a0AfH...",
  "expires_in": 3600,
  "scope": "...",
  "token_type": "Bearer"
}
```

---

## Endpoints utiles

### Channel info (Data API v3)

```
GET https://www.googleapis.com/youtube/v3/channels
  ?part=snippet,statistics
  &mine=true
  &access_token={TOKEN}
```

Retourne : channel_id, title, subscriber_count, video_count, view_count

### Channel metrics par jour (Analytics API v2)

```
GET https://youtubeanalytics.googleapis.com/v2/reports
  ?ids=channel==MINE
  &startDate=2026-01-01
  &endDate=2026-04-09
  &dimensions=day
  &metrics=views,estimatedMinutesWatched,averageViewDuration,subscribersGained,subscribersLost,likes,shares,comments
  &access_token={TOKEN}
```

### Metriques par video (Analytics API v2)

```
GET https://youtubeanalytics.googleapis.com/v2/reports
  ?ids=channel==MINE
  &filters=video=={VIDEO_ID}
  &startDate=2026-01-01
  &endDate=2026-04-09
  &metrics=views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,impressions,impressionsClickThroughRate,subscribersGained,subscribersLost,likes,shares,comments
  &access_token={TOKEN}
```

### Courbe de retention (Analytics API v2)

```
GET https://youtubeanalytics.googleapis.com/v2/reports
  ?ids=channel==MINE
  &filters=video=={VIDEO_ID}
  &dimensions=elapsedVideoTimeRatio
  &metrics=audienceWatchRatio,relativeRetentionPerformance
  &access_token={TOKEN}
```

Retourne 100 points (0.0 a 1.0) avec le ratio de retention a chaque point.

### Trending FR (Data API v3 — API Key, pas OAuth)

```
GET https://www.googleapis.com/youtube/v3/videos
  ?chart=mostPopular
  &regionCode=FR
  &part=snippet,statistics,contentDetails
  &maxResults=50
  &videoCategoryId={CATEGORY_ID}  (optionnel)
  &key={API_KEY}
```

### Categories (Data API v3 — API Key)

```
GET https://www.googleapis.com/youtube/v3/videoCategories
  ?regionCode=FR
  &hl=fr
  &part=snippet
  &key={API_KEY}
```

---

## Limites et quotas

| API | Quota | Detail |
|-----|-------|--------|
| YouTube Data API v3 | 10 000 units/jour | `videos.list` = 1 unit, `search.list` = 100 units (eviter) |
| YouTube Analytics API v2 | ~1 unit/requete | Quota genereux, pas de limite documentee stricte |
| Trending poll | ~2 units/appel | 50 videos * 1 unit. Budget : 96 units/jour pour 1 poll/15min |

### Tokens

| Type | Duree | Notes |
|------|-------|-------|
| Access token | 1 heure | Refresh automatique via refresh_token |
| Refresh token (Testing) | **7 jours** | App en mode Testing dans Google Cloud |
| Refresh token (Production) | Long-lived | Publier l'app pour des tokens persistants |

**ATTENTION** : en mode Testing, le refresh token expire apres 7 jours. Pour des tokens long-lived, passer l'app en mode **Published** (pas besoin de verification Google pour un usage interne — juste changer le statut).

---

## Erreurs courantes rencontrees

| Erreur | Cause | Solution |
|--------|-------|----------|
| "access_denied" 403 | Email pas ajoute comme test user | OAuth consent screen → Test users → Add |
| "ContentOS n'a pas termine la procedure de validation" | Meme chose — app en Testing sans test user | Ajouter l'email Google du user |
| Pas de refresh_token dans la reponse | `prompt=consent` manquant dans l'authorize URL | Ajouter `prompt=consent` |
| refresh_token expire apres 7 jours | App en mode Testing | Passer en mode Published |
| "Invalid redirect_uri" | URI pas dans les Authorized redirect URIs | Ajouter dans Credentials → OAuth client → Redirect URIs |
| `categoryId` en string | YouTube Data API retourne categoryId en string | Caster en int avant INSERT en DB |
| `publishedAt` en string | YouTube retourne ISO 8601 string | Parser avec `datetime.fromisoformat()` |
| Duration en ISO 8601 | `PT4M13S` au lieu de secondes | Parser avec regex : `PT(\d+H)?(\d+M)?(\d+S)?` |

---

## Variables d'environnement

```env
# OAuth (pour Analytics — donnees privees du createur)
YOUTUBE_CLIENT_ID=             # Google Cloud OAuth Client ID
YOUTUBE_CLIENT_SECRET=         # Google Cloud OAuth Client Secret
YOUTUBE_REDIRECT_URI=          # http://localhost:3000/... en dev (HTTP accepte par Google)

# API Key (pour Trending — donnees publiques)
YOUTUBE_API_KEY=               # Google Cloud API Key (restreindre a YouTube Data API v3)
```

---

## Difference entre les deux APIs

| | YouTube Data API v3 | YouTube Analytics API v2 |
|---|---|---|
| **Auth** | API Key (public) ou OAuth (prive) | OAuth uniquement |
| **Donnees** | Metadata videos, channels, trending | Metriques : views, watch time, retention, CTR |
| **Usage** | Trending, search, video info | Analytics createur |
| **Quota** | 10 000 units/jour | Genereux, ~1 unit/req |
| **Scope** | `youtube.readonly` | `yt-analytics.readonly` |
