#!/bin/bash
# Démarre le scheduler service
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SVC_DIR="$(dirname "$SCRIPT_DIR")"
VENV="/data/ai-manager/backend/.venv"
PORT="${SCHEDULER_PORT:-8701}"

# Charger les vars d'env du handler (même config)
if [ -f "/data/ai-manager/handler/.env" ]; then
    set -a && source /data/ai-manager/handler/.env && set +a
fi

export PYTHONPATH="$SVC_DIR/src:$PYTHONPATH"

echo "[scheduler] starting on port $PORT"
exec "$VENV/bin/uvicorn" scheduler_svc.app:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --log-level info
