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
JOB_TIMEOUT_SECONDS = int(os.environ.get("FACEFUSION_JOB_TIMEOUT_SECONDS", "1800"))
SOURCE_DIR = DATA_DIR / "source_faces"
TARGET_DIR = DATA_DIR / "targets"
OUTPUT_DIR = DATA_DIR / "outputs"
LOG_DIR = DATA_DIR / "logs"
PROJECT_DIR = DATA_DIR / "projects"
MODEL_DIR = Path(os.environ.get("MODEL_DIR", "/workspace/models"))

for folder in (SOURCE_DIR, TARGET_DIR, OUTPUT_DIR, LOG_DIR, PROJECT_DIR, MODEL_DIR):
    folder.mkdir(parents=True, exist_ok=True)

CSS = """
#hero {padding: 28px; border-radius: 24px; background: linear-gradient(135deg, #121826, #26314d); color: white; margin-bottom: 18px;}
#hero h1 {font-size: 42px; margin: 0 0 8px 0;}
#hero p {font-size: 17px; opacity: .92; max-width: 820px;}
.tile {padding: 20px; border-radius: 20px; border: 1px solid #e6e8ef; background: #ffffff; box-shadow: 0 10px 30px rgba(0,0,0,.06);}
.tile h3 {margin-top: 0;}
.step {padding: 14px 16px; border-radius: 16px; background: #f7f8fb; border: 1px solid #eceef5; margin: 8px 0;}
.good {padding: 12px 14px; border-radius: 14px; background: #eefaf2; border: 1px solid #d5f0de;}
.warn {padding: 12px 14px; border-radius: 14px; background: #fff8e8; border: 1px solid #f1dfad;}
"""


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
    if target.suffix.lower() in IMAGE_EXTENSIONS:
        return OUTPUT_DIR / f"facedeploy_{uuid.uuid4().hex[:10]}.png"
    return OUTPUT_DIR / f"facedeploy_{uuid.uuid4().hex[:10]}.mp4"


def _target_kind(target: Path) -> str:
    suffix = target.suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return "image"
    if suffix in VIDEO_EXTENSIONS:
        return "video"
    return "file"


def _run_facefusion(source: Path, target: Path, output: Path, preset_name: str) -> tuple[bool, str]:
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
    timed_out = False
    with log_path.open("w", encoding="utf-8") as log:
        log.write("Command:\n")
        log.write(" ".join(shlex.quote(part) for part in cmd) + "\n\n")
        log.flush()
        try:
            process = subprocess.run(
                cmd,
                cwd=str(FACEFUSION_DIR),
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=JOB_TIMEOUT_SECONDS,
            )
            returncode = process.returncode
        except subprocess.TimeoutExpired:
            # subprocess.run kills the child (and its output pipes) before
            # re-raising, so the process is guaranteed gone at this point --
            # a stuck job can no longer wedge the single-concurrency queue.
            timed_out = True
            returncode = -1
            log.write(f"\n\nTIMED OUT after {JOB_TIMEOUT_SECONDS}s, process killed.\n")

    elapsed = time.time() - started
    log_text = log_path.read_text(encoding="utf-8", errors="replace")[-7000:]
    ok = not timed_out and returncode == 0 and output.exists() and output.stat().st_size > 0
    status = "⏱️ Timed out" if timed_out else ("✅ Finished" if ok else "❌ Failed")
    summary = f"{status} in {elapsed:.1f}s\n\nOutput: {output if ok else 'none'}\nLog: {log_path}\n\n{log_text}"
    return ok, summary


def run_swap(source_upload, target_upload, preset_name: str, enhance: bool):
    if source_upload is None or target_upload is None:
        return None, None, "Upload both files, then press Start."

    try:
        source = _safe_copy(source_upload, SOURCE_DIR, "source", IMAGE_EXTENSIONS)
        target = _safe_copy(target_upload, TARGET_DIR, "target", allowed_targets)
        output = _output_path(target)
        ok, summary = _run_facefusion(source, target, output, preset_name)
        if ok:
            if _target_kind(output) == "image":
                return str(output), None, summary
            return None, str(output), summary
        return None, None, summary
    except Exception as exc:
        return None, None, f"Error: {exc}"


def list_projects() -> str:
    files = sorted(OUTPUT_DIR.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)[:25]
    if not files:
        return "No finished projects yet. Run your first image or video job from the Home tab."
    rows = ["| File | Size |", "|---|---:|"]
    for file in files:
        size_mb = file.stat().st_size / (1024 * 1024)
        rows.append(f"| `{file.name}` | {size_mb:.1f} MB |")
    return "\n".join(rows)


def system_check() -> str:
    checks = []
    checks.append(f"✅ Data folder: `{DATA_DIR}`")
    checks.append(f"✅ Output folder: `{OUTPUT_DIR}`")
    checks.append(f"{'✅' if FACEFUSION_DIR.exists() else '❌'} FaceFusion folder: `{FACEFUSION_DIR}`")
    try:
        result = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=8)
        checks.append("✅ NVIDIA GPU detected" if result.returncode == 0 else "⚠️ NVIDIA GPU not detected")
    except Exception:
        checks.append("⚠️ NVIDIA GPU check unavailable")
    return "\n".join(checks)


def build_job_tab(kind: str):
    is_video = kind == "video"
    title = "🎬 Video Face Swap" if is_video else "🖼️ Image Face Swap"
    target_types = ["video"] if is_video else ["image"]
    default_preset = "fast" if is_video else "quality"

    gr.Markdown(f"## {title}")
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown('<div class="step"><b>Step 1</b><br>Upload the face photo.</div>')
            source = gr.File(label="Source face", file_types=["image"], type="filepath")
        with gr.Column(scale=1):
            gr.Markdown('<div class="step"><b>Step 2</b><br>Upload the target file.</div>')
            target = gr.File(label="Target", file_types=target_types, type="filepath")
    with gr.Row():
        preset = gr.Radio(
            choices=list(PRESETS.keys()),
            value=default_preset,
            label="Quality level",
            info="Fast = tests, quality = default, hollywood = final render.",
        )
        start = gr.Button("🚀 Start", variant="primary", size="lg")
    with gr.Row():
        image_out = gr.Image(label="Image preview", visible=not is_video)
        video_out = gr.Video(label="Video preview", visible=is_video)
    download = gr.File(label="Download result")
    status = gr.Textbox(label="Status", lines=12)

    def run(source_upload, target_upload, preset_name):
        image_path, video_path, text = run_swap(source_upload, target_upload, preset_name)
        downloadable = image_path or video_path
        return image_path, video_path, downloadable, text

    start.click(run, inputs=[source, target, preset], outputs=[image_out, video_out, download, status])


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="FaceDeploy", css=CSS, theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            """
<div id="hero">
  <h1>FaceDeploy</h1>
  <p>No prompts. No node graphs. Upload files, choose a quality level, press Start, and download the result.</p>
</div>
"""
        )
        gr.Markdown(
            '<div class="warn"><b>Permission reminder:</b> only edit faces and footage you have consent to use.</div>'
        )
        with gr.Tabs():
            with gr.Tab("🏠 Home"):
                with gr.Row():
                    gr.Markdown('<div class="tile"><h3>🖼️ Image Swap</h3><p>Best for photos, posters, and thumbnails.</p><p>Go to the Image tab.</p></div>')
                    gr.Markdown('<div class="tile"><h3>🎬 Video Swap</h3><p>Best for short clips. Test 5–10 seconds first.</p><p>Go to the Video tab.</p></div>')
                    gr.Markdown('<div class="tile"><h3>📁 Projects</h3><p>Find finished outputs and logs.</p><p>Go to the Projects tab.</p></div>')
                gr.Markdown(
                    """
### Best results checklist

<div class="good">✅ Use a sharp source face photo</div>
<div class="good">✅ Match lighting and face angle when possible</div>
<div class="good">✅ Use Fast for tests, Quality for normal work, Hollywood for final renders</div>
"""
                )
            with gr.Tab("🖼️ Image"):
                build_job_tab("image")
            with gr.Tab("🎬 Video"):
                build_job_tab("video")
            with gr.Tab("📁 Projects"):
                refresh = gr.Button("Refresh projects")
                project_list = gr.Markdown(value=list_projects())
                refresh.click(list_projects, outputs=project_list)
            with gr.Tab("⚙️ Settings"):
                gr.Markdown("## Settings")
                gr.Markdown("These are visual presets. No command-line flags needed.")
                gr.Markdown("- **Fast**: quick drafts\n- **Quality**: best default\n- **Hollywood**: slower final renders")
                check = gr.Button("Run system check")
                check_out = gr.Markdown(value=system_check())
                check.click(system_check, outputs=check_out)
            with gr.Tab("🔧 Advanced"):
                gr.Markdown("Advanced tools are still available separately:")
                gr.Markdown("- FaceFusion UI: port `7860`\n- ComfyUI: port `8188`")
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
