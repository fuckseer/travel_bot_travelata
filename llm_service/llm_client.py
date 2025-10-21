import json
import re
import time

import requests
from utils.config import load_config

config = load_config()

API_KEY = config["llm"]["api_key"]
MODEL = config["llm"]["model"]
API_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """
You are a travel‑assistant model that converts a user's free‑form query into a structured JSON used 
to find package tours in a database.

Your task:
Extract both explicit parameters (country, departure city, resort, hotel category, type of meals, dates, budget)
and implicit preferences (quiet hotel, with pool, sea view, etc.).

Output only one clean JSON, no commentary or text, with this structure:

{
  "country": "",
  "departure_city": "",
  "resort": "",
  "hotel_category": "",
  "meal": "",
  "check_in_date": "",
  "check_in_range": {"from": "", "to": ""},
  "month": "",
  "duration_days": 0,
  "budget_eur": 0,
  "adults": 2,
  "kids": 0,
  "preferences": []
}

Guidelines
==========

• **country** – destination country (e.g. “Turkey”, “Египет”).  
  If several countries are mentioned, pick the main one.

• **departure_city** – city of departure (e.g. “Moscow”, “Ekaterinburg”).  
  Use only one city.

• **resort** – if a user specifies a region/resort (e.g. “Antalya”, “Хургада”), include it.

• **hotel_category** – extract text like “5*”, “luxury”, “budget”, or “3 stars”.

• **meal** – extract expression describing meal type 
  (e.g. “all inclusive”, “всё включено”, “breakfast only”).

• **Dates**
  - If exact date specified → `check_in_date = YYYY-MM-DD`.
  - If approximate ("early October", “в начале октября”) →
    fill `check_in_range`:
      • early month → from 1st to 10th  
      • mid month → 11th–20th  
      • end month → 21st–last day
  - Always fill `"month"` as text ("October", "январь").

• **duration_days** – number of nights.

• **budget_eur** – approximate value converted to euros (1 EUR ≈ 100 RUB ≈ 1.1 USD).

• **adults**, **kids** – numbers of travellers; default 2 adults, 0 kids.

• **preferences** – array of soft wishes not mapped to database filters  
  (examples: ["first beach line", "quiet area", "big pool", "good animation for kids"]).

Examples
========

User: "Хочу из Екатеринбурга в Турцию, Анталия, в начале октября, на 7 ночей, всё включено, отель 5 звёзд."

Answer:
{
  "country": "Турция",
  "departure_city": "Екатеринбург",
  "resort": "Анталия",
  "hotel_category": "5*",
  "meal": "всё включено",
  "check_in_date": "",
  "check_in_range": {"from": "2025-10-01", "to": "2025-10-10"},
  "month": "October",
  "duration_days": 7,
  "budget_eur": 0,
  "adults": 2,
  "kids": 0,
  "preferences": []
}

User: "I want to go to Thailand, Phuket, mid‑January for 10 nights, 1500 €, breakfast only, sea view"
Answer:
{
  "country": "Thailand",
  "departure_city": "",
  "resort": "Phuket",
  "hotel_category": "",
  "meal": "breakfast only",
  "check_in_date": "",
  "check_in_range": {"from": "2025-01-11", "to": "2025-01-20"},
  "month": "January",
  "duration_days": 10,
  "budget_eur": 1500,
  "adults": 2,
  "kids": 0,
  "preferences": ["sea view"]
}

Rules
=====
- Always output valid JSON only.
- Use Russian or English month names.
- Leave unknown fields as empty strings or zeros.

"""

def safe_json_parse(text: str) -> dict:
    text = text.strip().replace("\\_", "_")
    try:
        data = json.loads(text)
        if isinstance(data, str):
            data = json.loads(data)
        return data
    except Exception:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(0))
                if isinstance(data, str):
                    data = json.loads(data)
                return data
            except Exception:
                pass
    return {"raw": text}

def call_llm(messages: list[dict], temperature: float = 0.2) -> str:
    """Общий запрос к OpenRouter — с повтором и паузой при 404."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {"model": MODEL, "messages": messages, "temperature": temperature}

    for attempt in range(3):                               # максимум 3 попытки
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=45)
        if resp.ok:
            j = resp.json()
            return j["choices"][0]["message"]["content"]

        # 404 – обычно rate‑limit или privacy: ждём и повторяем
        if resp.status_code in (404, 429, 503):
            print(f"[LLM] {resp.status_code}, повтор через 3 сек.")
            time.sleep(3)
            continue

        raise RuntimeError(f"LLM error {resp.status_code}: {resp.text}")

    raise RuntimeError("LLM сервис не вернул корректный ответ после 3 попыток.")
# ----------------------------------------------------------------------------
# 1️⃣ парсинг пользовательского запроса → structured JSON
# ----------------------------------------------------------------------------
def parse_user_request(query: str) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]
    text = call_llm(messages, temperature=0)
    return safe_json_parse(text)
