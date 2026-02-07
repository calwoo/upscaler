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

### Step 4: CLI skeleton with argparse ✅

Create `upscale.py` with argument parsing and input validation only (no model logic yet). Script should parse args, validate that input path exists, and print the parsed configuration.

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

### Step 5: Model selection and initialization ✅

Add model loading logic to `upscale.py`:

- **Select model** based on `--scale` and `--model`:
  - `general` + 4x → `RealESRGAN_x4plus` with `RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)`
  - `general` + 2x → `RealESRGAN_x2plus` with `RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=2)`
  - `anime` + 4x → `RealESRGAN_x4plus_anime_6B` with `RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=6, num_grow_ch=32, scale=4)`
- **Initialize `RealESRGANer`** with auto GPU/CPU detection:
  - `device = 'cuda' if torch.cuda.is_available() else 'cpu'`
  - `half = True` only when on CUDA
  - Model weights auto-download from GitHub releases via URL
- **Optionally init GFPGAN** if `--face-enhance` is set, using the RealESRGAN upsampler as background upsampler

**Model weight URLs** (auto-download pattern used by Real-ESRGAN):
- `https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth`
- `https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth`
- `https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth`

### Step 6: Input/output path resolution ✅

Add path handling logic:

- If input is a file → output is treated as a file path (create parent dirs)
- If input is a directory → output is treated as a directory (create if needed), collect all image files (`*.png, *.jpg, *.jpeg, *.webp, *.bmp, *.tiff`)
- Apply `--suffix` and `--format` when building output filenames

### Step 7: Image processing loop

Add the core processing logic:

- Read each image with `cv2.imread` (handle alpha channel via `cv2.IMREAD_UNCHANGED`)
- Call `upsampler.enhance(img, outscale=scale)` (or `restorer.enhance()` if face-enhance)
- Save with `cv2.imwrite` to output path
- Print progress with image name and dimensions
- Wrap each image in try/except, print errors but continue processing remaining images

### Step 8: Write usage documentation

Write `docs/usage.md` covering CLI arguments, examples, and model descriptions.

## Test Plan

### Test 1: CLI argument parsing
- Run `python upscale.py --help` and verify all arguments are listed
- Run without required args, verify it exits with an error
- Run with invalid `--scale` value (e.g. 3), verify it rejects it

### Test 2: Single image upscale (4x general)
- Create a small test image (e.g. 64x64 solid color PNG)
- Run `python upscale.py -i test.png -o output.png --scale 4`
- Verify output exists and dimensions are 256x256

### Test 3: Single image upscale (2x general)
- Run `python upscale.py -i test.png -o output_2x.png --scale 2`
- Verify output dimensions are 128x128

### Test 4: Folder batch processing
- Create a folder with 2-3 small test images
- Run `python upscale.py -i ./test_images -o ./test_output --scale 4`
- Verify all images are upscaled in the output folder

### Test 5: Output format conversion
- Run with `--format jpg` on a PNG input
- Verify output is saved as `.jpg`

### Test 6: Suffix option
- Run with `--suffix _4x`
- Verify output filename includes the suffix

### Test 7: Face enhancement
- Run with `--face-enhance` on a portrait image
- Verify GFPGAN is invoked and output is produced

### Test 8: Error handling
- Run with a non-existent input path, verify graceful error
- Place a corrupt/non-image file in a batch folder, verify it skips and continues
