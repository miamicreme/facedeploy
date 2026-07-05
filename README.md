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

See [`models/README.md`](models/README.md) for the full layout.

---

## Quality preset

The recommended quality defaults are in:

```text
presets/hollywood-quality.yaml
```

Starting point:

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

Default mode launches ComfyUI:

```bash
APP_MODE=comfyui
```

You can also open a shell for debugging:

```bash
APP_MODE=shell
```

Example:

```bash
docker run --rm -it -e APP_MODE=shell YOUR_DOCKERHUB_NAME/facedeploy:latest
```

---

## Troubleshooting

### The pod opens but custom nodes are missing

Open the container logs. Most failures are dependency conflicts from custom nodes. This image installs node dependencies during build, but custom node projects change often.

Inside the pod terminal:

```bash
cd /workspace/ComfyUI
python3 main.py --listen 0.0.0.0 --port 8188
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
docker-compose.yml
scripts/start.sh
scripts/download_models.py
presets/hollywood-quality.yaml
models/README.md
runpod-template.md
```
