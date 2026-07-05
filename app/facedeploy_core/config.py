from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi"}
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS


@dataclass(frozen=True)
class Preset:
    key: str
    label: str
    description: str
    engine: str = "facefusion"
    face_swapper_model: str = "inswapper_128_fp16"
    face_enhancer_model: str | None = None
    face_enhancer_blend: int = 0
    image_quality: int = 95
    video_quality: int = 80
    video_memory_strategy: str = "moderate"

    def to_facefusion_args(self) -> list[str]:
        processors = ["face_swapper"]
        if self.face_enhancer_model:
            processors.append("face_enhancer")
        args = [
            "--execution-providers", "cuda",
            "--processors", *processors,
            "--face-swapper-model", self.face_swapper_model,
            "--output-image-quality", str(self.image_quality),
            "--output-video-quality", str(self.video_quality),
            "--video-memory-strategy", self.video_memory_strategy,
        ]
        if self.face_enhancer_model:
            args.extend([
                "--face-enhancer-model", self.face_enhancer_model,
                "--face-enhancer-blend", str(self.face_enhancer_blend),
            ])
        return args


PRESETS: dict[str, Preset] = {
    "fast": Preset(
        key="fast",
        label="Fast draft",
        description="Quick proof render for checking alignment and identity.",
        image_quality=90,
        video_quality=70,
        video_memory_strategy="moderate",
    ),
    "quality": Preset(
        key="quality",
        label="Quality default",
        description="Best daily default with light face enhancement.",
        face_enhancer_model="gfpgan_1.4",
        face_enhancer_blend=75,
        image_quality=95,
        video_quality=80,
        video_memory_strategy="moderate",
    ),
    "hollywood": Preset(
        key="hollywood",
        label="Hollywood slow",
        description="Slower final render with conservative restoration.",
        face_enhancer_model="codeformer",
        face_enhancer_blend=65,
        image_quality=98,
        video_quality=85,
        video_memory_strategy="strict",
    ),
}


@dataclass(frozen=True)
class Settings:
    data_dir: Path = field(default_factory=lambda: Path(os.environ.get("DATA_DIR", "/workspace/data")))
    facefusion_dir: Path = field(default_factory=lambda: Path(os.environ.get("FACEFUSION_DIR", "/workspace/facefusion")))
    models_dir: Path = field(default_factory=lambda: Path(os.environ.get("MODELS_DIR", "/workspace/models")))
    app_port: int = int(os.environ.get("APP_PORT", "3000"))

    @property
    def source_dir(self) -> Path:
        return self.data_dir / "source_faces"

    @property
    def target_dir(self) -> Path:
        return self.data_dir / "targets"

    @property
    def output_dir(self) -> Path:
        return self.data_dir / "outputs"

    @property
    def log_dir(self) -> Path:
        return self.data_dir / "logs"

    @property
    def job_dir(self) -> Path:
        return self.data_dir / "jobs"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "facedeploy.sqlite3"

    def ensure_dirs(self) -> None:
        for folder in [self.source_dir, self.target_dir, self.output_dir, self.log_dir, self.job_dir, self.models_dir]:
            folder.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
