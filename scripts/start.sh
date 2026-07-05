#!/usr/bin/env bash
set -e

export COMFYUI_DIR=${COMFYUI_DIR:-/workspace/ComfyUI}
export DATA_DIR=${DATA_DIR:-/workspace/data}

mkdir -p "$DATA_DIR/source_faces" "$DATA_DIR/target_videos" "$DATA_DIR/workflows" "$DATA_DIR/outputs"
mkdir -p "$COMFYUI_DIR/input" "$COMFYUI_DIR/output" "$COMFYUI_DIR/models"

# Handy symlinks inside ComfyUI for RunPod file browser workflows.
ln -sfn "$DATA_DIR/source_faces" "$COMFYUI_DIR/input/source_faces"
ln -sfn "$DATA_DIR/target_videos" "$COMFYUI_DIR/input/target_videos"
ln -sfn "$DATA_DIR/outputs" "$COMFYUI_DIR/output/facedeploy_outputs"

cd "$COMFYUI_DIR"
echo "Starting ComfyUI on 0.0.0.0:8188"
python3 main.py --listen 0.0.0.0 --port 8188
