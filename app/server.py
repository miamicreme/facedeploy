from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path

import gradio as gr

from presets import ALLOWED_EXTENSIONS, IMAGE_EXTENSIONS, PRESETS, VIDEO_EXTENSIONS

DATA_DIR = Path(os.environ.get("DATA_DIR", "/workspace/data"))
FACEFUSION_DIR = Path(os.environ.get("FACEFUSION_DIR", "/workspace/facefusion"))
SOURCE_DIR = DATA_DIR / "source_faces"
TARGET_DIR = DATA_DIR / "targets"
OUTPUT_DIR = DATA_DIR / "outputs"
LOG_DIR = DATA_DIR / "logs"
PROJECTS_FILE = DATA_DIR / "projects.json"

for folder in (SOURCE_DIR, TARGET_DIR, OUTPUT_DIR, LOG_DIR):
    folder.mkdir(parents=True, exist_ok=True)


def _safe_copy(upload_path: str, folder: Path, prefix: str, allowed: set[str] | None = None) -> Path:
    if not upload_path:
        raise ValueError("Choose a file first.")
    src = Path(upload_path)
    suffix = src.suffix.lower()
    valid = allowed or ALLOWED_EXTENSIONS
    if suffix not in valid:
        raise ValueError(f"Unsupported file type: {suffix}")
    dest = folder / f"{prefix}_{uuid.uuid4().hex[:10]}{suffix}"
    shutil.copy2(src, dest)
    return dest


def _output_path(target: Path) -> Path:
    suffix = target.suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return OUTPUT_DIR / f"facedeploy_{uuid.uuid4().hex[:10]}.png"
    return OUTPUT_DIR / f"facedeploy_{uuid.uuid4().hex[:10]}.mp4"


def _read_projects() -> list[dict[str, str]]:
    if not PROJECTS_FILE.exists():
        return []
    try:
        return json.loads(PROJECTS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _save_project(record: dict[str, str]) -> None:
    projects = _read_projects()
    projects.insert(0, record)
    PROJECTS_FILE.write_text(json.dumps(projects[:50], indent=2), encoding="utf-8")


def _projects_table() -> list[list[str]]:
    rows: list[list[str]] = []
    for item in _read_projects():
        rows.append([
            item.get("created", ""),
            item.get("kind", ""),
            item.get("preset", ""),
            item.get("status", ""),
            item.get("output", ""),
        ])
    return rows


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
    log_text = log_path.read_text(encoding="utf-8", errors="replace")[-5000:]
    ok = process.returncode == 0 and output.exists() and output.stat().st_size > 0
    status = "Finished" if ok else "Needs attention"
    summary = f"{status} in {elapsed:.1f}s\n\nLog tail:\n{log_text}"
    return ok, summary


def _run_swap(source_upload, target_upload, preset_name: str, kind: str, allowed_targets: set[str]):
    if source_upload is None or target_upload is None:
        return None, "Choose a source face and a target file.", _projects_table()

    try:
        source = _safe_copy(source_upload, SOURCE_DIR, "source", IMAGE_EXTENSIONS)
        target = _safe_copy(target_upload, TARGET_DIR, "target", allowed_targets)
        output = _output_path(target)
        ok, summary = _run_facefusion(source, target, output, preset_name)
        _save_project({
            "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "kind": kind,
            "preset": preset_name,
            "status": "done" if ok else "failed",
            "source": str(source),
            "target": str(target),
            "output": str(output) if ok else "",
        })
        if ok:
            return str(output), summary, _projects_table()
        return None, summary, _projects_table()
    except Exception as exc:  # noqa: BLE001 - beginner-friendly UI error
        return None, f"Error: {exc}", _projects_table()


def run_image(source_upload, target_upload, preset_name: str):
    return _run_swap(source_upload, target_upload, preset_name, "image", IMAGE_EXTENSIONS)


def run_video(source_upload, target_upload, preset_name: str):
    return _run_swap(source_upload, target_upload, preset_name, "video", VIDEO_EXTENSIONS)


def system_check() -> str:
    checks = []
    checks.append("✅ Upload folders ready" if DATA_DIR.exists() else "❌ Data folder missing")
    checks.append("✅ FaceFusion folder found" if FACEFUSION_DIR.exists() else "❌ FaceFusion folder missing")
    try:
        result = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=8)
        checks.append("✅ NVIDIA GPU visible" if result.returncode == 0 else "⚠️ NVIDIA GPU not visible")
    except Exception:
        checks.append("⚠️ NVIDIA GPU check unavailable")
    checks.append(f"📁 Outputs: {OUTPUT_DIR}")
    checks.append(f"📁 Logs: {LOG_DIR}")
    return "\n".join(checks)


def model_status() -> str:
    model_root = Path("/workspace/models")
    lines = ["Model storage", f"📁 {model_root}"]
    lines.append("✅ Model folder exists" if model_root.exists() else "⚠️ Model folder not found yet")
    lines.append("Use FaceFusion or ComfyUI once to let required models cache automatically.")
    lines.append("For RunPod later, mount persistent storage at /workspace so models are reused.")
    return "\n".join(lines)


def refresh_projects():
    return _projects_table()


CSS = """
#hero {border-radius: 24px; padding: 28px; background: linear-gradient(135deg, #111827, #312e81); color: white;}
#hero h1, #hero p {color: white;}
.workflow-card {border: 1px solid #e5e7eb; border-radius: 18px; padding: 18px; background: #ffffff;}
.big-button button {font-size: 18px !important; padding: 14px 18px !important; border-radius: 14px !important;}
.status-box textarea {font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;}
"""


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="FaceDeploy Studio", css=CSS, theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            """
<div id="hero">
<h1>FaceDeploy Studio</h1>
<p>No prompts. No cameras. Pick a workflow, upload files, press Start, download the result.</p>
</div>
"""
        )
        gr.Markdown("Use only faces and footage you have permission to edit.")

        with gr.Tabs():
            with gr.Tab("🖼️ Image Swap"):
                gr.Markdown("### Swap a face in a still image")
                with gr.Row():
                    image_source = gr.File(label="1. Source face", file_types=["image"], type="filepath")
                    image_target = gr.File(label="2. Target image", file_types=["image"], type="filepath")
                with gr.Row():
                    image_preset = gr.Radio(
                        choices=list(PRESETS.keys()),
                        value="quality",
                        label="3. Quality",
                    )
                    image_start = gr.Button("Start Image Swap", variant="primary", elem_classes=["big-button"])
                image_output = gr.File(label="4. Download finished image")
                image_status = gr.Textbox(label="Progress", lines=12, elem_classes=["status-box"])

            with gr.Tab("🎬 Video Swap"):
                gr.Markdown("### Swap a face in a video")
                with gr.Row():
                    video_source = gr.File(label="1. Source face", file_types=["image"], type="filepath")
                    video_target = gr.File(label="2. Target video", file_types=["video"], type="filepath")
                with gr.Row():
                    video_preset = gr.Radio(
                        choices=list(PRESETS.keys()),
                        value="fast",
                        label="3. Quality",
                    )
                    video_start = gr.Button("Start Video Swap", variant="primary", elem_classes=["big-button"])
                video_output = gr.File(label="4. Download finished video")
                video_status = gr.Textbox(label="Progress", lines=12, elem_classes=["status-box"])

            with gr.Tab("📁 Projects"):
                gr.Markdown("### Recent jobs")
                refresh = gr.Button("Refresh Projects")
                projects = gr.Dataframe(
                    headers=["Created", "Type", "Preset", "Status", "Output"],
                    value=_projects_table(),
                    interactive=False,
                )

            with gr.Tab("⚙️ Settings"):
                gr.Markdown("### Simple settings")
                gr.Radio(["Auto GPU", "CPU fallback"], value="Auto GPU", label="Processor")
                gr.Checkbox(value=True, label="Preserve original audio for videos")
                gr.Checkbox(value=True, label="Use face enhancement")
                gr.Dropdown(["MP4", "PNG"], value="MP4", label="Preferred output format")
                check = gr.Button("Run System Check")
                check_output = gr.Textbox(label="System status", lines=8)

            with gr.Tab("📦 Models"):
                gr.Markdown("### Models and cache")
                gr.Markdown("Models are cached automatically. For local use and RunPod later, keep `/workspace` persistent.")
                model_button = gr.Button("Check Model Storage")
                model_output = gr.Textbox(label="Model status", lines=8)

        image_start.click(run_image, inputs=[image_source, image_target, image_preset], outputs=[image_output, image_status, projects])
        video_start.click(run_video, inputs=[video_source, video_target, video_preset], outputs=[video_output, video_status, projects])
        refresh.click(refresh_projects, outputs=[projects])
        check.click(system_check, outputs=[check_output])
        model_button.click(model_status, outputs=[model_output])
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
