import os, yaml

def load_config(path: str = None) -> dict:
    if path is None:
        path = os.getenv("CONFIG_PATH")
        if path is None:
            BASE_DIR = os.path.dirname(os.path.dirname(__file__))
            path = os.path.join(BASE_DIR, "config.yaml")
    with open(path, "r") as f:
        return yaml.safe_load(f)

    
def get_db_path(cfg):
    db_path = cfg["database"]["path"]
    if not os.path.isabs(db_path):
        project_root = os.path.dirname(os.path.dirname(__file__))
        db_path = os.path.join(project_root, db_path)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return db_path