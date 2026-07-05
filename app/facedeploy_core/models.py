from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class JobKind(str, Enum):
    image = "image"
    video = "video"


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"
    canceled = "canceled"


class CreateJobRequest(BaseModel):
    kind: JobKind
    preset: str = "quality"


class JobRecord(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    kind: JobKind
    preset: str
    status: JobStatus = JobStatus.queued
    source_path: str
    target_path: str
    output_path: str | None = None
    log_path: str | None = None
    error: str | None = None
    progress: int = 0
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict[str, Any] = Field(default_factory=dict)

    def touch(self) -> None:
        self.updated_at = datetime.utcnow().isoformat()

    @property
    def output_exists(self) -> bool:
        return bool(self.output_path and Path(self.output_path).exists())


class HealthReport(BaseModel):
    ok: bool
    gpu_visible: bool
    ffmpeg_visible: bool
    facefusion_found: bool
    data_dir: str
    models_dir: str
    message: str
