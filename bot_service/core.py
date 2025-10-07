import json

import requests
from bot_service.tour_search import find_tours, get_city_id_by_name, get_country_id_by_name
from utils.config import load_config
from utils.db_helpers import (
    get_city_id_by_name,
    get_country_id_by_name,
    get_meal_id_by_name,
    get_hotel_category_id_by_name,
    get_resort_id_by_name,
)

config = load_config()
LLM_SERVICE_URL = config.get("llm_service", {}).get("url", "http://llm-service:8001/parse")

def parse_user_request_through_service(query: str) -> dict:
    """
    Отправляем запрос в llm_service HTTP API
    """
    try:
        resp = requests.post(LLM_SERVICE_URL, json={"query": query}, timeout=60)
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"error": f"LLM service {resp.status_code}", "details": resp.text}
    except Exception as e:
        return {"error": "llm_service_unavailable", "details": str(e)}



def enrich_with_reference_ids(params):
    # города / страны
    if params.get("departure_city") and not params.get("city_id"):
        cid = get_city_id_by_name(params["departure_city"])
        if cid:
            params["city_id"] = cid

    if params.get("country") and not params.get("country_id"):
        coid = get_country_id_by_name(params["country"])
        if coid:
            params["country_id"] = coid

    # курорт (если LLM упомянул)
    if params.get("resort") and not params.get("resort_id"):
        rid = get_resort_id_by_name(params["resort"])
        if rid:
            params["resort_id"] = rid

    # категория отеля
    if params.get("hotel_category") and not params.get("hotel_category_id"):
        hid = get_hotel_category_id_by_name(params["hotel_category"])
        if hid:
            params["hotel_category_id"] = hid

    # питание
    if params.get("meal") and not params.get("meal_id"):
        mid = get_meal_id_by_name(params["meal"])
        if mid:
            params["meal_id"] = mid

    return params

def process_user_query(user_text: str) -> str:
    # 1. получаем JSON от llm_service
    params = parse_user_request_through_service(user_text)
    print("=== RAW LLM response ===")
    print(params)
    params = enrich_with_reference_ids(params)
    if "error" in params:
        return f"⚠️ Ошибка LLM-сервиса: {params}"

    params = enrich_with_reference_ids(params)
    print("=== After enrichment ===")
    print(json.dumps(params, indent=2, ensure_ascii=False))

    # 2. ищем туры в SQLite
    tours = find_tours(params)
    if not tours:
        return "😔 Не нашлось туров по фильтрам. Попробуй изменить условия."

    # 3. собираем красивый ответ
    reply = "🔥 Нашёл подходящие туры:\n\n"
    for t in tours:
        reply += (f"🏨 {t['hotel_name']} ({t['nights']} ночей)\n"
                  f"💰 {t['price']} {t['currency']}\n"
                  f"📅 Заезд: {t['check_in']}\n"
                  f"🔗 {t['url']}\n\n")
    return reply