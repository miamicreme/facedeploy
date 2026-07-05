# Operational Readiness Assessment — FaceDeploy

**Verdict: operationally ready for single-tenant RunPod use. Overall rating: 8/10.**

The six remediation items below have all been implemented. What's left
(no disk quota/cleanup policy, no automated model fetch/verification) is
lower-severity and reasonable to defer for a hobbyist single-GPU deployment.

## Scoring (after remediation)

| Category | Rating | Notes |
|---|---|---|
| Build reproducibility | 8/10 | `Dockerfile` pins every clone to a specific commit SHA via a `pinned-clone` helper (shallow-fetch by SHA, not by branch), and custom node `pip install` failures are logged PASS/FAIL and fail the build instead of being swallowed by `\|\| true`. The one exception, `comfyui-reactor-node`, currently 401s on an anonymous clone (its upstream repo now requires auth) — the build detects this, logs a loud `WARNING`, and continues without it rather than pretending to succeed; `--build-arg REACTOR_NODE_URL=<mirror>` is documented for anyone with access to their own copy. |
| Documentation accuracy | 8/10 | `README.md`/`RUNPOD.md`/`QUICKSTART.md` now match the actual repo layout (`app/presets.py`, `models_manifest/`, real `APP_MODE` values and default, real `/workspace/data/targets` path) instead of pointing at files that don't exist. |
| Security | 7/10 | All three ports now sit behind an nginx reverse proxy requiring HTTP basic auth (`FACEDEPLOY_USER`/`FACEDEPLOY_PASSWORD`, or an auto-generated password printed once to logs); ComfyUI, FaceFusion, and the Gradio app themselves bind loopback-only. nginx's default unauthenticated site on port 80 is removed. Not a 10/10 because basic auth over plain HTTP (no TLS termination here) is still a floor, not a ceiling — fine behind RunPod's proxy for single-operator use, not a multi-tenant-grade control. |
| Testing / CI | 6/10 | Added `.github/workflows/ci.yml`: Python compiles, all shell scripts pass `bash -n` and shellcheck, Dockerfile is linted with hadolint, and `docker-compose.yml` is validated. It deliberately does not do a full `docker build` of the multi-GB CUDA image (impractical on free-tier runners) — that's the main remaining gap. |
| Observability | 7/10 | `start.sh` now runs ComfyUI, FaceFusion, the app, and nginx all under a shared watchdog that restarts a crashed process and logs the restart with a timestamp and exit code. `healthcheck.sh` checks the actual per-mode PID files plus the app's HTTP endpoint, so a crashed backend is now reported as unhealthy instead of always green. Log aggregation/rotation and alerting are still absent. |
| Error handling / recovery | 8/10 | The watchdog covers the "crash is silent and permanent" gap. `app/server.py`'s FaceFusion subprocess call now has a configurable timeout (`FACEFUSION_JOB_TIMEOUT_SECONDS`, default 30 min); `subprocess.run` kills the child on timeout, so a stuck job can no longer wedge the single-concurrency queue forever. |
| Resource management | 5/10 | Unchanged — Gradio queue concurrency is still capped at 1 (appropriate for one GPU), but there's still no quota/cleanup policy for `data/outputs`, `data/logs`, or uploaded files. Left as-is; out of scope for this pass. |
| Model management | 4/10 | Unchanged — placement is documented but fetching/verifying models is still a manual step. Left as-is; out of scope for this pass. |

## What's still open

- No automatic cleanup/rotation for `data/outputs`, `data/logs`, or uploaded source/target files — the volume grows unbounded over time.
- No automated model download/verification step for a fresh pod.
- CI does not attempt a real `docker build` (cost/time trade-off for a multi-GB CUDA image); a nightly or manually-triggered full build job would close this gap if needed.
- Basic auth over plain HTTP is a floor, not a ceiling, for anything beyond single-operator RunPod use — put a TLS-terminating proxy in front if this is ever exposed more broadly.
