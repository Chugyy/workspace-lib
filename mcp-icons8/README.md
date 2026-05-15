# MCP Icons8

Serveur MCP pour rechercher des icones dans le catalogue Icons8. Utilise mcp-remote comme bridge HTTP-to-stdio.

## Setup

Aucun credential necessaire.

```bash
# Assigner a un PID (editer meta.yaml du PID)
# mcp:
#   - mcp-icons8

# Rebuild
python3 registry.py build mcp
```

## Capabilities

- Recherche d'icones par mot-cle
- Filtrage par plateforme et categorie
- URL de telechargement en PNG
