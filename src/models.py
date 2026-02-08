from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer
import torch

from .utils import fetch_model_weights


def setup_model(args):
    """Initialize Real-ESRGAN (and optionally GFPGAN) based on CLI args."""
    if args.model == "general" and args.scale == 4:
        model_name = "RealESRGAN_x4plus"
        model = RRDBNet(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=23,
            num_grow_ch=32,
            scale=4,
        )
        netscale = 4
        url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
    elif args.model == "general" and args.scale == 2:
        model_name = "RealESRGAN_x2plus"
        model = RRDBNet(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=23,
            num_grow_ch=32,
            scale=2,
        )
        netscale = 2
        url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth"
    elif args.model == "anime":
        model_name = "RealESRGAN_x4plus_anime_6B"
        model = RRDBNet(
            num_in_ch=3, num_out_ch=3, num_feat=64, num_block=6, num_grow_ch=32, scale=4
        )
        netscale = 4
        url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth"

    if torch.cuda.is_available():
        device = torch.device(f"cuda:{args.gpu_id}" if args.gpu_id is not None else "cuda")
        use_half = True
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
        use_half = False
    else:
        device = torch.device("cpu")
        use_half = False

    cached_weights = fetch_model_weights(url)
    upsampler = RealESRGANer(
        scale=netscale,
        model_path=cached_weights,
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

        weights_url = "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.3.pth"
        cached_weights = fetch_model_weights(weights_url)
        face_enhancer = GFPGANer(
            model_path=cached_weights,
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

    return upsampler, face_enhancer, device
