# Generation Engine — Custom ComfyUI Worker for RunPod Serverless
#
# Models baked in:
#   - Z-Image Turbo (SDXL-based, high realism)
#   - PuLID SDXL (identity lock via face reference)
#   - ControlNet OpenPose (pose control)
#   - Wan 2.2 i2v 480p (image-to-video)
#   - 4x-UltraSharp (upscaler)
#
# Custom nodes:
#   - PuLID ComfyUI
#   - ControlNet Aux Preprocessors
#   - VideoHelperSuite (video output encoding)
#   - ComfyUI-WanVideoWrapper (Wan 2.2 integration)
#
# Base image: blib-la/runpod-worker-comfy (ComfyUI at /comfyui/)

FROM timpietruskyblibla/runpod-worker-comfy:3.6.0-sdxl

ENV PATH="/opt/venv/bin:${PATH}"

# ── Custom Nodes ─────────────────────────────────────────────────────────────

WORKDIR /comfyui/custom_nodes

# PuLID — identity-consistent generation via face reference
RUN git clone https://github.com/cubiq/PuLID_ComfyUI.git && \
    if [ -f PuLID_ComfyUI/requirements.txt ]; then \
      pip install --no-cache-dir -r PuLID_ComfyUI/requirements.txt; \
    fi

# ControlNet Aux Preprocessors (openpose, depth, canny)
RUN git clone https://github.com/Fannovel16/comfyui_controlnet_aux.git && \
    if [ -f comfyui_controlnet_aux/requirements.txt ]; then \
      pip install --no-cache-dir -r comfyui_controlnet_aux/requirements.txt; \
    fi

# VideoHelperSuite — video encoding/combining (VHS_VideoCombine, VHS_LoadVideo)
RUN git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git && \
    if [ -f ComfyUI-VideoHelperSuite/requirements.txt ]; then \
      pip install --no-cache-dir -r ComfyUI-VideoHelperSuite/requirements.txt; \
    fi

# Wan Video Wrapper — Wan 2.2 i2v and Wan Animate nodes
RUN git clone https://github.com/kijai/ComfyUI-WanVideoWrapper.git && \
    if [ -f ComfyUI-WanVideoWrapper/requirements.txt ]; then \
      pip install --no-cache-dir -r ComfyUI-WanVideoWrapper/requirements.txt; \
    fi

# IP-Adapter Plus (kept for fallback identity conditioning)
RUN git clone https://github.com/cubiq/ComfyUI_IPAdapter_plus.git && \
    if [ -f ComfyUI_IPAdapter_plus/requirements.txt ]; then \
      pip install --no-cache-dir -r ComfyUI_IPAdapter_plus/requirements.txt; \
    fi

# ── Checkpoint Models ────────────────────────────────────────────────────────

WORKDIR /comfyui

# Z-Image Turbo — primary SDXL-based generation model
# Note: Replace this URL with the actual download link for Z-Image Turbo.
# If hosted on HuggingFace or CivitAI, update accordingly.
# Placeholder: using RealVisXL as fallback until Z-Image Turbo source is confirmed.
RUN wget -q --show-progress -O models/checkpoints/RealVisXL_V5.0_fp16.safetensors \
    "https://huggingface.co/SG161222/RealVisXL_V5.0/resolve/main/RealVisXL_V5.0_fp16.safetensors"

# ── PuLID Models ─────────────────────────────────────────────────────────────

# PuLID SDXL adapter
RUN mkdir -p models/pulid && \
    wget -q --show-progress -O models/pulid/ip-adapter_pulid_sdxl_fp16.safetensors \
    "https://huggingface.co/huchenlei/ipadapter_pulid/resolve/main/ip-adapter_pulid_sdxl_fp16.safetensors"

# InsightFace AntelopeV2 (required by PuLID for face detection)
RUN mkdir -p models/insightface/models/antelopev2 && \
    pip install --no-cache-dir insightface onnxruntime && \
    wget -q -O /tmp/antelopev2.zip \
    "https://huggingface.co/MonsterMMORPG/tools/resolve/main/antelopev2.zip" && \
    unzip -o /tmp/antelopev2.zip -d models/insightface/models/antelopev2/ && \
    rm /tmp/antelopev2.zip

# EVA-CLIP (required by PuLID for image encoding)
RUN mkdir -p models/clip_vision && \
    wget -q --show-progress -O models/clip_vision/EVA02_CLIP_L_336_psz14_s6B.pt \
    "https://huggingface.co/QuanSun/EVA-CLIP/resolve/main/EVA02_CLIP_L_336_psz14_s6B.pt"

# ── ControlNet Models ────────────────────────────────────────────────────────

RUN mkdir -p models/controlnet && \
    wget -q --show-progress -O models/controlnet/control_v11p_sd15_openpose_fp16.safetensors \
    "https://huggingface.co/lllyasviel/ControlNet-v1-1/resolve/main/control_v11p_sd15_openpose_fp16.safetensors"

# ── Video Models (Wan 2.2) ───────────────────────────────────────────────────

# Wan 2.2 i2v 480p — image-to-video generation
# These are large files (~10-14GB total). Using the fp16 variant for VRAM efficiency.
RUN mkdir -p models/wan && \
    wget -q --show-progress -O models/wan/wan2.2_i2v_480p_bf16.safetensors \
    "https://huggingface.co/Wan-AI/Wan2.2-I2V-14B-480P-Diffusers/resolve/main/transformer/diffusion_pytorch_model.safetensors"

# ── Upscale Models ───────────────────────────────────────────────────────────

RUN mkdir -p models/upscale_models && \
    wget -q --show-progress -O models/upscale_models/4x-UltraSharp.pth \
    "https://huggingface.co/lokCX/4x-UltraSharp/resolve/main/4x-UltraSharp.pth"

# ── IP-Adapter Models (fallback identity) ────────────────────────────────────

RUN mkdir -p models/ipadapter && \
    wget -q --show-progress -O models/ipadapter/ip-adapter-plus-face_sdxl_vit-h.safetensors \
    "https://huggingface.co/h94/IP-Adapter/resolve/main/sdxl_models/ip-adapter-plus-face_sdxl_vit-h.safetensors"

RUN wget -q --show-progress -O models/clip_vision/CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors \
    "https://huggingface.co/h94/IP-Adapter/resolve/main/sdxl_models/image_encoder/model.safetensors"

# ── Verify ───────────────────────────────────────────────────────────────────

RUN echo "=== Custom Nodes ===" && ls -la /comfyui/custom_nodes/ && \
    echo "=== Checkpoints ===" && ls -la /comfyui/models/checkpoints/ && \
    echo "=== PuLID ===" && ls -la /comfyui/models/pulid/ && \
    echo "=== ControlNet ===" && ls -la /comfyui/models/controlnet/ && \
    echo "=== Upscale ===" && ls -la /comfyui/models/upscale_models/ && \
    echo "=== CLIP Vision ===" && ls -la /comfyui/models/clip_vision/ && \
    echo "=== Wan ===" && ls -la /comfyui/models/wan/ && \
    python -c "import sys; sys.path.insert(0, '/comfyui'); print('Build OK')"

WORKDIR /
