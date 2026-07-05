from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from .config import settings
from .models import JobRecord, JobStatus


SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  record_json TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
"""


class JobStore:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or settings.db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    def upsert(self, job: JobRecord) -> JobRecord:
        job.touch()
        payload = job.model_dump_json()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO jobs (id, record_json, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  record_json=excluded.record_json,
                  status=excluded.status,
                  updated_at=excluded.updated_at
                """,
                (job.id, payload, job.status.value, job.created_at, job.updated_at),
            )
        return job

    def get(self, job_id: str) -> JobRecord | None:
        with self.connect() as conn:
            row = conn.execute("SELECT record_json FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not row:
            return None
        return JobRecord.model_validate(json.loads(row["record_json"]))

    def list(self, limit: int = 50) -> list[JobRecord]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT record_json FROM jobs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [JobRecord.model_validate(json.loads(row["record_json"])) for row in rows]

    def set_status(self, job_id: str, status: JobStatus, error: str | None = None, progress: int | None = None) -> JobRecord | None:
        job = self.get(job_id)
        if not job:
            return None
        job.status = status
        job.error = error
        if progress is not None:
            job.progress = progress
        job.updated_at = datetime.utcnow().isoformat()
        return self.upsert(job)


store = JobStore()
