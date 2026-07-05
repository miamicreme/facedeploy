$ErrorActionPreference = "Stop"
Write-Host "Stopping FaceDeploy local containers..."
docker compose down
