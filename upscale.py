#!/usr/bin/env python3
"""Real-ESRGAN image upscaler CLI."""

import argparse
import sys
from pathlib import Path

import cv2

from src.models import setup_model
from src.utils import resolve_paths


def parse_args():
    parser = argparse.ArgumentParser(description="Upscale images using Real-ESRGAN")
    parser.add_argument(
        "-i", "--input", required=True, help="Path to an image file or folder of images"
    )
    parser.add_argument(
        "-o", "--output", required=True, help="Path for output image or output folder"
    )
    parser.add_argument(
        "--scale",
        type=int,
        default=4,
        choices=[2, 4],
        help="Upscale factor: 2 or 4 (default: 4)",
    )
    parser.add_argument(
        "--model",
        default="general",
        choices=["general", "anime"],
        help="Model choice: general or anime (default: general)",
    )
    parser.add_argument(
        "--face-enhance", action="store_true", help="Enable GFPGAN face enhancement"
    )
    parser.add_argument(
        "--tile",
        type=int,
        default=0,
        help="Tile size for large images, 0 = no tiling (default: 0)",
    )
    parser.add_argument(
        "--gpu-id", type=int, default=None, help="GPU device ID, omit for auto-detect"
    )
    parser.add_argument(
        "--suffix",
        default="_upscaled",
        help="Suffix appended to output filenames (default: _upscaled)",
    )
    parser.add_argument(
        "--format",
        default="auto",
        choices=["auto", "png", "jpg"],
        help="Output format: auto, png, or jpg (default: auto)",
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
    print(f"Face enhance: {args.face_enhance}")
    print(f"Tile size:    {args.tile}")
    print(f"Suffix:       {args.suffix}")
    print(f"Format:       {args.format}")
    print()

    upsampler, face_enhancer, device = setup_model(args)

    pairs = resolve_paths(args)
    print(f"Found {len(pairs)} image(s) to process\n")

    success = 0
    failed = 0
    for i, (inp, out) in enumerate(pairs, 1):
        try:
            img = cv2.imread(str(inp), cv2.IMREAD_UNCHANGED)
            if img is None:
                raise ValueError(f"Failed to read image: {inp}")

            h, w = img.shape[:2]
            print(f"[{i}/{len(pairs)}] {inp.name} ({w}x{h}) -> ", end="", flush=True)

            if face_enhancer:
                _, _, output = face_enhancer.enhance(
                    img,
                    has_aligned=False,
                    only_center_face=False,
                    paste_back=True,
                )
            else:
                output, _ = upsampler.enhance(img, outscale=args.scale)

            cv2.imwrite(str(out), output)
            oh, ow = output.shape[:2]
            print(f"{out.name} ({ow}x{oh})")
            success += 1
        except Exception as e:
            print(f"ERROR: {e}")
            failed += 1

    print(f"\nDone: {success} succeeded, {failed} failed")


if __name__ == "__main__":
    main()
