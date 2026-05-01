# Email

Lire, envoyer et rechercher des emails via Gmail API ou IMAP/SMTP.

## Setup

1. `cp .env.example .env`
2. Remplir les variables (voir Credentials ci-dessous)
3. `./setup.sh`

### Gmail

Deposer le fichier `credentials.json` (OAuth Client JSON) dans `assets/credentials.json`. Au premier lancement, le CLI ouvre un navigateur pour l'autorisation OAuth.

### IMAP/SMTP

Renseigner host, port, email et mot de passe dans `assets/config.json`.

## Credentials

| Variable | Ou la trouver |
|----------|---------------|
| `GMAIL_CREDENTIALS_PATH` | Google Cloud Console → APIs & Services → Credentials → OAuth Client → Download JSON |
| `IMAP_HOST` | Fournisseur email (ex: `imap.hostinger.com`) |
| `IMAP_PORT` | Port IMAP (993) |
| `SMTP_HOST` | Fournisseur email (ex: `smtp.hostinger.com`) |
| `SMTP_PORT` | Port SMTP (587) |
| `IMAP_EMAIL` | Adresse email du compte |
| `IMAP_PASSWORD` | Mot de passe du compte |

## Usage

```bash
cd ../../lib/email && .venv/bin/email --help
```

### Gmail

```bash
.venv/bin/email gmail list
.venv/bin/email gmail list --max 20 --unread
.venv/bin/email gmail read <message_id>
.venv/bin/email gmail send --to recipient@example.com --subject "Subject" --body "Body"
.venv/bin/email gmail draft --to recipient@example.com --subject "Subject" --body "Body"
.venv/bin/email gmail search "from:user@example.com newer_than:7d"
```

### IMAP/SMTP

```bash
.venv/bin/email imap list
.venv/bin/email imap list --limit 20 --unread
.venv/bin/email imap read <email_id>
.venv/bin/email imap send --to recipient@example.com --subject "Subject" --body "Body"
.venv/bin/email imap search --sender user@example.com
```

## Config

`assets/config.json` — Gmail OAuth credentials path + IMAP/SMTP credentials. Ce fichier contient des credentials et est gitignore.
