from __future__ import annotations

from pathlib import Path

from facedeploy_core.config import PRESETS, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, settings
from facedeploy_core.models import JobKind, JobRecord
from facedeploy_core.runner import build_facefusion_command, output_path_for


def test_presets_have_cli_args() -> None:
    for key, preset in PRESETS.items():
        args = preset.to_facefusion_args()
        assert "--execution-providers" in args, key
        assert "--face-swapper-model" in args, key


def test_output_path_image() -> None:
    job = JobRecord(kind=JobKind.image, preset="quality", source_path="/tmp/source.jpg", target_path="/tmp/target.png")
    assert output_path_for(job).suffix == ".png"


def test_output_path_video() -> None:
    job = JobRecord(kind=JobKind.video, preset="fast", source_path="/tmp/source.jpg", target_path="/tmp/target.mp4")
    assert output_path_for(job).suffix == ".mp4"


def test_command_uses_single_preset_source() -> None:
    job = JobRecord(kind=JobKind.image, preset="quality", source_path="/tmp/source.jpg", target_path="/tmp/target.png")
    cmd = build_facefusion_command(job)
    assert "headless-run" in cmd
    assert "--target-path" in cmd
    assert "--output-path" in cmd


def test_settings_dirs_are_paths() -> None:
    assert isinstance(settings.data_dir, Path)
    assert IMAGE_EXTENSIONS
    assert VIDEO_EXTENSIONS
