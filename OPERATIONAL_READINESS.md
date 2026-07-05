# Operational Readiness Assessment — FaceDeploy

**Verdict: NOT operationally ready. Overall rating: 3/10.**

This is fine as a personal/hobbyist RunPod image you build and run yourself, but it does not meet the bar for a production or multi-user deployment. Below is the evidence, by category.

## Scoring

| Category | Rating | Notes |
|---|---|---|
| Build reproducibility | 2/10 | Custom nodes and FaceFusion are `git clone --depth 1` with no pinned commit/tag — a rebuild today can silently pull different code than yesterday. Several `pip install ... \|\| true` lines swallow install failures instead of failing the build. |
| Documentation accuracy | 3/10 | `README.md` references files that do not exist in the repo: `models/README.md`, `runpod-template.md`, `presets/hollywood-quality.yaml`, `scripts/download_models.py`. The actual app lives in `app/` with presets in `app/presets.py`, which the README never mentions. |
| Security | 2/10 | All three exposed ports (3000 Gradio app, 7860 FaceFusion UI, 8188 ComfyUI) are bound to `0.0.0.0` with **no authentication**. Anyone who reaches the RunPod HTTP URL can run face-swap jobs or use ComfyUI's arbitrary workflow/code-execution surface. `show_api=False` on Gradio is cosmetic, not a security control. |
| Testing / CI | 0/10 | No test suite, no `.github/workflows`, no linting configuration. Nothing verifies a change before it ships. |
| Observability | 2/10 | `healthcheck.sh` only checks that port 3000 answers; it does not check ComfyUI (8188) or FaceFusion (7860), both of which are started as background/backgrounded processes with no supervisor. If either crashes after startup, the container reports healthy anyway. Logs go to per-run files under `/workspace/data/logs` with no aggregation, rotation, or alerting. |
| Error handling / recovery | 3/10 | `app/server.py`'s `run_swap` has reasonable try/except handling. But `scripts/start.sh` launches ComfyUI and FaceFusion with `&` and no restart logic (`start_facefusion_ui` even discards its own exit code with `\|\| true`), so a crash is silent and permanent until the container restarts. `subprocess.run` for FaceFusion jobs has no timeout, so a stuck job hangs indefinitely (queue concurrency is 1, so one stuck job blocks all future jobs). |
| Resource management | 5/10 | Gradio queue is capped at concurrency 1, which is appropriate for a single-GPU pod. No disk quota / cleanup policy for `data/outputs`, `data/logs`, or uploaded source/target files — the volume will grow unbounded over time. |
| Model management | 4/10 | Model placement is documented (`models_manifest/RECOMMENDED_MODELS.md`) but there is no automated fetch/verification step; a fresh pod requires manual upload before anything works. |

## What "operational readiness" would require

1. Pin all cloned repos to a specific commit/tag and make dependency install failures fail the build (remove blanket `\|\| true`).
2. Reconcile the docs (`README.md`, `QUICKSTART.md`, `RUNPOD.md`) with what's actually in the repo, or restore the missing files.
3. Put auth (even basic) in front of ports 3000, 7860, and 8188, or document clearly that the image must never be exposed without a reverse proxy / RunPod private networking.
4. Add a process supervisor (or at least a watchdog in `start.sh`) so a crashed ComfyUI/FaceFusion process is restarted and reflected in `healthcheck.sh`.
5. Add a timeout around the FaceFusion subprocess call in `app/server.py` so a stuck job can't wedge the single-concurrency queue permanently.
6. Add at least a smoke-test CI workflow (e.g., `docker build` + `doctor.sh`-style checks) so regressions are caught before merge.

None of this is a large lift, but as of this branch none of it exists, so operational readiness has **not** been achieved.
