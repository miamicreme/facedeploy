"""FaceDeploy backend core.

This package is the single source of truth for paths, presets, jobs, and processing.
The UI should call this backend instead of invoking FaceFusion directly.
"""

__all__ = ["config", "models", "store", "runner", "api"]
