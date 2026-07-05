#!/usr/bin/env bash
set -e

APP_MODE=${APP_MODE:-all}
DATA_DIR=${DATA_DIR:-/workspace/data}
INTERNAL_APP_PORT=${INTERNAL_APP_PORT:-13000}

# The public ports are behind nginx basic auth, so this checks the loopback
# (unauthenticated) ports the real services bind to, plus watchdog pidfiles,
# so a crashed-but-not-yet-restarted process is reported as unhealthy.
check_port() {
  curl -fsS "http://127.0.0.1:$1/" >/dev/null
}

check_pid() {
  local pidfile="$DATA_DIR/logs/$1.pid"
  [ -f "$pidfile" ] && kill -0 "$(cat "$pidfile")" 2>/dev/null
}

case "$APP_MODE" in
  app)
    check_port "$INTERNAL_APP_PORT" && check_pid app && check_pid nginx
    ;;
  comfyui)
    check_pid comfyui && check_pid nginx
    ;;
  facefusion)
    check_pid facefusion && check_pid nginx
    ;;
  shell)
    exit 0
    ;;
  all|*)
    check_port "$INTERNAL_APP_PORT" && check_pid app && check_pid comfyui && check_pid facefusion && check_pid nginx
    ;;
esac
