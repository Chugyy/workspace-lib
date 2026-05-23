# Agent Invoke

Invoquer des agents depuis n'importe quel PID. Supporte deux modes : PID (pointer vers un agent enregistre) et Runtime (composer l'identite de l'agent a la carte). Passe par l'API du AI Manager qui route vers le bon SDK (Claude, OpenRouter, Codex).

## Setup

```bash
cd ../../lib/agent-invoke && ./setup.sh
```

## Architecture

```
agent-invoke CLI
    │
    ▼
AI Manager API (HTTP)
    │
    ▼
UAS (Universal Agent Service)
    │
    ├─ claude-sdk (Anthropic)
    ├─ openrouter-sdk (multi-provider)
    └─ codex-sdk (OpenAI via codex-proxy)
```

L'outil ne spawne plus `claude` en subprocess. Il cree une conversation dans le AI Manager, envoie le prompt, et streame les evenements SSE en temps reel.

## Modes d'utilisation

### Mode PID (retrocompat)

Pointer vers un agent enregistre dans `pids/` ou `lib/`. L'agent est identifie par son `meta.yaml` (type: agent). Son `.agent/AGENT.built.md` et `.mcp.json` sont charges automatiquement.

```bash
# One-shot
agent-invoke ask context-search "Trouve tout sur HTR"

# Avec override de modele
agent-invoke ask context-search "Analyse approfondie" --model opus

# Session persistante
agent-invoke chat context-search "Debut d'analyse"

# Reprendre une session
agent-invoke resume <session-id> "Et les contacts ?"
```

### Mode Runtime (nouveau)

Composer l'identite de l'agent a la carte : choisir le cwd, les fichiers de system prompt, le modele. Pas de PID necessaire.

```bash
# Minimal : cwd + prompt
agent-invoke ask --cwd /data/workspace/context "liste les entites actives" -m sonnet

# Avec system prompt compose depuis des fichiers
agent-invoke ask --cwd /data/workspace/pids/dev \
  --prompt-file /data/workspace/lib/AGENT.infrastructure.md \
  --prompt-file /data/workspace/lib/AGENT.shared.md \
  -m haiku "resume les objectifs"

# Avec agent directory explicite (charge .agent/ depuis un autre chemin)
agent-invoke ask --cwd /data/workspace/context \
  --agent-dir /data/workspace/pids/dev/context-search \
  "cherche les specs HTR"
```

### Mode Direct (--agent-dir)

Pointer directement vers un dossier agent sans passer par le registre.

```bash
agent-invoke ask --agent-dir /path/to/my-agent "prompt"
```

## Commandes

| Commande | Description |
|----------|-------------|
| `ask` | Requete one-shot (pas de session persistante) |
| `chat` | Nouvelle session persistante |
| `resume` | Continuer une session existante |
| `agents` | Lister les agents disponibles (scan local pids/ + lib/) |
| `sessions` | Lister les sessions de conversation |
| `session` | Voir le detail d'une session |

## Options de `ask`

| Flag | Alias | Description | Default |
|------|-------|-------------|---------|
| `--model` | `-m` | Modele (alias: sonnet, opus, haiku, ou ID complet) | depuis meta.yaml ou sonnet |
| `--cwd` | | Repertoire de travail pour les tools (mode runtime) | repertoire de l'agent |
| `--agent-dir` | | Chemin vers le dossier agent (skip le registre) | - |
| `--prompt-file` | `-f` | Fichier(s) pour le system prompt (repetable) | - |
| `--timeout` | | Timeout en secondes | 300 |
| `--max-turns` | | Max turns agentic (compat, peu utilise) | 0 (= defaut agent) |
| `--json` | | Sortie JSON brute | false |

## Resolution du system prompt (UAS)

La resolution suit une chaine de priorite a 3 niveaux :

```
1. --prompt-file fourni (meme vide) → compose depuis les fichiers, PAS de auto-load
2. --agent-dir fourni → charge agentDir/.agent/AGENT.built.md
3. Sinon → charge workingDir/.agent/AGENT.built.md (retrocompat)

Dans tous les cas : si --model passe un systemPrompt inline → ajoute apres la base.
```

Cela permet :
- **Agent PID complet** : tout est charge depuis le `.agent/` du PID
- **Agent a la carte** : choisir exactement quels fichiers composent le system prompt
- **Agent nu** : `--prompt-file` sans fichiers = aucun system prompt

## Configuration

| Variable d'env | Description | Default |
|----------------|-------------|---------|
| `AI_MANAGER_URL` | URL du backend AI Manager | `http://127.0.0.1:4812` |
| `BACKEND_INTERNAL_KEY` | Cle d'auth interne | `proxy-internal-key` |

## Structure d'un agent

Chaque agent (dans `pids/` ou `lib/`) suit cette structure :

```
{agent-id}/
├── meta.yaml           # id, type: agent, model, max_turns, description
└── .agent/
    ├── AGENT.md        # Instructions source
    ├── AGENT.built.md  # Instructions compilees (infra + shared + PID)
    └── .mcp.json       # Serveurs MCP (genere par registry.py)
```

## Session Storage

Les sessions locales sont stockees en JSON dans `agents/sessions/` :

```
agents/sessions/{session-id}.json
```

Les conversations sont aussi persistees dans le AI Manager (DB SQLite).
