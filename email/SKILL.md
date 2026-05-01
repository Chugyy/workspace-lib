---
name: email-manager
description: Manage emails via Gmail API or IMAP/SMTP. Use when the user needs to list, read, search, or send emails. Supports two modes - Gmail (OAuth) for personal Gmail accounts, and IMAP/SMTP for professional email accounts. Always ask for confirmation before sending emails.
---

# Email Manager

## Setup

```bash
cd .claude/skills/email-manager && ./setup.sh
```

## CLI Usage

```bash
# Activate venv
source .claude/skills/email-manager/.venv/bin/activate

# Help
email --help
email gmail --help
email imap --help
```

## Gmail Commands

```bash
# List emails
email gmail list
email gmail list --max 20 --unread
email gmail list --sender user@example.com

# Read email
email gmail read <message_id>

# Send email
email gmail send --to recipient@example.com --subject "Subject" --body "Body"
email gmail send --to recipient@example.com --subject "Subject" --body "<h1>HTML</h1>" --html

# Create draft
email gmail draft --to recipient@example.com --subject "Subject" --body "Body"

# Search (Gmail query syntax)
email gmail search "from:user@example.com newer_than:7d"
email gmail search "has:attachment subject:invoice" --max 20
```

## IMAP/SMTP Commands

```bash
# List emails
email imap list
email imap list --limit 20 --unread
email imap list --folder "Sent"

# Read email
email imap read <email_id>

# Send email
email imap send --to recipient@example.com --subject "Subject" --body "Body"

# Search
email imap search --sender user@example.com
email imap search --subject "invoice"
```

## Config

`assets/config.json` — Gmail OAuth credentials path + IMAP/SMTP credentials.

## Gmail Query Patterns

- `from:user@example.com` — by sender
- `subject:keyword` — by subject
- `newer_than:7d` / `older_than:1m` — by date
- `has:attachment` — with attachments
- `is:unread` — unread only

## Notes

- Always ask confirmation before sending
- Include user signature from `config['user']` in emails
- Gmail: first run opens browser for OAuth authorization
