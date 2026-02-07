#!/usr/bin/env python3
"""Real-ESRGAN image upscaler CLI."""

import argparse
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Upscale images using Real-ESRGAN"
    )
    parser.add_argument(
        "-i", "--input", required=True,
        help="Path to an image file or folder of images"
    )
    parser.add_argument(
        "-o", "--output", required=True,
        help="Path for output image or output folder"
    )
    parser.add_argument(
        "--scale", type=int, default=4, choices=[2, 4],
        help="Upscale factor: 2 or 4 (default: 4)"
    )
    parser.add_argument(
        "--model", default="general", choices=["general", "anime"],
        help="Model choice: general or anime (default: general)"
    )
    parser.add_argument(
        "--face-enhance", action="store_true",
        help="Enable GFPGAN face enhancement"
    )
    parser.add_argument(
        "--tile", type=int, default=0,
        help="Tile size for large images, 0 = no tiling (default: 0)"
    )
    parser.add_argument(
        "--gpu-id", type=int, default=None,
        help="GPU device ID, omit for auto-detect"
    )
    parser.add_argument(
        "--suffix", default="_upscaled",
        help="Suffix appended to output filenames (default: _upscaled)"
    )
    parser.add_argument(
        "--format", default="auto", choices=["auto", "png", "jpg"],
        help="Output format: auto, png, or jpg (default: auto)"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: input path does not exist: {input_path}")
        sys.exit(1)

    print(f"Input:        {args.input}")
    print(f"Output:       {args.output}")
    print(f"Scale:        {args.scale}x")
    print(f"Model:        {args.model}")
    print(f"Face enhance: {args.face_enhance}")
    print(f"Tile size:    {args.tile}")
    print(f"GPU ID:       {args.gpu_id}")
    print(f"Suffix:       {args.suffix}")
    print(f"Format:       {args.format}")


if __name__ == "__main__":
    main()
