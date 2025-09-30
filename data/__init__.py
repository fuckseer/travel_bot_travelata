import os
import sqlite3

DB_PATH = "travelata.db"
MIGRATIONS_FILE = "migrations.sql"

def init_db():

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    with open(MIGRATIONS_FILE, "r", encoding="utf-8") as f:
        sql_script = f.read()
        cur.executescript(sql_script)

    con.commit()
    con.close()
    print(f"✅ SQLite база создана: {DB_PATH}")

if __name__ == "__main__":
    init_db()