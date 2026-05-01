# Meta / Instagram — Research

## Setup

1. `cp .env.example .env`
2. Remplir les variables (voir Credentials)

## Credentials

| Variable | Ou la trouver |
|----------|---------------|
| `INSTAGRAM_APP_ID` | developers.facebook.com > App > Instagram > Business login settings (PAS le Facebook App ID) |
| `INSTAGRAM_APP_SECRET` | Meme page que l'App ID (PAS le Facebook App Secret) |
| `INSTAGRAM_REDIRECT_URI` | HTTPS obligatoire — utiliser ngrok en dev |

## TL;DR

Instagram OAuth passe par **Instagram Business Login** (direct, pas Facebook Login).
Le flow Facebook Login necessite `pages_show_list` qui requiert d'etre "Tech Provider" Meta — a eviter.

---

## Prerequis

1. **Compte Instagram Professionnel** (Business ou Creator, pas personnel)
   - Instagram → Settings → For professionals → Switch to professional account
   - Rend le compte public automatiquement

2. **Page Facebook liee** (requise meme pour Instagram Login direct)
   - Creer une Page Facebook si inexistante
   - Page → Settings → Linked accounts → Instagram → Connect

3. **Meta Developer App** correctement configuree (voir section Setup ci-dessous)

---

## Setup de l'app Meta (etape par etape)

### Creation de l'app

1. Aller sur [developers.facebook.com](https://developers.facebook.com) → **Create App**
2. **Connect Business** → selectionner ou creer un portefeuille business → Next
3. **Choose Use Case** → selectionner **"Other"** → Next
   - ATTENTION : "Manage messages and content on Instagram" est le MAUVAIS use case pour OAuth + insights
   - "Other" est le seul qui donne acces au type Business avec Instagram Login
   - Note : Meta indique "this option is going away soon" — utiliser tant que disponible
4. **Select App Type** → selectionner **"Business"** → Next
5. Nom + email → Next

### Ajout du produit Instagram

6. Dashboard de l'app → chercher **"Instagram"** → cliquer **"Set up"**
7. Ca ajoute **"API setup with Instagram login"** dans la sidebar gauche

### Configuration du Business Login

8. Sidebar → **Instagram → API setup with Instagram login**
9. **Step 3 : "Set up Instagram business login"** → cliquer **"Business login settings"**
10. Ajouter le **Redirect URI** (ex: `https://xxxxx.ngrok-free.app/api/oauth/instagram/callback`)
    - HTTPS obligatoire — utiliser ngrok pour le dev local
11. Scopes disponibles dans la configuration :
    - `instagram_business_basic` (profil, media)
    - `instagram_business_manage_insights` (saves, reach, views, shares)
    - `instagram_business_content_publish` (publication)
    - `instagram_business_manage_messages` (DMs)
    - `instagram_business_manage_comments` (commentaires)

### Ajout de testeurs

12. Sidebar → **App Roles** → **Instagram Testers** → **Add Instagram Testers**
13. Entrer le username Instagram (ex: `hugo.processs`)
14. L'utilisateur doit **accepter l'invitation** sur Instagram :
    - Instagram → Settings → Apps and Websites → Tester Invites → Accept
    - ATTENTION : sans acceptation, erreur "Insufficient developer role"

---

## IDs et Secrets — NE PAS CONFONDRE

| Element | Ou le trouver | Usage |
|---------|---------------|-------|
| **Facebook App ID** | Dashboard → Settings → Basic (en haut) | PAS utilise pour Instagram Login |
| **Instagram App ID** | Instagram → API setup → Business login settings | `client_id` dans l'URL OAuth |
| **Facebook App Secret** | Dashboard → Settings → Basic | PAS utilise pour Instagram Login |
| **Instagram App Secret** | Instagram → API setup → Business login settings | `client_secret` pour le token exchange |

**Erreur courante** : utiliser le Facebook App ID/Secret au lieu de l'Instagram App ID/Secret → cause "Invalid platform app"

---

## Flow OAuth (Instagram Business Login)

### 1. Authorize

```
GET https://www.instagram.com/oauth/authorize
  ?client_id={INSTAGRAM_APP_ID}
  &redirect_uri={REDIRECT_URI}
  &response_type=code
  &scope=instagram_business_basic,instagram_business_manage_insights
  &state={STATE}
```

- `client_id` = **Instagram App ID** (PAS Facebook App ID)
- HTTPS obligatoire pour redirect_uri
- `state` : encoder le user_id dedans (le callback est public, pas de JWT)

### 2. Callback

Instagram redirige vers : `{REDIRECT_URI}?code={CODE}&state={STATE}#_`

**IMPORTANT** : le code a un suffix `#_` a retirer avant utilisation.

### 3. Token exchange (short-lived, 1h)

```
POST https://api.instagram.com/oauth/access_token
Content-Type: application/x-www-form-urlencoded (form-data, PAS JSON)

client_id={INSTAGRAM_APP_ID}
&client_secret={INSTAGRAM_APP_SECRET}
&grant_type=authorization_code
&redirect_uri={REDIRECT_URI}
&code={CODE}
```

Reponse :
```json
{
  "data": [{
    "access_token": "EAACEdEose0...",
    "user_id": "17841465934290948",
    "permissions": "instagram_business_basic,instagram_business_manage_insights"
  }]
}
```

Ou (format alternatif) :
```json
{
  "access_token": "EAACEdEose0...",
  "user_id": "17841465934290948",
  "permissions": "..."
}
```

### 4. Long-lived token (60 jours)

```
GET https://graph.instagram.com/access_token
  ?grant_type=ig_exchange_token
  &client_secret={INSTAGRAM_APP_SECRET}
  &access_token={SHORT_LIVED_TOKEN}
```

Reponse :
```json
{
  "access_token": "EAACEdEose0...",
  "token_type": "bearer",
  "expires_in": 5183944
}
```

### 5. Refresh (avant expiration, token doit avoir > 24h)

```
GET https://graph.instagram.com/refresh_access_token
  ?grant_type=ig_refresh_token
  &access_token={LONG_LIVED_TOKEN}
```

---

## Endpoints utiles (post-auth)

### Profil

```
GET https://graph.instagram.com/v22.0/me
  ?fields=user_id,username,name,profile_picture_url,followers_count,media_count,biography
  &access_token={TOKEN}
```

### Liste des media

```
GET https://graph.instagram.com/v22.0/{USER_ID}/media
  ?fields=id,caption,media_type,timestamp,permalink
  &limit=50
  &access_token={TOKEN}
```

Pagination par cursors (`after` / `before`).

### Insights par media

```
GET https://graph.instagram.com/v22.0/{MEDIA_ID}/insights
  ?metric={METRICS}
  &access_token={TOKEN}
```

Metriques par type de media :

| Metrique | Feed/Carousel | Reels | Stories |
|----------|:---:|:---:|:---:|
| `reach` | oui | oui | oui |
| `saved` | oui | oui | non |
| `shares` | oui | oui | oui |
| `likes` | oui | oui | non |
| `comments` | oui | oui | non |
| `views` | oui | oui | oui |
| `total_interactions` | oui | oui | oui |
| `ig_reels_avg_watch_time` | non | oui | non |
| `ig_reels_video_view_total_time` | non | oui | non |

### Insights account-level

```
GET https://graph.instagram.com/v22.0/{USER_ID}/insights
  ?metric=reach,views,accounts_engaged,total_interactions,follows_and_unfollows
  &period=day
  &since={YYYY-MM-DD}
  &until={YYYY-MM-DD}
  &access_token={TOKEN}
```

---

## Limites et pieges

| Piege | Detail |
|-------|--------|
| Rate limit | 200 calls/heure/token (surveiller header `X-App-Usage`) |
| Historique | 2 ans pour media insights, 90 jours pour demographics |
| Stories | Insights expirent apres 24h — necessite cron frequent |
| `impressions` | **Deprecie depuis avril 2025** — remplace par `views` |
| Retention Reels | Pas de courbe seconde par seconde — seulement avg watch time |
| Carousels | Pas d'insights pour les media individuels d'un carousel |
| Comptes < 100 followers | `follower_count` et `online_followers` indisponibles |
| Europe/Japon | `replies` retourne 0 (regulations privacy) |
| Token exchange | Doit etre en POST **form-data** (pas JSON, pas GET) |
| Code callback | A un suffix `#_` a retirer |
| App Review | Necessaire pour aller en production (multi-utilisateurs) |

---

## Erreurs courantes rencontrees

| Erreur | Cause | Solution |
|--------|-------|----------|
| "Invalid redirect_uri" | Redirect URI ne matche pas exactement le dashboard | Verifier caractere par caractere, HTTPS obligatoire |
| "Invalid platform app" | Mauvais `client_id` (Facebook au lieu d'Instagram) OU mauvais use case | Utiliser l'Instagram App ID + use case "Other" |
| "Error validating client secret" | Mauvais secret (Facebook au lieu d'Instagram) | Utiliser l'Instagram App Secret |
| "Insufficient developer role" | Compte pas ajoute comme testeur | App Roles → Instagram Testers + accepter l'invitation |
| "No Facebook Pages found" | Tentative d'utiliser le flow Facebook Login | Utiliser Instagram Business Login a la place |
| Page blanche / "page non disponible" | URL `www.instagram.com` avec Instagram App ID mais sans config | S'assurer que la configuration Business Login est creee |
| `pages_show_list` restricted | Necessite d'etre Tech Provider Meta | Utiliser Instagram Business Login (pas Facebook Login) |

---

## Variables d'environnement

```env
INSTAGRAM_APP_ID=              # Instagram App ID (PAS Facebook App ID)
INSTAGRAM_APP_SECRET=          # Instagram App Secret (PAS Facebook App Secret)
INSTAGRAM_REDIRECT_URI=        # HTTPS obligatoire (ngrok en dev)
```
