"""FastAPI — REST API du scheduler."""
from __future__ import annotations

import json
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from .models import Job, JobCreate, JobPatch
from . import engine, store


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine.start()
    yield
    engine.stop()


app = FastAPI(title="Scheduler", version="1.0.0", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/jobs", response_model=Job, status_code=201)
def create_job(body: JobCreate):
    next_run = engine.schedule(
        job_id="__preview__",  # on calcule juste la date, on supprime après
        schedule_type=body.schedule_type,
        cron=body.cron,
        run_at=body.run_at,
    )
    # On a schedulé avec un ID temporaire, on le supprime
    engine.unschedule("__preview__")

    job = store.create_job(body, next_run_at=next_run)

    # Schedule pour de vrai avec l'ID réel
    real_next = engine.schedule(job.id, body.schedule_type, body.cron, body.run_at)
    if real_next and real_next != next_run:
        store.update_status(job.id, "scheduled", next_run_at=real_next)

    return store.get_job(job.id)


@app.get("/jobs", response_model=list[Job])
def list_jobs():
    return store.list_jobs()


@app.get("/jobs/{job_id}", response_model=Job)
def get_job(job_id: str):
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@app.patch("/jobs/{job_id}", response_model=Job)
def patch_job(job_id: str, body: JobPatch):
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if body.name is not None:
        store.update_fields(job_id, name=body.name)
    if body.event_payload is not None:
        import json as _json
        store.update_fields(job_id, event_payload=_json.dumps(body.event_payload))
    return store.get_job(job_id)


@app.delete("/jobs/{job_id}")
def delete_job(job_id: str):
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    engine.unschedule(job_id)
    store.delete_job(job_id)
    return {"deleted": job_id}


@app.post("/jobs/{job_id}/pause", response_model=Job)
def pause_job(job_id: str):
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status != "scheduled":
        raise HTTPException(400, f"Job is '{job.status}', cannot pause")
    engine.unschedule(job_id)
    store.update_status(job_id, "paused")
    return store.get_job(job_id)


@app.post("/jobs/{job_id}/resume", response_model=Job)
def resume_job(job_id: str):
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status != "paused":
        raise HTTPException(400, f"Job is '{job.status}', cannot resume")
    next_run = engine.schedule(job.id, job.schedule_type, job.cron, job.run_at)
    store.update_status(job_id, "scheduled", next_run_at=next_run)
    return store.get_job(job_id)
