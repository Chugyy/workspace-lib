# Scheduler

Service de scheduling persistant. Cree des jobs cron ou one-shot qui postent des events a l'aggregator AI Manager. Stockage SQLite, moteur APScheduler.

## Setup

1. `cp .env.example .env`
2. Remplir `AGGREGATOR_URL` et `AGGREGATOR_API_KEY`
3. `./setup.sh`

## Credentials

| Variable | Ou la trouver |
|----------|---------------|
| `AGGREGATOR_URL` | AI Manager aggregator URL (e.g. `http://127.0.0.1:4811`) |
| `AGGREGATOR_API_KEY` | Aggregator API key (dans la config AI Manager) |
| `SCHEDULER_PORT` | Port du service HTTP (default: `8701`) |

## Usage

Le scheduler est un service FastAPI autonome, demarre via le start script :

```bash
cd ../../lib/scheduler && ./scripts/start.sh
```

### API REST

```bash
# Health check
curl http://localhost:8701/health

# Creer un job cron
curl -X POST http://localhost:8701/jobs -H "Content-Type: application/json" \
  -d '{"name":"daily-check","schedule_type":"cron","cron":"0 9 * * *","event_type":"check.daily","event_payload":{}}'

# Creer un job one-shot
curl -X POST http://localhost:8701/jobs -H "Content-Type: application/json" \
  -d '{"name":"reminder","schedule_type":"date","run_at":"2026-04-30T10:00:00Z","event_type":"reminder.fire","event_payload":{}}'

# Lister les jobs
curl http://localhost:8701/jobs

# Pause / Resume
curl -X POST http://localhost:8701/jobs/{job_id}/pause
curl -X POST http://localhost:8701/jobs/{job_id}/resume

# Supprimer un job
curl -X DELETE http://localhost:8701/jobs/{job_id}
```

## Architecture

- **engine.py** : APScheduler (BackgroundScheduler) — gere les declenchements et poste les events a l'aggregator
- **store.py** : Persistence SQLite (`data/jobs.db`)
- **models.py** : Pydantic models (Job, JobCreate, JobPatch)
- **app.py** : Routes FastAPI
