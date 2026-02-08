# Plan: Add HuggingFace Swin2SR Denoising Layer Before Super-Resolution

## Context

Noise in input images gets amplified during super-resolution. Adding a denoising preprocessing step produces significantly cleaner upscaled results. We'll use the HuggingFace `transformers` library's `Swin2SRForImageSuperResolution` model with the `caidas/swin2SR-realworld-sr-x4-64-bsrgan-psnr` checkpoint, which is trained on degraded inputs (noise, blur, compression artifacts) and produces clean restored output.

Since no pure 1:1 denoising checkpoint exists in `transformers`, the denoising step internally upscales 4x via Swin2SR then downscales back to the original resolution before feeding into Real-ESRGAN.

## Pipeline

```
Input Image (noisy)
  → [--denoise] Swin2SR 4x upscale → cv2 downscale to original res → clean image
  → Real-ESRGAN upscale → Final Output
```

## Steps

### Step 1: Create `src/denoise.py` ✅

New module with two functions:

- **`setup_denoiser(device)`** — Loads `Swin2SRForImageSuperResolution` and `AutoImageProcessor` from `caidas/swin2SR-realworld-sr-x4-64-bsrgan-psnr` via `transformers`. Places model on the given device in eval mode. Returns `(model, processor)`.

- **`denoise_image(model, processor, img, device)`** — Takes a cv2 BGR uint8 numpy array, converts to PIL RGB, runs through the Swin2SR model, converts the 4x output back to numpy, downscales to original (H, W) with `cv2.INTER_LANCZOS4`, and returns BGR uint8. Handles edge cases (grayscale → 3ch, BGRA → preserve alpha).

### Step 2: Modify `src/models.py` — return device ✅

Change `setup_model()` to return `(upsampler, face_enhancer, device)` so the denoiser can share the same device. Currently `device` is a local variable inside `setup_model`.

### Step 3: Modify `upscale.py` — add `--denoise` flag and integrate ✅

- Add `--denoise` argparse flag (`store_true`, help: "Enable Swin2SR denoising before upscaling")
- After `setup_model()`, conditionally call `setup_denoiser(device)`
- In the processing loop, after `cv2.imread` and before SR, call `denoise_image()` if enabled
- Print denoise status in the header info block

### Step 4: Update `requirements.txt` ✅

Add `transformers` (for model loading) and `huggingface_hub` (transitive dep, but explicit is better).

### Step 5: Update tests ✅

- Update `test_cli.py` to check `--denoise` flag appears in `--help` output
- Add a unit test for the `DnCNN` / denoiser setup path validation

### Step 6: Update docs ✅

- Update `docs/usage.md` with `--denoise` flag documentation

### Step 7: Install new deps and verify ✅

- `uv pip install transformers huggingface_hub` in the existing venv
- Run `pytest` to verify all tests pass
- Run a manual test with `--denoise` on a sample image (if available)

## Files to modify

| File | Action |
|---|---|
| `src/denoise.py` | **Create** — Swin2SR denoiser module |
| `src/models.py` | **Edit** — return `device` from `setup_model()` |
| `upscale.py` | **Edit** — add `--denoise` flag + integration |
| `requirements.txt` | **Edit** — add `transformers`, `huggingface_hub` |
| `tests/test_cli.py` | **Edit** — add `--denoise` to help flag list |
| `docs/usage.md` | **Edit** — document `--denoise` |

## Key transformers API usage

```python
from transformers import AutoImageProcessor, Swin2SRForImageSuperResolution

processor = AutoImageProcessor.from_pretrained("caidas/swin2SR-realworld-sr-x4-64-bsrgan-psnr")
model = Swin2SRForImageSuperResolution.from_pretrained("caidas/swin2SR-realworld-sr-x4-64-bsrgan-psnr")
model.to(device).eval()

inputs = processor(pil_image, return_tensors="pt").to(device)
with torch.no_grad():
    outputs = model(**inputs)
# outputs.reconstruction → (1, C, H*4, W*4) tensor
```

## Verification

1. `pytest` — all existing + new tests pass
2. `python upscale.py --help` — shows `--denoise` flag
3. Manual run: `python upscale.py -i sample.png -o out.png --denoise --scale 4` (if sample image available)
