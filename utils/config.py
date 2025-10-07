import os, yaml

import os, yaml

def load_config(path: str = None) -> dict:
    config_path = path or os.getenv("CONFIG_PATH", "config.yaml")

    if not os.path.isabs(config_path):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        config_path = os.path.join(base_dir, config_path)

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config not found: {config_path}")

    with open(config_path, "r") as f:
        return yaml.safe_load(f)

    
def get_db_path(cfg):
    db_path = cfg["database"]["path"]
    if not os.path.isabs(db_path):
        project_root = os.path.dirname(os.path.dirname(__file__))
        db_path = os.path.join(project_root, db_path)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return db_path