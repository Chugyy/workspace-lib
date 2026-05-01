#!/bin/bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

if [ ! -d ".venv" ]; then
    uv venv .venv
fi

uv pip install --python .venv/bin/python3 httpx typer pyyaml rich

chmod +x context-hub
echo "✅ context-hub CLI ready"
