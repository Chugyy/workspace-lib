# PM — Process Manager CLI

Thin CLI client over the AI Manager Process API. List, start, stop, restart, add and remove internal processes (pm2) and manage Dokploy deployed services.

## Setup

1. `cp .env.example .env`
2. Remplir les variables si les defaults ne conviennent pas
3. `./setup.sh`

## Credentials

| Variable | Ou la trouver |
|----------|---------------|
| `PM_API_URL` | AI Manager backend URL (default: `http://127.0.0.1:4810`) |
| `PM_API_KEY` | AI Manager internal API key (default: `proxy-internal-key`) |

## Usage

```bash
cd ../../lib/pm && .venv/bin/pm list               # List all processes
cd ../../lib/pm && .venv/bin/pm list -c core        # Filter by category
cd ../../lib/pm && .venv/bin/pm info <name>         # Process details
cd ../../lib/pm && .venv/bin/pm start <name>        # Start a process
cd ../../lib/pm && .venv/bin/pm stop <name>         # Stop a process
cd ../../lib/pm && .venv/bin/pm restart <name>      # Restart a process
cd ../../lib/pm && .venv/bin/pm logs <name> -n 100  # Show logs
cd ../../lib/pm && .venv/bin/pm health              # Health checks
cd ../../lib/pm && .venv/bin/pm add <name> -s /path/to/script.sh -c connector  # Add process
cd ../../lib/pm && .venv/bin/pm remove <name>       # Remove process

# Dokploy subcommands
cd ../../lib/pm && .venv/bin/pm dokploy start <app-id>
cd ../../lib/pm && .venv/bin/pm dokploy stop <app-id>
cd ../../lib/pm && .venv/bin/pm dokploy redeploy <app-id>
```

All commands support `--json` for raw JSON output.
