#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
MARKER="$VENV_DIR/.installed"

# Setup venv + deps if needed (once)
if [ ! -f "$MARKER" ]; then
    [ ! -d "$VENV_DIR" ] && python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip -q 2>/dev/null
    pip install -e "$SCRIPT_DIR" -q 2>/dev/null
    touch "$MARKER"
else
    source "$VENV_DIR/bin/activate"
fi

# Forward all args to agent-invoke
agent-invoke "$@"
