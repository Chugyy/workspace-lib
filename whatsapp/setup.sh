#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

echo "=== WhatsApp Manager Setup (WAHA) ==="

# 1. Python venv
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip -q
pip install -e "$SCRIPT_DIR" -q

if command -v whatsapp &> /dev/null; then
    echo "✓ whatsapp CLI installed"
    whatsapp --help
else
    echo "CLI installed in venv. Use: source $VENV_DIR/bin/activate && whatsapp"
fi

# 2. Check Docker / WAHA
echo ""
if command -v docker &> /dev/null; then
    if docker ps --format '{{.Names}}' | grep -q '^waha$'; then
        echo "✓ WAHA container is running"
    else
        echo "⚠ WAHA container not found. Start it with:"
        echo "  docker run -d --name waha --restart unless-stopped -p 3000:3000 \\"
        echo "    -v waha_sessions:/app/.sessions \\"
        echo "    -e WHATSAPP_DEFAULT_ENGINE=NOWEB \\"
        echo "    -e WHATSAPP_API_KEY=waha-internal-key \\"
        echo "    devlikeapro/waha"
    fi
else
    echo "⚠ Docker not found — WAHA requires Docker"
fi
