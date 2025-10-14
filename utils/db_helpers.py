import sqlite3
from utils.config import load_config, get_db_path

config = load_config()
DB_PATH = get_db_path(config)


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

def get_meal_ids_by_name(meal: str) -> list[int]:
    """
    Возвращает список id типов питания, подходящих под запрос (все вариации 'всё включено' и т.д.)
    """
    if not meal:
        return []

    name = meal.lower()
    ids = []

    # правила для синонимов
    group_map = {
        "все включено": ["всё включено", "all inclusive", "ультра всё включено"],
        "ультра все включено": ["ультра всё включено", "ultra all inclusive"],
        "без алкоголя": ["без алкоголя"],
        "завтрак": ["завтрак", "breakfast"],
        "полупансион": ["завтрак+ужин", "завтрак и ужин", "half board"],
        "полный пансион": ["завтрак, обед, ужин", "full board"],
        "без питания": ["без питания", "no meals"]
    }

    # вспомогательная функция для поиска по подстроке
    def find_like(needle):
        res = []
        for k, v in MEAL_MAP.items():
            if needle in k:
                res.append(v)
        return res

    # собираем все варианты
        # === обновлённая часть ===
    for key, synonyms in group_map.items():
        if any(syn in name for syn in synonyms):
            ids.extend(find_like(key))
            ids.extend(find_like(synonyms[0]))
            # без break — ищем все группы
    # === конец обновлённой части ===

    # если ничего не нашли вообще — fallback‑поиск
    if not ids:
        for k, v in MEAL_MAP.items():
            if name in k or k in name:
                ids.append(v)

    return list(set(ids))