---
name: agent-invoke
description: Invoke shared agents from any PID and maintain persistent conversations. Use when you need to delegate a task to a specialized agent (context search, web research, challenge) or continue a previous agent conversation. Agents live in lib/ with their own .claude/ config.
---

# Agent Invoke

Invoke shared agents defined in `lib/` from any PID. Supports one-shot queries, persistent sessions, and conversation resumption.

## Setup

```bash
cd lib/agent-invoke && ./setup.sh
```

## CLI Usage

```bash
source lib/agent-invoke/.venv/bin/activate
```

## Commands

### Ask (one-shot, no session persistence)

```bash
agent-invoke ask context-search "Trouve tout ce qu'on sait sur HTR"
```

### Chat (new persistent session)

```bash
agent-invoke chat context-search "Analyse le client HTR en profondeur"
# Returns: session_id + response
```

### Resume (continue existing session)

```bash
agent-invoke resume <session-id> "Et ses contacts ?"
```

### List sessions

```bash
agent-invoke sessions
agent-invoke sessions --agent context-search
agent-invoke sessions --last 5
```

### View a session

```bash
agent-invoke session <session-id>
```

### List available agents

```bash
agent-invoke agents
```

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--model` | Override agent model | from meta.yaml |
| `--timeout` | Timeout in seconds | 300 |
| `--max-turns` | Max agentic turns | 10 |
| `--json` | Output raw JSON | false |

## Agent Directory Structure

Each agent in `lib/` follows this structure:

```
lib/{agent-id}/
├── meta.yaml           # id, description, model, max_turns
└── .claude/
    ├── CLAUDE.md       # System prompt, role, rules
    └── settings.json   # Permissions, allowed tools
```

## Session Storage

Sessions are stored as JSON in `lib/sessions/`:

```
lib/sessions/{session-id}.json
```
