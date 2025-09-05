-- ======================
-- TravelBot - DB schema
-- ======================

-- Справочник стран
CREATE TABLE IF NOT EXISTS countries (
    id INTEGER PRIMARY KEY,   -- id из Travelata API
    name TEXT NOT NULL
);

-- Справочник городов вылета
CREATE TABLE IF NOT EXISTS cities (
    id INTEGER PRIMARY KEY,   -- id из Travelata API
    name TEXT NOT NULL
);

-- Справочник курортов
CREATE TABLE IF NOT EXISTS resorts (
    id INTEGER PRIMARY KEY,   -- id из Travelata API
    country_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (country_id) REFERENCES countries(id)
);

-- Таблица туров (кэш от Travelata API)
CREATE TABLE IF NOT EXISTS tours (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_id INTEGER,              -- уникальный id тура из Travelata
    country_id INTEGER,
    city_id INTEGER,             -- город вылета
    resort_id INTEGER,           -- курорт
    hotel_name TEXT,             -- название отеля
    nights INTEGER,
    price INTEGER,
    currency TEXT,
    url TEXT,
    check_in DATE,               -- дата заезда
    adults INTEGER,
    kids INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (country_id) REFERENCES countries(id),
    FOREIGN KEY (city_id) REFERENCES cities(id),
    FOREIGN KEY (resort_id) REFERENCES resorts(id)
);

-- Индексы для ускорения поиска
CREATE INDEX IF NOT EXISTS idx_tours_country ON tours(country_id);
CREATE INDEX IF NOT EXISTS idx_tours_city ON tours(city_id);
CREATE INDEX IF NOT EXISTS idx_tours_resort ON tours(resort_id);
CREATE INDEX IF NOT EXISTS idx_tours_checkin ON tours(check_in);