---
name: image-generator
description: Generate images via OpenAI gpt-image-2 (default) or NanoBanana API. Supports text-to-image and image-to-image editing. Use for thumbnails, visuals, or any AI-generated graphic.
---

# Image Generator

## CLI

`setup.sh` is self-contained: handles venv creation, install, and execution. No activation needed.

```bash
LIB_TOOL="lib/image-generator"
$LIB_TOOL/setup.sh --help
```

### generate

```bash
# OpenAI (default) — gpt-image-2
$LIB_TOOL/setup.sh generate \
  --prompt "A futuristic dashboard with dark theme" \
  --format 16:9 \
  --resolution 2k \
  --quality high \
  --num 1 \
  --name "dashboard"

# With exact pixel size (overrides format+resolution)
$LIB_TOOL/setup.sh generate \
  --prompt "Portrait photo" \
  --size 1920x1080 \
  --quality high

# Image editing with reference
$LIB_TOOL/setup.sh generate \
  --prompt "Add dramatic lighting and increase contrast" \
  --ref photo.png \
  --format 16:9 \
  --quality high

# NanoBanana fallback
$LIB_TOOL/setup.sh generate \
  --prompt "A landscape" \
  --provider nanobanana \
  --model pro \
  --format 16:9
```

| Param | Description | Default |
|-------|-------------|---------|
| `--prompt` / `-p` | Image description or edit instruction | required |
| `--ref` / `-r` | Reference images (local paths), comma-separated | none |
| `--provider` | Provider: `openai` (default), `nanobanana` | `openai` |
| `--model` / `-m` | NanoBanana model: `base`, `pro`. Ignored for OpenAI. | `pro` |
| `--format` / `-f` | Aspect ratio: `1:1`, `16:9`, `9:16`, `4:3`, `3:4` | `1:1` |
| `--resolution` | Resolution: `1k`, `2k`, `4k` | `1k` |
| `--quality` / `-q` | OpenAI quality: `low`, `medium`, `high`. Ignored for NanoBanana. | `high` |
| `--size` / `-s` | Exact pixel size (e.g. `1920x1080`). Overrides format+resolution. OpenAI only. | none |
| `--output` / `-o` | Output directory | `output/` |
| `--num` / `-n` | Number of images (1-4 nanobanana, 1-8 openai) | `1` |
| `--name` | Output filename prefix | `generated` |
| `--cloud-upload` | Upload to Personal Cloud after generation | `false` |
| `--cloud-prefix` | Object key prefix in Personal Cloud (e.g. `thumbnails/04-mon-slug`) | `thumbnails` |

### Size resolution (OpenAI)

If `--size` is given, it's used directly (must be multiples of 16, max edge < 3840px).
Otherwise, `--format` + `--resolution` are combined:

| Format | 1k | 2k | 4k |
|--------|-------|-------|-------|
| 1:1 | 1024x1024 | 2048x2048 | 2880x2880 |
| 16:9 | 1024x576 | 2560x1440 | 3840x2160 |
| 9:16 | 576x1024 | 1440x2560 | 2160x3840 |
| 4:3 | 1024x768 | 2048x1536 | 3072x2304 |
| 3:4 | 768x1024 | 1536x2048 | 2304x3072 |

### models

```bash
$LIB_TOOL/setup.sh models
```

### test

```bash
$LIB_TOOL/setup.sh test                          # test OpenAI (default)
$LIB_TOOL/setup.sh test --provider nanobanana     # test NanoBanana
```

## Providers

### OpenAI gpt-image-2 (default)

Reasoning-based image generation. The model plans, searches for references, generates candidates, and verifies the result against the prompt.

| Quality | Cost/img (1024x1024) | Use case |
|---------|---------------------|----------|
| `low` | ~$0.006 | Drafts, rapid ideation, previews |
| `medium` | ~$0.05 | Social media, standard content |
| `high` | ~$0.21 | Print, thumbnails, text-heavy, brand work |

Strengths: accurate text rendering, consistent characters, up to 2K+ resolution, up to 8 images per prompt.

### NanoBanana (fallback, `--provider nanobanana`)

| Model | Base | Cost/img | Resolutions |
|-------|------|----------|-------------|
| `base` | Gemini 2.5 Flash | ~$0.02 | 1k |
| **`pro`** (default) | Gemini 3 Pro | $0.09-0.12 | 1k, 2k, 4k |

## Image Editing (image-to-image)

Pass the existing image as `--ref` + describe the edit in `--prompt`.

```bash
# OpenAI (default)
$LIB_TOOL/setup.sh generate \
  -p "Enlarge the person's head by 20%. Keep everything else identical." \
  -r existing-thumbnail.png \
  -f 16:9 \
  -q high

# NanoBanana
$LIB_TOOL/setup.sh generate \
  -p "Enlarge the person's head by 20%." \
  -r existing-thumbnail.png \
  --provider nanobanana \
  -m base \
  -f 16:9
```

## Hugo Reference Photos

`assets/hugo-photos/` — PNG, detoured.

| File | Description |
|------|-------------|
| `hugo-a-moitie-endormi.png` | Half-asleep, tired look |
| `hugo-enjoue.png` | Cheerful, happy |
| `hugo-montre-du-doigt-regard-proche.png` | Pointing, close-up gaze |
| `hugo-neutre.png` | Neutral expression |
| `hugo-regarad-tres-proche-coquin.png` | Very close-up, playful |
| `hugo-regard-proche-suspicieux.png` | Close-up, suspicious |
| `hugo-souriant.png` | Smiling |

## Prompt Guide — YouTube Thumbnails

This section is for the LLM agent. When generating thumbnails, build the prompt yourself following these rules, then call `image-gen generate`.

### Prompt structure (for gpt-image-2, in this order)

1. **Scene type**: "Wide landscape YouTube thumbnail, strictly 16:9."
2. **Background**: Describe setting, gradient, atmosphere, lighting direction.
3. **Subject**: Main element — person (expression, framing, position) or object (size, placement).
4. **Face fidelity** (if ref photo): "CRITICAL: Match EXACTLY the face from the reference. Preserve facial structure, eye shape, jawline, nose, skin texture. Face must be LARGE — at least 25% of image height."
5. **Text overlay**: 'Bold text reading "[EXACT TEXT]" in [color], thick sans-serif uppercase, with drop shadow. Placed [position]. Text must be LARGE.'
6. **Composition constraints**: "Single focal point, max 3 visual elements, nothing important in bottom-right corner (YouTube duration badge)."
7. **Quality**: "High contrast, vivid colors, sharp edges, photoréaliste."

### Example prompt

```
Wide landscape YouTube thumbnail, strictly 16:9. Dark gradient background from #0a0b0f to #03467b, subtle radial glow of electric blue at 10% in center. Young French man (late 20s, short dark hair), shocked expression with wide eyes and open mouth, cropped bust up on the left third. Bold text reading "DE A A Z" in white, thick sans-serif uppercase, with drop shadow, filling the right two-thirds. Single focal point on the face. Nothing important in bottom-right corner. High contrast, professional, vivid colors, photoréaliste.
```

### CLI call

```bash
$LIB_TOOL/setup.sh generate \
  -p "[prompt above]" \
  -f 16:9 \
  --resolution 2k \
  -q high \
  -r assets/hugo-photos/hugo-enjoue.png \
  --name "thumbnail-de-a-a-z"
```

## Config

API keys in `.env`:
- `OPENAI_API_KEY` — for gpt-image-2 (default provider)
- `NANOBANANA_API_KEY` — for NanoBanana fallback
