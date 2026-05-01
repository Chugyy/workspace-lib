#!/bin/bash
# The CLI reuses the venv from the mp4-transcriber service (already has all deps)
SERVICE_VENV="/data/workspace/pids/dev/mp4-transcriber/venv"

if [ ! -f "$SERVICE_VENV/bin/python3" ]; then
    echo "Error: mp4-transcriber service venv not found at $SERVICE_VENV"
    echo "Make sure the service is deployed first."
    exit 1
fi

# Install CLI deps if missing
VIRTUAL_ENV="$SERVICE_VENV" uv pip install httpx typer rich -q 2>/dev/null || \
    "$SERVICE_VENV/bin/python3" -m pip install httpx typer rich -q

# Create CLI entrypoint in a local bin/
mkdir -p "$(dirname "${BASH_SOURCE[0]}")"/bin
ENTRY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/bin/mp4-transcriber"
CLI_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/src/cli.py"

cat > "$ENTRY" << SCRIPT
#!/bin/bash
exec "$SERVICE_VENV/bin/python3" "$CLI_SRC" "\$@"
SCRIPT
chmod +x "$ENTRY"

echo "✓ mp4-transcriber CLI prêt"
echo "  Binaire : $ENTRY"
echo "  Usage   : mp4-transcriber --help"
echo "  Env     : MP4_TRANSCRIBER_URL (défaut: http://localhost:8765)"
echo "            MP4_TRANSCRIBER_AUTHORIZATION (optionnel: Bearer sk_live_...)"
