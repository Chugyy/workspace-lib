# Discord — Research

## OAuth2 (pour l'auth)

### Scopes necessaires

| Scope | Donne acces a |
|-------|---------------|
| `identify` | id, username, global_name, avatar hash, locale, etc. |
| `email` | email, verified |

Pour plus tard (bot) : `guilds` (serveurs du user), `guilds.members.read` (roles dans un serveur).

### Flow OAuth2 (Authorization Code Grant)

1. **Redirect** vers `https://discord.com/oauth2/authorize?response_type=code&client_id=X&scope=identify%20email&redirect_uri=X&state=CSRF_TOKEN`
2. **Callback** : Discord redirige vers `redirect_uri?code=AUTH_CODE&state=CSRF_TOKEN`
3. **Exchange** : `POST https://discord.com/api/oauth2/token` (content-type: `application/x-www-form-urlencoded`, PAS JSON)
4. **Fetch user** : `GET https://discord.com/api/v10/users/@me` avec `Authorization: Bearer ACCESS_TOKEN`

### Tokens

- Access token : **7 jours** (604800s)
- Refresh token : **n'expire jamais** (sauf revocation user, changement mot de passe)
- Revoquer l'un revoque les deux

### Rate limits

- 50 req/s par application
- 10 000 requetes invalides par 10 min = ban IP Cloudflare

### User object (champs utiles)

```json
{
  "id": "80351110224678912",       // discord_id (snowflake string)
  "username": "nelly",              // username unique
  "global_name": "Nelly",          // display name (nullable)
  "avatar": "8342729096ea...",     // hash (nullable)
  "email": "nelly@example.com",    // requires email scope
  "verified": true
}
```

**Avatar URL** : `https://cdn.discordapp.com/avatars/{id}/{hash}.png?size=256`
**Default avatar** : `https://cdn.discordapp.com/embed/avatars/{(int(id) >> 22) % 6}.png`

### Gotchas

1. Token/revoke endpoints = `application/x-www-form-urlencoded` UNIQUEMENT (pas JSON)
2. `state` param obligatoire pour CSRF
3. Avatar = hash, pas URL. Construire l'URL manuellement
4. Redirect URI doit matcher EXACTEMENT (trailing slash inclus)
5. `discriminator` deprecie — utiliser `global_name` ou `username`
6. Scopes separes par espace (pas virgule)

### Setup

1. https://discord.com/developers/applications → New Application
2. Tab OAuth2 → copier Client ID, generer Client Secret
3. Ajouter Redirect URI(s)

### Lib Python

Pas besoin de lib dediee — `httpx` (async) suffit pour 3 appels HTTP. `fastapi-discord` existe mais abstraction inutile.

---

## Bot Discord (pour plus tard)

### Capacites

- Lire les membres d'un serveur et leurs roles : OUI (intent `GUILD_MEMBERS` privilegiee)
- Mapper roles Discord → roles app : OUI (fetch roles du serveur, matcher par nom)
- Envoyer des DM : OUI (si bot et user partagent un serveur)
- Envoyer dans un channel : OUI (permissions `SEND_MESSAGES` + `VIEW_CHANNEL`)

### Intents necessaires

| Intent | Pourquoi | Privilegiee ? |
|--------|----------|---------------|
| `GUILD_MEMBERS` | Lire membres + roles | Oui |
| `MESSAGE_CONTENT` | Lire messages (pas besoin si slash commands) | Oui |

Recommandation : slash commands → pas besoin de `MESSAGE_CONTENT`.

### Lib Python

`discord.py` (le plus mature, communaute la plus large, maintenu activement).
Alternative : `Pycord` (meilleur support slash commands out-of-box).

### Meme application pour OAuth + Bot

**OUI.** Une seule Discord Application supporte les deux. Le bot token est separe des OAuth tokens.

---

## Variables d'env

| Variable | Source |
|----------|--------|
| `DISCORD_CLIENT_ID` | Discord Developer Portal → OAuth2 |
| `DISCORD_CLIENT_SECRET` | Discord Developer Portal → OAuth2 |
| `DISCORD_REDIRECT_URI` | URL callback de l'app |
| `DISCORD_BOT_TOKEN` | Discord Developer Portal → Bot (pour plus tard) |

## Champs DB pour la table users

- `discord_id` (text, unique)
- `discord_username` (text)
- `discord_display_name` (text, nullable)
- `discord_avatar_hash` (text, nullable)
- `discord_email` (text, nullable)
- `discord_access_token` (text)
- `discord_refresh_token` (text)
- `discord_token_expires_at` (timestamp)
