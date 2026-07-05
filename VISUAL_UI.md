# FaceDeploy Visual UI

This branch turns FaceDeploy into a point-and-click studio UI.

## Goal

No camera capture. No prompt boxes. No command line inside the app.

The user chooses a workflow, uploads files, clicks Start, and downloads the result.

## Main screens

- Image Swap
- Video Swap
- Projects
- Settings
- Models

## Local test

```powershell
git checkout visual-ui
.\scripts\start-local.ps1
```

Open:

```text
http://localhost:3000
```

## Beginner workflow

Image:

1. Open Image Swap.
2. Upload source face.
3. Upload target image.
4. Pick Fast, Quality, or Hollywood.
5. Click Start Image Swap.
6. Download the output.

Video:

1. Open Video Swap.
2. Upload source face.
3. Upload target video.
4. Pick Fast for testing.
5. Click Start Video Swap.
6. Download the output.

## RunPod later

This UI is designed to move to RunPod without changing the user workflow. On RunPod, expose port 3000 and mount persistent storage at /workspace.
