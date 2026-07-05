#!/usr/bin/env bash
set -e

echo "=== GPU ==="
nvidia-smi || true

echo "=== Python ==="
python3 --version
python3 -m pip --version

echo "=== PyTorch CUDA ==="
python3 - <<'PY'
import torch
print('torch:', torch.__version__)
print('cuda available:', torch.cuda.is_available())
print('cuda version:', torch.version.cuda)
print('device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none')
PY

echo "=== FFmpeg ==="
ffmpeg -version | head -n 3 || true

echo "=== Custom nodes ==="
ls -1 /workspace/ComfyUI/custom_nodes || true
