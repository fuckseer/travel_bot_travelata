import sqlite3
import datetime
from utils.config import load_config
from sentence_transformers import SentenceTransformer, util
from math import fabs

from utils.db_helpers import get_meal_ids_by_name

# === Config & model init ===
config = load_config()
DB_PATH = config["database"]["path"]

# лёгкая multilingual модель для эмбеддингов
# (поддерживает русский и английский)
embedder = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

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
    """Ищет ID города по названию в таблице cities (регистронезависимо)."""
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
    """Ищет ID страны по названию (регистронезависимо, работает и для латиницы, и для кириллицы)."""
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
    """
    Отбор туров по SQL-фильтрам:
    страна, город, ночи, бюджет, дата, курорт, категория отеля, питание.
    """
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    query = """
        SELECT id, hotel_name, nights, price, currency, url, check_in,
               hotel_category_id, meal_id, resort_id
        FROM tours
        WHERE 1=1
    """
    q_params = {}

    # Страна
    if params.get("country_id"):
        query += " AND country_id = :country_id"
        q_params["country_id"] = params["country_id"]

    # Город вылета
    if params.get("city_id"):
        query += " AND city_id = :city_id"
        q_params["city_id"] = params["city_id"]

    # Курорт
    if params.get("resort_id"):
        query += " AND resort_id = :resort_id"
        q_params["resort_id"] = params["resort_id"]

    # Категория отеля
    if params.get("hotel_category_id"):
        query += " AND hotel_category_id = :hotel_category_id"
        q_params["hotel_category_id"] = params["hotel_category_id"]

    # Питание
    if params.get("meal_id"):
        meal_value = params["meal_id"]
        if isinstance(meal_value, list):
            meal_placeholders = []
            for i, mid in enumerate(meal_value):
                key = f"meal_{i}"
                meal_placeholders.append(f":{key}")
                q_params[key] = mid
            query += f" AND meal_id IN ({','.join(meal_placeholders)})"
        else:
            query += " AND meal_id = :meal_id"
            q_params["meal_id"] = meal_value
    elif params.get("meal"):
        ids = get_meal_ids_by_name(params["meal"])
        if ids:
            meal_placeholders = []
            for i, mid in enumerate(ids):
                name = f"meal_{i}"
                meal_placeholders.append(f":{name}")
                q_params[name] = mid
            query += f" AND meal_id IN ({','.join(meal_placeholders)})"

    # Количество ночей
    if params.get("duration_days"):
        d = int(params["duration_days"])
        query += " AND nights BETWEEN :nfrom AND :nto"
        q_params["nfrom"] = max(d - 1, 1)
        q_params["nto"] = d + 1

    # Бюджет (евро → рубли ~100)
    if params.get("budget_eur"):
        query += " AND price <= :budget"
        q_params["budget"] = int(params["budget_eur"] * 100)

    # Дата (либо диапазон)
    if params.get("check_in_date"):
        d = params["check_in_date"]
        query += " AND check_in BETWEEN :date_from AND :date_to"
        q_params["date_from"] = d
        q_params["date_to"] = add_days(d, 5)
    elif params.get("check_in_range"):
        d_from = params["check_in_range"].get("from")
        d_to = params["check_in_range"].get("to")
        if d_from and d_to:
            query += " AND check_in BETWEEN :date_from AND :date_to"
            q_params["date_from"] = d_from
            q_params["date_to"] = d_to
    elif params.get("month"):
        m = month_to_number(params["month"])
        if m:
            query += " AND CAST(strftime('%m', check_in) AS INT) = :month"
            q_params["month"] = m

    query += " ORDER BY price ASC LIMIT :limit"
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
        }
        for row in rows
    ]

    # Удалим дубликаты отелей с одинаковой датой
    unique = {}
    for t in results:
        key = (t["hotel_name"], t["check_in"])
        if key not in unique:
            unique[key] = t
    return list(unique.values())


# === RAG rerank ===

def rag_rerank(tours, preferences, duration_days=None, top_k=5):
    """
    Перерасчёт туров по смысловой схожести с пожеланиями (Semantic RAG)
    + штраф за отклонение по количеству ночей.
    """
    if not tours:
        return []
    if not preferences:
        return sorted(tours, key=lambda t: (t["check_in"], t["price"]))[:top_k]

    pref_text = ", ".join(preferences)
    pref_vec = embedder.encode(pref_text, convert_to_tensor=True)

    tour_texts = [f"{t['hotel_name']} cat:{t['hotel_category_id']} meal:{t['meal_id']}"
                  for t in tours]
    tour_vecs = embedder.encode(tour_texts, convert_to_tensor=True)
    sims = util.cos_sim(pref_vec, tour_vecs)[0]

    scored = []
    for t, s in zip(tours, sims):
        score = float(s)
        if duration_days and t.get("nights"):
            # penalty за отличие по длительности
            score -= fabs(t["nights"] - duration_days) * 0.05
        scored.append((t, score))

    # Сортировка: сначала по score, потом по check_in / price
    best = sorted(scored, key=lambda x: (-x[1], x[0]["check_in"], x[0]["price"]))
    return [t for t, _ in best[:top_k]]


# === Main find ===

def find_tours(params):
    """
    Главная функция: SQL фильтр + RAG rerank.
    """
    candidates = sql_filter(params, limit=100)
    if not candidates:
        return []

    prefs = params.get("preferences", [])
    best = rag_rerank(candidates, prefs, duration_days=params.get("duration_days"), top_k=5)
    return best