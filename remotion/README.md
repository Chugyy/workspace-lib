# Remotion — Programmatic Video Tool

Create and render videos programmatically with React. Generate video segments, animated overlays, title cards, chapter intros, lower thirds, or any motion graphics. Supports rendering MP4/WebM videos and PNG stills.

## Setup

1. `./setup.sh`

Requires Node.js >= 18 and npm.

## Credentials

No credentials required. This tool runs locally.

## Usage

```bash
TOOL="../../lib/remotion"

# List available compositions
$TOOL/scripts/render.sh list

# Render a video
$TOOL/scripts/render.sh video TitleCard output/intro.mp4 --props '{"title":"My Video"}'

# Render a still
$TOOL/scripts/render.sh still KeyPoint output/keypoint.png --props '{"icon":"star","text":"Key insight"}'

# Preview in browser (interactive)
$TOOL/scripts/render.sh preview
```

## How It Works

Remotion renders React components frame by frame into video via headless Chrome. You write JSX/CSS/SVG, and Remotion captures each frame and encodes to MP4.

See `SKILL.md` for detailed API reference, animation patterns, and composition architecture.

## Outputs

- **output/** : Rendered videos (.mp4, .webm) and stills (.png, .gif)
