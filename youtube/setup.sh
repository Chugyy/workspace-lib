#!/bin/bash
# YouTube Tool — self-contained runner.
# Usage: ./setup.sh download <url> [--audio-only]
#        ./setup.sh transcript <url> [--lang fr]
#        ./setup.sh search "query" [--max 10]
#        ./setup.sh upload <file> --title "..." --description "..."
#        ./setup.sh auth
# If no args: installs/updates and prints help.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

# Ensure venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo "[youtube] Creating virtual environment..."
    python3 -m venv "$VENV_DIR" 2>/dev/null
fi

# Ensure package is installed (check CLI entry point)
if [ ! -f "$VENV_DIR/bin/yt-tool" ]; then
    echo "[youtube] Installing dependencies..."
    "$VENV_DIR/bin/pip" install --upgrade pip -q 2>/dev/null
    "$VENV_DIR/bin/pip" install -e "$SCRIPT_DIR" -q 2>/dev/null
fi

# Run
if [ $# -eq 0 ]; then
    "$VENV_DIR/bin/yt-tool" --help
else
    "$VENV_DIR/bin/yt-tool" "$@"
fi
