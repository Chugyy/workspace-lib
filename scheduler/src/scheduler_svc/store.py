"""Persistance SQLite des jobs."""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import Job, JobCreate

DB_PATH = Path(__file__).parent.parent.parent / "data" / "jobs.db"


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id           TEXT PRIMARY KEY,
                name         TEXT NOT NULL,
                schedule_type TEXT NOT NULL,
                cron         TEXT,
                run_at       TEXT,
                event_source TEXT NOT NULL,
                event_type   TEXT NOT NULL,
                event_payload TEXT NOT NULL,
                status       TEXT NOT NULL DEFAULT 'scheduled',
                created_at   TEXT NOT NULL,
                last_run_at  TEXT,
                next_run_at  TEXT
            )
        """)


def _row_to_job(row: sqlite3.Row) -> Job:
    return Job(
        id=row["id"],
        name=row["name"],
        schedule_type=row["schedule_type"],
        cron=row["cron"],
        run_at=datetime.fromisoformat(row["run_at"]) if row["run_at"] else None,
        event_source=row["event_source"],
        event_type=row["event_type"],
        event_payload=json.loads(row["event_payload"]),
        status=row["status"],
        created_at=datetime.fromisoformat(row["created_at"]),
        last_run_at=datetime.fromisoformat(row["last_run_at"]) if row["last_run_at"] else None,
        next_run_at=datetime.fromisoformat(row["next_run_at"]) if row["next_run_at"] else None,
    )


def create_job(data: JobCreate, next_run_at: Optional[datetime] = None) -> Job:
    job_id = str(uuid.uuid4())
    now = datetime.utcnow()
    with _conn() as conn:
        conn.execute(
            """INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                job_id, data.name, data.schedule_type,
                data.cron,
                data.run_at.isoformat() if data.run_at else None,
                data.event_source, data.event_type,
                json.dumps(data.event_payload),
                "scheduled", now.isoformat(),
                None,
                next_run_at.isoformat() if next_run_at else None,
            ),
        )
    return get_job(job_id)


def list_jobs() -> list[Job]:
    with _conn() as conn:
        rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
    return [_row_to_job(r) for r in rows]


def get_job(job_id: str) -> Optional[Job]:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    return _row_to_job(row) if row else None


def update_status(
    job_id: str,
    status: str,
    last_run_at: Optional[datetime] = None,
    next_run_at: Optional[datetime] = None,
) -> None:
    with _conn() as conn:
        conn.execute(
            "UPDATE jobs SET status=?, last_run_at=?, next_run_at=? WHERE id=?",
            (
                status,
                last_run_at.isoformat() if last_run_at else None,
                next_run_at.isoformat() if next_run_at else None,
                job_id,
            ),
        )


def update_fields(job_id: str, **fields) -> None:
    if not fields:
        return
    sets = ", ".join(f"{k}=?" for k in fields)
    vals = list(fields.values()) + [job_id]
    with _conn() as conn:
        conn.execute(f"UPDATE jobs SET {sets} WHERE id=?", vals)


def delete_job(job_id: str) -> bool:
    with _conn() as conn:
        cur = conn.execute("DELETE FROM jobs WHERE id=?", (job_id,))
    return cur.rowcount > 0
