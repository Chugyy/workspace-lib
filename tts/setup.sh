#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
MODELS_DIR="$SCRIPT_DIR/models"

KOKORO_MODEL_URL="https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
VOICES_URL="https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"

# --- 1. Virtual environment ---
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip -q
pip install -e "$SCRIPT_DIR" -q

# --- 2. Download Kokoro ONNX models (if not present) ---
mkdir -p "$MODELS_DIR"

if [ ! -f "$MODELS_DIR/kokoro-v1.0.onnx" ]; then
    echo "Downloading Kokoro ONNX model (~311 MB)..."
    wget -q --show-progress -O "$MODELS_DIR/kokoro-v1.0.onnx" "$KOKORO_MODEL_URL"
    echo "Model downloaded."
else
    echo "Model kokoro-v1.0.onnx already present."
fi

if [ ! -f "$MODELS_DIR/voices-v1.0.bin" ]; then
    echo "Downloading voices file..."
    wget -q --show-progress -O "$MODELS_DIR/voices-v1.0.bin" "$VOICES_URL"
    echo "Voices downloaded."
else
    echo "Voices voices-v1.0.bin already present."
fi

# --- 3. Verify ---
if command -v tts &> /dev/null; then
    echo ""
    echo "tts CLI installed"
    tts --help
else
    echo "CLI installed in venv. Use: source $VENV_DIR/bin/activate && tts"
fi
