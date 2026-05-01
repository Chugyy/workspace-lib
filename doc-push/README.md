# doc-push

Git add + doc-sync agent + git commit + git push. Detecte si les changements impactent la documentation et invoque l'agent `doc-sync` automatiquement avant le commit.

## Setup

Aucune installation requise. Le script utilise `bash` et `git` disponibles sur le systeme.

Prerequis : l'agent `doc-sync` doit etre installe via `agent-invoke`.

## Usage

```bash
cd ../../lib/doc-push && ./doc-push.sh "commit message"
```

Le script :
1. Detecte les fichiers modifies via `git diff`
2. Verifie si les changements impactent la documentation (migrations, CRUD, jobs, services, routes, composants)
3. Si oui, invoque l'agent `doc-sync` pour mettre a jour les docs
4. `git add -A` + `git commit` + `git push`

## Patterns detectes

Le script considere qu'un changement impacte la documentation s'il touche :
- `app/database/migrations/`, `app/database/crud/`
- `app/core/jobs/`, `app/core/services/`, `app/core/utils/`
- `app/api/routes/`, `app/api/models/`
- `src/components/`, `src/app/`
