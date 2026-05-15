# MCP Dokploy

Serveur MCP pour gerer les deploiements via Dokploy. Applications, bases de donnees, domaines, monitoring.

## Setup

```bash
profile add mcp-dokploy default
```

## Credentials

| Variable | Ou la trouver |
|----------|---------------|
| `DOKPLOY_URL` | URL de l'API Dokploy (ex: `https://app.dokploy.com/api`) |
| `DOKPLOY_API_KEY` | Dokploy dashboard > Settings > API |

## Usage

```bash
# Assigner a un PID (editer meta.yaml du PID)
# mcp:
#   - mcp-dokploy

# Rebuild
python3 registry.py build mcp
```

## Capabilities

- CRUD applications, bases de donnees (Postgres, MySQL)
- Deploy, redeploy, start, stop
- Gestion des domaines et certificats
- Monitoring et logs
- Gestion des variables d'environnement
