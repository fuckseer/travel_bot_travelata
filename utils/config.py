import os, yaml

def load_config(path: str = None) -> dict:
    if path is None:
        path = os.getenv("CONFIG_PATH")
        if path is None:
            BASE_DIR = os.path.dirname(os.path.dirname(__file__))
            path = os.path.join(BASE_DIR, "config.yaml")
    with open(path, "r") as f:
        return yaml.safe_load(f)