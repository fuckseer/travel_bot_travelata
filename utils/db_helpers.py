import sqlite3
from utils.config import load_config

config = load_config()
DB_PATH = config["database"]["path"]


# --- Универсальные функции ---

def _load_lookup(table, key="name"):
    """Загружает маппинг {name.lower(): id} из указанных таблиц."""
    con = sqlite3.connect(DB_PATH)
    data = con.execute(f"SELECT LOWER({key}), id FROM {table}").fetchall()
    con.close()
    return {k.strip().lower(): v for k, v in data}


def _find_in_lookup(lookup: dict, text: str):
    if not text:
        return None
    name = text.lower().strip()
    # сначала точное совпадение
    for k, v in lookup.items():
        if name == k:
            return v
    # потом частичные совпадения
    for k, v in lookup.items():
        if name in k or k in name:
            return v
    return None

# --- Загрузка всех справочников в память при старте ---

CITY_MAP = _load_lookup("cities")
COUNTRY_MAP = _load_lookup("countries")
RESORT_MAP = _load_lookup("resorts")
CATEGORY_MAP = _load_lookup("hotel_categories")
MEAL_MAP = _load_lookup("meals")


# --- Публичные функции ---

def get_city_id_by_name(city: str) -> int | None:
    return _find_in_lookup(CITY_MAP, city)

def get_country_id_by_name(country: str) -> int | None:
    return _find_in_lookup(COUNTRY_MAP, country)

def get_resort_id_by_name(resort: str) -> int | None:
    return _find_in_lookup(RESORT_MAP, resort)

def get_hotel_category_id_by_name(category: str) -> int | None:
    """Находит ID по названию категории, например '5*' или 'четыре звезды'."""
    if not category:
        return None
    text = category.lower()
    # добавить короткие синонимы
    if "5" in text:
        text = "5"
    elif "4" in text:
        text = "4"
    return _find_in_lookup(CATEGORY_MAP, text)

def get_meal_id_by_name(meal: str) -> int | None:
    """Ищет ID типа питания, например 'all inclusive' или 'всё включено'."""
    if not meal:
        return None
    synonyms = {
        "всё включено": "все включено",
        "все включено": "все включено",
        "all inclusive": "все включено",
        "завтрак": "завтрак",
        "полупансион": "полупансион",
        "без питания": "без питания",
    }
    key = synonyms.get(meal.lower(), meal.lower())
    return _find_in_lookup(MEAL_MAP, key)