# FaceDeploy

Top-shelf RunPod-ready Docker setup for a high-quality ComfyUI face-swap pipeline.

This repository builds a CUDA container that launches ComfyUI on port `8188` with the core custom nodes used for high-quality face-swap and video workflows:

- ComfyUI
- ComfyUI-Manager
- ReActor face swap node
- Video Helper Suite
- Impact Pack
- Impact Subpack
- WAS Node Suite
- ControlNet Auxiliary Preprocessors
- FFmpeg
- RunPod-friendly startup scripts

> Use this only with faces and footage you have permission to use. Do not use it to impersonate, defraud, harass, or create non-consensual intimate content.

---

## What you install on your Dell G7

Your Dell G7 does **not** need to run the heavy AI workload. It only needs to build and push the Docker image. RunPod does the GPU processing.

Install these on your laptop:

1. **Docker Desktop for Windows**
2. **WSL 2 / Ubuntu**
3. **Git for Windows**
4. **Visual Studio Code**
5. A **Docker Hub** account

After installing Docker Desktop, open PowerShell and run:

```powershell
docker --version
```

Then log in to Docker Hub:

```powershell
docker login
```

---

## Build the image

Clone this repo:

```powershell
git clone https://github.com/miamicreme/facedeploy.git
cd facedeploy
```

Replace `YOUR_DOCKERHUB_NAME` with your Docker Hub username:

```powershell
docker build -t YOUR_DOCKERHUB_NAME/facedeploy:latest .
```

Push it:

```powershell
docker push YOUR_DOCKERHUB_NAME/facedeploy:latest
```

---

## Run locally for a quick smoke test

This only checks that the container launches. Your Dell G7 may not be strong enough for production processing.

```powershell
docker run --rm -it -p 8188:8188 YOUR_DOCKERHUB_NAME/facedeploy:latest
```

Open:

```text
http://localhost:8188
```

---

## RunPod setup

Create a new pod using your custom image:

```text
YOUR_DOCKERHUB_NAME/facedeploy:latest
```

Recommended GPUs:

| Level | GPU |
|---|---|
| Best value | RTX 4090 |
| Excellent | RTX 6000 Ada |
| Datacenter | L40S / A100 |

Expose port:

```text
8188 HTTP
```

Add a persistent volume mounted at:

```text
/workspace/ComfyUI/models
```

Suggested volume size:

```text
80 GB minimum
150–250 GB recommended
```

When the pod starts, open the RunPod HTTP link for port `8188`.

---

## Model placement

The image does not bake in huge model weights. This keeps the Docker image smaller and lets your RunPod volume persist models between pods.

Put models here:

```text
/workspace/ComfyUI/models
```

Useful folders:

```text
/workspace/ComfyUI/models/checkpoints
/workspace/ComfyUI/models/vae
/workspace/ComfyUI/models/upscale_models
/workspace/ComfyUI/models/controlnet
/workspace/ComfyUI/models/insightface
/workspace/ComfyUI/models/facerestore_models
```

See [`models_manifest/RECOMMENDED_MODELS.md`](models_manifest/RECOMMENDED_MODELS.md) for the full layout.

---

## Quality preset

The beginner upload app (port 3000) ships three presets, defined in [`app/presets.py`](app/presets.py):

| Preset | Use for | Notes |
|---|---|---|
| `fast` | Quick tests | Swap only, `inswapper_128_fp16`, no enhancer |
| `quality` | Default | Swap + light `gfpgan_1.4` enhancement (75% blend) |
| `hollywood` | Final renders | Swap + `codeformer` enhancement (65% blend), strict memory strategy |

If you're building a manual ComfyUI workflow instead of using the upload app, a reasonable starting point:

- Detector: RetinaFace/InsightFace where available
- Swap: ReActor / InsightFace-based swap
- Face restoration: light CodeFormer or GFPGAN, not heavy
- Mask expansion: 12–18 px
- Mask blur: 8–12 px
- Restore strength: conservative, usually 0.2–0.4
- Process video as frames for best quality
- Preserve original audio with FFmpeg

---

## Recommended workflow

For highest quality, use a frame-based workflow:

```text
Input video
  ↓
Video Helper Suite: load video / extract frames
  ↓
ReActor: swap face
  ↓
FaceDetailer: refine face region
  ↓
Light face restoration
  ↓
Color match / blend
  ↓
Video Helper Suite: combine frames
  ↓
FFmpeg: preserve original audio
```

Do short test clips first. Once the settings look right, process the full video.

---

## Container modes

Default mode (`APP_MODE=all`, or unset) launches the upload app, FaceFusion, and ComfyUI together:

```bash
APP_MODE=all       # default: app + facefusion + comfyui
APP_MODE=app       # only the upload app (port 3000)
APP_MODE=comfyui   # only ComfyUI (port 8188)
APP_MODE=facefusion # only FaceFusion (port 7860)
APP_MODE=shell     # open a shell for debugging, no services start
```

Example:

```bash
docker run --rm -it -e APP_MODE=shell YOUR_DOCKERHUB_NAME/facedeploy:latest
```

---

## Authentication

All three ports (3000, 7860, 8188) sit behind an nginx reverse proxy that
requires HTTP basic auth — none of the upload app, FaceFusion, or ComfyUI
have their own login. On first start, if `FACEDEPLOY_PASSWORD` isn't set,
a random password is generated and printed once to the container logs.
Set `FACEDEPLOY_USER` / `FACEDEPLOY_PASSWORD` yourself to pick your own
credentials instead of relying on the generated one.

---

## Troubleshooting

### The pod opens but custom nodes are missing

Open the container logs. Most failures are dependency conflicts from custom nodes. This image installs node dependencies during build, but custom node projects change often.

The `comfyui-reactor-node` clone in particular is best-effort: its upstream
repo currently requires authentication to clone anonymously, so the build
logs a `WARNING` and skips it rather than failing the whole image. If you
need ReActor-based ComfyUI workflows, rebuild with
`--build-arg REACTOR_NODE_URL=<your mirror>` pointing at a copy you have
access to. This does not affect the upload app or FaceFusion, which use
neither ComfyUI nor this node.

Inside the pod terminal (port 8188 is already bound by the nginx auth proxy, so restart ComfyUI on its internal port instead):

```bash
cd /workspace/ComfyUI
python3 main.py --listen 127.0.0.1 --port ${INTERNAL_COMFYUI_PORT:-18188}
```

### Out of memory

Use a shorter clip, lower resolution, or a stronger GPU. For best video work, use an RTX 4090 or better.

### First run is slow

Some nodes download small helper files on first use. Persistent RunPod storage prevents repeated downloads.

---

## Repo structure

```text
Dockerfile
README.md
QUICKSTART.md
RUNPOD.md
OPERATIONAL_READINESS.md
docker-compose.yml
app/server.py               # Gradio upload app (port 3000)
app/presets.py               # fast / quality / hollywood presets
app/requirements.txt
scripts/start.sh
scripts/doctor.sh
scripts/healthcheck.sh
models_manifest/RECOMMENDED_MODELS.md
workflows/README.md
```
