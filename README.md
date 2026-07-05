# FaceDeploy

RunPod-ready Docker setup for a high-quality ComfyUI face-swap and face-refinement workflow.

This repo is designed for your Dell G7 to **build and push** the image, while RunPod does the heavy GPU work.

> Use this only with people/media you have permission to edit. Do not use it to impersonate, deceive, harass, or create non-consensual sexual content.

## What you get

- CUDA/PyTorch ComfyUI container
- FFmpeg video/audio tools
- ComfyUI-Manager
- ReActor face swap node
- Video Helper Suite
- Impact Pack / FaceDetailer support
- WAS Node Suite
- KJNodes
- Frame interpolation support
- Beginner RunPod instructions
- Persistent model/data folder layout

Large model files are **not** baked into the Docker image. Mount a RunPod volume to keep models between sessions:

```text
/workspace/ComfyUI/models
```

## Beginner setup on your Dell G7

Install these:

1. Docker Desktop for Windows
2. WSL 2 Ubuntu
3. Git for Windows
4. Visual Studio Code
5. Docker Hub account

Open PowerShell:

```powershell
docker --version
docker login
git clone https://github.com/miamicreme/facedeploy.git
cd facedeploy
```

Build and push. Replace `YOUR_DOCKERHUB_NAME`:

```powershell
docker build -t YOUR_DOCKERHUB_NAME/facedeploy:latest .
docker push YOUR_DOCKERHUB_NAME/facedeploy:latest
```

## RunPod setup

Create a pod with one of these GPUs:

- Best value: RTX 4090
- Great for longer 4K jobs: A6000, L40S, A100 40GB, A100 80GB

Use custom image:

```text
YOUR_DOCKERHUB_NAME/facedeploy:latest
```

Expose HTTP port:

```text
8188
```

Mount a persistent volume at:

```text
/workspace/ComfyUI/models
```

Optional data volume:

```text
/workspace/data
```

Open the RunPod HTTP service for port `8188` to launch ComfyUI.

## Folder map

```text
/workspace/ComfyUI/input
/workspace/ComfyUI/output
/workspace/ComfyUI/models
/workspace/ComfyUI/custom_nodes
/workspace/data/source_faces
/workspace/data/target_videos
/workspace/data/workflows
/workspace/data/outputs
```

## Top-shelf workflow

Use a staged workflow instead of one-click processing:

```text
Target video
  ↓
Extract frames with Video Helper Suite
  ↓
Detect face with InsightFace / RetinaFace-style detector
  ↓
Swap with ReActor
  ↓
FaceDetailer pass
  ↓
Light CodeFormer or GFPGAN restoration
  ↓
Color-match face to frame
  ↓
Optional face-region upscale only
  ↓
Rebuild video
  ↓
Copy original audio with FFmpeg
```

Starting settings:

```text
Restoration strength: 0.20-0.40
Mask expansion: 12-24 px
Mask blur: 8-16 px
Batch size: start low, raise after stable
FPS: preserve source FPS
Codec: H.264 for compatibility, H.265 for smaller files
```

Use sharp source images with similar lighting and angle to the target footage. For difficult videos, use several source images when the workflow supports it: front, left, right, smile, neutral.

## Model placement

Use ComfyUI-Manager to download models, or place them manually:

```text
/workspace/ComfyUI/models/insightface
/workspace/ComfyUI/models/facerestore_models
/workspace/ComfyUI/models/upscale_models
/workspace/ComfyUI/models/checkpoints
/workspace/ComfyUI/models/controlnet
```

See `models_manifest/RECOMMENDED_MODELS.md` for what categories to install.

## Local test

If your laptop has NVIDIA Docker GPU support:

```powershell
docker run --gpus all -p 8188:8188 `
  -v ${PWD}\models:/workspace/ComfyUI/models `
  -v ${PWD}\data:/workspace/data `
  YOUR_DOCKERHUB_NAME/facedeploy:latest
```

If local GPU support is not configured, just build/push from your Dell G7 and run on RunPod.

## Audio restore command

If a workflow outputs silent video:

```bash
ffmpeg -i swapped_video.mp4 -i original_video.mp4 \
  -map 0:v:0 -map 1:a:0? -c:v copy -c:a aac -shortest final_with_audio.mp4
```

## Troubleshooting

### Missing nodes

Open ComfyUI-Manager, install missing custom nodes, then restart the pod.

### ReActor / InsightFace errors

In the pod terminal:

```bash
cd /workspace/ComfyUI
python3 -m pip install insightface onnxruntime-gpu
```

Then restart.

### Out of memory

Lower resolution, batch size, frame batch count, FaceDetailer crop size, or upscale factor. For 4K, process face crops instead of full frames.
