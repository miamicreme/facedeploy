#!/usr/bin/env bash
set -euo pipefail

export COMFYUI_DIR=${COMFYUI_DIR:-/workspace/ComfyUI}
export FACEFUSION_DIR=${FACEFUSION_DIR:-/workspace/facefusion}
export DATA_DIR=${DATA_DIR:-/workspace/data}
export MODELS_DIR=${MODELS_DIR:-/workspace/models}
export APP_PORT=${APP_PORT:-3000}
export FACEFUSION_PORT=${FACEFUSION_PORT:-7860}
export COMFYUI_PORT=${COMFYUI_PORT:-8188}
export APP_MODE=${APP_MODE:-backend}

mkdir -p "$DATA_DIR/source_faces" "$DATA_DIR/targets" "$DATA_DIR/workflows" "$DATA_DIR/outputs" "$DATA_DIR/logs" "$DATA_DIR/jobs"
mkdir -p "$COMFYUI_DIR/input" "$COMFYUI_DIR/output" "$COMFYUI_DIR/models"
mkdir -p "$MODELS_DIR/facefusion" "$MODELS_DIR/cache" "$MODELS_DIR/huggingface"

ln -sfn "$DATA_DIR/source_faces" "$COMFYUI_DIR/input/source_faces"
ln -sfn "$DATA_DIR/targets" "$COMFYUI_DIR/input/targets"
ln -sfn "$DATA_DIR/outputs" "$COMFYUI_DIR/output/facedeploy_outputs"

show_urls() {
  echo ""
  echo "FaceDeploy services are starting:"
  echo "  Backend API:       http://0.0.0.0:${APP_PORT}/api/health"
  echo "  API docs:          http://0.0.0.0:${APP_PORT}/docs"
  echo "  FaceFusion UI:     http://0.0.0.0:${FACEFUSION_PORT}"
  echo "  ComfyUI:           http://0.0.0.0:${COMFYUI_PORT}"
  echo ""
}

start_comfyui() {
  cd "$COMFYUI_DIR"
  echo "Starting ComfyUI on 0.0.0.0:${COMFYUI_PORT}"
  python3 main.py --listen 0.0.0.0 --port "$COMFYUI_PORT" > "$DATA_DIR/logs/comfyui.log" 2>&1 &
}

start_facefusion_ui() {
  cd "$FACEFUSION_DIR"
  echo "Starting FaceFusion UI on 0.0.0.0:${FACEFUSION_PORT}"
  python3 facefusion.py run --host 0.0.0.0 --port "$FACEFUSION_PORT" > "$DATA_DIR/logs/facefusion-ui.log" 2>&1 || \
  python3 facefusion.py run --listen 0.0.0.0 --port "$FACEFUSION_PORT" > "$DATA_DIR/logs/facefusion-ui.log" 2>&1 || true &
}

start_backend() {
  cd /opt/facedeploy/app
  echo "FaceDeploy backend API running on port ${APP_PORT}"
  exec python3 server_backend.py --host 0.0.0.0 --port "$APP_PORT"
}

case "$APP_MODE" in
  backend)
    show_urls
    start_backend
    ;;
  all)
    show_urls
    start_comfyui
    start_facefusion_ui
    start_backend
    ;;
  comfyui)
    cd "$COMFYUI_DIR"
    exec python3 main.py --listen 0.0.0.0 --port "$COMFYUI_PORT"
    ;;
  facefusion)
    cd "$FACEFUSION_DIR"
    exec python3 facefusion.py run --host 0.0.0.0 --port "$FACEFUSION_PORT"
    ;;
  shell)
    exec /bin/bash
    ;;
  *)
    echo "Unknown APP_MODE=$APP_MODE"
    exit 1
    ;;
esac
