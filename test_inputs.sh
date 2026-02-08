#!/usr/bin/env bash
# Run the Real-ESRGAN upscaler on all images in test_inputs/ and save to outputs/
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

mkdir -p outputs outputs_denoised

echo "=== Running upscaler (2x, no denoising) on test_inputs/ ==="
uv run python upscale.py --scale 2 -i test_inputs -o outputs "$@"
echo "=== Done. Results saved to outputs/ ==="

echo ""
echo "=== Running upscaler (2x, WITH denoising) on test_inputs/ ==="
uv run python upscale.py --scale 2 --denoise -i test_inputs -o outputs_denoised --suffix _denoised "$@"
echo "=== Done. Results saved to outputs_denoised/ ==="
