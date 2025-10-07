import requests
import sqlite3
from utils.config import load_config

config = load_config()
BASE_URL = config["travelata"]["base_url"]
API_TOKEN = config["travelata"]["token"]
DB_PATH = config["database"]["path"]

HEADERS = {
    "Authorization": f"Token {API_TOKEN}",
    "User-Agent": "Mozilla/5.0"
}

def get_connection():
    return sqlite3.connect(DB_PATH)

# -------------------------------
# Справочники
# -------------------------------

def save_countries():
    url = f"{BASE_URL}/directory/countries"
    resp = requests.get(url, headers=HEADERS).json()
    data = resp.get("data", [])
    con = get_connection()
    cur = con.cursor()
    for c in data:
        cur.execute("INSERT OR REPLACE INTO countries (id, name) VALUES (?, ?)", (c["id"], c["name"]))
    con.commit(); con.close()
    print(f"✅ Загружены страны: {len(data)}")

def save_cities():
    url = f"{BASE_URL}/directory/departureCities"
    resp = requests.get(url, headers=HEADERS).json()
    data = resp.get("data", [])
    con = get_connection()
    cur = con.cursor()
    for c in data:
        cur.execute("INSERT OR REPLACE INTO cities (id, name) VALUES (?, ?)", (c["id"], c["name"]))
    con.commit(); con.close()
    print(f"✅ Загружены города вылета: {len(data)}")

def save_resorts():
    url = f"{BASE_URL}/directory/resorts"
    resp = requests.get(url, headers=HEADERS).json()
    data = resp.get("data", [])
    con = get_connection()
    cur = con.cursor()
    for r in data:
        cur.execute("INSERT OR REPLACE INTO resorts (id, country_id, name) VALUES (?, ?, ?)",
                    (r["id"], r["countryId"], r["name"]))
    con.commit(); con.close()
    print(f"✅ Загружены курорты: {len(data)}")

def save_hotel_categories():
    url = f"{BASE_URL}/directory/hotelCategories"
    resp = requests.get(url, headers=HEADERS).json()
    data = resp.get("data", [])
    con = get_connection()
    cur = con.cursor()
    for cat in data:
        cur.execute("INSERT OR REPLACE INTO hotel_categories (id, name) VALUES (?, ?)", (cat["id"], cat["name"]))
    con.commit(); con.close()
    print(f"✅ Загружены категории отелей: {len(data)}")

def save_meals():
    url = f"{BASE_URL}/directory/meals"
    resp = requests.get(url, headers=HEADERS).json()
    data = resp.get("data", [])
    con = get_connection()
    cur = con.cursor()
    for m in data:
        cur.execute("INSERT OR REPLACE INTO meals (id, name) VALUES (?, ?)", (m["id"], m["name"]))
    con.commit(); con.close()
    print(f"✅ Загружены типы питания: {len(data)}")

# -------------------------------
# Туровые предложения
# -------------------------------

def get_cheapest_tours(country_id: int, city_id: int, nights_from=7, nights_to=12, adults=2, kids=0):
    query = {
        "countries[]": country_id,
        "departureCity": city_id,
        "nightRange[from]": nights_from,
        "nightRange[to]": nights_to,
        "touristGroup[adults]": adults,
        "touristGroup[kids]": kids,
        "touristGroup[infants]": 0,
        "checkInDateRange[from]": "2025-10-07",
        "checkInDateRange[to]": "2025-11-06",
        "hotelCategories[]": [2, 3, 4, 7, 8],  # 2-5*
        "resorts[]": [2162, 2163, 2159]  # любые курорты страны (из справочника)
    }
    resp = requests.get(f"{BASE_URL}/statistic/cheapestTours", params=query, headers=HEADERS)
    if resp.status_code == 200:
        return resp.json().get("data", [])
    return []

def save_tours(tours, country_id, city_id):
    con = get_connection()
    cur = con.cursor()
    for t in tours:
        # цена может быть int или {"amount": ..., "currency": ...}
        if isinstance(t.get("price"), dict):
            price = t["price"].get("amount")
            currency = t["price"].get("currency", "RUB")
        else:
            price = t.get("price")
            currency = "RUB"

        cur.execute("""
            INSERT INTO tours(api_id, country_id, city_id, resort_id, hotel_name,
                             nights, price, currency, url, check_in, adults, kids,
                             hotel_category_id, meal_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            t.get("hotelId"),
            country_id,
            city_id,
            t.get("resortId"),
            t.get("hotelName"),
            t.get("nights"),
            price,
            currency,
            t.get("tourPageUrl"),
            t.get("checkinDate"),
            2,
            0,
            t.get("hotelCategory"),
            t.get("mealId")
        ))
    con.commit()
    con.close()
    print(f"💾 Сохранено {len(tours)} туров ({country_id}/{city_id})")

def load_and_save_cheapest_tours(country_id, city_id, nights_from=7, nights_to=12):
    tours = get_cheapest_tours(country_id, city_id, nights_from, nights_to)
    if tours:
        save_tours(tours, country_id, city_id)
    else:
        print(f"⚠️ Нет данных для {country_id}/{city_id}")

# -------------------------------
# Массовая загрузка популярных направлений
# -------------------------------

if __name__ == "__main__":
    # Загрузим справочники
    save_countries()
    save_cities()
    save_resorts()
    save_hotel_categories()
    save_meals()

    countries = {92: "Турция"}
    cities = {2: "Москва", 25: "Екатеринбург"}

    for c_id in countries:
        for city_id in cities:
            print(f"🔎 Загружаю {countries[c_id]} из {cities[city_id]} (5–14 ночей)")
            load_and_save_cheapest_tours(c_id, city_id, 5, 14)