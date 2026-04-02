# Generation Engine — RunPod ComfyUI Worker

Custom ComfyUI Docker image for RunPod Serverless with all models baked in.

## What's Included

### Custom Nodes
| Node | Purpose |
|------|---------|
| PuLID_ComfyUI | Identity-consistent generation via face reference |
| comfyui_controlnet_aux | Pose/depth/canny preprocessors |
| ComfyUI-VideoHelperSuite | Video encoding and loading |
| ComfyUI-WanVideoWrapper | Wan 2.2 i2v and animate nodes |
| ComfyUI_IPAdapter_plus | Fallback identity conditioning |

### Models
| Model | Size | Purpose |
|-------|------|---------|
| RealVisXL V5.0 fp16 | ~3.5 GB | SDXL checkpoint (fallback until Z-Image Turbo confirmed) |
| PuLID SDXL fp16 | ~1.7 GB | Face identity adapter |
| AntelopeV2 | ~0.3 GB | InsightFace detection (PuLID dependency) |
| EVA-CLIP L/336 | ~0.8 GB | Image encoder (PuLID dependency) |
| ControlNet OpenPose fp16 | ~0.7 GB | Pose control |
| Wan 2.2 i2v 480p | ~14 GB | Image-to-video generation |
| 4x-UltraSharp | ~0.07 GB | Image upscaling |
| IP-Adapter Plus Face SDXL | ~0.7 GB | Fallback identity |
| CLIP-ViT-H-14 | ~3.5 GB | Vision encoder (IP-Adapter) |

**Total image size: ~25-30 GB**

## Deploy

### Option A: GitHub Actions (recommended)

1. **Create a GitHub repo from this directory:**
   ```bash
   cd deploy
   git init
   git add .
   git commit -m "GenEngine ComfyUI worker"
   gh repo create genengine-comfyui-worker --public --push --source .
   ```

2. **Add GitHub Secrets** (repo → Settings → Secrets):
   | Secret | Value |
   |--------|-------|
   | `DOCKERHUB_USERNAME` | Your Docker Hub username |
   | `DOCKERHUB_TOKEN` | Docker Hub access token |

3. **Trigger build**: push or go to Actions → "Build GenEngine Worker" → Run workflow.

4. **Image will be pushed to**: `your-username/genengine-comfyui:latest`

### Option B: Build locally (if you have Docker)

```bash
cd deploy
docker build -t genengine-comfyui:latest .
docker push your-username/genengine-comfyui:latest
```

### Create RunPod Endpoint

1. Go to [runpod.io/console/serverless](https://www.runpod.io/console/serverless)
2. **New Endpoint** with:
   - **Container Image**: `your-username/genengine-comfyui:latest`
   - **GPU**: RTX A5000 (24GB) for images, A100 (40/80GB) for video
   - **Min Workers**: 0
   - **Max Workers**: 2
   - **Idle Timeout**: 5s
   - **Execution Timeout**: 300s (600s for video)
   - **Container Disk**: 40 GB
3. Note the **Endpoint ID**

### Connect to Engine

Update `.env`:
```env
RUNPOD_API_KEY=rpa_...
RUNPOD_ENDPOINT_ID=your-new-endpoint-id
```

## GPU Sizing

| Task | Min VRAM | Recommended GPU |
|------|----------|-----------------|
| Image generation (SDXL + PuLID) | 12 GB | RTX A5000 (24GB) |
| Image + ControlNet | 16 GB | RTX A5000 (24GB) |
| Video i2v (Wan 2.2 480p) | 24 GB | A100 40GB |
| Video + character swap | 32 GB | A100 40GB or 80GB |
| Upscale only | 8 GB | RTX A5000 |

## Cost Estimate

| GPU | $/sec | ~Image (30s) | ~Video 3s (120s) |
|-----|-------|-------------|------------------|
| RTX A5000 | $0.00025 | ~$0.008 | N/A (too small) |
| A100 40GB | $0.00076 | ~$0.023 | ~$0.091 |
| A100 80GB | $0.00120 | ~$0.036 | ~$0.144 |

## Known Issues

1. **Z-Image Turbo**: The Dockerfile currently uses RealVisXL V5.0 as the primary checkpoint.
   Once you have the Z-Image Turbo safetensors file (from CivitAI or direct download),
   replace the checkpoint download line and update `zimage_base.json` template's `ckpt_name`.

2. **Wan 2.2 model paths**: The WanVideoWrapper node may expect models in a specific
   subdirectory. If video fails, check the node's expected model path vs where we placed it.

3. **Build time**: First build takes 30-45 minutes due to large model downloads.
   Subsequent builds use Docker layer caching.

## Test

```bash
python -m generation_engine.test_connection --dry-run
```
