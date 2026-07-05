#!/usr/bin/env bash
set -e
PORT=${APP_PORT:-3000}
curl -fsS "http://127.0.0.1:${PORT}/" >/dev/null
