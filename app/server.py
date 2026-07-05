from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import time
import uuid
from pathlib import Path

import gradio as gr

from presets import ALLOWED_EXTENSIONS, IMAGE_EXTENSIONS, PRESETS

DATA_DIR = Path(os.environ.get("DATA_DIR", "/workspace/data"))
FACEFUSION_DIR = Path(os.environ.get("FACEFUSION_DIR", "/workspace/facefusion"))
SOURCE_DIR = DATA_DIR / "source_faces"
TARGET_DIR = DATA_DIR / "targets"
OUTPUT_DIR = DATA_DIR / "outputs"
LOG_DIR = DATA_DIR / "logs"

for folder in (SOURCE_DIR, TARGET_DIR, OUTPUT_DIR, LOG_DIR):
    folder.mkdir(parents=True, exist_ok=True)


def _safe_copy(upload_path: str, folder: Path, prefix: str) -> Path:
    if not upload_path:
        raise ValueError("Missing upload file.")
    src = Path(upload_path)
    suffix = src.suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {suffix}")
    dest = folder / f"{prefix}_{uuid.uuid4().hex[:10]}{suffix}"
    shutil.copy2(src, dest)
    return dest


def _output_path(target: Path) -> Path:
    suffix = target.suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return OUTPUT_DIR / f"facedeploy_{uuid.uuid4().hex[:10]}.png"
    return OUTPUT_DIR / f"facedeploy_{uuid.uuid4().hex[:10]}.mp4"


def _run_facefusion(source: Path, target: Path, output: Path, preset_name: str) -> tuple[bool, str]:
    preset = PRESETS[preset_name]
    log_path = LOG_DIR / f"run_{output.stem}.log"

    base_cmd = [
        "python3",
        str(FACEFUSION_DIR / "facefusion.py"),
        "headless-run",
        "--source-paths",
        str(source),
        "--target-path",
        str(target),
        "--output-path",
        str(output),
    ]
    cmd = base_cmd + list(preset["args"])

    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")

    started = time.time()
    with log_path.open("w", encoding="utf-8") as log:
        log.write("Command:\n")
        log.write(" ".join(shlex.quote(part) for part in cmd) + "\n\n")
        log.flush()
        process = subprocess.run(
            cmd,
            cwd=str(FACEFUSION_DIR),
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
        )

    elapsed = time.time() - started
    log_text = log_path.read_text(encoding="utf-8", errors="replace")[-9000:]
    ok = process.returncode == 0 and output.exists() and output.stat().st_size > 0
    status = "DONE" if ok else "FAILED"
    summary = f"{status} in {elapsed:.1f}s\n\nLog tail:\n{log_text}"
    return ok, summary


def run_swap(source_upload, target_upload, preset_name: str):
    if source_upload is None or target_upload is None:
        return None, "Upload both a source face image and a target image/video."

    try:
        source = _safe_copy(source_upload, SOURCE_DIR, "source")
        target = _safe_copy(target_upload, TARGET_DIR, "target")
        output = _output_path(target)
        ok, summary = _run_facefusion(source, target, output, preset_name)
        if ok:
            return str(output), summary
        return None, summary
    except Exception as exc:  # noqa: BLE001 - show helpful beginner-friendly error
        return None, f"Error: {exc}"


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="FaceDeploy") as demo:
        gr.Markdown(
            """
# FaceDeploy

Upload a **source face** and a **target image/video**, choose a preset, and download the result.

Use only with people you have permission to edit. Do not use this to impersonate, harass, deceive, or create non-consensual intimate content.
"""
        )
        with gr.Row():
            source = gr.File(label="Source face image", file_types=["image"], type="filepath")
            target = gr.File(label="Target image or video", file_types=["image", "video"], type="filepath")
        preset = gr.Dropdown(
            choices=list(PRESETS.keys()),
            value="quality",
            label="Preset",
            info="Start with quality. Use fast for tests and hollywood for final renders.",
        )
        run = gr.Button("Run face swap", variant="primary")
        output = gr.File(label="Download result")
        log = gr.Textbox(label="Status / log", lines=18)
        run.click(run_swap, inputs=[source, target, preset], outputs=[output, log])
        gr.Markdown(
            """
## Tips for better results

Use a sharp 1024px+ source face, similar lighting, and similar head angle. For long videos, test a short clip first.

Advanced users can also open FaceFusion on port `7860` and ComfyUI on port `8188`.
"""
        )
    return demo


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=3000, type=int)
    args = parser.parse_args()
    demo = build_ui()
    demo.queue(default_concurrency_limit=1).launch(
        server_name=args.host,
        server_port=args.port,
        show_api=False,
        allowed_paths=[str(DATA_DIR)],
    )


if __name__ == "__main__":
    main()
