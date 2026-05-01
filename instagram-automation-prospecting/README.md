# Instagram Automation & Prospecting — Research

## Setup

1. `cp .env.example .env`
2. Remplir les variables selon le scenario choisi (voir Credentials)

## Credentials

| Variable | Ou la trouver |
|----------|---------------|
| `INSTAGRAM_USERNAME` | Username du compte Instagram source |
| `INSTAGRAM_PASSWORD` | Password du compte (stocke chiffre) |
| `PROXY_URL` | Proxy residentiel dedie (Oxylabs, Bright Data...) |
| `HIKERAPI_KEY` | https://hikerapi.com (Scenario B, production) |
| `UNIPILE_API_KEY` | https://unipile.com (lecture inbox managed, optionnel) |

> Recherche réalisée en avril 2026. Couvre : feed scraping, profile scraping, DM sending/reading, anti-bot.
> Pour l'API officielle Meta/Instagram (OAuth, Business API), voir `meta-instagram.md`.

---

## TL;DR — Recommandations Architecturales

| Besoin | Solution recommandée | Risque |
|--------|---------------------|--------|
| **Scraping profiles publics** | instagrapi (private API) + proxy résidentiel | Moyen |
| **Browsing du feed** | instagrapi `get_timeline_feed()` | Moyen |
| **Envoi DMs froids** | instagrapi `direct_send()` + warm-up progressif | Élevé |
| **Lecture inbox/conversations** | instagrapi `direct_threads()` + `direct_messages()` | Faible |
| **À grande échelle (>10 comptes)** | HikerAPI SaaS (managed) | Faible |
| **DMs officiels uniquement** | ManyChat / Meta Graph API (messages réactifs seulement) | Nul |

**Verdict principal** : Pour du cold prospecting avec DM, **instagrapi est le seul outil Python pratique en 2026**, mais il viole les CGU Instagram. L'approche commerciale la plus sûre est HikerAPI (SaaS managed) ou AutoReacher pour les campagnes.

---

## A. Python Libraries — Private/Unofficial API

### 1. instagrapi — RECOMMANDÉ

- **GitHub** : https://github.com/subzeroid/instagrapi
- **PyPI** : https://pypi.org/project/instagrapi/
- **Dernière version** : 2.2.1 (juillet 2025), 2.3.0 (février 2026)
- **Statut** : Activement maintenu — ~2170 commits, 6.1k stars, 895 forks
- **Python** : >= 3.9
- **Licence** : MIT

#### Capacités détaillées

**Feed / Timeline :**
```python
cl.get_timeline_feed(feed_type="cold_start_fetch")  # Première page
cl.get_timeline_feed(max_id=prev_next_max_id)       # Pagination (scroll)
```
- Retourne les posts du feed de l'utilisateur connecté
- Bug connu : `max_id` peut être ignoré dans certaines versions (issue #1789)

**Profile scraping :**
```python
cl.user_info_by_username("username")  # Bio, followers, following, posts
cl.user_info(user_id)                 # Par user_id
cl.user_followers(user_id, amount=100)
cl.user_following(user_id, amount=100)
```
- Inclut : bio, follower_count, following_count, media_count, is_verified, external_url

**Envoi de DMs :**
```python
cl.direct_send(text="Hello", user_ids=[123456])          # Cold DM à un user
cl.direct_answer(thread_id, text="Hello")                 # Répondre dans un thread
cl.direct_send_photo(path, user_ids=[123456])
cl.direct_send_video(path, user_ids=[123456])
cl.direct_media_share(media_id, user_ids=[123456])
cl.direct_story_share(story_id, user_ids=[123456])
cl.direct_profile_share(user_id, user_ids=[123456])
```

**Lecture inbox / conversations :**
```python
cl.direct_threads(amount=20)                     # Inbox (liste des threads)
cl.direct_pending_inbox(amount=20)               # Message requests
cl.direct_thread(thread_id, amount=20)           # Thread spécifique
cl.direct_messages(thread_id, amount=20)         # Messages dans un thread
cl.direct_search(query="username")               # Chercher un thread
cl.direct_thread_by_participants(user_ids=[...]) # Thread par participants
```

**Gestion threads :**
```python
cl.direct_thread_hide(thread_id)
cl.direct_message_delete(thread_id, message_id)
cl.direct_thread_mark_unread(thread_id)
cl.direct_thread_mute(thread_id)
```

#### Limitations connues

- Les auteurs eux-mêmes disent : *"instagrapi more suits for testing or research than a working business"*
- Risque de ban élevé en production sans proxy résidentiel + warm-up
- Recommandent HikerAPI pour usage en production
- Challenges 2FA / CAPTCHA à gérer manuellement
- Fonctionne avec le Mobile API Instagram (reverse-engineered)

#### Risque ban : **MOYEN-ÉLEVÉ**

---

### 2. aiograpi — Variante Async

- **GitHub** : https://github.com/subzeroid/aiograpi
- **PyPI** : https://pypi.org/project/aioinstagrapi/
- **Statut** : Maintenu par la même équipe (subzeroid), moins actif qu'instagrapi
- **Python** : >= 3.9 (async/await)
- **Mêmes capacités qu'instagrapi** mais en asyncio

Utile si le projet est entièrement async (FastAPI). Même niveau de risque.

---

### 3. instaloader — POUR SCRAPING PUBLIC UNIQUEMENT

- **Site** : https://instaloader.github.io/
- **PyPI** : https://pypi.org/project/instaloader/
- **Dernière version** : 4.15 (18 novembre 2025)
- **Statut** : Activement maintenu
- **Python** : >= 3.8

#### Capacités

- Téléchargement de posts, videos, Stories, Highlights, Reels
- Scraping profils publics (bio, compteurs)
- Scraping hashtags, locations
- **NE supporte PAS** : DM sending, DM reading, feed timeline browsing

#### Limitations critiques

- Rate limits stricts : ~1-2 req/30s en anonyme
- Accès limité aux données privées (stories, followers) même en authentifié
- Pas conçu pour l'automatisation de masse
- **Usage recommandé** : scraping ponctuel de profils publics, pas de DMs

#### Risque ban : **MOYEN** (compte peut être restreint en usage intensif)

---

### 4. instagram_private_api (ping) — ABANDONNÉ

- **GitHub** : https://github.com/ping/instagram_private_api
- **Statut** : **ABANDONNÉ** — dernier commit 2021, ne supporte plus les API Instagram actuelles
- **Verdict** : NE PAS UTILISER en 2026

---

## B. Outils Open Source Prospecting / Automation

### InstaPy — ABANDONNÉ

- **GitHub** : https://github.com/InstaPy/InstaPy
- **Statut** : Archived / Abandonné
- **Technologie** : Selenium-based
- **Verdict** : NE PAS UTILISER — trop vieux, Selenium trop détectable

### instagrapi-rest — REST Wrapper instagrapi

- **GitHub** : https://github.com/subzeroid/instagrapi-rest
- **Description** : API REST FastAPI wrappant instagrapi, deployable en container
- **Usage** : Permet d'exposer toutes les capacités instagrapi via HTTP
- **Utilité** : Pratique pour architectures microservices

### awesome-instagram-scrapers (référence)

- **GitHub** : https://github.com/The-Web-Scraping-Playbook/awesome-instagram-scrapers
- **Contenu** : Catalogue de scrapers — la majorité sont **non maintenus depuis 2023**
- **Verdict** : Tous les alternatives listées montrent "❌ Not maintained"

### DM Automation bots (GitHub)

La plupart des repos GitHub de DM bots sont des **projets étudiants** à risque élevé :
- `DhruvAthaide/Instagram-Messaging-Automation` — Selenium, haut risque
- `b31ngd3v/instagram-auto-dm` — Script basique, non maintenu
- `Oxlac/MR.DM` — Chrome extension, très risqué

**Verdict** : Aucun outil open source de prospecting complet et maintenu n'existe en dehors d'instagrapi.

---

## C. Browser Automation

### Approche Playwright / Puppeteer

**Principe** : Contrôler un vrai navigateur pour simuler des actions humaines.

**Stack anti-détection 2025-2026 :**
- `playwright-extra` + `playwright-stealth` plugin
- Fingerprint randomization (Canvas, WebGL, TLS)
- Mobile User-Agent + viewport mobile
- Delays aléatoires, scroll humain
- Proxies résidentiels rotatifs (pas datacenter)

**Avantages :**
- Peut tout faire qu'un humain : naviguer le feed, lire profils, envoyer DMs
- Pas limité par le reverse-engineering de l'API mobile

**Inconvénients :**
- **Détection sophistiquée** : Instagram analyse TLS fingerprint, HTTP/2 headers, Canvas/WebGL
- Chromium headless est détectable même avec stealth plugins en 2026
- Ressources lourdes (RAM/CPU par session)
- Maintenance élevée (Instagram change régulièrement son JS)

**Résumé détection** : Instagram en 2026 bloque les Chrome extensions immédiatement. Les approches headless browser sont détectées via :
1. TLS/SSL fingerprinting
2. HTTP/2 header ordering
3. Canvas/WebGL fingerprinting
4. Comportement de scroll (vitesse, patterns)
5. Fréquence des actions

**Verdict** : Playwright est une option mais complexe à maintenir et risquée. **instagrapi via Mobile API est moins détectable** qu'un browser headless.

---

## D. Outils Commerciaux (référence)

### HikerAPI — RECOMMANDÉ POUR PRODUCTION

- **Site** : https://hikerapi.com
- **Description** : SaaS géré par l'équipe d'instagrapi. Proxies, fingerprints, comptes managés inclus.
- **Volume** : 4-5 millions de requêtes/jour, 300 req/s
- **Pricing** : Pay-per-request, pas de subscription obligatoire
- **Endpoints** : 100+ endpoints (profils, DMs, feed, etc.)
- **Avantage clé** : Zéro maintenance anti-ban côté client
- **Intégration Python** : Via requests HTTP standard

**Cas d'usage recommandé** : Production avec >3 comptes ou >1000 profils/jour.

---

### PhantomBuster

- **Site** : https://phantombuster.com
- **Pricing** : $79/mo (Start) → $183/mo (Grow) → $505/mo (Scale)
- **Capacités Instagram** : Profile scraping, follower extraction, DM (limité)
- **API** : Oui — REST API pour lancer/monitorer les "Phantoms"
- **Intégration** : `apify-client` ou requests HTTP
- **Limitation** : Pas de cold DM direct à grande échelle, orienté LinkedIn
- **Verdict** : Bon pour scraping public, pas optimal pour prospecting DM Instagram

---

### AutoReacher

- **Site** : https://autoreacher.com
- **Description** : Plateforme SaaS spécialisée cold DM Instagram
- **Capacités** :
  - Scraping de leads (profils, followers, hashtags)
  - DM séquences multi-étapes personnalisées
  - AI replies automatiques
  - Multi-compte (100+ comptes)
  - Proxy mobile 5G inclus par compte
  - Warm-up automatique des comptes
- **Volume** : 120,000 DMs/mois maximum
- **API** : Non documentée publiquement
- **Méthode** : Unofficial Private API (similaire à instagrapi)
- **Risque** : MOYEN (warm-up + proxy inclus mitiguent)

---

### ReachOwl

- **Site** : https://reachowl.com
- **Description** : Chrome extension — automation via vraie session navigateur
- **Capacités** : DM automation, ciblage par bio keywords, followers/following
- **Méthode** : Browser session réelle (pas d'API)
- **Risque** : Instagram détecte les Chrome extensions — **BAN QUASI CERTAIN en 2026**
- **Verdict** : À ÉVITER

---

### ManyChat

- **Site** : https://manychat.com
- **Pricing** : Free tier + $15+/mo
- **Méthode** : **API officielle Meta (Messenger API)** — partenaire officiel Meta
- **Capacités** :
  - DM automatiques en réponse à commentaires/mentions stories
  - Séquences de nurturing
  - Collecte leads (email, phone)
  - Webhooks temps réel
- **Limitation critique** : **PAS de cold DM**. Peut uniquement contacter les utilisateurs qui ont interagi (commenté, mentionné) dans les 24 dernières heures.
- **Risque ban** : NUL (API officielle)
- **Verdict** : Excellent pour inbound/réactif, INUTILISABLE pour cold prospecting

---

### Apify (acteurs Instagram)

- **Site** : https://apify.com
- **Pricing** : Pay-per-use (compute units)
- **Acteurs disponibles** :
  - `apify/instagram-profile-scraper` : profils publics
  - `apify/instagram-scraper` : posts, hashtags
  - `apify/instagram-search-scraper` : recherche
- **API** : Oui — REST API + Python SDK (`apify-client`)
- **Limitation** : Données publiques uniquement, pas de DMs
- **Verdict** : Bon pour scraping de masse profils publics, pas pour DMs

---

### Expandi

- **Site** : https://expandi.io
- **Spécialité** : LinkedIn uniquement
- **Instagram** : NON
- **Verdict** : Hors scope

---

### Unipile — INTÉRESSANT POUR DM INBOX

- **Site** : https://www.unipile.com
- **Description** : API unifiée multi-canal (Instagram, LinkedIn, Gmail, Outlook...)
- **Capacités Instagram** :
  - Send & Receive DMs
  - List conversations/threads
  - Real-time webhooks (nouveaux messages)
  - Read receipts, réactions
  - Media (images, videos, voice notes)
- **Limitation** : Positionnée pour réception/gestion inbox (support/CRM), pas cold outreach
- **API** : REST + webhooks
- **Verdict** : Très pertinent pour la **lecture et gestion des conversations** en production

---

## E. Anti-Bot Instagram — État 2025-2026

### Rate Limits Officiels (Graph API)

| Action | Limite officielle |
|--------|-----------------|
| DMs automatisés | **200 DMs/heure** (réduit depuis 5000 en octobre 2024) |
| Fenêtre de message | 24h après interaction utilisateur uniquement |
| DM par utilisateur | 1 message automatisé / user / 24h |
| API calls | 200 calls/heure/token (`X-App-Usage` header) |

### Rate Limits Officieux (Private API / instagrapi)

Basés sur les retours communautaires 2025-2026 :

| Action | Limite safe | Limite absolue |
|--------|-------------|---------------|
| DMs froids/jour | 30-50 | ~150 |
| Profile views/heure | 50-100 | ~500 |
| Follows/jour | 50-100 | ~200 |
| Likes/heure | 30-50 | ~150 |
| Délai entre DMs | 30-120 secondes | minimum 10s |

### Ce qui déclenche les bans

**Bans immédiats :**
- Chrome extensions simulant des actions (détecté instantanément)
- IP datacenter non rotatives
- Actions sans délai (burst instantané)
- Compte neuf + actions immédiates (pas de warm-up)
- DMs en masse vers des comptes qui n'ont jamais interagi

**Bans progressifs (shadowban → restriction → suspension) :**
- >200 DMs/jour depuis la même IP
- Taux de réponse < 30% (signaux de spam)
- DM delivery rate < 70% (messages qui arrivent en "requests")
- Engagement artificiel détecté (likes/follows sans visites profilées)
- Plusieurs comptes depuis la même IP

**Indicators de détection en 2026 :**
1. TLS fingerprinting (Playwright/Selenium vs Mobile SDK)
2. HTTP/2 header ordering
3. Canvas/WebGL fingerprinting (browsers headless)
4. Patterns de comportement (vitesse, régularité parfaite)
5. Device fingerprint (instagrapi simule un appareil mobile)
6. Session age et historique du compte

### Meilleures pratiques anti-ban

```
Phase warm-up (nouveau compte) :
  Semaine 1-2 : Seulement navigation, likes manuels
  Semaine 3-4 : Follows/unfollows (<30/jour)
  Mois 2 : DMs progressifs (5/jour → 20/jour → 50/jour)
  Mois 3+ : Régime de croisière (30-80 DMs/jour)

Pendant l'automation :
  - Proxy résidentiel ou mobile dédié par compte
  - Délais aléatoires (30s-120s entre DMs)
  - Pause la nuit (pas d'action entre 23h-8h)
  - Varier les patterns (pas toujours même heure)
  - Session Instagram cohérente (browser fingerprint stable)
  - Éviter les IPs datacenter
```

---

## Matrice de Décision Finale

| Solution | Feed Scroll | Profile Scrape | DM Send | DM Read | Ban Risk | Maintenance | Coût |
|----------|:-----------:|:--------------:|:-------:|:-------:|:--------:|:-----------:|:----:|
| **instagrapi** | ✅ | ✅ | ✅ | ✅ | Moyen | Actif | Free |
| **aiograpi** | ✅ | ✅ | ✅ | ✅ | Moyen | Actif | Free |
| **instaloader** | ❌ | ✅ (public) | ❌ | ❌ | Faible | Actif | Free |
| **Playwright stealth** | ✅ | ✅ | ✅ | ✅ | Élevé | Manuel | Free |
| **HikerAPI** | ✅ | ✅ | ✅ | ✅ | Faible | SaaS | Pay/req |
| **AutoReacher** | ❌ | ✅ | ✅ | ✅ | Moyen | SaaS | Abonnement |
| **ManyChat** | ❌ | ❌ | ⚠️ réactif | ✅ | Nul | SaaS | $15+/mo |
| **Unipile** | ❌ | ❌ | ⚠️ limité | ✅ | Faible | SaaS | Pay/req |
| **PhantomBuster** | ❌ | ✅ | ❌ | ❌ | Faible | SaaS | $79+/mo |
| **Apify** | ❌ | ✅ (public) | ❌ | ❌ | Faible | SaaS | Pay/use |
| **ReachOwl** | ❌ | ✅ | ✅ | ✅ | Très élevé | SaaS | Abonnement |

**Légende** : ✅ = supporté | ❌ = non supporté | ⚠️ = partiel/conditionnel

---

## Architecture Recommandée pour le Projet

### Scenario A — DIY Python (risque assumé)

```
Stack :
  - instagrapi (feed, profiles, DMs)
  - Proxy résidentiel rotatif (Oxylabs, Bright Data, ou Oxylabs)
  - 1 proxy dédié par compte Instagram
  - Warm-up progressif (classe dédiée)
  - Rate limiter (délais aléatoires)
  - Session persistence (settings.json par compte)

Endpoints utilisés :
  cl.get_timeline_feed()           → collecter profils du feed
  cl.user_info_by_username()       → scraper profil
  cl.direct_send(user_ids=[...])   → envoyer DM froid
  cl.direct_threads()              → lire inbox
  cl.direct_messages(thread_id)    → lire conversation
```

### Scenario B — Hybrid (recommended pour production)

```
Stack :
  - HikerAPI pour feed/profile scraping (robuste, géré)
  - instagrapi pour DM sending (avec proxy dédié)
  - Unipile pour lecture/gestion inbox (webhooks temps réel)

Avantage : Sépare les risques. HikerAPI absorbe les bans de scraping.
```

### Scenario C — SaaS pur (si pas de dev)

```
  - AutoReacher : campagnes DM complètes
  - Apify : scraping profils publics en masse
  - ManyChat : nurturing conversationnel post-DM
```

---

## Variables d'Environnement Nécessaires

| Variable | Description |
|----------|-------------|
| `INSTAGRAM_USERNAME` | Username du compte source |
| `INSTAGRAM_PASSWORD` | Password (stocké chiffré) |
| `INSTAGRAM_SESSION_FILE` | Chemin vers le fichier session serialisé |
| `PROXY_URL` | Proxy résidentiel dédié (`http://user:pass@host:port`) |
| `HIKERAPI_KEY` | Clé API HikerAPI (si Scenario B) |
| `UNIPILE_API_KEY` | Clé Unipile (si lecture inbox managed) |

---

## Sources Consultées

- [instagrapi GitHub](https://github.com/subzeroid/instagrapi)
- [instagrapi Documentation](https://subzeroid.github.io/instagrapi/)
- [aiograpi GitHub](https://github.com/subzeroid/aiograpi)
- [instaloader Documentation](https://instaloader.github.io/)
- [HikerAPI](https://hikerapi.com)
- [Unipile Instagram DM API](https://www.unipile.com/instagram-dm-api-integration-for-saas/)
- [FlowGent — 12 Best Instagram DM Tools](https://flowgent.ai/blog/instagram-dm-automation-tool)
- [Instagram DM Rate Limits 2026](https://creatorflow.so/blog/instagram-api-rate-limits-explained/)
- [Instagram Ban Wave 2026](https://sumgenius.ai/blog/instagram-dm-bot-ban-wave-2026/)
- [How to Scrape Instagram 2026 — Scrapfly](https://scrapfly.io/blog/posts/how-to-scrape-instagram)
- [AutoReacher](https://autoreacher.com/)
- [ReachOwl](https://reachowl.com/)
- [awesome-instagram-scrapers](https://github.com/The-Web-Scraping-Playbook/awesome-instagram-scrapers)
