FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    COMFYUI_DIR=/workspace/ComfyUI

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    python3 \
    python3-pip \
    python3-venv \
    ffmpeg \
    wget \
    curl \
    aria2 \
    ca-certificates \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --upgrade pip setuptools wheel

RUN git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git ${COMFYUI_DIR}

WORKDIR ${COMFYUI_DIR}

# CUDA 12.4 PyTorch wheels for NVIDIA RunPod GPUs.
RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
RUN pip3 install -r requirements.txt

WORKDIR ${COMFYUI_DIR}/custom_nodes

RUN git clone --depth 1 https://github.com/ltdrdata/ComfyUI-Manager.git
RUN git clone --depth 1 https://github.com/Gourieff/comfyui-reactor-node.git
RUN git clone --depth 1 https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git
RUN git clone --depth 1 https://github.com/ltdrdata/ComfyUI-Impact-Pack.git
RUN git clone --depth 1 https://github.com/WASasquatch/was-node-suite-comfyui.git
RUN git clone --depth 1 https://github.com/Fannovel16/comfyui_controlnet_aux.git

WORKDIR ${COMFYUI_DIR}

# Install node requirements. `|| true` keeps the build usable if a node has optional/fragile extras.
RUN for req in \
      custom_nodes/comfyui-reactor-node/requirements.txt \
      custom_nodes/ComfyUI-VideoHelperSuite/requirements.txt \
      custom_nodes/ComfyUI-Impact-Pack/requirements.txt \
      custom_nodes/was-node-suite-comfyui/requirements.txt \
      custom_nodes/comfyui_controlnet_aux/requirements.txt; \
    do \
      if [ -f "$req" ]; then pip3 install -r "$req" || true; fi; \
    done

# Common packages used by face and video workflows.
RUN pip3 install \
    insightface \
    onnxruntime-gpu \
    opencv-python-headless \
    moviepy \
    imageio-ffmpeg \
    av \
    scikit-image \
    piexif \
    GitPython \
    safetensors \
    accelerate \
    transformers \
    diffusers || true

COPY scripts/ /workspace/scripts/
COPY runpod/ /workspace/runpod/
RUN chmod +x /workspace/scripts/*.sh /workspace/runpod/*.sh

EXPOSE 8188

CMD ["/workspace/runpod/start.sh"]
