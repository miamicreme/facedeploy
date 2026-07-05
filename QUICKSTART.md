# FaceDeploy Quickstart

## Ports

Expose these HTTP ports on RunPod:

- 3000: simple upload page
- 7860: FaceFusion interface
- 8188: ComfyUI

## Persistent storage

Mount your RunPod volume at:

```text
/workspace
```

## Build

```powershell
git clone https://github.com/miamicreme/facedeploy.git
cd facedeploy
docker build -t YOUR_DOCKERHUB_NAME/facedeploy:latest .
docker push YOUR_DOCKERHUB_NAME/facedeploy:latest
```

## RunPod image

```text
YOUR_DOCKERHUB_NAME/facedeploy:latest
```

## Login

All three ports require HTTP basic auth. Check the container logs on first
start for a generated password (or set `FACEDEPLOY_USER` /
`FACEDEPLOY_PASSWORD` yourself before starting the pod).

## Beginner workflow

1. Open port 3000 and log in.
2. Upload the source face image.
3. Upload the target image or video.
4. Pick `quality` first.
5. Use `fast` for tests and `hollywood` for final renders.
6. Download the output.

## Logs

Each run writes logs to:

```text
/workspace/data/logs
```

Outputs are saved to:

```text
/workspace/data/outputs
```
