# RunPod Quick Start

## 1. Build on your Dell G7

```powershell
git clone https://github.com/miamicreme/facedeploy.git
cd facedeploy
docker login
docker build -t YOUR_DOCKERHUB_NAME/facedeploy:latest .
docker push YOUR_DOCKERHUB_NAME/facedeploy:latest
```

## 2. Create a RunPod pod

Use image:

```text
YOUR_DOCKERHUB_NAME/facedeploy:latest
```

Expose HTTP port:

```text
8188
```

Attach persistent storage to:

```text
/workspace/ComfyUI/models
```

Optional storage:

```text
/workspace/data
```

## 3. First launch

Open the pod terminal and run:

```bash
/doctor.sh
```

Then open the HTTP link for port 8188.

## 4. Where to upload files

```text
/workspace/data/source_faces
/workspace/data/target_videos
```

Those folders are symlinked into ComfyUI input folders automatically.

## 5. Preserve original audio

```bash
ffmpeg -i swapped_video.mp4 -i original_video.mp4 \
  -map 0:v:0 -map 1:a:0? -c:v copy -c:a aac -shortest final_with_audio.mp4
```
