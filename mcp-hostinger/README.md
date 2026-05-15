# MCP Hostinger

Serveur MCP pour gerer les services Hostinger : domaines, DNS, VPS, hebergement web, billing.

## Setup

```bash
profile add mcp-hostinger default
```

## Credentials

| Variable | Ou la trouver |
|----------|---------------|
| `HOSTINGER_API_KEY` | hpanel.hostinger.com > Account > API |

## Usage

```bash
# Assigner a un PID (editer meta.yaml du PID)
# mcp:
#   - mcp-hostinger

# Rebuild
python3 registry.py build mcp
```

## Capabilities

- Gestion des domaines (achat, DNS, transfert, WHOIS)
- Configuration DNS (A, AAAA, CNAME, MX, TXT...)
- Gestion VPS (start, stop, rebuild, firewall, snapshots)
- Hebergement web (sites, deployments, SSL)
- Billing (abonnements, moyens de paiement)
