# MCP Playwright

Serveur MCP pour l'automatisation navigateur via Playwright. Permet la navigation, les screenshots, les interactions DOM et l'evaluation JavaScript.

## Setup

Aucun credential necessaire.

```bash
# Assigner a un PID (editer meta.yaml du PID)
# mcp:
#   - mcp-playwright

# Rebuild
python3 registry.py build mcp
```

## Capabilities

- Navigation web (navigate, back, tabs)
- Screenshots et snapshots DOM
- Interactions (click, fill, hover, drag, drop)
- Evaluation JavaScript dans la page
- Upload de fichiers
- Gestion des dialogues
