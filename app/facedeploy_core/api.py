from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .config import IMAGE_EXTENSIONS, PRESETS, VIDEO_EXTENSIONS, settings
from .models import JobKind, JobRecord
from .runner import health_report, run_job
from .store import store

app = FastAPI(title="FaceDeploy Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _copy_upload(upload: UploadFile, folder: Path, allowed: set[str], prefix: str) -> str:
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")
    destination = folder / f"{prefix}_{uuid4().hex[:12]}{suffix}"
    with destination.open("wb") as handle:
        shutil.copyfileobj(upload.file, handle)
    return str(destination)


@app.get("/api/health")
def health():
    return health_report()


@app.get("/api/presets")
def presets():
    return [preset.__dict__ for preset in PRESETS.values()]


@app.get("/api/jobs")
def list_jobs(limit: int = 50):
    return store.list(limit=limit)


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    job = store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.post("/api/jobs/image")
def create_image_job(
    background_tasks: BackgroundTasks,
    source: UploadFile = File(...),
    target: UploadFile = File(...),
    preset: str = "quality",
):
    if preset not in PRESETS:
        raise HTTPException(status_code=400, detail="Unknown preset")
    source_path = _copy_upload(source, settings.source_dir, IMAGE_EXTENSIONS, "source")
    target_path = _copy_upload(target, settings.target_dir, IMAGE_EXTENSIONS, "target")
    job = JobRecord(kind=JobKind.image, preset=preset, source_path=source_path, target_path=target_path)
    store.upsert(job)
    background_tasks.add_task(run_job, job.id)
    return job


@app.post("/api/jobs/video")
def create_video_job(
    background_tasks: BackgroundTasks,
    source: UploadFile = File(...),
    target: UploadFile = File(...),
    preset: str = "fast",
):
    if preset not in PRESETS:
        raise HTTPException(status_code=400, detail="Unknown preset")
    source_path = _copy_upload(source, settings.source_dir, IMAGE_EXTENSIONS, "source")
    target_path = _copy_upload(target, settings.target_dir, VIDEO_EXTENSIONS, "target")
    job = JobRecord(kind=JobKind.video, preset=preset, source_path=source_path, target_path=target_path)
    store.upsert(job)
    background_tasks.add_task(run_job, job.id)
    return job


@app.get("/api/jobs/{job_id}/download")
def download_output(job_id: str):
    job = store.get(job_id)
    if not job or not job.output_path:
        raise HTTPException(status_code=404, detail="Output not found")
    output = Path(job.output_path)
    if not output.exists():
        raise HTTPException(status_code=404, detail="Output file missing")
    return FileResponse(output, filename=output.name)


@app.get("/api/jobs/{job_id}/log")
def download_log(job_id: str):
    job = store.get(job_id)
    if not job or not job.log_path:
        raise HTTPException(status_code=404, detail="Log not found")
    log = Path(job.log_path)
    if not log.exists():
        raise HTTPException(status_code=404, detail="Log file missing")
    return FileResponse(log, filename=log.name)
