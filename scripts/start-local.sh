#!/usr/bin/env bash
set -euo pipefail

echo "FaceDeploy local startup"
echo "Checking Docker..."
docker --version

echo "Checking NVIDIA GPU access from Docker..."
if docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi; then
  echo "GPU check passed."
else
  echo "GPU check failed. The app can still start, but processing may be slow or fail without CUDA."
fi

echo "Creating local workspace folders..."
mkdir -p ./workspace/data/source_faces ./workspace/data/targets ./workspace/data/outputs ./workspace/data/logs ./workspace/models

echo "Starting Docker Compose..."
docker compose up --build
