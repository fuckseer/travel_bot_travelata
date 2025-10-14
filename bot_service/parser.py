import sqlite3
import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from utils.config import load_config, get_db_path

DB_PATH = get_db_path(load_config())


def parse_hotel_description(html: str) -> str:
    """Извлекает текстовое описание и атрибуты из HTML."""
    soup = BeautifulSoup(html, "html.parser")
    parts = []

    # основной блок описания
    text_block = soup.select_one(".attributes__text")
    if text_block:
        parts.append(text_block.get_text(" ", strip=True))

    # иконки (пляж, бар и т.д.)
    icons = [i.get_text(strip=True) for i in soup.select(".attributes__icon-text")]
    if icons:
        parts.append(" | ".join(icons))

    # секции .attrGroup (удобства, пляж, спорт и пр.)
    for g in soup.select(".attrGroup"):
        title = g.select_one(".attrGroupName")
        content = g.select_one(".attrGroupContent")
        if title and content:
            parts.append(f"{title.get_text(strip=True)}: {content.get_text(' ', strip=True)}")

    return "\n".join(parts).strip()


def hotel_exists(cur, api_id: int) -> bool:
    """Проверяет, есть ли отель уже в hotel_descriptions."""
    cur.execute("SELECT 1 FROM hotel_descriptions WHERE hotel_api_id = ?", (api_id,))
    return cur.fetchone() is not None


def scrape_hotels(batch_size: int = 10):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.row_factory = sqlite3.Row

    # получаем уникальные отели без описаний
    hotels = cur.execute("""
        SELECT DISTINCT api_id, hotel_name, url
        FROM tours
        WHERE url IS NOT NULL
        ORDER BY api_id
    """).fetchall()

    print(f"Всего найдено {len(hotels)} уникальных отелей.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/122.0.0.0 Safari/537.36",
            locale="ru-RU",
        )
        page = context.new_page()

        processed = 0
        for h in hotels:
            api_id, name, url = h["api_id"], h["hotel_name"], h["url"]

            # проверяем перед парсингом
            if hotel_exists(cur, api_id):
                continue

            print(f"→ [{processed+1}/{len(hotels)}] {api_id}: {name}")

            try:
                page.goto(url, wait_until="networkidle", timeout=60000)
                time.sleep(10)
                html = page.content()
                desc = parse_hotel_description(html)
            except Exception as e:
                print(f"⚠️ Ошибка загрузки {api_id}: {e}")
                continue

            if desc:
                cur.execute("""
                    INSERT OR IGNORE INTO hotel_descriptions (hotel_api_id, hotel_name, description)
                    VALUES (?, ?, ?)
                """, (api_id, name, desc))
                con.commit()
                print(f"✅ Сохранено: {api_id} ({len(desc)} символов)")
            else:
                print(f"⚠️ Пустое описание: {api_id}")

            processed += 1
            if processed % batch_size == 0:
                print(f"⏸️ Обработано {processed}, маленькая пауза...")
                time.sleep(5)
            else:
                time.sleep(2)

        browser.close()
    con.close()


if __name__ == "__main__":
    scrape_hotels(batch_size=20)