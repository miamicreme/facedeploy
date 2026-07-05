from __future__ import annotations

import argparse
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
PROJECT_DIR = DATA_DIR / "projects"
MODEL_DIR = Path(os.environ.get("MODEL_DIR", "/workspace/models"))

for folder in (SOURCE_DIR, TARGET_DIR, OUTPUT_DIR, LOG_DIR, PROJECT_DIR, MODEL_DIR):
    folder.mkdir(parents=True, exist_ok=True)

APP_CSS = """
.gradio-container { max-width: 1220px !important; }
.fd-hero {
  border-radius: 28px; padding: 30px; margin-bottom: 18px;
  background: linear-gradient(135deg, rgba(56,120,255,.18), rgba(176,83,255,.16));
  border: 1px solid rgba(255,255,255,.14);
}
.fd-hero h1 { font-size: 42px; margin: 0 0 8px 0; letter-spacing: -1px; }
.fd-hero p { font-size: 17px; opacity: .88; margin: 0; }
.fd-card { border-radius: 22px; padding: 18px; border: 1px solid rgba(255,255,255,.12); }
.fd-step { font-weight: 700; font-size: 18px; margin-bottom: 8px; }
.fd-big button { min-height: 54px; font-size: 18px !important; font-weight: 700 !important; border-radius: 16px !important; }
.fd-pill { display:inline-block; padding:6px 10px; border-radius:999px; background:rgba(120,120,120,.14); margin:3px; }
.fd-footer { opacity:.75; font-size:13px; margin-top:16px; }
"""


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
    if target.suffix.lower() in IMAGE_EXTENSIONS:
        return OUTPUT_DIR / f"facedeploy_{uuid.uuid4().hex[:10]}.png"
    return OUTPUT_DIR / f"facedeploy_{uuid.uuid4().hex[:10]}.mp4"


def _project_note(source: Path, target: Path, output: Path, preset_name: str, ok: bool, elapsed: float) -> None:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    project = PROJECT_DIR / f"{output.stem}.txt"
    project.write_text(
        "\n".join([
            f"created={stamp}",
            f"status={'done' if ok else 'failed'}",
            f"preset={preset_name}",
            f"source={source}",
            f"target={target}",
            f"output={output}",
            f"seconds={elapsed:.1f}",
        ]),
        encoding="utf-8",
    )


def _run_facefusion(source: Path, target: Path, output: Path, preset_name: str, enhance: bool = True) -> tuple[bool, str]:
    preset = PRESETS[preset_name]
    log_path = LOG_DIR / f"run_{output.stem}.log"
    args = list(preset["args"])
    if not enhance:
        args = [item for item in args if item != "face_enhancer"]

    cmd = [
        "python3",
        str(FACEFUSION_DIR / "facefusion.py"),
        "headless-run",
        "--source-paths",
        str(source),
        "--target-path",
        str(target),
        "--output-path",
        str(output),
    ] + args

    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")

    started = time.time()
    with log_path.open("w", encoding="utf-8") as log:
        log.write("Command:\n")
        log.write(" ".join(shlex.quote(part) for part in cmd) + "\n\n")
        log.flush()
        process = subprocess.run(cmd, cwd=str(FACEFUSION_DIR), env=env, stdout=log, stderr=subprocess.STDOUT, text=True)

    elapsed = time.time() - started
    log_text = log_path.read_text(encoding="utf-8", errors="replace")[-7000:]
    ok = process.returncode == 0 and output.exists() and output.stat().st_size > 0
    _project_note(source, target, output, preset_name, ok, elapsed)
    status = "✅ Finished" if ok else "❌ Failed"
    summary = f"{status} in {elapsed:.1f}s\n\nSaved to: {output}\nLog: {log_path}\n\n{log_text}"
    return ok, summary


def run_swap(source_upload, target_upload, preset_name: str, enhance: bool):
    if source_upload is None or target_upload is None:
        return None, "Upload both a source face image and a target image/video."
    try:
        source = _safe_copy(source_upload, SOURCE_DIR, "source")
        target = _safe_copy(target_upload, TARGET_DIR, "target")
        output = _output_path(target)
        ok, summary = _run_facefusion(source, target, output, preset_name, enhance)
        return (str(output) if ok else None), summary
    except Exception as exc:
        return None, f"Error: {exc}"


def run_image(source_upload, target_upload, preset_name: str, enhance: bool):
    if target_upload and Path(target_upload).suffix.lower() not in IMAGE_EXTENSIONS:
        return None, "This tile is for images only. Use the Video tab for videos."
    return run_swap(source_upload, target_upload, preset_name, enhance)


def run_video(source_upload, target_upload, preset_name: str, enhance: bool):
    if target_upload and Path(target_upload).suffix.lower() not in VIDEO_EXTENSIONS:
        return None, "This tile is for videos only. Use the Image tab for images."
    return run_swap(source_upload, target_upload, preset_name, enhance)


def list_projects() -> str:
    outputs = sorted(OUTPUT_DIR.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)[:30]
    if not outputs:
        return "No projects yet. Run your first image or video swap."
    rows = []
    for path in outputs:
        size_mb = path.stat().st_size / (1024 * 1024)
        mtime = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        rows.append(f"- **{path.name}** · {size_mb:.1f} MB · {mtime} · `{path}`")
    return "\n".join(rows)


def _check_command(label: str, cmd: list[str], first_line: bool = False, allow_fail: bool = False) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        text = (result.stdout or result.stderr or "").strip()
        if first_line:
            text = text.splitlines()[0] if text else "OK"
        icon = "✅" if result.returncode == 0 else "⚠️"
        return f"{icon} **{label}:** {text}"
    except Exception as exc:
        icon = "⚠️" if allow_fail else "❌"
        return f"{icon} **{label}:** {exc}"


def system_check() -> str:
    lines = ["### Local system check"]
    lines.append(_check_command("Python", ["python3", "--version"]))
    lines.append(_check_command("FFmpeg", ["ffmpeg", "-version"], first_line=True))
    lines.append(_check_command("NVIDIA GPU", ["nvidia-smi"], first_line=True, allow_fail=True))
    lines.append(f"Models folder: `{MODEL_DIR}`")
    lines.append(f"Outputs folder: `{OUTPUT_DIR}`")
    return "\n".join(lines)


def repair_folders() -> str:
    for folder in (SOURCE_DIR, TARGET_DIR, OUTPUT_DIR, LOG_DIR, PROJECT_DIR, MODEL_DIR):
        folder.mkdir(parents=True, exist_ok=True)
    return "✅ Folders checked and repaired."


def preset_cards() -> str:
    return """
<span class="fd-pill">Fast: quick drafts</span>
<span class="fd-pill">Quality: best normal default</span>
<span class="fd-pill">Hollywood: slower final render</span>
"""


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="FaceDeploy Local", css=APP_CSS, theme=gr.themes.Soft()) as demo:
        gr.HTML("""
<div class="fd-hero">
  <h1>FaceDeploy Local</h1>
  <p>Visual upload workflow. No cameras. No prompts. No node graphs. Upload files, choose quality, click Start.</p>
</div>
""")
        gr.Markdown("Use only with faces and footage you have permission to edit. Do not use this to impersonate, deceive, harass, or create non-consensual intimate content.")

        with gr.Tabs():
            with gr.Tab("🖼️ Swap Image"):
                gr.HTML('<div class="fd-card"><div class="fd-step">Image workflow</div>Upload a face photo and a target image. Then click Start.</div>')
                with gr.Row():
                    img_source = gr.File(label="1. Source face image", file_types=["image"], type="filepath")
                    img_target = gr.File(label="2. Target image", file_types=["image"], type="filepath")
                with gr.Row():
                    img_preset = gr.Radio(choices=[("Fast", "fast"), ("Quality", "quality"), ("Hollywood", "hollywood")], value="quality", label="3. Quality level")
                    img_enhance = gr.Checkbox(value=True, label="Face enhancement")
                gr.HTML(preset_cards())
                with gr.Row(elem_classes=["fd-big"]):
                    img_run = gr.Button("Start Image Swap", variant="primary")
                img_output = gr.File(label="Download result")
                img_log = gr.Textbox(label="Progress and result log", lines=10)
                img_run.click(run_image, inputs=[img_source, img_target, img_preset, img_enhance], outputs=[img_output, img_log])

            with gr.Tab("🎬 Swap Video"):
                gr.HTML('<div class="fd-card"><div class="fd-step">Video workflow</div>Start with a short 5–10 second 720p clip on your Dell G7.</div>')
                with gr.Row():
                    vid_source = gr.File(label="1. Source face image", file_types=["image"], type="filepath")
                    vid_target = gr.File(label="2. Target video", file_types=["video"], type="filepath")
                with gr.Row():
                    vid_preset = gr.Radio(choices=[("Fast", "fast"), ("Quality", "quality"), ("Hollywood", "hollywood")], value="fast", label="3. Quality level")
                    vid_enhance = gr.Checkbox(value=True, label="Face enhancement")
                gr.HTML(preset_cards())
                with gr.Row(elem_classes=["fd-big"]):
                    vid_run = gr.Button("Start Video Swap", variant="primary")
                vid_output = gr.File(label="Download result")
                vid_log = gr.Textbox(label="Progress and result log", lines=10)
                vid_run.click(run_video, inputs=[vid_source, vid_target, vid_preset, vid_enhance], outputs=[vid_output, vid_log])

            with gr.Tab("📁 My Projects"):
                gr.Markdown("Outputs from previous runs appear here.")
                refresh = gr.Button("Refresh Projects")
                projects = gr.Markdown(list_projects())
                refresh.click(list_projects, outputs=projects)

            with gr.Tab("⚙️ Settings"):
                gr.Markdown("""
### Simple settings

The beginner app keeps the hard settings hidden. Use these defaults locally:

- Images: `Quality`
- Short test videos: `Fast`
- Final local image renders: `Hollywood`
- Final long video renders: RunPod later
""")
                check = gr.Button("Run System Check")
                repair = gr.Button("Repair Folders")
                check_result = gr.Markdown(system_check())
                repair_result = gr.Markdown("")
                check.click(system_check, outputs=check_result)
                repair.click(repair_folders, outputs=repair_result)

            with gr.Tab("📦 Models"):
                gr.Markdown(f"""
### Models and cache

Models are stored here:

`{MODEL_DIR}`

The first run can take longer while model files initialize. Keep the `workspace` folder so files are reused.

For now this page is intentionally button-free so you do not accidentally download huge models on your Dell G7. We can add one-click model downloads later for RunPod.
""")

        gr.HTML('<div class="fd-footer">Advanced engines still run in the background: FaceFusion on port 7860 and ComfyUI on port 8188.</div>')
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
        allowed_paths=[str(DATA_DIR), str(MODEL_DIR)],
    )


if __name__ == "__main__":
    main()
