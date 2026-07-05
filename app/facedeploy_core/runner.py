from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import time
from pathlib import Path

from .config import IMAGE_EXTENSIONS, PRESETS, VIDEO_EXTENSIONS, settings
from .models import HealthReport, JobKind, JobRecord, JobStatus
from .store import store


def output_path_for(job: JobRecord) -> Path:
    target_suffix = Path(job.target_path).suffix.lower()
    if target_suffix in IMAGE_EXTENSIONS or job.kind == JobKind.image:
        return settings.output_dir / f"{job.id}.png"
    return settings.output_dir / f"{job.id}.mp4"


def build_facefusion_command(job: JobRecord) -> list[str]:
    if job.preset not in PRESETS:
        raise ValueError(f"Unknown preset: {job.preset}")
    output_path = output_path_for(job)
    preset = PRESETS[job.preset]
    return [
        "python3",
        str(settings.facefusion_dir / "facefusion.py"),
        "headless-run",
        "--source-paths",
        job.source_path,
        "--target-path",
        job.target_path,
        "--output-path",
        str(output_path),
        *preset.to_facefusion_args(),
    ]


def validate_job_files(job: JobRecord) -> None:
    source = Path(job.source_path)
    target = Path(job.target_path)
    if not source.exists():
        raise FileNotFoundError(f"Source file not found: {source}")
    if not target.exists():
        raise FileNotFoundError(f"Target file not found: {target}")
    if source.suffix.lower() not in IMAGE_EXTENSIONS:
        raise ValueError("Source must be an image.")
    if job.kind == JobKind.image and target.suffix.lower() not in IMAGE_EXTENSIONS:
        raise ValueError("Image jobs require an image target.")
    if job.kind == JobKind.video and target.suffix.lower() not in VIDEO_EXTENSIONS:
        raise ValueError("Video jobs require a video target.")


def run_job(job_id: str) -> JobRecord:
    job = store.get(job_id)
    if not job:
        raise ValueError(f"Job not found: {job_id}")

    job.status = JobStatus.running
    job.progress = 5
    job.log_path = str(settings.log_dir / f"{job.id}.log")
    job.output_path = str(output_path_for(job))
    store.upsert(job)

    try:
        validate_job_files(job)
        cmd = build_facefusion_command(job)
        env = os.environ.copy()
        env.setdefault("PYTHONUNBUFFERED", "1")
        started = time.time()

        with Path(job.log_path).open("w", encoding="utf-8") as log:
            log.write("FaceDeploy backend runner\n")
            log.write("Command:\n")
            log.write(" ".join(shlex.quote(part) for part in cmd) + "\n\n")
            log.flush()
            result = subprocess.run(
                cmd,
                cwd=str(settings.facefusion_dir),
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
            )
            log.write(f"\nExit code: {result.returncode}\n")
            log.write(f"Elapsed seconds: {time.time() - started:.1f}\n")

        output = Path(job.output_path)
        if result.returncode != 0 or not output.exists() or output.stat().st_size == 0:
            raise RuntimeError(f"Processing failed. See log: {job.log_path}")

        job.status = JobStatus.done
        job.progress = 100
        job.error = None
        return store.upsert(job)
    except Exception as exc:  # noqa: BLE001
        job.status = JobStatus.failed
        job.progress = 100
        job.error = str(exc)
        return store.upsert(job)


def health_report() -> HealthReport:
    gpu_visible = False
    ffmpeg_visible = shutil.which("ffmpeg") is not None
    facefusion_found = (settings.facefusion_dir / "facefusion.py").exists()
    try:
        gpu_visible = subprocess.run(["nvidia-smi"], capture_output=True, timeout=8).returncode == 0
    except Exception:
        gpu_visible = False
    ok = ffmpeg_visible and facefusion_found
    message = "Backend ready" if ok else "Backend needs attention"
    return HealthReport(
        ok=ok,
        gpu_visible=gpu_visible,
        ffmpeg_visible=ffmpeg_visible,
        facefusion_found=facefusion_found,
        data_dir=str(settings.data_dir),
        models_dir=str(settings.models_dir),
        message=message,
    )
