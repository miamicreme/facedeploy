#!/usr/bin/env bash
set -euo pipefail

export COMFYUI_DIR=${COMFYUI_DIR:-/workspace/ComfyUI}
export FACEFUSION_DIR=${FACEFUSION_DIR:-/workspace/facefusion}
export DATA_DIR=${DATA_DIR:-/workspace/data}
export APP_PORT=${APP_PORT:-3000}
export FACEFUSION_PORT=${FACEFUSION_PORT:-7860}
export COMFYUI_PORT=${COMFYUI_PORT:-8188}
export APP_MODE=${APP_MODE:-all}

# Loopback-only ports for the real services. nginx is the only process
# allowed to bind the public ports above, and it requires HTTP basic auth.
# ComfyUI, FaceFusion, and the Gradio app have no auth of their own, and
# previously all three listened on 0.0.0.0 directly -- anyone who reached
# the RunPod URL could run jobs or drive ComfyUI with no credentials at all.
INTERNAL_APP_PORT=${INTERNAL_APP_PORT:-13000}
INTERNAL_FACEFUSION_PORT=${INTERNAL_FACEFUSION_PORT:-17860}
INTERNAL_COMFYUI_PORT=${INTERNAL_COMFYUI_PORT:-18188}
export INTERNAL_APP_PORT INTERNAL_FACEFUSION_PORT INTERNAL_COMFYUI_PORT

mkdir -p "$DATA_DIR/source_faces" "$DATA_DIR/targets" "$DATA_DIR/workflows" "$DATA_DIR/outputs" "$DATA_DIR/logs"
mkdir -p "$COMFYUI_DIR/input" "$COMFYUI_DIR/output" "$COMFYUI_DIR/models"
mkdir -p /workspace/models/facefusion /workspace/models/cache /workspace/models/huggingface

# Handy symlinks inside ComfyUI for RunPod file browser workflows.
ln -sfn "$DATA_DIR/source_faces" "$COMFYUI_DIR/input/source_faces"
ln -sfn "$DATA_DIR/targets" "$COMFYUI_DIR/input/targets"
ln -sfn "$DATA_DIR/outputs" "$COMFYUI_DIR/output/facedeploy_outputs"

setup_auth() {
  local user="${FACEDEPLOY_USER:-facedeploy}"
  local pass="${FACEDEPLOY_PASSWORD:-}"
  if [ -z "$pass" ]; then
    pass="$(head -c 18 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 20)"
    echo ""
    echo "=================================================================="
    echo " No FACEDEPLOY_PASSWORD set -- generated one for this container:"
    echo "   user:     $user"
    echo "   password: $pass"
    echo " Set FACEDEPLOY_USER / FACEDEPLOY_PASSWORD env vars to pick your own."
    echo "=================================================================="
    echo ""
  fi
  htpasswd -bc /etc/nginx/.htpasswd "$user" "$pass" >/dev/null
}

write_nginx_conf() {
  mkdir -p /etc/nginx/conf.d
  : > /etc/nginx/conf.d/facedeploy.conf
  for entry in "${APP_PORT}:${INTERNAL_APP_PORT}" "${FACEFUSION_PORT}:${INTERNAL_FACEFUSION_PORT}" "${COMFYUI_PORT}:${INTERNAL_COMFYUI_PORT}"; do
    public="${entry%%:*}"
    internal="${entry##*:}"
    cat >> /etc/nginx/conf.d/facedeploy.conf <<CONF
server {
    listen 0.0.0.0:${public};
    client_max_body_size 4096m;
    location / {
        auth_basic "FaceDeploy";
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://127.0.0.1:${internal};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_read_timeout 3600s;
    }
}
CONF
  done
}

show_urls() {
  echo ""
  echo "FaceDeploy services are starting (HTTP basic-auth protected):"
  echo "  Simple upload app: http://0.0.0.0:${APP_PORT}"
  echo "  FaceFusion UI:     http://0.0.0.0:${FACEFUSION_PORT}"
  echo "  ComfyUI:           http://0.0.0.0:${COMFYUI_PORT}"
  echo ""
}

# Restarts "$@" whenever it exits, so a ComfyUI/FaceFusion crash is noticed
# and recovered instead of leaving the container silently half-working.
watchdog() {
  local name="$1"; shift
  local pidfile="$DATA_DIR/logs/${name}.pid"
  local logfile="$DATA_DIR/logs/${name}.log"
  (
    while true; do
      "$@" >>"$logfile" 2>&1 &
      local pid=$!
      echo "$pid" > "$pidfile"
      # `wait` failing is the crash case this loop exists to catch, so it
      # must not trip `set -e` (inherited into this subshell) before the
      # restart below runs.
      local code=0
      wait "$pid" || code=$?
      echo "$(date -u +%FT%TZ) ${name} exited (code ${code}), restarting in 3s" >> "$logfile"
      sleep 3
    done
  ) &
}

start_nginx() {
  setup_auth
  write_nginx_conf
  nginx -t
  watchdog nginx nginx -g 'daemon off;'
}

start_comfyui() {
  cd "$COMFYUI_DIR"
  echo "Starting ComfyUI (internal) on 127.0.0.1:${INTERNAL_COMFYUI_PORT}"
  watchdog comfyui python3 main.py --listen 127.0.0.1 --port "$INTERNAL_COMFYUI_PORT"
}

# FaceFusion command flags change between versions, so try --host first and
# fall back to --listen; keep it best-effort and do not block the beginner app.
run_facefusion_ui() {
  python3 facefusion.py run --host 127.0.0.1 --port "$INTERNAL_FACEFUSION_PORT" || \
  python3 facefusion.py run --listen 127.0.0.1 --port "$INTERNAL_FACEFUSION_PORT"
}

start_facefusion_ui() {
  cd "$FACEFUSION_DIR"
  echo "Starting FaceFusion (internal) on 127.0.0.1:${INTERNAL_FACEFUSION_PORT}"
  watchdog facefusion run_facefusion_ui
}

start_facedeploy_app() {
  cd /opt/facedeploy/app
  echo "FaceDeploy upload app (internal) on 127.0.0.1:${INTERNAL_APP_PORT}"
  watchdog app python3 server.py --host 127.0.0.1 --port "$INTERNAL_APP_PORT"
}

case "$APP_MODE" in
  app)
    start_nginx
    show_urls
    start_facedeploy_app
    wait
    ;;
  comfyui)
    start_nginx
    echo "ComfyUI available at http://0.0.0.0:${COMFYUI_PORT} (basic auth)"
    start_comfyui
    wait
    ;;
  facefusion)
    start_nginx
    echo "FaceFusion available at http://0.0.0.0:${FACEFUSION_PORT} (basic auth)"
    start_facefusion_ui
    wait
    ;;
  shell)
    exec /bin/bash
    ;;
  all|*)
    start_nginx
    show_urls
    start_comfyui
    start_facefusion_ui
    start_facedeploy_app
    wait
    ;;
esac
