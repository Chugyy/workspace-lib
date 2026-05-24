#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
    if command -v virtualenv &> /dev/null; then
        virtualenv "$VENV_DIR" -q
    else
        python3 -m venv "$VENV_DIR"
    fi
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip -q
pip install -e "$SCRIPT_DIR" -q

if command -v roadmap &> /dev/null; then
    echo "roadmap CLI installed"
    roadmap --help
else
    echo "CLI installed in venv. Use: source $VENV_DIR/bin/activate && roadmap"
fi
