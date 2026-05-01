# Infrastructure

Documentation systeme obligatoire injectee dans tous les CLAUDE.md.
Ce contenu est maintenu par le systeme — NE PAS modifier directement dans les CLAUDE.md.
Source : `lib/CLAUDE.infrastructure.md` → `python3 registry.py build shared`

---

## Detection d'environnement

**En debut de conversation**, toujours executer :

```bash
python3 ../../lib/detect-env.py
```

Cela identifie l'appareil courant (VPS vs Mac vs Windows). Adapter le comportement en consequence :

| Device | Sync disponible | Push/Pull | Contexte |
|--------|----------------|-----------|----------|
| `vps`  | Oui (origin)   | Push OK   | Serveur distant — agents autonomes |
| `mac`  | Oui (origin)   | Push OK   | Machine locale, dev interactif |
| `windows` | Oui (origin) | Push OK  | Machine locale, dev interactif |

**Regles conditionnelles :**
- Sur **VPS** : ne PAS proposer `/sync` (on est deja sur le serveur). Proposer un `git commit + push` direct si pertinent.
- Sur **Mac/Windows** : proposer `/sync` pour pousser les changements vers le VPS.
- Sur **VPS** : les URLs de previsualisation montrees a l'utilisateur utilisent l'IP publique du VPS (detectee automatiquement par `detect-env.py`) au lieu de `localhost`. Les `curl` internes et health checks gardent `localhost`.

---

## Diagrammes

Quand tu veux illustrer une architecture, un flow, ou des relations entre composants, utilise **Mermaid** (bloc ` ```mermaid `). Le frontend rend ces blocs en SVG interactifs. Ne PAS utiliser d'ASCII art / box-drawing characters — ils ne s'affichent pas correctement.

---

## Fichiers proteges (`.claude/`)

Les outils `Write`, `Edit` et `cat >` sont bloques par Claude Code sur les fichiers dans `.claude/` (protection "sensitive file"). Si tu dois modifier un fichier dans `.claude/resources/`, `.claude/agents/`, ou `.claude/skills/` :

1. **Demander a l'utilisateur** : "Le fichier X est protege par Claude Code. Je peux contourner via Python — OK pour toi ?"
2. **Si oui**, utiliser Python via Bash pour lire, modifier et reecrire :

```bash
python3 -c "
from pathlib import Path
p = Path('.claude/resources/rules/mon-fichier.md')
c = p.read_text()
c = c.replace('ancien', 'nouveau')
p.write_text(c)
"
```

Ne JAMAIS bypass silencieusement — toujours demander avant.

---

## Ressources partagees

Deux registries indexent toutes les ressources disponibles dans le workspace. Ne pas maintenir de listes manuelles — toujours interroger les registries.

### Lib (`../../lib/`)

La lib contient les outils, agents, recherches et templates partages entre tous les PIDs. Chaque item a un `meta.yaml` avec un `id`, un `type` et une `description`.

**Types disponibles :**

| Type | Description | Utilisation |
|------|-------------|-------------|
| `tool` | CLI wrapper autour d'un service | `{cli} <action> [--profile name]` |
| `agent` | Agent IA autonome (PID dans `pids/`) | `agent-invoke ask {id} "prompt"` |
| `research` | Documentation d'un service externe | Lire le README.md pour integration |
| `template` | Projet de reference reutilisable | Copier et adapter |
| `profile` | Profil de base pour agents | Heritage de config |

**Interroger le registry :**

```bash
# Voir tout
cat ../../lib/registry.json | python3 -c "import sys,json; items=json.load(sys.stdin)['items']; [print(f\"{i['type']:10s} {i['id']:25s} {i['description']}\") for i in items]"

# Filtrer par type
cat ../../lib/registry.json | python3 -c "import sys,json; [print(i['id'],'-',i['description']) for i in json.load(sys.stdin)['items'] if i['type']=='tool']"

# Chercher par nom
grep -i "email" ../../lib/registry.json
```

**Utiliser un outil CLI :**

Les CLIs de la lib sont disponibles globalement via PATH (injecte par ecosystem.config.js).

```bash
# Pattern general — appel direct, pas besoin de cd
<cli-command> <action> [--arg value ...]

# Avec un profil specifique (multi-instance)
<cli-command> <action> --profile mon-profil

# Voir les commandes disponibles
<cli-command> --help

# Si l'outil n'est pas dans le PATH (setup initial)
cd ../../lib/<tool-id> && ./setup.sh
```

**Resolution des credentials** : chaque CLI charge automatiquement ses credentials depuis le systeme de profils (`lib/.profiles/`). Voir la section "Systeme de profils" ci-dessous.

### Context store (`../../context/`)

Le context store est la **memoire factuelle partagee** entre tous les agents et PIDs. Il contient tout ce qui est vrai et durable : clients, contacts, projets, strategies, specs, notes, rapports. C'est la source de verite pour les faits — pas les preferences (CLAUDE.md), pas le code (git), pas les conversations (ephemeres).

**Principe** : stockage plat en markdown avec frontmatter YAML. Un fichier = une entite. Le registry (`context/registry.json`) est auto-genere et indexe toutes les entites + un graphe de relations bidirectionnel.

**Types disponibles** (definis dans `context/types.yaml`) :

| Categorie | Types | Usage |
|-----------|-------|-------|
| `permanent` | identity, objectives, constraints, strategy, clients, projects | Rarement modifie, fondamental |
| `on-demand` | client, contact, project, spec, note | Cree au besoin, lie a un contexte |
| `flux` | call, email, message, report | Evenements ponctuels, flux continu |
| `personal` | health | Donnees personnelles |

#### Lire le context store

```bash
# Recherche par mot-cle dans les fichiers
grep -ri "terme" ../../context/store/

# Voir toutes les entites indexees
cat ../../context/registry.json | python3 -c "import sys,json; [print(f\"{e['type']:25s} {e['id']:30s} {e['status']}\") for e in json.load(sys.stdin)['entities']]"

# Voir les relations d'une entite
cat ../../context/registry.json | python3 -c "import sys,json; g=json.load(sys.stdin)['graph']; print(g.get('entity-id', []))"

# Recherche complexe (croisement, synthese) — deleguer a l'agent context-search
agent-invoke ask context-search "Trouve tout ce qu'on sait sur HTR"
```

#### Creer une entite

1. **Creer le fichier** `../../context/store/{id}.md` avec le frontmatter obligatoire :

```markdown
---
id: client-acme
type: on-demand/client
created: 2026-04-25
updated: 2026-04-25
status: active
refs: [contact-john, project-acme-website]
scope: global
---

# Client : ACME Corp

Contenu libre en markdown. Les mentions @contact-john dans le texte
sont auto-detectees et ajoutees au graphe de relations.
```

**Champs obligatoires du frontmatter :**

| Champ | Format | Description |
|-------|--------|-------------|
| `id` | kebab-case | Identifiant unique, = nom du fichier sans `.md` |
| `type` | `categorie/sous-type` | Un type valide de `types.yaml` |
| `created` | `YYYY-MM-DD` | Date de creation |
| `updated` | `YYYY-MM-DD` | Date de derniere modification |
| `status` | `active`, `draft`, `archived`, `closing` | Etat du cycle de vie |
| `refs` | liste YAML `[id-1, id-2]` | References explicites a d'autres entites |
| `scope` | `global` | Toujours `global` (reserve pour usage futur) |

**Conventions de nommage** (id et fichier) :
- Clients : `client-{nom}` → `client-acme.md`
- Contacts : `contact-{prenom}` → `contact-john.md`
- Projets : `project-{nom}` → `project-acme-website.md`
- Specs : `{sujet}` → `htr-weight-system.md`
- Notes : `note-{sujet}` → `note-refonte-backend.md`

2. **Reconstruire le registry** apres creation/modification :

```bash
cd ../../ && python3 registry.py build context
```

Cela re-scanne `context/store/*.md`, valide les frontmatters, extrait les `@mentions` du contenu, et reconstruit le graphe bidirectionnel.

#### Lier des entites

Deux mecanismes (les deux sont fusionnes automatiquement dans le graphe) :

1. **Refs explicites** (frontmatter) — pour les relations structurelles connues a la creation :
```yaml
refs: [client-htr, project-contentos]
```

2. **@mentions** (contenu) — pour les references naturelles dans le texte :
```markdown
Discussion avec @contact-kilian sur le projet @project-htr-platform.
```

Le registry builder extrait les `@mentions` via regex (`@[\w-]+`) et les fusionne avec les `refs` du frontmatter. Le graphe est **bidirectionnel** : si A reference B, alors B connait A automatiquement.

#### Modifier une entite existante

1. **Editer le fichier** `../../context/store/{id}.md`
2. **Mettre a jour le champ `updated`** dans le frontmatter avec la date du jour
3. **Ajouter/retirer des `refs`** si les relations changent
4. **Reconstruire** : `cd ../../ && python3 registry.py build context`

#### Archiver une entite

Ne pas supprimer le fichier — changer le `status` a `archived` et reconstruire. Les entites archivees restent dans le graphe mais sont filtrees par les agents.

#### Quand creer une entite

| Situation | Action |
|-----------|--------|
| Nouveau client identifie | Creer `client-{nom}` + `contact-{prenom}` pour chaque interlocuteur |
| Nouveau projet demarre | Creer `project-{nom}`, lier au client |
| Spec technique importante | Creer `on-demand/spec`, lier au projet |
| Appel ou email significatif | Creer `flux/call` ou `flux/email`, lier au contact |
| Decision strategique | Modifier les entites `permanent/` existantes |
| Information factuelle a retenir | `on-demand/note` |

**Ne PAS creer d'entite pour** : les preferences de dev (→ CLAUDE.md), les bugs (→ issues git), les taches (→ todo), les conversations ephemeres.

### Agents partages

Les agents autonomes vivent dans `pids/` et sont invocables via `agent-invoke` depuis n'importe quel PID.

**IMPORTANT** : Toujours invoquer directement via Bash. Ne PAS lancer un sub-agent (Agent tool) pour executer agent-invoke.

```bash
agent-invoke ask <agent> "prompt"                  # one-shot
agent-invoke chat <agent> "prompt"                 # session persistante
agent-invoke resume <session-id> "follow-up"       # reprendre
agent-invoke agents                                # lister les agents disponibles
agent-invoke sessions                              # lister les sessions
```

---

## Systeme de profils (credentials)

Les credentials des outils CLI sont gerees par un **systeme de profils** centralise dans `lib/.profiles/`. Le code (lib/) est separe des credentials (profiles/). Chaque outil peut avoir plusieurs profils (multi-instance).

### Structure

```
lib/.profiles/
├── resolver.py         # Module de resolution (commite)
├── .gitignore          # Ignore les sous-dossiers (credentials)
├── telegram/
│   ├── default.json    # Profil "default"
│   ├── bot-support.json # Profil alternatif
│   └── _default        # Contient "default\n"
├── email/
│   ├── default.json
│   └── _default
└── whatsapp/
    ├── default.json
    └── _default
```

### Chaine de resolution

Quand un CLI charge ses credentials, le resolver suit cet ordre :

1. **`--profile name`** — argument explicite passe au CLI
2. **`<TOOL_ID>_PROFILE=name`** — variable d'environnement (utile dans les handler actions)
3. **`_default`** — fichier marqueur dans le dossier du tool
4. **Profil unique** — si un seul `.json` existe, il est utilise automatiquement

### Gerer les profils

```bash
# Lister tous les outils et leurs profils
profile list

# Lister les profils d'un outil
profile list telegram

# Voir la config d'un profil (secrets masques)
profile show telegram default

# Voir avec les secrets en clair
profile show telegram default --secrets

# Creer un profil (interactif, lit meta.yaml)
profile add telegram bot-support

# Importer depuis un config.json ou .env existant
profile import telegram default

# Changer le profil par defaut
profile set-default telegram bot-support

# Supprimer un profil
profile remove telegram bot-support
```

### Utiliser un profil dans un script / handler action

```python
# Depuis un handler action ou un script Python
import sys
from pathlib import Path
sys.path.insert(0, str(Path("/data/workspace/lib/.profiles")))
from resolver import resolve

config = resolve("email")                   # profil par defaut
config = resolve("email", "newsletter")     # profil specifique
```

```bash
# Depuis un script shell — utiliser le CLI directement
email send --to "user@example.com" --subject "Test" --body "Hello"

# Forcer un profil via env var (utile dans ecosystem.config.js)
EMAIL_PROFILE=newsletter email send --to "user@example.com" --subject "Test" --body "Hello"
```

### Convention pour les CLIs

Chaque CLI de la lib qui a besoin de credentials DOIT :

1. Importer le resolver au demarrage :
```python
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / ".profiles"))
```

2. Ajouter un callback `--profile` / `-p` :
```python
_profile_name: Optional[str] = None

@app.callback()
def main(profile: Optional[str] = typer.Option(None, "--profile", "-p")):
    global _profile_name
    _profile_name = profile
```

3. Resoudre via `resolve(tool_id, _profile_name)` avec fallback legacy

---

## Infrastructure AI Manager

L'AI Manager fournit des capacites reutilisables par tous les PIDs :

### Interactive Cards (notifications structurees)

Une action handler peut creer une **conversation interactive** avec des cards structurees : texte markdown, formulaires (text, textarea, select, toggle, date, number), grilles cle/valeur, et boutons d'action.

Les boutons supportent 4 types d'action :
- **webhook** — POST/PUT/DELETE vers une URL
- **event** — cree un event dans l'aggregator (boucle de retour)
- **resolve** — marque la conversation comme resolue
- **link** — ouvre une URL

**Quand utiliser** : quand un event necessite une reponse humaine structuree (validation, choix, formulaire) plutot qu'un simple log ou une conversation libre.

**Doc complete** : `rules/use-cases/handler-action.md` (section Interactive Cards)

**Exemple minimal** depuis un script d'action :

```python
import httpx, os

BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:4810")
BACKEND_KEY = os.environ.get("BACKEND_INTERNAL_KEY", "proxy-internal-key")

httpx.post(f"{BACKEND_URL}/api/conversations", 
    headers={"X-Internal-Key": BACKEND_KEY},
    json={
        "pid": "system", "model": "claude-sonnet-4-20250514",
        "initiated_by": "proxy",
        "first_message": {
            "content": "Titre de la notification",
            "interactive": {
                "body": [
                    {"type": "text", "text": "**Details**", "weight": "bold"},
                    {"type": "input", "id": "reply", "input_type": "textarea", "label": "Reponse"}
                ],
                "actions": [
                    {"id": "ok", "label": "Valider", "style": "primary", 
                     "action": {"type": "event", "source": "interactive:mon-pid", "event_type": "reply.sent"},
                     "inputs": "all", "resolves": True},
                    {"id": "skip", "label": "Ignorer", "style": "ghost", "action": {"type": "resolve"}}
                ]
            }
        }
    })
```

### Personal Cloud (stockage de fichiers)

Personal Cloud est une API de stockage de fichiers (type S3) integree a l'AI Manager. Elle permet a tout PID ou service de stocker et recuperer des fichiers via une API REST avec presigned URLs.

**URL interne** : `http://127.0.0.1:8200` (ou via `PERSONAL_CLOUD_URL` dans le `.env` du backend)

**Authentification** : header `Authorization: Bearer sk_live_...` (API key par service, creee via l'admin API)

**Endpoints principaux :**

| Methode | Endpoint | Description |
|---------|----------|-------------|
| `PUT` | `/v1/objects/{key}` | Upload un fichier (multipart) |
| `GET` | `/v1/objects/{key}` | Download un fichier |
| `DELETE` | `/v1/objects/{key}` | Supprime un fichier |
| `GET` | `/v1/objects?prefix=...` | Liste les objets (pagination par cursor) |
| `POST` | `/v1/presign` | Genere une URL presignee (upload ou download sans API key) |
| `PATCH` | `/v1/objects/{key}` | Modifie visibilite/metadata |

**Presigned URLs** : permettent un acces temporaire sans API key. Utile pour servir des fichiers dans un frontend ou partager un lien.

```python
import httpx

CLOUD_URL = "http://127.0.0.1:8200"
API_KEY = "sk_live_..."

# Upload
with open("photo.jpg", "rb") as f:
    httpx.put(f"{CLOUD_URL}/v1/objects/photos/photo.jpg",
        headers={"Authorization": f"Bearer {API_KEY}"},
        files={"file": ("photo.jpg", f, "image/jpeg")})

# Presigned download URL (valide 1h)
resp = httpx.post(f"{CLOUD_URL}/v1/presign",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={"method": "GET", "key": "photos/photo.jpg", "expires_in": 3600})
url = resp.json()["url"]  # URL accessible sans auth
```

**Multi-tenant** : chaque API key est liee a un `service_id`. Les objets sont isoles par service. Un service ne voit que ses propres fichiers.

---

## Standards — Contrats obligatoires

Ces standards s'appliquent a TOUT agent qui cree ou modifie un element du workspace.
Violation = rejet. Pas d'exception.

### Standard : Outil de la lib (`../../lib/{tool-id}/`)

Chaque outil de la lib DOIT respecter cette structure :

```
lib/tool-id/
├── meta.yaml           # OBLIGATOIRE — identite et dependances
├── README.md           # OBLIGATOIRE — guide d'utilisation (lisible par IA et humain)
├── .gitignore          # OBLIGATOIRE — au minimum : .env, .venv/, tmp/
├── setup.sh            # OBLIGATOIRE si l'outil a des dependances a installer
├── inputs/             # OPTIONNEL — fichiers d'entree (contenu gitignore, .gitkeep commite)
│   └── .gitkeep
├── outputs/            # OPTIONNEL — fichiers de sortie (contenu gitignore, .gitkeep commite)
│   └── .gitkeep
├── downloads/          # OPTIONNEL — fichiers telecharges (contenu gitignore, .gitkeep commite)
│   └── .gitkeep
└── tmp/                # OPTIONNEL — fichiers temporaires (entierement gitignore, pas de .gitkeep)
```

**Credentials** : gerees par le systeme de profils (`lib/.profiles/`), PAS par des `.env` dans le dossier de l'outil. Le `meta.yaml` declare les variables requises dans `requires.env` — le CLI `profile add` les utilise pour le setup interactif.

**meta.yaml obligatoire :**

```yaml
id: tool-id              # kebab-case, = nom du dossier
type: tool               # tool | research | template | agent | profile
description: >
  Une phrase qui decrit ce que fait l'outil.
requires:
  env:                   # Variables d'env necessaires (cles de la .env.example)
    - VAR_NAME: "Ou la trouver / comment l'obtenir"
  system:                # Dependances systeme
    - python3
  setup: "pip install -r requirements.txt"   # Commande d'installation
```

**README.md obligatoire — structure minimale :**

```markdown
# Tool Name

Ce que fait l'outil en une phrase.

## Setup

1. `./setup.sh`
2. `profile add tool-id default` (configure les credentials)

## Credentials

| Variable | Ou la trouver |
|----------|---------------|
| `API_KEY` | https://example.com/settings → API |

## Usage

\`\`\`bash
cli action --arg value
cli action --profile other-profile
\`\`\`

## Inputs / Outputs

- **inputs/** : [description des fichiers attendus]
- **outputs/** : [description des fichiers produits]
```

**INTERDIT dans la lib :**
- `.env` commite (credentials reelles)
- `.venv/` commite
- `assets/config.json` avec credentials (legacy — utiliser le systeme de profils)
- Credentials hardcodees dans le code source
- Fichiers de donnees personnelles (transcriptions, resultats specifiques a un utilisateur)

### Standard : PID (`../../pids/{pid-name}/`)

Chaque PID DOIT avoir :

```
pids/pid-name/
├── .claude/
│   ├── CLAUDE.md           # OBLIGATOIRE — instructions de l'agent
│   ├── .env.example        # OBLIGATOIRE — credentials necessaires avec commentaires d'aide
│   ├── README.md           # OBLIGATOIRE — guide d'onboarding
│   ├── build.py            # OBLIGATOIRE — genere .mcp.json depuis .env + .mcp.json.example
│   ├── agents/             # OPTIONNEL — agents specialises
│   ├── skills/             # OPTIONNEL — skills disponibles
│   └── resources/          # OPTIONNEL — rules, templates, scripts
├── .mcp.json.example       # OBLIGATOIRE — config MCP avec placeholders ${VAR}
└── [runtime data]          # GITIGNORE — projets, outputs, donnees personnelles
```

**`.mcp.json.example`** utilise des placeholders `${VAR}` qui sont remplaces par `build.py` depuis `.claude/.env` :

```json
{
  "mcpServers": {
    "example": {
      "command": "npx",
      "args": ["-y", "example-mcp"],
      "env": {
        "API_KEY": "${EXAMPLE_API_KEY}"
      },
      "_comment": "Description + ou trouver la cle."
    }
  }
}
```

**INTERDIT dans un PID :**
- `.claude/.env` commite (credentials reelles)
- `.mcp.json` commite (genere par build.py, contient des credentials)
- Donnees runtime commitees (projets, outputs, bases de donnees)

### Standard : Entite du context store (`../../context/store/`)

Voir la section "Creer une entite" ci-dessus. Rappel du contrat :
- Frontmatter YAML obligatoire : `id`, `type`, `created`, `updated`, `status`, `refs`, `scope`
- Un fichier = une entite
- `id` = nom du fichier sans `.md`
- Reconstruire le registry apres creation : `cd ../../ && python3 registry.py build context`

### Standard : Recherche service externe (`../../lib/{service}/`)

Quand le skill `/research` cree une documentation de service externe :

```
lib/service-name/
├── meta.yaml           # type: research
├── README.md           # Documentation complete du service
├── .env.example        # Credentials necessaires pour l'integration
└── .gitignore          # .env, .venv/
```

Le README d'une research sert de **spec d'integration** pour l'agent `build-service`. Il doit contenir :
- Ce que fait le service
- Les endpoints / SDK utilises
- Les limites et quotas
- Les exemples de code

### Verification : checklist avant commit

Avant de commiter un nouvel outil ou PID, verifier :

- [ ] `meta.yaml` present et complet (lib) ou `CLAUDE.md` present (PID)
- [ ] `README.md` present avec section Setup + Credentials
- [ ] `.gitignore` present et couvre `.env`, `.venv/`, `tmp/`, outputs
- [ ] Aucune credential hardcodee dans le code (`grep -r "sk-\|ghp_\|xoxb-" .`)
- [ ] `setup.sh` present si des dependances sont a installer
- [ ] Dossiers `inputs/`, `outputs/` avec `.gitkeep` si utilises
- [ ] `build.py` present dans le PID (genere .mcp.json)
- [ ] CLI integre le resolver de profils si l'outil a besoin de credentials
- [ ] `meta.yaml` `requires.env` liste les variables pour `profile add`
