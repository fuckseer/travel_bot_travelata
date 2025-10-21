import json
import re
import sqlite3
import datetime
import time

import requests
from math import fabs
from utils.config import load_config, get_db_path
from utils.db_helpers import get_meal_ids_by_name

# === Config ===
config = load_config()
DB_PATH = get_db_path(config)
LLM_URL_PARSE = config["llm_service"]["url_parse"]
LLM_URL_SUMMARIZE = config["llm_service"]["url_summarize"]
LLM_URL_SIMILARITY = config["llm_service"]["url_similarity"]

# === Helper functions ===
def month_to_number(month_str: str) -> int:
    months = {
        "january": 1, "february": 2, "march": 3,
        "april": 4, "may": 5, "june": 6,
        "july": 7, "august": 8, "september": 9,
        "october": 10, "november": 11, "december": 12,
        "январь": 1, "февраль": 2, "март": 3,
        "апрель": 4, "май": 5, "июнь": 6,
        "июль": 7, "август": 8, "сентябрь": 9,
        "октябрь": 10, "ноябрь": 11, "декабрь": 12,
    }
    return months.get(month_str.lower(), 0) if month_str else 0

def add_days(date_str: str, days: int) -> str:
    try:
        date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        new_date = date + datetime.timedelta(days=days)
        return new_date.strftime("%Y-%m-%d")
    except Exception:
        return date_str

def get_city_id_by_name(city_name: str) -> int | None:
    if not city_name:
        return None
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "SELECT id FROM cities WHERE LOWER(name) LIKE ? LIMIT 1",
        (f"%{city_name.lower()}%",)
    )
    row = cur.fetchone()
    con.close()
    return row[0] if row else None

def get_country_id_by_name(country_name: str) -> int | None:
    if not country_name:
        return None
    name = country_name.lower().strip()
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "SELECT id FROM countries WHERE LOWER(name) LIKE ? LIMIT 1",
        (f"%{name}%",),
    )
    row = cur.fetchone()
    con.close()
    return row[0] if row else None

# === SQL filter ===
def sql_filter(params, limit=100):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    query = """
        SELECT t.id,
               t.hotel_name,
               t.nights,
               t.price,
               t.currency,
               t.url,
               t.check_in,
               t.hotel_category_id,
               t.meal_id,
               t.resort_id,
               hd.description
        FROM tours AS t
        LEFT JOIN hotel_descriptions AS hd
            ON t.api_id = hd.hotel_api_id
        WHERE 1=1
    """
    q_params = {}
    # --- фильтры ---
    if params.get("country_id"):
        query += " AND t.country_id = :country_id"
        q_params["country_id"] = params["country_id"]
    if params.get("city_id"):
        query += " AND t.city_id = :city_id"
        q_params["city_id"] = params["city_id"]
    if params.get("resort_id"):
        query += " AND t.resort_id = :resort_id"
        q_params["resort_id"] = params["resort_id"]
    if params.get("hotel_category_id"):
        query += " AND t.hotel_category_id = :hotel_category_id"
        q_params["hotel_category_id"] = params["hotel_category_id"]
    # --- питание ---
    if params.get("meal_id"):
        meal_value = params["meal_id"]
        if isinstance(meal_value, list):
            placeholders = []
            for i, mid in enumerate(meal_value):
                key = f"meal_{i}"
                placeholders.append(f":{key}")
                q_params[key] = mid
            query += " AND t.meal_id IN (" + ",".join(placeholders) + ")"
        else:
            query += " AND t.meal_id = :meal_id"
            q_params["meal_id"] = meal_value
    elif params.get("meal"):
        ids = get_meal_ids_by_name(params["meal"])
        if ids:
            meal_placeholders = []
            for i, mid in enumerate(ids):
                key = f"meal_{i}"
                meal_placeholders.append(f":{key}")
                q_params[key] = mid
            query += f" AND t.meal_id IN ({','.join(meal_placeholders)})"

    if params.get("duration_days"):
        d = int(params["duration_days"])
        query += " AND t.nights BETWEEN :nfrom AND :nto"
        q_params["nfrom"] = max(d - 1, 1)
        q_params["nto"] = d + 1
    if params.get("budget_eur"):
        query += " AND t.price <= :budget"
        q_params["budget"] = int(params["budget_eur"] * 100)
    if params.get("check_in_date"):
        d = params["check_in_date"]
        query += " AND t.check_in BETWEEN :date_from AND :date_to"
        q_params["date_from"] = d
        q_params["date_to"] = add_days(d, 5)
    elif params.get("check_in_range"):
        d_from = params["check_in_range"].get("from")
        d_to = params["check_in_range"].get("to")
        if d_from and d_to:
            query += " AND t.check_in BETWEEN :date_from AND :date_to"
            q_params["date_from"] = d_from
            q_params["date_to"] = d_to
    elif params.get("month"):
        m = month_to_number(params["month"])
        if m:
            query += " AND CAST(strftime('%m', t.check_in) AS INT) = :month"
            q_params["month"] = m

    query += " ORDER BY t.price ASC LIMIT :limit"
    q_params["limit"] = limit

    cur.execute(query, q_params)
    rows = cur.fetchall()
    con.close()

    results = [
        {
            "id": row[0],
            "hotel_name": row[1],
            "nights": row[2],
            "price": row[3],
            "currency": row[4],
            "url": row[5],
            "check_in": row[6],
            "hotel_category_id": row[7],
            "meal_id": row[8],
            "resort_id": row[9],
            "description": row[10] or "",
        }
        for row in rows
    ]
    uniq = {}
    for t in results:
        k = (t["hotel_name"], t["check_in"])
        if k not in uniq:
            uniq[k] = t
    return list(uniq.values())

# === RAG rerank via LLM similarity ===
def rag_rerank(tours, preferences, duration_days=None, top_k=5):
    if not tours:
        return []
    if not preferences:
        return sorted(tours, key=lambda t: (t["check_in"], t["price"]))[:top_k]
    pref_text = ", ".join(preferences)
    scored = []
    for t in tours:
        tour_text = f"{t['hotel_name']} cat:{t['hotel_category_id']} meal:{t['meal_id']} {t.get('description','')[:1000]}"
        try:
            payload = {"query": pref_text, "context": tour_text}
            resp = requests.post(LLM_URL_SIMILARITY, json=payload, timeout=20)
            if resp.ok:
                score = float(resp.json().get("score", 0))
            else:
                score = 0.0
        except Exception:
            score = 0.0
        if duration_days and t.get("nights"):
            score -= fabs(t["nights"] - duration_days) * 0.05
        scored.append((t, score))
        time.sleep(2)
    best = sorted(scored, key=lambda x: (-x[1], x[0]["check_in"], x[0]["price"]))
    return [t for t, _ in best[:top_k]]

# === Summarization ===
def _clean_summary(raw_text: str) -> str:
    text = raw_text.strip()
    text = re.sub(r"(?i)^based on[^\.\n]*[\.\n]", "", text)
    text = re.sub(r"\n?\s*\d+\.\s*", " ", text)
    text = re.sub(r"\s+", " ", text)
    sents = re.split(r"(?<=[.!?])\s+", text)
    if len(sents) > 3:
        text = " ".join(sents[:3])
    return text.strip()

def summarize_selection_batch(tours, user_query):
    summarized = []
    for t in tours:
        hotel_data = {
            "hotel": t.get("hotel_name"),
            "category": t.get("hotel_category_id"),
            "meal_id": t.get("meal_id"),
            "description": t.get("description", "")[:1500],
        }
        payload = {"query": user_query, "hotel": hotel_data}
        try:
            r = requests.post(LLM_URL_SUMMARIZE, json=payload, timeout=25)
            if r.ok:
                raw = r.json().get("summary") or r.json().get("response") or r.text
                reason = _clean_summary(raw)
            else:
                reason = f"Ошибка {r.status_code}"
        except Exception as e:
            reason = f"Ошибка LLM: {e}"
        t["reason"] = reason
        summarized.append(t)
    return summarized

# === Main entry ===
def find_tours(params):
    candidates = sql_filter(params, limit=150)
    if not candidates:
        return []
    prefs = params.get("preferences", [])
    best = rag_rerank(
        candidates, prefs, duration_days=params.get("duration_days"), top_k=5
    )
    user_query = params.get("user_text", "")
    best = summarize_selection_batch(best, user_query)
    return best