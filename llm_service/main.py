import json
import re

from fastapi import FastAPI
from pydantic import BaseModel
from llm_service.llm_client import parse_user_request, call_llm  # теперь пакет виден

app = FastAPI()

class Query(BaseModel):
    query: str

@app.post("/parse")
def parse_request(q: Query):
    parsed = parse_user_request(q.query)
    return parsed

@app.post("/similarity")
def similarity(req: dict):
    query = req.get("query", "")
    context = req.get("context", "")
    prompt = (
        "Оцени сходство между двумя текстами от 0 до 1. "
        "Первый текст — описание пожеланий пользователя, "
        "второй — описание отеля. "
        f"\n\nПожелания:\n{query}\n\nОтель:\n{context}\n\n"
        "Верни только одно число — коэффициент сходства (0–1)."
    )
    messages = [{"role": "user", "content": prompt}]
    answer = call_llm(messages, temperature=0)
    # Пытаемся извлечь число
    try:
        score = float(re.findall(r"\d\.\d+|\d", answer)[0])
    except Exception:
        score = 0.0
    return {"score": score}

@app.post("/summarize")
def summarize(req: dict):
    """
    Краткая генерация объяснения выбора: почему именно этот отель.
    Принимает {"query": "...", "hotel": {...}} и возвращает {"summary": "..."}.
    """
    user_query = req.get("query", "")
    hotel = req.get("hotel", {})

    prompt = (
        "Пользовательский запрос:\n"
        f"{user_query}\n\n"
        "Описание отеля:\n"
        f"{json.dumps(hotel, ensure_ascii=False, indent=2)}\n\n"
        "Сравни запрос и отель, напиши 2–3 предложения на русском, "
        "почему этот вариант соответствует пожеланиям пользователя. "
        "Не используй списки, не упоминай слово 'пользователь'. "
        "Только короткий связный текст."
    )

    messages = [{"role": "user", "content": prompt}]
    text = call_llm(messages, temperature=0.4)

    # простая очистка результата
    clean = re.sub(r"(?i)^based on[^\n]*\n?", "", text).strip()
    return {"summary": clean}