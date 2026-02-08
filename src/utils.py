import os
from pathlib import Path
import urllib

WEIGHTS_DIR: str = "weights"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}


def fetch_model_weights(url: str):
    filename = os.path.basename(url)
    weights_dir = os.path.join(Path(os.path.dirname(__file__)).parent, WEIGHTS_DIR)
    weights_filepath = os.path.join(weights_dir, filename)

    if not os.path.exists(weights_dir):
        os.mkdir(weights_dir)

    # download weights
    if not os.path.exists(weights_filepath):
        print(f"Downloading weights to {weights_filepath}...")
        urllib.request.urlretrieve(url, weights_filepath)
        print("Download complete.")

    return weights_filepath


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
