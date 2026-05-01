#!/bin/bash
# Render a Remotion composition to video or still
# Usage:
#   ./render.sh video <CompositionId> [output.mp4] [--props '{"key":"val"}']
#   ./render.sh still <CompositionId> [output.png] [--props '{"key":"val"}'] [--frame 0]
#   ./render.sh list
#   ./render.sh preview

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOL_DIR="$(dirname "$SCRIPT_DIR")"
cd "$TOOL_DIR"

# Check setup
if [ ! -d "node_modules/remotion" ]; then
    echo "Remotion not installed. Run: ./setup.sh"
    exit 1
fi

MODE="${1:-list}"
shift 2>/dev/null

case "$MODE" in
    video)
        COMP_ID="${1:?Missing composition ID}"
        OUTPUT="${2:-output/${COMP_ID}.mp4}"
        shift 2 2>/dev/null
        echo "Rendering $COMP_ID → $OUTPUT"
        npx remotion render src/index.ts "$COMP_ID" "$OUTPUT" "$@"
        echo "Done: $OUTPUT"
        ;;
    still)
        COMP_ID="${1:?Missing composition ID}"
        OUTPUT="${2:-output/${COMP_ID}.png}"
        shift 2 2>/dev/null
        echo "Rendering still $COMP_ID → $OUTPUT"
        npx remotion still src/index.ts "$COMP_ID" "$OUTPUT" "$@"
        echo "Done: $OUTPUT"
        ;;
    list)
        echo "Available compositions:"
        npx remotion compositions src/index.ts 2>/dev/null
        ;;
    preview)
        echo "Starting Remotion Studio..."
        npx remotion studio src/index.ts
        ;;
    *)
        echo "Usage:"
        echo "  render.sh video <id> [output.mp4] [remotion flags]"
        echo "  render.sh still <id> [output.png] [remotion flags]"
        echo "  render.sh list"
        echo "  render.sh preview"
        exit 1
        ;;
esac
