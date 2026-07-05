from __future__ import annotations

from facedeploy_core.config import ALLOWED_EXTENSIONS, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, PRESETS as CORE_PRESETS

# Compatibility shim for older Gradio prototype code.
# New UI work should import facedeploy_core.config directly.
PRESETS: dict[str, dict[str, object]] = {
    key: {
        "label": preset.label,
        "description": preset.description,
        "args": preset.to_facefusion_args(),
    }
    for key, preset in CORE_PRESETS.items()
}
