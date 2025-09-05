import os, yaml

def load_config(path: str = None) -> dict:
    config_path = path or os.getenv("CONFIG_PATH", "config.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)