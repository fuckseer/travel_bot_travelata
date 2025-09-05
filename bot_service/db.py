import sqlite3
from bot_service.config import load_config

config = load_config()
DB_PATH = config["database"]["path"]

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    con = get_connection()
    cur = con.cursor()
    cur.executescript(open("data/migrations.sql").read())
    con.commit()
    con.close()

def save_tours(tours, country_id, city_id):
    con = get_connection()
    cur = con.cursor()
    for t in tours:
        cur.execute("""
            INSERT INTO tours(api_id, country_id, city_id, resort_id, nights, price, url, check_in, adults, kids)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            t.get("id"), country_id, city_id, t.get("resortId"),
            t.get("nightCount"), t["price"]["amount"], t.get("detailsPageUrl"),
            t.get("checkInDate"), t.get("adults", 2), t.get("kids", 0)
        ))
    con.commit()
    con.close()