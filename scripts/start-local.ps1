$ErrorActionPreference = "Stop"

Write-Host "FaceDeploy local startup"
Write-Host "Checking Docker..."

docker --version | Out-Host

Write-Host "Checking NVIDIA GPU access from Docker..."
$gpuOk = $false
try {
  docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi | Out-Host
  $gpuOk = $true
} catch {
  Write-Host "GPU check failed. The app can still start, but processing may be slow or fail without CUDA."
}

Write-Host "Creating local workspace folders..."
New-Item -ItemType Directory -Force -Path ".\workspace\data\source_faces" | Out-Null
New-Item -ItemType Directory -Force -Path ".\workspace\data\targets" | Out-Null
New-Item -ItemType Directory -Force -Path ".\workspace\data\outputs" | Out-Null
New-Item -ItemType Directory -Force -Path ".\workspace\data\logs" | Out-Null
New-Item -ItemType Directory -Force -Path ".\workspace\models" | Out-Null

Write-Host "Starting Docker Compose..."
docker compose up --build
