---
name: agent-invoke
description: Invoke shared agents from any PID. Two modes — PID (pointer vers un agent enregistre) et Runtime (composer l'identite a la carte avec --cwd, --prompt-file, --model). Passe par l'API AI Manager qui route vers le bon SDK (Claude, OpenRouter, Codex).
---

# Agent Invoke

Documentation complete : `lib/agent-invoke/README.md`

## Quick Reference

```bash
# Mode PID (retrocompat)
agent-invoke ask <agent> "prompt"                    # one-shot
agent-invoke ask <agent> "prompt" --model opus       # override modele
agent-invoke chat <agent> "prompt"                   # session persistante
agent-invoke resume <session-id> "follow-up"         # reprendre

# Mode Runtime (nouveau)
agent-invoke ask --cwd /path "prompt" -m sonnet                    # cwd seul
agent-invoke ask --cwd /path -f /path/file.md "prompt"             # system prompt compose
agent-invoke ask --agent-dir /path/to/.agent "prompt"              # agent directory direct

# Utilitaires
agent-invoke agents                                  # lister les agents
agent-invoke sessions                                # lister les sessions
```

## Options de `ask`

| Flag | Alias | Description |
|------|-------|-------------|
| `--model` | `-m` | Modele (sonnet, opus, haiku, ou ID complet) |
| `--cwd` | | Working directory pour les tools (mode runtime) |
| `--agent-dir` | | Chemin vers le dossier agent (skip registre) |
| `--prompt-file` | `-f` | Fichier(s) de system prompt (repetable) |
| `--timeout` | | Timeout en secondes (default: 300) |
| `--json` | | Sortie JSON brute |
