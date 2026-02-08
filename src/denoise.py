"""Swin2SR-based denoising preprocessor for cleaning images before super-resolution."""

import cv2
import numpy as np
import torch
from PIL import Image


def setup_denoiser(device):
    """Load the Swin2SR model and processor for denoising.

    Uses the caidas/swin2SR-realworld-sr-x4-64-bsrgan-psnr checkpoint,
    which is trained on degraded inputs (noise, blur, compression artifacts).

    Args:
        device: torch.device to place the model on.

    Returns:
        Tuple of (model, processor).
    """
    from transformers import AutoImageProcessor, Swin2SRForImageSuperResolution

    checkpoint = "caidas/swin2SR-realworld-sr-x4-64-bsrgan-psnr"
    processor = AutoImageProcessor.from_pretrained(checkpoint)
    model = Swin2SRForImageSuperResolution.from_pretrained(checkpoint)
    model.to(device).eval()

    print(f"Denoiser: Swin2SR ({checkpoint})")
    return model, processor


def denoise_image(model, processor, img, device):
    """Denoise a cv2 BGR image using Swin2SR.

    Runs the image through Swin2SR (which 4x upscales internally),
    then downscales back to the original resolution to extract the
    denoising benefit without changing dimensions.

    Args:
        model: Swin2SRForImageSuperResolution model.
        processor: AutoImageProcessor for the model.
        img: cv2 BGR uint8 numpy array (HxWxC or HxW for grayscale).
        device: torch.device the model is on.

    Returns:
        Denoised cv2 BGR uint8 numpy array at the original resolution.
    """
    orig_h, orig_w = img.shape[:2]
    alpha = None

    # Handle grayscale: convert to 3-channel BGR
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    # Handle BGRA: strip and preserve alpha channel
    if img.shape[2] == 4:
        alpha = img[:, :, 3]
        img = img[:, :, :3]

    # Convert BGR -> RGB -> PIL
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb)

    # Run through Swin2SR
    inputs = processor(pil_image, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs)

    # Extract the reconstruction tensor -> numpy
    output_tensor = outputs.reconstruction.squeeze(0).clamp(0, 1)
    output_np = (output_tensor.cpu().permute(1, 2, 0).numpy() * 255).astype(np.uint8)

    # Convert RGB back to BGR
    output_bgr = cv2.cvtColor(output_np, cv2.COLOR_RGB2BGR)

    # Downscale back to original resolution
    output_bgr = cv2.resize(output_bgr, (orig_w, orig_h), interpolation=cv2.INTER_LANCZOS4)

    # Reattach alpha channel if present
    if alpha is not None:
        output_bgr = np.dstack([output_bgr, alpha])

    return output_bgr
