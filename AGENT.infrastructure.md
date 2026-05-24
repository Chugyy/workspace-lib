# Infrastructure

Documentation systeme obligatoire injectee dans tous les AGENT.md.
Ce contenu est maintenu par le systeme — NE PAS modifier directement dans les AGENT.md.
Source : `lib/AGENT.infrastructure.md` → `python3 registry.py build shared`

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

## Ressources partagees

Deux registries indexent toutes les ressources disponibles dans le workspace. Ne pas maintenir de listes manuelles — toujours interroger les registries.

### Lib (`../../lib/`)

La lib contient les outils, agents, recherches et templates partages entre tous les PIDs. Chaque item a un `meta.yaml` avec un `id`, un `type` et une `description`.

**Types disponibles :**

| Type | Description | Utilisation |
|------|-------------|-------------|
| `tool` | CLI wrapper autour d'un service | `{cli} <action> [--profile name]` |
| `mcp` | Serveur MCP (Model Context Protocol) | Declare dans `meta.yaml`, ajoute via `mcp:` list dans le PID |
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

Quand tu dois utiliser un outil (envoyer un message, generer une image, transcrire, etc.) :

1. **Chercher l'outil** dans le registry :
```bash
cat ../../lib/registry.json | python3 -c "import sys,json; [print(i['id'],'-',i['description']) for i in json.load(sys.stdin)['items'] if i['type']=='tool']"
```

2. **Lire sa doc agent** (contient install, credentials, commandes) :
```bash
cat ../../lib/{tool-id}/AGENT.md
```

3. **Appeler directement** — les CLIs sont dans le PATH, pas besoin de `cd` ni d'activer un venv :
```bash
{tool-id} {action} [--arg value ...]
{tool-id} {action} --profile autre-profil
{tool-id} --help
```

Si `command not found` → suivre la section **Install** du AGENT.md de l'outil.
Les credentials sont chargees automatiquement via le systeme de profils (`lib/.profiles/`). Voir la section "Systeme de profils" ci-dessous.

**IMPORTANT** : ne JAMAIS `cd` dans `lib/` pour executer un outil. Ne JAMAIS `source .venv/bin/activate`. L'appel est toujours direct depuis le PID courant.

### Context store (`../../context/`)

Le context store est la **memoire factuelle partagee** entre tous les agents et PIDs. Il contient tout ce qui est vrai et durable : clients, contacts, projets, strategies, specs, notes, rapports. C'est la source de verite pour les faits — pas les preferences (AGENT.md), pas le code (git), pas les conversations (ephemeres).

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

**Ne PAS creer d'entite pour** : les preferences de dev (→ AGENT.md), les bugs (→ issues git), les taches (→ todo), les conversations ephemeres.

### Agents partages

Les agents autonomes vivent dans `pids/` et sont invocables via `agent-invoke` depuis n'importe quel PID.

**Documentation complete** : `lib/agent-invoke/README.md`

**IMPORTANT** : Toujours invoquer directement via Bash. Ne PAS lancer un sub-agent (Agent tool) pour executer agent-invoke.

#### Commandes

| Commande | Description |
|----------|-------------|
| `agent-invoke ask <agent> "prompt"` | One-shot — execute et retourne le resultat |
| `agent-invoke chat <agent> "prompt"` | Session persistante — cree une conversation suivie |
| `agent-invoke resume <session-id> "follow-up"` | Reprendre une session existante |
| `agent-invoke agents` | Lister tous les agents disponibles (pids/ + lib/) |
| `agent-invoke sessions` | Lister les sessions actives |
| `agent-invoke session <session-id>` | Voir l'historique complet d'une session |

#### Options

| Option | Description |
|--------|-------------|
| `--model`, `-m` | Modele a utiliser (sonnet, opus, haiku) — surcharge le meta.yaml de l'agent |
| `--timeout` | Timeout en secondes (defaut: 300) |
| `--max-turns` | Nombre max de tours agentic |
| `--json` | Sortie JSON brute (utile pour le piping) |

#### Mode Runtime (sans agent enregistre)

Composer une identite a la carte pour des invocations ponctuelles :

```bash
# Executer dans un repertoire specifique avec un modele choisi
agent-invoke ask --cwd /path/to/project "prompt" -m sonnet

# Composer un system prompt depuis un fichier
agent-invoke ask --cwd /path -f /path/instructions.md "prompt"

# Pointer vers un repertoire agent (avec meta.yaml + .claude/)
agent-invoke ask --agent-dir /path/to/agent "prompt"
```

#### Resolution d'agent

L'outil cherche l'agent dans cet ordre :
1. `pids/{agent-name}` — PID direct
2. `pids/*/{agent-name}` — sous-dossier d'un PID
3. `lib/{agent-name}` — agent partage dans la lib

#### Structure requise pour un agent

```
{agent-name}/
├── meta.yaml          # type: agent, id, description, model
└── .claude/
    ├── CLAUDE.md      # System prompt de l'agent
    └── settings.json  # Permissions et config
```

### Roadmaps (suivi de projet)

Deux outils complementaires pour gerer les roadmaps :

- **CLI `roadmap`** — operations CRUD rapides : creer, modifier, suivre les taches, gerer les dependances. Utilisable par tout agent ou en ligne de commande.
- **Skill `/roadmap`** — processus conversationnel en 6 etapes pour concevoir une roadmap complete from scratch (intention, KPIs, etat des lieux, macro, detail, scripts + wiring). A utiliser quand on part de zero et qu'on veut un accompagnement structure.

**Documentation complete** : `lib/roadmap/README.md`

#### Profils

Le CLI supporte plusieurs instances AI Manager via le systeme de profils :

```bash
roadmap --profile stable list     # Backend stable (port 4810)
roadmap --profile dev list        # Backend dev (port 4812)
roadmap list                      # Profil par defaut (_default)
```

Creer un profil : `profile add roadmap <nom>` avec `backend_url` et `internal_key`.

#### Commandes principales

```bash
# Roadmaps
roadmap list [--pid <pid>]                        # lister
roadmap show <id>                                 # details
roadmap create "Nom" [--pid dev] [--desc "..."]   # creer
roadmap update <id> --name "..." --status active   # modifier
roadmap delete <id> [--force]                     # supprimer
roadmap duplicate <id>                            # copie profonde (taches + deps)
roadmap state <id>                                # etat enrichi (statuts runtime)
roadmap graph <id>                                # graphe de dependances topologique

# Controle
roadmap start <id>                                # demarrer (lance les taches level-0)
roadmap stop <id> [--hard]                        # stopper (--hard annule les taches en cours)
roadmap pause <id>                                # pause (running continue, pas de nouveaux triggers)

# Taches
roadmap task list <id>                            # lister les taches
roadmap task add <id> "Nom" [--parent <pid>] [--script path]
roadmap task add <id> "Nom" --sub-roadmap <rid>   # delegation vers sous-roadmap
roadmap task show <id> <task_id>                  # details + etat runtime
roadmap task check <id> <task_id>                 # marquer termine
roadmap task uncheck <id> <task_id>               # retirer le marquage
roadmap task start <id> <task_id>                 # demarrer l'execution
roadmap task cancel <id> <task_id>                # annuler une tache en cours
roadmap task retry <id> <task_id>                 # relancer apres echec
roadmap task reset <id> <task_id>                 # remettre en pending

# Dependances
roadmap dep list <id>                             # lister
roadmap dep add <id> --task <tid> --on <dep_id>   # ajouter (detection de cycles)
roadmap dep remove <id> <dep_id>                  # supprimer

# Blocks (notes/annotations)
roadmap block list <id> [--task <tid>]            # lister
roadmap block add <id> "contenu" [--task <tid>]   # ajouter
```

#### Options globales

| Option | Description |
|--------|-------------|
| `--profile`, `-p` | Profil a utiliser (stable, dev, etc.) |
| `--json`, `-j` | Sortie JSON brute (utile pour piping et scripting) |

#### Resolution d'ID

Les IDs peuvent etre des prefixes (8 premiers caracteres) ou des sous-chaines du nom (insensible a la casse). Si ambigu, le CLI affiche les correspondances.

#### Sous-roadmaps (delegation hierarchique)

Une tache peut deleguer vers une sous-roadmap via `--sub-roadmap`. Quand la sous-roadmap se termine, la tache parente est automatiquement marquee comme completee.

```bash
# Creer une roadmap parent + des sous-roadmaps
roadmap create "Projet X" --pid dev
roadmap create "Projet X - Backend"
roadmap create "Projet X - Frontend"

# Lier les sous-roadmaps comme taches du parent
roadmap task add <parent-id> "Backend API" --sub-roadmap <backend-id>
roadmap task add <parent-id> "Frontend UI" --sub-roadmap <frontend-id>

# Ajouter des dependances entre taches (frontend apres backend)
roadmap dep add <parent-id> --task <frontend-tid> --on <backend-tid>
```

#### Workflow typique

```bash
# 1. Creer la roadmap
roadmap create "Mon projet" --pid dev --desc "Description"

# 2. Ajouter des taches (hiérarchie via --parent)
roadmap task add <id> "Phase 1 - Setup"
roadmap task add <id> "Phase 2 - Build" 
roadmap task add <id> "Sous-tache 2a" --parent <phase2-tid>

# 3. Definir les dependances
roadmap dep add <id> --task <phase2-tid> --on <phase1-tid>

# 4. Suivre l'avancement
roadmap state <id>       # vue d'ensemble avec statuts
roadmap graph <id>       # graphe de dependances par niveaux

# 5. Marquer l'avancement
roadmap task check <id> <tid>    # fait
roadmap task start <id> <tid>    # lancer un script
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

## Serveurs MCP (Model Context Protocol)

Les serveurs MCP donnent aux agents des outils supplementaires (Playwright, Dokploy, Hostinger, etc.). Ils sont definis une seule fois dans `lib/` et partages entre tous les PIDs qui en ont besoin.

### Architecture

```
lib/mcp-{id}/meta.yaml     ← Definition du serveur (commande, args, env)
lib/.profiles/mcp-{id}/    ← Credentials (si besoin)
pids/{pid}/meta.yaml        ← Liste des MCPs voulus (mcp: [...])
                ↓
    python3 registry.py build mcp
                ↓
pids/{pid}/.mcp.json        ← Genere, pret pour Claude Code
```

Le build MCP fait 3 choses pour chaque PID :
1. Lit la liste `mcp:` dans `meta.yaml` du PID
2. Charge la definition de chaque MCP depuis `lib/mcp-{id}/meta.yaml`
3. Resout les credentials depuis `lib/.profiles/mcp-{id}/` et substitue les `${VAR}`

### Ajouter un MCP a un PID existant

**Cas 1 — Le MCP existe deja dans la lib** (verifier avec `ls ../../lib/mcp-*/meta.yaml`) :

```bash
# 1. Ajouter au PID (editer meta.yaml)
#    mcp:
#      - mcp-origin-ui
#      - mcp-mon-nouveau-mcp    ← ajouter cette ligne

# 2. Si le MCP a besoin de credentials et qu'aucun profil n'existe :
profile add mcp-mon-nouveau-mcp default

# 3. Regenerer
cd ../../ && python3 registry.py build mcp
```

**Cas 2 — Le MCP n'existe pas encore dans la lib** : voir "Creer un nouveau MCP" ci-dessous.

### Creer un nouveau MCP dans la lib

Creer `lib/mcp-{id}/meta.yaml` avec la structure suivante :

```yaml
id: mcp-{id}
type: mcp
description: >
  Ce que fait ce serveur MCP en une phrase.
mcp:
  transport: stdio          # stdio | http
  command: npx              # commande a executer (stdio uniquement)
  args: ["-y", "package"]   # arguments de la commande
  env:                      # variables d'environnement (optionnel)
    API_KEY: "${MA_CLE}"    # ${VAR} sera substitue depuis le profil
requires:                   # necessaire UNIQUEMENT si le MCP a des credentials
  env:
    - MA_CLE: "Ou trouver cette cle (URL, dashboard, etc.)"
```

Puis :

```bash
# 1. Creer le profil avec les credentials
profile add mcp-{id} default

# 2. Ajouter au(x) PID(s) qui en ont besoin (editer meta.yaml)
# 3. Regenerer
cd ../../ && python3 registry.py build mcp
```

### Les 4 patterns de configuration

**HTTP sans credentials** (le plus simple) :

```yaml
# lib/mcp-shadcn/meta.yaml
id: mcp-shadcn
type: mcp
mcp:
  transport: http
  url: "https://www.shadcn.io/api/mcp"
```

**Stdio sans credentials** :

```yaml
# lib/mcp-origin-ui/meta.yaml
id: mcp-origin-ui
type: mcp
mcp:
  transport: stdio
  command: npx
  args: ["--yes", "github:kelvinchng/origin-ui-mcp"]
```

**Stdio avec credentials dans env** (pattern le plus courant) :

```yaml
# lib/mcp-dokploy/meta.yaml
id: mcp-dokploy
type: mcp
mcp:
  transport: stdio
  command: npx
  args: ["-y", "@ahdev/dokploy-mcp"]
  env:
    DOKPLOY_URL: "${DOKPLOY_URL}"
    DOKPLOY_API_KEY: "${DOKPLOY_API_KEY}"
requires:
  env:
    - DOKPLOY_URL: "URL de l'API Dokploy (ex: https://app.dokploy.com/api)"
    - DOKPLOY_API_KEY: "Cle API depuis Dokploy Settings > API"
```

**Stdio avec credentials dans args** (quand le package les attend en CLI) :

```yaml
# lib/mcp-ssh-personal-vps/meta.yaml
id: mcp-ssh-personal-vps
type: mcp
mcp:
  name: ssh-mcp-personal-vps    # nom custom dans .mcp.json (sinon derive de l'id)
  transport: stdio
  command: npx
  args:
    - "-y"
    - "@fangjunjie/ssh-mcp-server"
    - "--host"
    - "${VPS_HOST}"
    - "--username"
    - "${VPS_USERNAME}"
requires:
  env:
    - VPS_HOST: "IP ou hostname du serveur"
    - VPS_USERNAME: "Utilisateur SSH (ex: root)"
```

### Champs de la section `mcp:`

| Champ | Obligatoire | Description |
|-------|:-----------:|-------------|
| `transport` | oui | `stdio` (process local) ou `http` (URL distante) |
| `command` | stdio | Commande a lancer (`npx`, `node`, `python3`...) |
| `args` | stdio | Arguments de la commande (liste YAML) |
| `env` | non | Variables d'environnement passees au process |
| `url` | http | URL du serveur MCP distant |
| `headers` | non | Headers HTTP supplementaires |
| `name` | non | Nom du serveur dans `.mcp.json` (defaut: `id` sans prefixe `mcp-`) |

### Multi-profils

Un meme MCP peut avoir plusieurs profils de credentials. Utile quand un outil a plusieurs instances (ex: un compte staging et un compte prod).

```yaml
# Dans le meta.yaml du PID :
mcp:
  - mcp-dokploy              # utilise le profil par defaut
  - mcp-dokploy:staging      # utilise le profil "staging"
```

La resolution suit la chaine : profil explicite → `_default` → profil unique.

### Lister les MCPs disponibles

```bash
# Tous les MCPs de la lib
cat ../../lib/registry.json | python3 -c "import sys,json; [print(i['id'],'-',i['description']) for i in json.load(sys.stdin)['items'] if i['type']=='mcp']"

# MCPs actifs dans le PID courant
cat meta.yaml | grep "mcp-"
```

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
type: tool               # tool | mcp | research | template | agent | profile
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
├── .agent/
│   ├── AGENT.md            # OBLIGATOIRE — instructions de l'agent (source)
│   ├── AGENT.built.md      # GENERE — instructions completes (infra + shared + PID)
│   ├── .env.example        # OBLIGATOIRE — credentials necessaires
│   ├── agents/             # OPTIONNEL — agents specialises
│   ├── skills/             # OPTIONNEL — skills disponibles
│   ├── resources/          # OPTIONNEL — rules, templates, scripts
│   └── rules/              # OPTIONNEL — best practices
├── .claude/                # GENERE — compatibilite Claude Code local
│   ├── CLAUDE.md           # Copie de AGENT.built.md
│   └── skills/, agents/    # Copies depuis .agent/
├── .mcp.json               # GENERE — par registry.py build mcp
├── meta.yaml               # OBLIGATOIRE — identite PID + liste mcp:
└── [runtime data]          # GITIGNORE — projets, outputs, donnees personnelles
```

**Configuration MCP** : les MCPs sont declares dans `meta.yaml` du PID et generes centralement par `registry.py build mcp`. Voir la section "Serveurs MCP" ci-dessus.

```yaml
# meta.yaml du PID
id: mon-pid
mcp:
  - mcp-playwright
  - mcp-dokploy
```

**INTERDIT dans un PID :**
- `.agent/.env` commite (credentials reelles)
- `.mcp.json` commite (genere par registry.py, contient des credentials)
- Donnees runtime commitees (projets, outputs, bases de donnees)

### Standard : Serveur MCP (`../../lib/mcp-{id}/`)

Chaque serveur MCP de la lib DOIT respecter :

```
lib/mcp-{id}/
├── meta.yaml           # OBLIGATOIRE — type: mcp + section mcp:
└── README.md           # OPTIONNEL — si le MCP a une doc specifique
```

**meta.yaml obligatoire :**

```yaml
id: mcp-{id}             # kebab-case, prefixe mcp-, = nom du dossier
type: mcp                # TOUJOURS "mcp"
description: >
  Une phrase qui decrit ce que fait ce serveur MCP.
mcp:
  transport: stdio       # stdio | http
  command: npx           # obligatoire si stdio
  args: ["-y", "pkg"]    # obligatoire si stdio
  env:                   # optionnel — ${VAR} substitues depuis le profil
    API_KEY: "${MA_CLE}"
requires:                # obligatoire si le MCP a des credentials
  env:
    - MA_CLE: "Ou la trouver"
```

**Credentials** : gerees par le systeme de profils (`lib/.profiles/mcp-{id}/`), PAS par des `.env`. Le `requires.env` declare les variables — le CLI `profile add mcp-{id} default` les utilise pour le setup interactif.

**INTERDIT :**
- Credentials hardcodees dans le meta.yaml
- `.env` dans le dossier du MCP

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

- [ ] `meta.yaml` present et complet (lib) ou `.agent/AGENT.md` present (PID)
- [ ] `README.md` present avec section Setup + Credentials
- [ ] `.gitignore` present et couvre `.env`, `.venv/`, `tmp/`, outputs
- [ ] Aucune credential hardcodee dans le code (`grep -r "sk-\|ghp_\|xoxb-" .`)
- [ ] `setup.sh` present si des dependances sont a installer
- [ ] Dossiers `inputs/`, `outputs/` avec `.gitkeep` si utilises
- [ ] MCPs declares dans `meta.yaml` du PID (liste `mcp:`) et generes via `registry.py build mcp`
- [ ] MCPs de la lib ont `type: mcp` et une section `mcp:` dans leur meta.yaml
- [ ] CLI integre le resolver de profils si l'outil a besoin de credentials
- [ ] `meta.yaml` `requires.env` liste les variables pour `profile add`
