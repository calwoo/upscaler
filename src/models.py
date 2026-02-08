import os
import urllib

WEIGHTS_DIR: str = "weights"


def fetch_model_weights(url: str):
    filename = os.path.basename(url)
    weights_dir = os.path.join(os.path.dirname(__file__), WEIGHTS_DIR)
    weights_filepath = os.path.join(weights_dir, filename)

    if not os.path.exists(weights_dir):
        os.mkdir(weights_dir)

    # download weights
    if not os.path.exists(weights_filepath):
        print(f"Downloading weights to {weights_filepath}...")
        urllib.request.urlretrieve(url, weights_filepath)
        print("Download complete.")

    return weights_filepath
