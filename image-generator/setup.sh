#!/bin/bash
# Image Generator — self-contained runner.
# Usage: ./setup.sh generate -p "prompt" -f 16:9
#        ./setup.sh models
#        ./setup.sh test
# If no args: installs/updates and prints help.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

# Ensure venv exists with pip
if [ ! -d "$VENV_DIR" ] || [ ! -f "$VENV_DIR/bin/pip" ]; then
    rm -rf "$VENV_DIR"
    python3 -m venv "$VENV_DIR" 2>/dev/null
    # If ensurepip is missing, bootstrap pip manually
    if [ ! -f "$VENV_DIR/bin/pip" ]; then
        python3 -m venv --without-pip "$VENV_DIR" 2>/dev/null
        "$VENV_DIR/bin/python3" -c "
import urllib.request, os, sys
get_pip = os.path.join('$VENV_DIR', 'get-pip.py')
urllib.request.urlretrieve('https://bootstrap.pypa.io/get-pip.py', get_pip)
" 2>/dev/null
        "$VENV_DIR/bin/python3" "$VENV_DIR/get-pip.py" -q 2>/dev/null
        rm -f "$VENV_DIR/get-pip.py"
    fi
fi

# Ensure package is installed
if [ ! -f "$VENV_DIR/bin/image-gen" ]; then
    "$VENV_DIR/bin/pip" install --upgrade pip -q 2>/dev/null
    "$VENV_DIR/bin/pip" install -e "$SCRIPT_DIR" -q 2>/dev/null
fi

# Run
if [ $# -eq 0 ]; then
    "$VENV_DIR/bin/image-gen" --help
else
    "$VENV_DIR/bin/image-gen" "$@"
fi
