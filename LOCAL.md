# FaceDeploy Local Mode

This branch is tuned for running the project on your Dell G7 first, then moving to RunPod later.

## Start here

Open PowerShell in this repo and run:

```powershell
.\scripts\start-local.ps1
```

Then open:

```text
http://localhost:3000
```

Use the `fast` preset for your first test.

## Local ports

| Port | App |
|---:|---|
| 3000 | Simple upload page |
| 7860 | Advanced UI |
| 8188 | ComfyUI |

## Local folders

Files stay in:

```text
./workspace/data/source_faces
./workspace/data/targets
./workspace/data/outputs
./workspace/data/logs
./workspace/models
```

## Useful commands

Stop everything:

```powershell
docker compose down
```

Show logs:

```powershell
docker compose logs -f
```
