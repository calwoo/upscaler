#!/usr/bin/env python3
"""Real-ESRGAN image upscaler CLI."""

import argparse
import sys
from pathlib import Path

import cv2
import torch
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer


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


def setup_model(args):
    """Initialize Real-ESRGAN (and optionally GFPGAN) based on CLI args."""
    if args.model == "general" and args.scale == 4:
        model_name = "RealESRGAN_x4plus"
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
        netscale = 4
        url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
    elif args.model == "general" and args.scale == 2:
        model_name = "RealESRGAN_x2plus"
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=2)
        netscale = 2
        url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth"
    elif args.model == "anime":
        model_name = "RealESRGAN_x4plus_anime_6B"
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=6, num_grow_ch=32, scale=4)
        netscale = 4
        url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth"

    use_half = torch.cuda.is_available()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if args.gpu_id is not None:
        device = torch.device(f"cuda:{args.gpu_id}" if torch.cuda.is_available() else "cpu")

    upsampler = RealESRGANer(
        scale=netscale,
        model_path=url,
        model=model,
        tile=args.tile,
        tile_pad=10,
        pre_pad=0,
        half=use_half,
        device=device,
    )

    face_enhancer = None
    if args.face_enhance:
        from gfpgan import GFPGANer
        face_enhancer = GFPGANer(
            model_path="https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.3.pth",
            upscale=args.scale,
            arch="clean",
            channel_multiplier=2,
            bg_upsampler=upsampler,
        )

    print(f"Model:  {model_name}")
    print(f"Device: {device}")
    print(f"Half:   {use_half}")
    if face_enhancer:
        print("Face enhancement: enabled")

    return upsampler, face_enhancer


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}


def resolve_paths(args):
    """Build list of (input_path, output_path) tuples from CLI args."""
    input_path = Path(args.input)
    output_path = Path(args.output)

    if input_path.is_file():
        # Single file mode: output is treated as a file path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        out_file = _apply_format(output_path, args.format, input_path)
        return [(input_path, out_file)]

    # Directory mode
    output_path.mkdir(parents=True, exist_ok=True)
    pairs = []
    for img_file in sorted(input_path.iterdir()):
        if img_file.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        stem = img_file.stem + args.suffix
        ext = _resolve_extension(args.format, img_file)
        out_file = output_path / f"{stem}{ext}"
        pairs.append((img_file, out_file))

    if not pairs:
        print(f"Warning: no image files found in {input_path}")

    return pairs


def _resolve_extension(fmt, source_path):
    """Determine output file extension based on --format flag."""
    if fmt == "auto":
        return source_path.suffix
    return f".{fmt}"


def _apply_format(output_path, fmt, source_path):
    """Apply --format to a single-file output path."""
    if fmt == "auto":
        return output_path
    return output_path.with_suffix(f".{fmt}")


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

    upsampler, face_enhancer = setup_model(args)

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
                    img, has_aligned=False, only_center_face=False, paste_back=True,
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
