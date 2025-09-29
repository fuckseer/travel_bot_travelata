import os
import json
import re
import requests
from utils.config import load_config

config = load_config()

API_KEY = config["llm"]["api_key"]
MODEL = config["llm"]["model"]
API_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """
Ты — помощник по подбору туристических туров.
Твоя задача: разобрать запрос пользователя и вернуть только JSON следующего вида:

{
  "month": "",
  "duration_days": 0,
  "budget_eur": 0,
  "adults": 2,
  "kids": 0,
  "country": "",
  "departure_city": "",
  "preferences": ["список пожеланий пользователя"]
}

Правила:
- Если данные не указаны — оставь пустую строку ("") или 0.
- В поле "preferences" собери все пожелания и дополнительные условия, которые не относятся напрямую к дате/стране/бюджету.
- "preferences" должен быть массивом строк, например:
  ["первая береговая линия", "бар у пляжа", "all inclusive"]
- Ответь строго одним JSON-объектом без комментариев и без дополнительного текста.

"""


def safe_json_parse(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                pass
    return {"raw": text}


def parse_user_request(query: str) -> dict:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ],
        "temperature": 0,
    }

    resp = requests.post(API_URL, headers=headers, json=payload)

    if resp.status_code != 200:
        return {"error": resp.status_code, "details": resp.text}

    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    return safe_json_parse(content)