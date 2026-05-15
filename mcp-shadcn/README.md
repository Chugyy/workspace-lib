# MCP shadcn/ui

Serveur MCP HTTP pour acceder a la documentation et installer les composants shadcn/ui.

## Setup

Aucun credential necessaire. Transport HTTP direct.

```bash
# Assigner a un PID (editer meta.yaml du PID)
# mcp:
#   - mcp-shadcn

# Rebuild
python3 registry.py build mcp
```

## Capabilities

- Documentation des composants shadcn/ui
- Installation de composants
- Exemples d'utilisation
