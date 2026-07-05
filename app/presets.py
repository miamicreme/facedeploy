from __future__ import annotations

PRESETS: dict[str, dict[str, object]] = {
    "fast": {
        "label": "Fast draft",
        "description": "Quick proof for checking the face match before spending GPU time.",
        "args": [
            "--execution-providers", "cuda",
            "--processors", "face_swapper",
            "--face-swapper-model", "inswapper_128_fp16",
            "--output-image-quality", "90",
            "--output-video-quality", "70",
            "--video-memory-strategy", "moderate",
        ],
    },
    "quality": {
        "label": "Quality default",
        "description": "Strong default: swap plus light enhancement without overcooking faces.",
        "args": [
            "--execution-providers", "cuda",
            "--processors", "face_swapper", "face_enhancer",
            "--face-swapper-model", "inswapper_128_fp16",
            "--face-enhancer-model", "gfpgan_1.4",
            "--face-enhancer-blend", "75",
            "--output-image-quality", "95",
            "--output-video-quality", "80",
            "--video-memory-strategy", "moderate",
        ],
    },
    "hollywood": {
        "label": "Hollywood slow",
        "description": "Highest-quality default. Slower, cleaner, and best for final renders.",
        "args": [
            "--execution-providers", "cuda",
            "--processors", "face_swapper", "face_enhancer",
            "--face-swapper-model", "inswapper_128_fp16",
            "--face-enhancer-model", "codeformer",
            "--face-enhancer-blend", "65",
            "--output-image-quality", "98",
            "--output-video-quality", "85",
            "--video-memory-strategy", "strict",
        ],
    },
}

ALLOWED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp",
    ".mp4", ".mov", ".mkv", ".webm", ".avi",
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi"}
