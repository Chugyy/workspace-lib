#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip -q
pip install -e "$SCRIPT_DIR" -q

# Check ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "Warning: ffmpeg not found. Install: sudo apt install ffmpeg"
else
    echo "ffmpeg: $(ffmpeg -version 2>&1 | head -1)"
fi

# Create downloads directory
mkdir -p "$SCRIPT_DIR/downloads"

if command -v transcribe &> /dev/null; then
    echo "✓ transcribe CLI installed"
    transcribe --help
else
    echo "CLI installed in venv. Use: source $VENV_DIR/bin/activate && transcribe"
fi
