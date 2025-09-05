import requests, json

from bot_service.config import load_config
config = load_config()

OLLAMA_SERVICE_URL = config["ollama"]["url"]

def parse_user_request(query: str) -> dict:
    try:
        r = requests.post(OLLAMA_SERVICE_URL, json={"query": query}, timeout=60)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print("LLAMA error:", e)
    return {}