# Usage

## Basic Usage

```bash
# Activate the virtual environment
source .venv/bin/activate

# Upscale a single image (4x, general model)
python upscale.py -i photo.jpg -o photo_upscaled.png

# Upscale all images in a folder
python upscale.py -i ./input_images -o ./output_images
```

## CLI Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `-i, --input` | Path to an image file or folder of images (required) | — |
| `-o, --output` | Path for output image or output folder (required) | — |
| `--scale` | Upscale factor: `2` or `4` | `4` |
| `--model` | Model: `general` or `anime` | `general` |
| `--face-enhance` | Enable GFPGAN face enhancement | off |
| `--denoise` | Enable Swin2SR denoising before upscaling | off |
| `--tile` | Tile size for large images (0 = no tiling) | `0` |
| `--gpu-id` | GPU device ID (omit for auto-detect) | auto |
| `--suffix` | Suffix for output filenames in folder mode | `_upscaled` |
| `--format` | Output format: `auto`, `png`, or `jpg` | `auto` |

## Examples

### 4x upscale with general model (default)

```bash
python upscale.py -i photo.jpg -o photo_4x.png
```

### 2x upscale

```bash
python upscale.py -i photo.jpg -o photo_2x.png --scale 2
```

### Anime model

```bash
python upscale.py -i anime_screenshot.png -o anime_4x.png --model anime
```

### Face enhancement

Adds GFPGAN face restoration on top of the upscale:

```bash
python upscale.py -i portrait.jpg -o portrait_enhanced.png --face-enhance
```

### Batch folder processing

Processes all images (`.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.tiff`) in the input folder:

```bash
python upscale.py -i ./low_res/ -o ./high_res/ --scale 4
```

Output filenames get the `--suffix` appended (default: `_upscaled`):
- `low_res/photo.jpg` -> `high_res/photo_upscaled.jpg`

### Custom suffix

```bash
python upscale.py -i ./input/ -o ./output/ --suffix _4x
```

### Format conversion

Force output to JPEG regardless of input format:

```bash
python upscale.py -i photo.png -o photo_out.jpg --format jpg
```

### Denoising before upscaling

Cleans noisy or compressed images before super-resolution using a Swin2SR model. This prevents noise from being amplified during upscaling:

```bash
python upscale.py -i noisy_photo.jpg -o clean_4x.png --denoise
```

Can be combined with other flags:

```bash
python upscale.py -i ./noisy_photos/ -o ./clean_upscaled/ --denoise --scale 2
```

The Swin2SR model weights are downloaded automatically from HuggingFace on first use.

### Tiling for large images

If you run out of GPU memory on large images, use tiling:

```bash
python upscale.py -i large_photo.jpg -o large_4x.png --tile 400
```

## Models

| Model | Flag | Best For | Scale |
|-------|------|----------|-------|
| RealESRGAN_x4plus | `--model general --scale 4` | Photos, general images | 4x |
| RealESRGAN_x2plus | `--model general --scale 2` | Photos, general images | 2x |
| RealESRGAN_x4plus_anime_6B | `--model anime` | Anime, illustrations | 4x |

Model weights are downloaded automatically on first use from the Real-ESRGAN GitHub releases.

## Error Handling

- Non-existent input paths exit immediately with an error
- In batch mode, corrupt or unreadable images are skipped and processing continues
- A summary of succeeded/failed images is printed at the end
