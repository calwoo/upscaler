# Plan: Real-ESRGAN Image Upscaler Script

## Context

Build a CLI script from scratch in `/home/calvin/projects/upscaler` that uses Real-ESRGAN to perform super-resolution upscaling on images. The script accepts a single image or a folder of images and outputs the upscaled results. Scale factor is configurable (2x, 4x).

## Implementation Steps

### Step 1: Set up virtual environment with `uv` ✅

```bash
uv venv  # creates .venv/ using CPython 3.12.3
source .venv/bin/activate
```

### Step 2: Create `requirements.txt` ✅

```
realesrgan
basicsr
gfpgan
facexlib
opencv-python
Pillow
torch
torchvision
numpy
tqdm
```

### Step 3: Install dependencies with `uv` ✅

```bash
uv pip install -r requirements.txt
```

### Step 4: Create `upscale.py` — Main CLI Script

A single-file Python script using `argparse` with the following interface:

```
python upscale.py -i <input> -o <output> [--scale 4] [--model general] [--face-enhance] [--tile 400] [--gpu-id 0]
```

**Arguments:**
| Arg | Description | Default |
|-----|-------------|---------|
| `-i, --input` | Path to an image file or folder of images (required) | — |
| `-o, --output` | Path for output image or output folder (required) | — |
| `--scale` | Upscale factor: 2 or 4 | `4` |
| `--model` | Model choice: `general`, `anime` | `general` |
| `--face-enhance` | Enable GFPGAN face enhancement | `False` |
| `--tile` | Tile size for large images (0 = no tiling) | `0` |
| `--gpu-id` | GPU device ID, or `None` for CPU | auto-detect |
| `--suffix` | Suffix appended to output filenames (e.g., `_upscaled`) | `_upscaled` |
| `--format` | Output format: `auto`, `png`, `jpg` | `auto` (same as input) |

**Implementation logic:**

1. **Parse args** with `argparse`
2. **Select model** based on `--scale` and `--model`:
   - `general` + 4x → `RealESRGAN_x4plus` with `RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)`
   - `general` + 2x → `RealESRGAN_x2plus` with `RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=2)`
   - `anime` + 4x → `RealESRGAN_x4plus_anime_6B` with `RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=6, num_grow_ch=32, scale=4)`
3. **Initialize `RealESRGANer`** with auto GPU/CPU detection:
   - `device = 'cuda' if torch.cuda.is_available() else 'cpu'`
   - `half = True` only when on CUDA
   - Model weights auto-download from GitHub releases via URL
4. **Optionally init GFPGAN** if `--face-enhance` is set, using the RealESRGAN upsampler as background upsampler
5. **Resolve input/output paths:**
   - If input is a file → output is treated as a file path (create parent dirs)
   - If input is a directory → output is treated as a directory (create if needed), process all image files (`*.png, *.jpg, *.jpeg, *.webp, *.bmp, *.tiff`)
6. **Process each image:**
   - Read with `cv2.imread` (handles alpha channel via `cv2.IMREAD_UNCHANGED`)
   - Call `upsampler.enhance(img, outscale=scale)` (or `restorer.enhance()` if face-enhance)
   - Save with `cv2.imwrite` to output path
   - Print progress with image name and dimensions
7. **Error handling:** Wrap each image in try/except, print errors but continue processing remaining images

**Model weight URLs** (auto-download pattern used by Real-ESRGAN):
- `https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth`
- `https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth`
- `https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth`

## Verification

1. Activate venv: `source .venv/bin/activate`
2. Test single image: `python upscale.py -i test.jpg -o test_upscaled.jpg --scale 4`
3. Test folder: `python upscale.py -i ./input_images -o ./output_images --scale 2`
4. Test face enhance: `python upscale.py -i portrait.jpg -o portrait_up.png --face-enhance`
5. Verify output images exist and have expected dimensions (input dims * scale factor)
