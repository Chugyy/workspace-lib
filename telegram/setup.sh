#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip -q
pip install -e "$SCRIPT_DIR" -q

if command -v telegram &> /dev/null; then
    echo "✓ telegram CLI installed"
    telegram --help
else
    echo "CLI installed in venv. Use: source $VENV_DIR/bin/activate && telegram"
fi
