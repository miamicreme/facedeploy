#!/usr/bin/env bash
set -euo pipefail

COMFYUI_DIR="${COMFYUI_DIR:-/workspace/ComfyUI}"
MODELS_DIR="${MODELS_DIR:-$COMFYUI_DIR/models}"

mkdir -p \
  "$MODELS_DIR/checkpoints" \
  "$MODELS_DIR/vae" \
  "$MODELS_DIR/upscale_models" \
  "$MODELS_DIR/facerestore_models" \
  "$MODELS_DIR/insightface" \
  "$MODELS_DIR/reactor" \
  "$MODELS_DIR/controlnet"

download_if_missing() {
  local url="$1"
  local out="$2"
  if [[ -f "$out" ]]; then
    echo "Already exists: $out"
    return 0
  fi
  echo "Downloading: $url"
  aria2c -x 8 -s 8 -k 1M --continue=true -o "$(basename "$out")" -d "$(dirname "$out")" "$url"
}

# Lightweight starter assets. Add heavier checkpoints manually to the mounted models volume.
# Real-ESRGAN general upscaler; useful for non-face detail passes.
download_if_missing \
  "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/RealESRGAN_x4plus.pth" \
  "$MODELS_DIR/upscale_models/RealESRGAN_x4plus.pth"

# CodeFormer face restoration model.
download_if_missing \
  "https://github.com/sczhou/CodeFormer/releases/download/v0.1.0/codeformer.pth" \
  "$MODELS_DIR/facerestore_models/codeformer.pth"

echo "Model download step complete."
echo "For ReActor/InsightFace, open ComfyUI once; missing face-analysis assets may be pulled by the node or can be added manually to the models volume."
