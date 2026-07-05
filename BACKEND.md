# FaceDeploy Backend Core

This branch builds the backend first and makes it the single source of truth. The UI should be added later and should call the API only.

## Source of truth

Backend ownership is centralized in:

```text
app/facedeploy_core/config.py
```

It owns:

- Folder paths
- File type rules
- Quality presets
- FaceFusion CLI arguments
- Runtime settings

The UI should not duplicate preset logic or paths.

## Backend files

```text
app/facedeploy_core/config.py   # settings and presets
app/facedeploy_core/models.py   # Pydantic models
app/facedeploy_core/store.py    # SQLite job store
app/facedeploy_core/runner.py   # processing engine wrapper
app/facedeploy_core/api.py      # FastAPI endpoints
app/server_backend.py           # API server entrypoint
```

## API endpoints

```text
GET  /api/health
GET  /api/presets
GET  /api/jobs
GET  /api/jobs/{job_id}
POST /api/jobs/image
POST /api/jobs/video
GET  /api/jobs/{job_id}/download
GET  /api/jobs/{job_id}/log
```

## Local run

```powershell
git checkout backend-core
.\scripts\start-local.ps1
```

Open API docs:

```text
http://localhost:3000/docs
```

Health check:

```text
http://localhost:3000/api/health
```

## Docker mode

Default mode on this branch is:

```text
APP_MODE=backend
```

This starts the API only on port 3000. Use this while building and testing backend behavior.

To also start ComfyUI and FaceFusion UI:

```text
APP_MODE=all
```

## Next step

Once the backend is tested, build the visual UI as a separate frontend that only talks to these API endpoints.
