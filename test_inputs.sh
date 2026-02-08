#!/usr/bin/env bash
# Run the Real-ESRGAN upscaler on all images in test_inputs/ and save to outputs/
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

mkdir -p outputs

echo "=== Running upscaler on test_inputs/ ==="
uv run python upscale.py --scale 2 -i test_inputs -o outputs "$@"
echo "=== Done. Results saved to outputs/ ==="
