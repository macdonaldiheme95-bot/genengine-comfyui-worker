# Generation Engine — Custom ComfyUI Worker for RunPod Serverless
#
# Models baked in:
#   - Z-Image Turbo (SDXL-based, high realism)
#   - PuLID SDXL (identity lock via face reference)
#   - ControlNet OpenPose (pose control)
#   - Wan 2.2 i2v 480p (image-to-video)
#   - 4x-UltraSharp (upscaler)
#   - RIFE 4.9 + FILM (frame interpolation)
#
# Custom nodes:
#   - PuLID ComfyUI
#   - ControlNet Aux Preprocessors
#   - VideoHelperSuite (video output encoding)
#   - ComfyUI-WanVideoWrapper (Wan 2.2 integration)
#   - ComfyUI-Frame-Interpolation (RIFE / FILM VFI)
#
# Base image: blib-la/runpod-worker-comfy (ComfyUI at /comfyui/)

FROM timpietruskyblibla/runpod-worker-comfy:3.6.0-sdxl

ENV PATH="/opt/venv/bin:${PATH}"

# Upgrade pip first — base image has old pip with resolver bugs
RUN pip install --no-cache-dir --upgrade pip

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
# Install accelerate first (main heavy dep), then the rest
RUN git clone https://github.com/kijai/ComfyUI-WanVideoWrapper.git && \
    pip install --no-cache-dir accelerate && \
    if [ -f ComfyUI-WanVideoWrapper/requirements.txt ]; then \
      pip install --no-cache-dir -r ComfyUI-WanVideoWrapper/requirements.txt; \
    fi

# IP-Adapter Plus (kept for fallback identity conditioning)
RUN git clone https://github.com/cubiq/ComfyUI_IPAdapter_plus.git && \
    if [ -f ComfyUI_IPAdapter_plus/requirements.txt ]; then \
      pip install --no-cache-dir -r ComfyUI_IPAdapter_plus/requirements.txt; \
    fi

# Frame Interpolation — RIFE / FILM VFI nodes. Wan renders ~16fps; interpolating
# before retiming keeps slow motion and speed ramps from stuttering.
# Pinned to the commit that was tested with the checkpoints baked in below.
# install.py is skipped: it installs cupy, which only GMFSS/M2M/STMFNet/Sepconv
# need (not RIFE/FILM). torch, torchvision and opencv-contrib-python are dropped
# from its requirements so the base image's CUDA torch and the OpenCV already
# installed by controlnet_aux stay as they are.
RUN git clone https://github.com/Fannovel16/ComfyUI-Frame-Interpolation.git && \
    git -C ComfyUI-Frame-Interpolation checkout -q 26545cc2dd95bc3d27f056016300673bdeee78f5 && \
    grep -vE '^(torch|torchvision|opencv-contrib-python)[[:space:]]*$' \
      ComfyUI-Frame-Interpolation/requirements-no-cupy.txt > /tmp/vfi-requirements.txt && \
    pip install --no-cache-dir -r /tmp/vfi-requirements.txt && \
    rm /tmp/vfi-requirements.txt && \
    { python -c "import cv2" || pip install --no-cache-dir opencv-python-headless; }

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
    python -c "import zipfile; zipfile.ZipFile('/tmp/antelopev2.zip').extractall('models/insightface/models/antelopev2/')" && \
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

# ── Frame Interpolation Models ───────────────────────────────────────────────

# RIFE 4.9 (fast; the node's default) and FILM (slower; better on large motion).
# Baked into the node's ckpts/ folder so cold starts don't download them.
# Checksums pin the exact files that were tested.
RUN VFI=custom_nodes/ComfyUI-Frame-Interpolation/ckpts && \
    mkdir -p $VFI/rife $VFI/film && \
    wget -q --show-progress -O $VFI/rife/rife49.pth \
    "https://github.com/Fannovel16/ComfyUI-Frame-Interpolation/releases/download/models/rife49.pth" && \
    wget -q --show-progress -O $VFI/film/film_net_fp32.pt \
    "https://github.com/dajes/frame-interpolation-pytorch/releases/download/v1.0.0/film_net_fp32.pt" && \
    printf '%s  %s\n' \
      e55fd00f3cc184e3c65961f4bb827a9da022e78eed36b055242c0ac30000d533 $VFI/rife/rife49.pth \
      10aadc0d25ad586e3af7dd7703f75ec1186fbfe2e11c0d219d30ecfe2db10aa3 $VFI/film/film_net_fp32.pt \
    | sha256sum -c -

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
    echo "=== Frame Interpolation ===" && ls -la /comfyui/custom_nodes/ComfyUI-Frame-Interpolation/ckpts/*/ && \
    python -c "import cv2, einops, kornia, scipy" && \
    python -c "import sys; sys.path.insert(0, '/comfyui'); print('Build OK')"

WORKDIR /
