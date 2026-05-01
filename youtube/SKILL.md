---
name: youtube
description: YouTube tool — download video/audio, get transcripts, search, upload with thumbnail. Self-contained setup.sh handles everything.
---

# YouTube Tool

## CLI

`setup.sh` is self-contained: handles venv creation, install, and execution. No activation needed.

```bash
LIB_TOOL="lib/youtube"
$LIB_TOOL/setup.sh --help
```

### download

Download a video or extract audio only.

```bash
$LIB_TOOL/setup.sh download "https://youtube.com/watch?v=..." [--audio-only] [--output ./dir] [--name filename]
```

| Param | Description | Default |
|-------|-------------|---------|
| `url` | YouTube video URL | required |
| `--audio-only` / `-a` | Extract audio as mp3 | false |
| `--output` / `-o` | Output directory | `output/` |
| `--name` / `-n` | Output filename (no extension) | video title |

### transcript

Get the transcript (subtitles) of a video.

```bash
$LIB_TOOL/setup.sh transcript "https://youtube.com/watch?v=..." [--lang fr] [--timestamps] [--save]
```

| Param | Description | Default |
|-------|-------------|---------|
| `url` | YouTube video URL | required |
| `--lang` / `-l` | Preferred subtitle language | `fr` |
| `--timestamps` / `-t` | Include timestamps per segment | false |
| `--save` / `-s` | Save transcript to `output/` | false |

Uses `youtube-transcript-api` (fetches existing subtitles, no download needed). Falls back to any available language if preferred not found.

### search

Search YouTube and get structured results.

```bash
$LIB_TOOL/setup.sh search "query" [--max 10] [--json]
```

| Param | Description | Default |
|-------|-------------|---------|
| `query` | Search query | required |
| `--max` / `-m` | Max results (1-50) | `10` |
| `--json` / `-j` | Output raw JSON | false |

Returns: title, URL, channel, views, duration, date, thumbnail URL, description excerpt.

### upload

Upload a video to YouTube. **Requires OAuth2 auth** (run `auth` first).

```bash
$LIB_TOOL/setup.sh upload ./video.mp4 \
  --title "Video Title" \
  --description "Description text" \
  --tags "tag1,tag2,tag3" \
  --privacy private \
  --thumbnail ./thumb.png
```

| Param | Description | Default |
|-------|-------------|---------|
| `file` | Video file path | required |
| `--title` / `-t` | Video title | required |
| `--description` / `-d` | Video description | `""` |
| `--tags` | Comma-separated tags | none |
| `--category` / `-c` | YouTube category ID | `22` (People & Blogs) |
| `--privacy` / `-p` | `private`, `unlisted`, or `public` | `private` |
| `--thumbnail` | Thumbnail image path (PNG/JPG, 1280x720) | none |

Uploads are resumable (large files supported). Thumbnail is set automatically if provided.

### thumbnail

Set a custom thumbnail on an existing video.

```bash
$LIB_TOOL/setup.sh thumbnail VIDEO_ID ./thumbnail.png
```

### auth

Authenticate with Google YouTube API (opens browser).

```bash
$LIB_TOOL/setup.sh auth
```

First run opens a browser for OAuth2 consent. Token is saved to `credentials/token.json` and auto-refreshed on subsequent calls.

## YouTube Category IDs

| ID | Category |
|----|----------|
| `1` | Film & Animation |
| `2` | Autos & Vehicles |
| `10` | Music |
| `15` | Pets & Animals |
| `17` | Sports |
| `20` | Gaming |
| `22` | People & Blogs |
| `23` | Comedy |
| `24` | Entertainment |
| `25` | News & Politics |
| `26` | Howto & Style |
| `27` | Education |
| `28` | Science & Technology |

## Config

OAuth2 credentials in `credentials/client_secret.json`. Token auto-saved to `credentials/token.json` after first auth.
