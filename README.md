
# 🤖 AI Travel Assistant

**AI Travel Assistant** — это умный Telegram‑бот, который помогает подбирать туры из базы Travelata.  
Он понимает живой текст пользователя (“Хочу в Турцию, первая линия, всё включено, до 1200 €”),
структурирует запрос через LLM (OpenRouter), фильтрует туры по SQL, а затем
*семантически переранжирует (LLM Rerank)* результаты по смыслу описаний отелей.

---

## 🎥 Демо

![AI Travel Assistant demo](demo.gif)

---

## ✨ Основные возможности
- 💬 **Натуральный язык.** Пользователь просто пишет, как если бы говорил с агентом;
- 🧠 **LLM‑парсер.** OpenRouter LLM выделяет страну, даты, бюджет, тип питания, предпочтения;
- 🗂 **Travelata API + SQLite.** Реальные туры и отели кэшируются для быстрого SQL‑поиска;
- ⚡️ **Гибридный поиск.**  
  - *SQL фильтры* → страна, дата, ночи, бюджет, питание;  
  - *LLM Rerank* → переоценка по смыслу описаний отелей (через `llm_service:/similarity`);
- 🗣 **Объяснение.** Для каждого результата генерируется короткое «почему выбран именно этот отель» (через `llm_service:/summarize`);
- 🤖 **Telegram‑бот** на `python‑telegram‑bot v20`.

---

## 🏗️ Архитектура

```
ai-travel-bot/
├── bot_service/          # Telegram‑бот и логика поиска
│   ├── core.py           # обработка запросов пользователя
│   ├── tour_search.py    # SQL + LLM Rerank + Summarization
│   ├── handlers.py       # Telegram‑обработчики сообщений
├── llm_service/          # FastAPI‑сервис с OpenRouter‑LLM
│   ├── main.py           # endpoints /parse /similarity /summarize
│   └── llm_client.py     # низкоуровневые вызовы OpenRouter API
├── data/                 # SQLite база и словари
├── config.yaml           # токены, пути, ключи LLM
├── docker-compose.yaml   # быстрый запуск в двух сервисах
└── README.md
```

### 🔁 Поток запроса
1. **Пользователь** пишет:  
   `Хочу в Турцию в июле, 7 ночей, первая линия, всё включено, 1200 €`;
2. **`llm_service:/parse`** создаёт JSON-параметры;
3. **`bot_service/sql_filter()`** находит кандидатов в SQLite;
4. **`llm_service:/similarity`** выполняет *LLM Rerank*: оценивает смысловую схожесть
   между пожеланиями и описанием отеля;
5. **`llm_service:/summarize`** генерирует объяснение выбора;
6. **Telegram‑бот** возвращает от пользователя:
   ```
   🏨 Sherwood Dreams Resort — 194 486 RUB
   📅 29 окт 2025
   🤖 Отель на первой линии, питание Ultra AI, подходит для спокойного пляжного отдыха.
   ```

---

## 🧠 LLM Reranking (Semantic RAG)

**LLM Rerank** — ключевая часть поиска:

- На вход:  
  *описания отелей* (из `hotel_descriptions.description`) и *мягкие предпочтения* пользователя;
- Сервис `/similarity` в `llm_service` формирует prompt:  
  > «Оцени сходство между пожеланиями и описанием отеля — верни число 0–1».
- Полученный score используется для сортировки результатов (чем выше, тем релевантнее).
- Таким образом, система не просто фильтрует, но и понимает смысл запроса:
  *"бар у моря", "первая линия", "для детей" и т.п.*

---

## 🐳 Быстрый старт

```bash
git clone https://github.com/yourname/ai-travel-bot.git
cd ai-travel-bot

# отредактируйте config.yaml (Telegram token, OpenRouter API‑key)
docker-compose up --build
```

После сборки:
- Бот будет доступен как `bot-service`,  
- LLM‑сервис на `http://localhost:8001`.

---

## ⚙️ config.yaml пример

```yaml
telegram:
  token: "YOUR_TELEGRAM_BOT_TOKEN"

travelata:
  base_url: "https://api-gateway.travelata.ru"
  token: "YOUR_TRAVELATA_TOKEN"

database:
  path: "data/travelata.db"

llm:
  api_key: "sk-your-openrouter-key"
  model: "mistralai/mixtral-8x7b"

llm_service:
  url_parse: "http://llm-service:8001/parse"
  url_similarity: "http://llm-service:8001/similarity"
  url_summarize: "http://llm-service:8001/summarize"
```

---

## 🧭 Команды Docker

| Операция | Команда |
|-----------|----------|
| Сборка и запуск | `docker-compose up --build` |
| Просмотр логов | `docker-compose logs -f bot-service` |
| Подключиться к БД | `docker exec -it bot-service sqlite3 /data/travelata.db` |
| Очистить | `docker-compose down -v` |

---

## 📈 Развитие проекта
- [ ] Добавить кэш открытых embedding’ов (FastAPI memory / Redis);  
- [ ] Поддержка нескольких источников (Travelata, Expedia, Aviasales);  
- [ ] Рейтинг качества LLM‑rerank (метрики nDCG / MRR);  
- [ ] Web‑интерфейс (Streamlit / React) для демо.

---

## 🧾 Лицензия
MIT License  

---

### 🙌 Нашли ошибку?
Присылайте PR или создайте Issue — будем рады сделать бота ещё умнее 🚀
