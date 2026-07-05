FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    COMFYUI_DIR=/workspace/ComfyUI \
    DATA_DIR=/workspace/data

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    git python3 python3-pip python3-venv python3-dev ffmpeg wget curl ca-certificates \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --upgrade pip setuptools wheel
RUN python3 -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

RUN git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git ${COMFYUI_DIR}
WORKDIR ${COMFYUI_DIR}
RUN python3 -m pip install -r requirements.txt

WORKDIR ${COMFYUI_DIR}/custom_nodes
RUN git clone --depth 1 https://github.com/ltdrdata/ComfyUI-Manager.git && \
    git clone --depth 1 https://github.com/Gourieff/comfyui-reactor-node.git && \
    git clone --depth 1 https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git && \
    git clone --depth 1 https://github.com/ltdrdata/ComfyUI-Impact-Pack.git && \
    git clone --depth 1 https://github.com/WASasquatch/was-node-suite-comfyui.git && \
    git clone --depth 1 https://github.com/kijai/ComfyUI-KJNodes.git && \
    git clone --depth 1 https://github.com/Fannovel16/ComfyUI-Frame-Interpolation.git && \
    git clone --depth 1 https://github.com/Fannovel16/comfyui_controlnet_aux.git

WORKDIR ${COMFYUI_DIR}
RUN for req in \
      custom_nodes/comfyui-reactor-node/requirements.txt \
      custom_nodes/ComfyUI-VideoHelperSuite/requirements.txt \
      custom_nodes/ComfyUI-Impact-Pack/requirements.txt \
      custom_nodes/was-node-suite-comfyui/requirements.txt \
      custom_nodes/ComfyUI-KJNodes/requirements.txt \
      custom_nodes/ComfyUI-Frame-Interpolation/requirements.txt \
      custom_nodes/comfyui_controlnet_aux/requirements.txt; \
    do \
      if [ -f "$req" ]; then python3 -m pip install -r "$req" || true; fi; \
    done

RUN python3 -m pip install insightface onnx onnxruntime-gpu opencv-python-headless imageio-ffmpeg moviepy mediapipe || true

COPY scripts/start.sh /start.sh
COPY scripts/doctor.sh /doctor.sh
RUN chmod +x /start.sh /doctor.sh

RUN mkdir -p \
    ${DATA_DIR}/source_faces ${DATA_DIR}/target_videos ${DATA_DIR}/workflows ${DATA_DIR}/outputs \
    ${COMFYUI_DIR}/models/insightface ${COMFYUI_DIR}/models/facerestore_models ${COMFYUI_DIR}/models/upscale_models

EXPOSE 8188
WORKDIR ${COMFYUI_DIR}
CMD ["/start.sh"]
