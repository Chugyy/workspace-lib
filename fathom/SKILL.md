---
name: fathom
description: Fetch transcripts from Fathom call recordings. Use when the user provides a Fathom URL (fathom.video/share/... or fathom.video/calls/...) or a numeric recording ID and wants to retrieve, analyze, or summarize a call transcript.
---

# Fathom

## Setup

```bash
cd .claude/skills/fathom && ./setup.sh
```

## CLI Usage

```bash
# Activate venv
source .claude/skills/fathom/.venv/bin/activate

# Help
fathom --help
```

## Commands

```bash
# Fetch transcript by share URL
fathom transcript "https://fathom.video/share/<token>"

# Fetch transcript by calls URL
fathom transcript "https://fathom.video/calls/124392814"

# Fetch by numeric recording ID
fathom transcript 124392814

# Save to file
fathom transcript "https://fathom.video/share/<token>" --output /tmp/transcript.txt
```

## Config

`assets/config.json` — Fathom API key + base URL.

## Output

- Transcript printed to stdout
- Temp file path printed to stderr as `TEMP_FILE:/tmp/fathom_...txt`
- Format: `[timestamp] Speaker: text`
