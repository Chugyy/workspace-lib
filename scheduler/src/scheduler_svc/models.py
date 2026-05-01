from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, model_validator


class JobCreate(BaseModel):
    name: str
    schedule_type: Literal["cron", "once"]
    cron: Optional[str] = None        # requis si schedule_type == "cron"
    run_at: Optional[datetime] = None  # requis si schedule_type == "once" (UTC)
    # L'event posté au proxy quand le job se déclenche
    event_source: str = "scheduler"
    event_type: str = "job.fired"
    event_payload: dict[str, Any] = {}

    @model_validator(mode="after")
    def check_schedule(self) -> JobCreate:
        if self.schedule_type == "cron" and not self.cron:
            raise ValueError("cron requis quand schedule_type='cron'")
        if self.schedule_type == "once" and not self.run_at:
            raise ValueError("run_at requis quand schedule_type='once'")
        return self


class JobPatch(BaseModel):
    name: Optional[str] = None
    event_payload: Optional[dict[str, Any]] = None


class Job(BaseModel):
    id: str
    name: str
    schedule_type: Literal["cron", "once"]
    cron: Optional[str] = None
    run_at: Optional[datetime] = None
    event_source: str
    event_type: str
    event_payload: dict[str, Any]
    status: Literal["scheduled", "paused", "done", "failed"]
    created_at: datetime
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
