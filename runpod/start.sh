#!/usr/bin/env bash
set -euo pipefail

COMFYUI_DIR="${COMFYUI_DIR:-/workspace/ComfyUI}"
MODELS_DIR="${MODELS_DIR:-$COMFYUI_DIR/models}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8188}"

mkdir -p "$MODELS_DIR" \
  "$COMFYUI_DIR/input" \
  "$COMFYUI_DIR/output" \
  "$COMFYUI_DIR/user/default/workflows"

# Optional: set AUTO_DOWNLOAD_MODELS=true to pull starter models when the pod starts.
# Keep large models on a RunPod network volume mounted at /workspace/ComfyUI/models.
if [[ "${AUTO_DOWNLOAD_MODELS:-false}" == "true" ]]; then
  /workspace/scripts/download_models.sh
fi

cd "$COMFYUI_DIR"
exec python3 main.py --listen "$HOST" --port "$PORT"
