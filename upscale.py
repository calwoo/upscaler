#!/usr/bin/env python3
"""Real-ESRGAN image upscaler CLI."""

import argparse
import sys
from pathlib import Path

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


if __name__ == "__main__":
    main()
