import json
import os
import re
import requests
from fastapi import FastAPI
from pydantic import BaseModel

# имя сервиса "ollama" доступно внутри docker-compose по сети
OLLAMA_URL = "http://ollama:11434/api/generate"
MODEL = os.getenv("MODEL", "mistral:7b-instruct")

# Промпт: строго один JSON, без текста
SYSTEM_PROMPT = """
Ты — помощник по путешествиям.
Разбери запрос и верни только JSON-объект с параметрами:

{
  "month": "",
  "duration_days": 0,
  "budget_eur": 0,
  "adults": 2,
  "kids": 0,
  "country": "",
  "departure_city": ""
}

⚠️ ВАЖНО: верни только чистый JSON, без других слов.
"""

class Query(BaseModel):
    query: str

app = FastAPI()

def safe_json_parse(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)  # ищем {...} внутри
        if match:
            try:
                return json.loads(match.group(0))
            except Exception as e2:
                print("⚠ JSON parse error:", e2, "| raw:", text[:200])
    return {}

@app.post("/parse")
def parse_request(q: Query):
    payload = {
        "model": MODEL,
        "prompt": SYSTEM_PROMPT + "\nЗапрос: " + q.query,
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload)

    if response.status_code != 200:
        return {"error": "ollama_failed", "status": response.status_code, "body": response.text}

    data = response.json()
    # Ollama chat формат:
    # { "message": { "role": "assistant", "content": "..." }, "done": true }
    text = ""
    if "message" in data and "content" in data["message"]:
        text = data["message"]["content"]

    parsed = safe_json_parse(text)
    if not parsed:
        return {"error": "parse_failed", "raw": text}

    return parsed