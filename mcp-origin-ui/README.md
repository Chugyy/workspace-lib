# MCP Origin UI

Serveur MCP pour rechercher et inspecter les composants Origin UI (537 composants React, 39 categories).

## Setup

Aucun credential necessaire.

```bash
# Assigner a un PID (editer meta.yaml du PID)
# mcp:
#   - mcp-origin-ui

# Rebuild
python3 registry.py build mcp
```

## Capabilities

- Recherche de composants par nom ou categorie
- Details d'un composant (code, preview, dependencies)
- Liste des categories disponibles
