# ERP

Gerer les leads, notes et contacts via Personal Dashboard API.

## Setup

1. `cp .env.example .env`
2. Remplir les variables (voir Credentials ci-dessous)
3. `./setup.sh`

Configurer `assets/config.json` avec l'URL de l'API et les credentials.

## Credentials

| Variable | Ou la trouver |
|----------|---------------|
| `ERP_API_URL` | URL de l'API Personal Dashboard |
| `ERP_EMAIL` | Email du compte admin |
| `ERP_PASSWORD` | Mot de passe du compte admin |

## Usage

```bash
cd ../../lib/erp && .venv/bin/erp --help
```

### Leads

```bash
.venv/bin/erp lead list
.venv/bin/erp lead list --status to_contact --heat hot
.venv/bin/erp lead get 123
.venv/bin/erp lead create --name "Doe" --email "john@example.com"
.venv/bin/erp lead update 123 --status contacted --heat hot
.venv/bin/erp lead delete 123
.venv/bin/erp lead search "john doe"
```

### Notes

```bash
.venv/bin/erp note list 123
.venv/bin/erp note get 456
.venv/bin/erp note create --lead-id 123 --title "Follow-up" --content "Discussion..."
.venv/bin/erp note delete 456
```

## Lead Status Values

`to_contact` | `contacted` | `no_response` | `to_call_back` | `action_required` | `appointment_scheduled`

## Heat Level Values

`cold` | `warm` | `hot` | `very_hot`
