FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    COMFYUI_DIR=/workspace/ComfyUI \
    FACEFUSION_DIR=/workspace/facefusion \
    DATA_DIR=/workspace/data \
    HF_HOME=/workspace/models/huggingface \
    XDG_CACHE_HOME=/workspace/models/cache

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    git python3 python3-pip python3-venv python3-dev ffmpeg wget curl ca-certificates \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 build-essential \
    nginx apache2-utils \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --upgrade pip setuptools wheel
RUN python3 -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# Pinned commit SHAs, so a rebuild months from now fetches the same code that
# was tested, not whatever the default branch happens to be that day. Bump
# these deliberately when you want to pick up upstream changes.
ENV COMFYUI_REF=985fb9d6adc974df9783d3d355cf86b992956212 \
    COMFYUI_MANAGER_REF=16a212aa706588331be163e7dbe4a0775f00282d \
    VIDEOHELPERSUITE_REF=4ee72c065db22c9d96c2427954dc69e7b908444b \
    IMPACT_PACK_REF=429d0159ad429e64d2b3916e6e7be9c22d025c3c \
    WAS_NODE_SUITE_REF=ea935d1044ae5a26efa54ebeb18fe9020af49a45 \
    KJNODES_REF=e27a505b3ba6ce42687fe00500deda103d9d6071 \
    FRAME_INTERPOLATION_REF=26545cc2dd95bc3d27f056016300673bdeee78f5 \
    CONTROLNET_AUX_REF=e8b689a513c3e6b63edc44066560ca5919c0576e \
    FACEFUSION_REF=3f81a8a78454089d720b8f318a12ae1702c4633b

# Shallow-fetches a single pinned commit instead of "whatever HEAD is today".
# Fails the build (no `|| true`) if the fetch or checkout doesn't succeed.
RUN printf '%s\n' \
      '#!/usr/bin/env bash' \
      'set -euo pipefail' \
      'url="$1"; ref="$2"; dest="$3"' \
      'mkdir -p "$dest"' \
      'git -C "$dest" init -q' \
      'git -C "$dest" remote add origin "$url"' \
      'git -C "$dest" fetch --depth 1 origin "$ref"' \
      'git -C "$dest" checkout -q FETCH_HEAD' \
      > /usr/local/bin/pinned-clone && chmod +x /usr/local/bin/pinned-clone

# ---------- ComfyUI advanced workflow backend ----------
RUN pinned-clone https://github.com/comfyanonymous/ComfyUI.git "${COMFYUI_REF}" "${COMFYUI_DIR}"
WORKDIR ${COMFYUI_DIR}
RUN python3 -m pip install -r requirements.txt

RUN pinned-clone https://github.com/ltdrdata/ComfyUI-Manager.git "${COMFYUI_MANAGER_REF}" custom_nodes/ComfyUI-Manager && \
    pinned-clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git "${VIDEOHELPERSUITE_REF}" custom_nodes/ComfyUI-VideoHelperSuite && \
    pinned-clone https://github.com/ltdrdata/ComfyUI-Impact-Pack.git "${IMPACT_PACK_REF}" custom_nodes/ComfyUI-Impact-Pack && \
    pinned-clone https://github.com/WASasquatch/was-node-suite-comfyui.git "${WAS_NODE_SUITE_REF}" custom_nodes/was-node-suite-comfyui && \
    pinned-clone https://github.com/kijai/ComfyUI-KJNodes.git "${KJNODES_REF}" custom_nodes/ComfyUI-KJNodes && \
    pinned-clone https://github.com/Fannovel16/ComfyUI-Frame-Interpolation.git "${FRAME_INTERPOLATION_REF}" custom_nodes/ComfyUI-Frame-Interpolation && \
    pinned-clone https://github.com/Fannovel16/comfyui_controlnet_aux.git "${CONTROLNET_AUX_REF}" custom_nodes/comfyui_controlnet_aux

# comfyui-reactor-node is no longer reachable as an anonymous clone (GitHub now
# returns 401 Unauthorized for it), so its commit history can't be inspected
# to pin a known-good SHA the way the other nodes above are pinned. Rather
# than let that failure disappear behind `|| true`, this is called out
# loudly at build time. Pass --build-arg REACTOR_NODE_URL=<your mirror> (and
# optionally REACTOR_NODE_REF=<sha>) if you have access to a copy of the node
# and want it pinned and installed. The FaceDeploy app (port 3000) and
# FaceFusion do not depend on this node, so it is opt-in, not required.
ARG REACTOR_NODE_URL=https://github.com/Gourieff/comfyui-reactor-node.git
ARG REACTOR_NODE_REF=HEAD
RUN if git ls-remote "${REACTOR_NODE_URL}" >/dev/null 2>&1; then \
      pinned-clone "${REACTOR_NODE_URL}" "${REACTOR_NODE_REF}" custom_nodes/comfyui-reactor-node; \
    else \
      echo ""; \
      echo "WARNING: could not reach ${REACTOR_NODE_URL} (it now requires auth to clone)."; \
      echo "WARNING: skipping the ReActor custom node. ComfyUI will start without it."; \
      echo "WARNING: to use ReActor workflows, pass --build-arg REACTOR_NODE_URL=<your mirror>"; \
      echo "WARNING: or COPY your own copy of the node into custom_nodes/comfyui-reactor-node."; \
      echo ""; \
    fi

WORKDIR ${COMFYUI_DIR}
# Third-party custom node dependencies frequently conflict with each other
# and with ComfyUI's own pins; that is a real, ongoing upstream problem, not
# something this build should hide. Each attempt is logged with a clear
# PASS/FAIL instead of being silently swallowed, and the build fails if a
# node's requirements can't even be found where expected.
RUN missing=0; \
    for req in \
      custom_nodes/comfyui-reactor-node/requirements.txt \
      custom_nodes/ComfyUI-VideoHelperSuite/requirements.txt \
      custom_nodes/ComfyUI-Impact-Pack/requirements.txt \
      custom_nodes/was-node-suite-comfyui/requirements.txt \
      custom_nodes/ComfyUI-KJNodes/requirements.txt \
      custom_nodes/ComfyUI-Frame-Interpolation/requirements.txt \
      custom_nodes/comfyui_controlnet_aux/requirements.txt; \
    do \
      if [ -f "$req" ]; then \
        if python3 -m pip install -r "$req"; then \
          echo "PASS: $req"; \
        else \
          echo "FAIL: $req (custom node install failed, see log above)"; \
          missing=1; \
        fi; \
      else \
        echo "SKIP: $req (node not present)"; \
      fi; \
    done; \
    exit "$missing"

RUN python3 -m pip install insightface onnx onnxruntime-gpu opencv-python-headless imageio-ffmpeg moviepy mediapipe

# ---------- FaceFusion beginner-friendly web UI and headless processor ----------
WORKDIR /workspace
RUN pinned-clone https://github.com/facefusion/facefusion.git "${FACEFUSION_REF}" "${FACEFUSION_DIR}"
WORKDIR ${FACEFUSION_DIR}
RUN python3 -m pip install -r requirements.txt
RUN python3 -m pip install gradio fastapi uvicorn pydantic pyyaml python-multipart

# ---------- FaceDeploy upload wrapper ----------
COPY app /opt/facedeploy/app
COPY scripts/start.sh /start.sh
COPY scripts/doctor.sh /doctor.sh
COPY scripts/healthcheck.sh /healthcheck.sh
RUN chmod +x /start.sh /doctor.sh /healthcheck.sh

# nginx's default site listens on 0.0.0.0:80 with no auth; remove it so the
# only public listeners are the basic-auth-gated ones start.sh configures.
RUN rm -f /etc/nginx/sites-enabled/default

RUN mkdir -p \
    ${DATA_DIR}/source_faces ${DATA_DIR}/targets ${DATA_DIR}/workflows ${DATA_DIR}/outputs ${DATA_DIR}/logs \
    /workspace/models/facefusion /workspace/models/huggingface /workspace/models/cache \
    ${COMFYUI_DIR}/models/insightface ${COMFYUI_DIR}/models/facerestore_models ${COMFYUI_DIR}/models/upscale_models

EXPOSE 3000 7860 8188
WORKDIR /workspace
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=5 CMD /healthcheck.sh
CMD ["/start.sh"]
