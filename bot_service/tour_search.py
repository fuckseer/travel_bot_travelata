import sqlite3
from utils.config import load_config, get_db_path
from sentence_transformers import SentenceTransformer, util
import torch

# Загружаем конфигурацию
config = load_config()
DB_PATH = get_db_path(config)

# Модель для эмбеддингов (многоязычная, легкая)
embedder = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

def sql_filter(params, limit=50):
    """
    Первичный фильтр по SQL: страна, город, ночи, бюджет.
    """
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    query = """
        SELECT id, hotel_name, nights, price, currency, url, check_in,
               hotel_category_id, meal_id
        FROM tours
        WHERE 1=1
    """
    q_params = {}

    # фильтры
    if "country_id" in params:
        query += " AND country_id = :country_id"
        q_params["country_id"] = params["country_id"]

    if "city_id" in params:
        query += " AND city_id = :city_id"
        q_params["city_id"] = params["city_id"]

    if "duration_days" in params:
        duration = params["duration_days"]
        query += " AND nights BETWEEN :nfrom AND :nto"
        q_params["nfrom"] = duration - 1
        q_params["nto"] = duration + 1

    if "budget_eur" in params and params["budget_eur"]:
        query += " AND price <= :budget"
        q_params["budget"] = params["budget_eur"] * 100  # если рубли — приведи к scale

    query += " ORDER BY price ASC LIMIT :limit"
    q_params["limit"] = limit

    cur.execute(query, q_params)
    rows = cur.fetchall()
    con.close()

    # преобразуем в список dict
    results = []
    for row in rows:
        results.append({
            "id": row[0],
            "hotel_name": row[1],
            "nights": row[2],
            "price": row[3],
            "currency": row[4],
            "url": row[5],
            "check_in": row[6],
            "hotel_category_id": row[7],
            "meal_id": row[8]
        })

    return results


def rag_rerank(tours, preferences, top_k=5):
    """
    Доранжировка через эмбеддинг поиска.
    preferences: list[str]
    """
    if not preferences:
        return tours[:top_k]

    # объединяем все пожелания в строку
    pref_text = ", ".join(preferences)
    pref_vec = embedder.encode(pref_text, convert_to_tensor=True)

    # эмбедды туров
    tour_texts = [f"{t['hotel_name']} cat:{t['hotel_category_id']} meal:{t['meal_id']}" for t in tours]
    tour_vecs = embedder.encode(tour_texts, convert_to_tensor=True)

    # считаем cosine similarity
    sims = util.cos_sim(pref_vec, tour_vecs)[0]

    # сортируем по sim
    scored = sorted(zip(tours, sims), key=lambda x: float(x[1]), reverse=True)

    return [t for t, score in scored[:top_k]]


def find_tours(params):
    """
    Главная функция: SQL фильтр + RAG ранжирование.
    params: dict из LLM
    """
    candidates = sql_filter(params, limit=50)
    if not candidates:
        return []

    prefs = params.get("preferences", [])
    best = rag_rerank(candidates, prefs, top_k=5)
    return best


if __name__ == "__main__":
    params = {
        "country_id": 92,
        "city_id": 2,
        "duration_days": 7,
        "budget_eur": 1200,
        "preferences": ["первая линия", "бар у пляжа", "all inclusive"]
    }

    tours = find_tours(params)
    for t in tours:
        print(f"🏨 {t['hotel_name']} | {t['nights']} ночей | {t['price']} {t['currency']}")
        print(f"   Заезд: {t['check_in']}")
        print(f"   Ссылка: {t['url']}\n")