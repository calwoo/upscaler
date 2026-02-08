import os


WEIGHTS_DIR: str = "weights"

def fetch_model_weights(url: str):
    if not os.path.exists(os.path.join(os.path.dirname(__file__), WEIGHTS_DIR)):
        ...
