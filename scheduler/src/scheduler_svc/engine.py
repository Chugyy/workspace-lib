"""APScheduler engine — gère les déclenchements et poste les events au proxy."""
from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from . import store

AGGREGATOR_URL = os.getenv("AGGREGATOR_URL", "").rstrip("/")
AGGREGATOR_API_KEY = os.getenv("AGGREGATOR_API_KEY", "")

_scheduler = BackgroundScheduler(timezone="UTC")


# ---------------------------------------------------------------------------
# Déclenchement d'un job
# ---------------------------------------------------------------------------

def _fire(job_id: str) -> None:
    """Appelé par APScheduler quand un job se déclenche."""
    job = store.get_job(job_id)
    if not job or job.status not in ("scheduled",):
        return

    now = datetime.now(timezone.utc)

    event = {
        "source": job.event_source,
        "type": job.event_type,
        "payload": {**job.event_payload, "job_id": job.id, "job_name": job.name},
    }

    try:
        body = json.dumps(event).encode()
        req = urllib.request.Request(
            f"{AGGREGATOR_URL}/events",
            data=body,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": AGGREGATOR_API_KEY,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10):
            pass

        if job.schedule_type == "once":
            store.update_status(job_id, "done", last_run_at=now)
        else:
            aps_job = _scheduler.get_job(job_id)
            next_run = aps_job.next_run_time if aps_job else None
            store.update_status(job_id, "scheduled", last_run_at=now, next_run_at=next_run)

        print(f"[scheduler] fired job '{job.name}' ({job_id})")

    except Exception as exc:
        print(f"[scheduler] error firing job {job_id}: {exc}")
        store.update_status(job_id, "failed", last_run_at=now)


# ---------------------------------------------------------------------------
# API du moteur
# ---------------------------------------------------------------------------

def schedule(job_id: str, schedule_type: str, cron: Optional[str], run_at: Optional[datetime]) -> Optional[datetime]:
    """Ajoute un job dans APScheduler. Retourne next_run_at."""
    if schedule_type == "cron":
        parts = cron.split()
        trigger = CronTrigger(
            minute=parts[0], hour=parts[1],
            day=parts[2], month=parts[3], day_of_week=parts[4],
            timezone="UTC",
        )
    else:
        trigger = DateTrigger(run_date=run_at, timezone="UTC")

    aps_job = _scheduler.add_job(_fire, trigger, args=[job_id], id=job_id, replace_existing=True)
    return aps_job.next_run_time


def unschedule(job_id: str) -> None:
    try:
        _scheduler.remove_job(job_id)
    except Exception:
        pass


def next_run(job_id: str) -> Optional[datetime]:
    aps_job = _scheduler.get_job(job_id)
    return aps_job.next_run_time if aps_job else None


def start() -> None:
    store.init_db()
    _scheduler.start()

    # Restaure les jobs persistés
    restored = 0
    for job in store.list_jobs():
        if job.status == "scheduled":
            try:
                schedule(job.id, job.schedule_type, job.cron, job.run_at)
                restored += 1
            except Exception as exc:
                print(f"[scheduler] could not restore job {job.id}: {exc}")

    print(f"[scheduler] started — {restored} job(s) restored from DB")


def stop() -> None:
    _scheduler.shutdown(wait=False)
