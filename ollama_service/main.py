import json, requests, re
from fastapi import FastAPI
from pydantic import BaseModel

OLLAMA_URL = "http://ollama:11434/api/generate"
MODEL = "llama3:8b"

PROMPT = """
Ты — помощник по путешествиям.
Ответь строго одним JSON-объектом, без текста до и после.
Пример:
{
  "month": "july",
  "duration_days": 7,
  "budget_eur": 1000,
  "adults": 2,
  "kids": 0,
  "country": "Spain",
  "departure_city": "Moscow"
}

Вопрос: {query}
"""

class Query(BaseModel):
    query: str

app = FastAPI()

def safe_json_parse(llm_text: str) -> dict:
    llm_text = llm_text.strip()
    try:
        return json.loads(llm_text)
    except Exception:
        match = re.search(r"\{.*\}", llm_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception as e:
                print("json parse error:", e)
    return {}

@app.post("/parse")
def parse_request(q: Query):
    payload = {
        "model": MODEL,
        "prompt": PROMPT.format(query=q.query),
        "options": {
            "temperature": 0  # максимально детерминированный вывод
        }
    }
    response = requests.post(OLLAMA_URL, json=payload, stream=True)

    full_text = ""
    for line in response.iter_lines():
        if line:
            data = json.loads(line.decode())
            if "response" in data:
                full_text += data["response"]

    parsed = safe_json_parse(full_text)
    return parsed or {"error": "Could not parse JSON", "raw": full_text}