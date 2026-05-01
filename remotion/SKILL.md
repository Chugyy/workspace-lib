---
name: remotion
description: Create and render videos programmatically with React. Use when the user wants to generate video segments, animated overlays, title cards, chapter intros, lower thirds, or any motion graphics. Supports rendering MP4/WebM videos and PNG stills.
---

# Remotion — Programmatic Video Tool

## Setup

```bash
cd lib/remotion && ./setup.sh
```

## Quick Commands

```bash
TOOL="lib/remotion"

# List available compositions
$TOOL/scripts/render.sh list

# Render a video
$TOOL/scripts/render.sh video TitleCard output/intro.mp4 --props '{"title":"My Video","subtitle":"Episode 1"}'

# Render a still (thumbnail, frame capture)
$TOOL/scripts/render.sh still KeyPoint output/keypoint.png --props '{"icon":"🚀","text":"Key insight"}'

# Preview in browser (interactive)
$TOOL/scripts/render.sh preview
```

## Core Concepts (for the AI)

### What is Remotion?
Remotion = React components rendered frame by frame into video. You write JSX, CSS, SVG — Remotion captures each frame via headless Chrome and encodes to MP4.

### The Frame Model
- A video = function(frame) → pixels
- `useCurrentFrame()` returns the current frame number (0-indexed)
- `useVideoConfig()` returns `{ fps, durationInFrames, width, height }`
- Duration in seconds = `durationInFrames / fps`

### Key APIs

| API | Purpose |
|-----|---------|
| `useCurrentFrame()` | Get current frame number |
| `useVideoConfig()` | Get fps, duration, dimensions |
| `<AbsoluteFill>` | Full-frame container (position: absolute, 100% w/h) |
| `<Sequence from={30} durationInFrames={60}>` | Show children only during frame range |
| `interpolate(frame, inputRange, outputRange)` | Map frame to any value (opacity, position, scale) |
| `spring({ frame, fps, config })` | Physics-based easing (damping, stiffness, mass) |
| `<Img src={staticFile("image.png")}/>` | Static image from `public/` folder |
| `<Audio src={staticFile("audio.mp3")}/>` | Audio track |
| `<OffthreadVideo src="..."/>` | Embed video (better perf than `<Video>`) |
| `staticFile("filename")` | Reference file from `public/` directory |

### interpolate() — The Core Animation Function

```tsx
import { interpolate, useCurrentFrame } from "remotion";

const frame = useCurrentFrame();

// Fade in over frames 0-15
const opacity = interpolate(frame, [0, 15], [0, 1], {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
});

// Move from 100px to 0px over frames 0-30
const translateY = interpolate(frame, [0, 30], [100, 0], {
  extrapolateRight: "clamp",
});
```

**Always use `extrapolateLeft: "clamp"` and `extrapolateRight: "clamp"`** to prevent values from going beyond the target range.

### spring() — Physics-Based Animation

```tsx
import { spring, useCurrentFrame, useVideoConfig } from "remotion";

const frame = useCurrentFrame();
const { fps } = useVideoConfig();

const scale = spring({
  frame,
  fps,
  config: { damping: 12, stiffness: 100, mass: 1 },
});
// scale goes from 0 → ~1 with natural bounce
```

### Sequence — Timeline Orchestration

```tsx
import { Sequence } from "remotion";

// Show title from frame 0 to 60, then subtitle from frame 30 to 90
<>
  <Sequence from={0} durationInFrames={60}>
    <TitleCard title="Hello" />
  </Sequence>
  <Sequence from={30} durationInFrames={60}>
    <TextOverlay text="World" />
  </Sequence>
</>
```

## Project Structure

```
lib/remotion/
├── SKILL.md              ← This file (AI reference)
├── meta.yaml             ← Tool metadata
├── setup.sh              ← Install Node deps
├── remotion.config.ts    ← Remotion config
├── tsconfig.json         ← TypeScript config
├── package.json          ← NPM deps
├── scripts/
│   └── render.sh         ← CLI wrapper (video/still/list/preview)
├── src/
│   ├── index.ts          ← Entry point (registerRoot)
│   ├── Root.tsx           ← Composition registry
│   ├── lib/
│   │   └── animations.ts ← Shared animation helpers (fadeIn, fadeOut, slideIn, scaleIn)
│   └── compositions/     ← Reusable components
│       ├── TextOverlay.tsx
│       ├── TitleCard.tsx
│       ├── ChapterTitle.tsx
│       ├── LowerThird.tsx
│       └── KeyPoint.tsx
├── public/               ← Static assets (images, audio, fonts)
├── templates/            ← Composition templates for copy/customize
└── output/               ← Rendered videos and stills
```

## Available Compositions

| ID | Description | Key Props |
|----|-------------|-----------|
| `TextOverlay` | Centered text with fade in/out, transparent bg | `text`, `fontSize`, `color`, `backgroundColor` |
| `TitleCard` | Full-screen title + subtitle, slide-in animation | `title`, `subtitle`, `backgroundColor`, `accentColor` |
| `ChapterTitle` | Numbered chapter header, slides from left | `number`, `title`, `accentColor` |
| `LowerThird` | Name/role bar at bottom of screen | `name`, `role`, `accentColor` |
| `KeyPoint` | Highlighted insight with emoji icon | `icon`, `text`, `backgroundColor`, `accentColor` |

## Shared Animation Helpers (`src/lib/animations.ts`)

| Function | Signature | Description |
|----------|-----------|-------------|
| `fadeIn` | `(frame, delay?, duration?)` | Opacity 0→1 |
| `fadeOut` | `(frame, endFrame, duration?)` | Opacity 1→0 |
| `fadeInOut` | `(frame, totalFrames, fadeDuration?)` | Full lifecycle fade |
| `slideIn` | `(frame, fps, fromOffset, delay?)` | Spring-based slide |
| `scaleIn` | `(frame, fps, delay?)` | Spring-based scale 0→1 |

## How to Create a New Composition

1. Create `src/compositions/MyComp.tsx`:

```tsx
import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { fadeInOut } from "../lib/animations";

type Props = {
  text: string;
  // ... your props
};

export const MyComp: React.FC<Props> = ({ text }) => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps } = useVideoConfig();
  const opacity = fadeInOut(frame, durationInFrames);

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div style={{ opacity }}>
        <h1 style={{ color: "#fff", fontSize: 48 }}>{text}</h1>
      </div>
    </AbsoluteFill>
  );
};
```

2. Register in `src/Root.tsx`:

```tsx
import { MyComp } from "./compositions/MyComp";

// Inside Root component:
<Composition
  id="MyComp"
  component={MyComp}
  durationInFrames={90}
  fps={30}
  width={1920}
  height={1080}
  defaultProps={{ text: "Hello" }}
/>
```

3. Render:

```bash
lib/remotion/scripts/render.sh video MyComp output/mycomp.mp4 --props '{"text":"Custom text"}'
```

## Rendering Options

### Override duration/fps/dimensions via CLI

```bash
# 5 seconds at 60fps, 4K
scripts/render.sh video TitleCard output/intro.mp4 \
  --props '{"title":"Hello"}' \
  --fps 60 \
  --width 3840 \
  --height 2160 \
  --duration 150
```

### Codecs

| Codec | Extension | Use case |
|-------|-----------|----------|
| `h264` (default) | `.mp4` | Best compatibility |
| `h265` | `.mp4` | Smaller files, less compatible |
| `vp9` | `.webm` | Web-optimized |
| `prores` | `.mov` | Professional editing (lossless) |
| `gif` | `.gif` | Short loops |

```bash
scripts/render.sh video MyComp output/clip.webm --codec vp9
```

## Use Case: Face-cam Overlay Workflow

The primary use case for the content PID. Workflow:

1. **Input**: transcript/script with timestamps
2. **AI generates**: a sequence of Remotion compositions timed to the transcript
3. **Output**: individual overlay clips (transparent bg) to composite over face-cam footage

### Creating Transparent Overlays

For overlays on face-cam video, use `backgroundColor: "transparent"` on `<AbsoluteFill>` and render with:

```bash
# PNG sequence (for compositing in video editors)
npx remotion render src/index.ts MyComp output/overlay --image-format png --codec png

# Or WebM with alpha channel
npx remotion render src/index.ts MyComp output/overlay.webm --codec vp8
```

### Timed Sequence from Script

Create a master composition that uses `<Sequence>` to orchestrate overlays:

```tsx
// Each segment maps to a timestamp in the script
<>
  <Sequence from={0} durationInFrames={90}>
    <ChapterTitle number="01" title="Introduction" />
  </Sequence>
  <Sequence from={150} durationInFrames={120}>
    <KeyPoint icon="💡" text="Key concept explained here" />
  </Sequence>
  <Sequence from={450} durationInFrames={90}>
    <TextOverlay text="Important stat: 42%" />
  </Sequence>
</>
```

Frame calculation: `frame = timestamp_seconds * fps`

## Rules

- **Always use 1920x1080** (16:9) unless explicitly asked otherwise
- **Always 30fps** unless explicitly asked otherwise
- **Use the shared animation helpers** from `src/lib/animations.ts` — don't rewrite interpolate/spring boilerplate
- **Transparent backgrounds** for overlays meant to go on top of face-cam footage
- **Dark backgrounds** (`#0f172a`, `#1e293b`) for standalone title cards
- **Inter font family** as default — consistent with modern branding
- **Tailwind-like colors** — use the slate/blue palette (`#f8fafc`, `#94a3b8`, `#3b82f6`, `#0f172a`)
- **Props must be serializable** — no functions, no React elements in props, only primitives/arrays/objects
- **Static assets** go in `public/` and are referenced via `staticFile("filename")`
