# Interactive Card CLI

Cree des conversations interactives (notifications, formulaires, tickets) dans l'AI Manager.

## Installation

```bash
cd ../lib/interactive-card && ./setup.sh
```

## Env vars

| Variable | Description | Default |
|----------|-------------|---------|
| `BACKEND_URL` | URL du backend AI Manager | `http://127.0.0.1:4810` |
| `BACKEND_INTERNAL_KEY` | Cle API interne du backend | `proxy-internal-key` |

Les scripts d'action du handler ont deja ces variables dans leur environnement.

## Commandes

### `notify` — notification simple

Cree une notification avec texte + bouton resolve.

```bash
interactive-card notify "Nouvelle reservation" "**Client**: John Doe\nDate: demain 14h"
interactive-card notify "Alerte" "Paiement echoue" --button "Compris"
```

### `prompt` — formulaire interactif

Cree un formulaire avec champs et boutons d'action.

```bash
# Formulaire avec texte, facts et input
interactive-card prompt "Approuver la demande ?" \
    --text "Un client souhaite reserver" \
    --fact "Client=John Doe" --fact "Montant=500 EUR" \
    --input "reply:textarea:Votre reponse:Tapez ici..." \
    --approve "Approuver" --reject "Refuser" \
    --event-source "interactive:booking" \
    --event-type "booking.approved"

# Select avec options
interactive-card prompt "Definir la priorite" \
    --input "level:select:Priorite" \
    --options "level:low=Basse,medium=Moyenne,high=Haute" \
    --approve "Valider" \
    --event-source "interactive:triage"
```

**Flags `--input`** : format `id:type:label[:placeholder]`
- Types : `text`, `textarea`, `select`, `number`, `date`, `toggle`

**Flags `--options`** : format `input_id:value1=Label1,value2=Label2`

### `create` — JSON complet

Controle total via JSON brut.

```bash
# Argument direct
interactive-card create '{"body":[...],"actions":[...]}'

# Depuis un fichier
interactive-card create --file card.json --title "A verifier"

# Depuis stdin (pipe)
echo '{"body": [...], "actions": [...]}' | interactive-card create -
```

### `test` — verifier la connexion

```bash
interactive-card test
```

## Utilisation depuis un script d'action

```python
import subprocess, json

result = subprocess.run(
    ["../lib/interactive-card/.venv/bin/interactive-card", "prompt",
     "Nouveau lead a traiter",
     "--text", f"Email: {payload['email']}",
     "--fact", f"Source={event['source']}",
     "--fact", f"Type={event['type']}",
     "--input", "reply:textarea:Reponse:Votre reponse...",
     "--approve", "Traiter",
     "--reject", "Ignorer",
     "--event-source", "interactive:lead",
     "--event-type", "lead.treated"],
    capture_output=True, text=True
)
data = json.loads(result.stdout)
conversation_id = data["conversation_id"]
```

## Utilisation programmatique (Python)

```python
from interactive_card.builder import CardBuilder
from interactive_card.client import create_conversation

card = (CardBuilder()
    .text("**Alerte paiement**", bold=True)
    .fact_set({"Client": "John", "Montant": "500 EUR"})
    .input("action", "select", label="Action",
           options={"refund": "Rembourser", "retry": "Relancer", "ignore": "Ignorer"})
    .button("validate", "Valider", "primary",
            action_type="event", source="interactive:billing",
            event_type="payment.action", inputs="all", resolves=True)
    .button("skip", "Plus tard", "ghost", action_type="resolve")
    .build())

result = create_conversation(card, title="Paiement echoue")
```
