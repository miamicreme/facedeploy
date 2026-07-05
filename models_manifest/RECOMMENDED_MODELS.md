# Recommended model categories

This repo does not redistribute model weights. Use only models whose licenses and terms allow your intended use.

## Face analysis / swap

Place InsightFace / ReActor-compatible files under:

```text
/workspace/ComfyUI/models/insightface
```

Typical category:

- InsightFace buffalo_l package
- ReActor-compatible ONNX swap model

## Face restoration

Place restoration models under:

```text
/workspace/ComfyUI/models/facerestore_models
```

Useful categories:

- CodeFormer-style restoration
- GFPGAN-style restoration

Use low restoration strength first. Heavy restoration can erase identity or create a plastic look.

## Upscale

Place upscale models under:

```text
/workspace/ComfyUI/models/upscale_models
```

Useful categories:

- 2x face/detail upscalers
- 4x general upscalers

For realism, upscale only the face crop or final frame when needed. Do not over-sharpen.

## Checkpoints / ControlNet

Only needed if your workflow uses generative repair, inpainting, or ControlNet guidance:

```text
/workspace/ComfyUI/models/checkpoints
/workspace/ComfyUI/models/controlnet
```
