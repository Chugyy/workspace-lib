---
name: erp-manager
description: Manage ERP leads, notes, and contacts via Personal Dashboard API. Use for creating/updating leads, tracking interactions, searching contacts, and managing lead notes.
---

# ERP Manager

## Setup

```bash
cd .claude/skills/erp-manager && ./setup.sh
```

## CLI Usage

```bash
# Activate venv
source .claude/skills/erp-manager/.venv/bin/activate

# Help
erp --help
erp lead --help
erp note --help
```

## Lead Commands

```bash
# List leads
erp lead list
erp lead list --status to_contact
erp lead list --heat hot --limit 50
erp lead list --search "ACME"

# Get lead
erp lead get 123

# Create lead
erp lead create --name "Doe" --email "john@example.com"
erp lead create --name "Doe" --email "john@example.com" --first-name "John" --company "ACME" --heat warm

# Update lead
erp lead update 123 --status contacted --heat hot
erp lead update 123 --phone "+33612345678"

# Delete lead
erp lead delete 123

# Search
erp lead search "john doe"
```

## Note Commands

```bash
# List notes for a lead
erp note list 123

# Get note
erp note get 456

# Create note
erp note create --lead-id 123 --title "Follow-up call" --content "Discussed pricing..."

# Delete note
erp note delete 456
```

## Config

`assets/config.json` — API URL + credentials. Token auto-saved to `assets/token.json`.

## Lead Status Values

`to_contact` | `contacted` | `no_response` | `to_call_back` | `action_required` | `appointment_scheduled`

## Heat Level Values

`cold` | `warm` | `hot` | `very_hot`
