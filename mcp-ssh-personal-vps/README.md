# MCP SSH Personal VPS

Serveur MCP pour acceder a un VPS via SSH. Permet l'execution de commandes distantes et le transfert de fichiers.

## Setup

```bash
profile add mcp-ssh-personal-vps default
```

## Credentials

| Variable | Ou la trouver |
|----------|---------------|
| `VPS_HOST` | IP ou hostname du serveur |
| `VPS_USERNAME` | Utilisateur SSH (generalement `root`) |
| `SSH_KEY_PATH` | Chemin vers la cle privee (ex: `/root/.ssh/id_ed25519`) |
| `SSH_PASSPHRASE` | Passphrase de la cle SSH |

## Usage

```bash
# Assigner a un PID (editer meta.yaml du PID)
# mcp:
#   - mcp-ssh-personal-vps

# Rebuild
python3 registry.py build mcp
```

## Capabilities

- Execution de commandes distantes
- Upload / download de fichiers
- Listing de serveurs configures
