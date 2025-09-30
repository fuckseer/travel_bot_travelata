from llm_service.llm_client import parse_user_request
from bot_service.travelata_api import get_cheapest_tours
from bot_service.db import save_tours

def process_user_query(query: str) -> str:
    # 1. LLaMA парсит параметры
    params = parse_user_request(query)
    if not params:
        return "Не понял запрос 😔 Попробуй ещё раз."

    # 2. (на ближайшее время — хардкод) id страны/города → позже сделаем mapping через справочники
    country_id, city_id = 92, 2  # Турция, Москва для MVP
    tours = get_cheapest_tours(country_id, city_id, params)

    if not tours:
        return "😔 По условиям ничего не нашлось. Попробуй изменить запрос."

    # 3. Сохраняем в БД
    save_tours(tours, country_id, city_id)

    # 4. Берем первый тур для примера
    best = tours[0]
    return (f"🌍 Нашёл тур:\n"
            f"🏨 {best.get('hotelName')} — {best.get('nightCount')} ночей\n"
            f"💰 Цена: {best['price']['amount']} {best['price']['currency']}\n"
            f"🔗 {best['detailsPageUrl']}")