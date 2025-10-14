-- Справочник стран
CREATE TABLE IF NOT EXISTS countries (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

-- Справочник городов вылета
CREATE TABLE IF NOT EXISTS cities (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

-- Справочник курортов
CREATE TABLE IF NOT EXISTS resorts (
    id INTEGER PRIMARY KEY,
    country_id INTEGER,
    name TEXT NOT NULL,
    FOREIGN KEY (country_id) REFERENCES countries(id)
);

-- Категории отелей
CREATE TABLE IF NOT EXISTS hotel_categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

-- Типы питания
CREATE TABLE IF NOT EXISTS meals (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

-- Горящие туры
CREATE TABLE IF NOT EXISTS tours (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_id INTEGER,                -- ID тура в Travelata
    country_id INTEGER,            -- страна
    city_id INTEGER,               -- город вылета
    resort_id INTEGER,             -- курорт
    hotel_name TEXT,               -- название отеля
    nights INTEGER,                -- количество ночей
    price INTEGER,                 -- цена
    currency TEXT,                 -- валюта
    url TEXT,                      -- ссылка на тур
    check_in DATE,                 -- дата заезда
    adults INTEGER DEFAULT 2,
    kids INTEGER DEFAULT 0,
    hotel_category_id INTEGER,     -- категория отеля
    meal_id INTEGER,               -- питание
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    FOREIGN KEY (country_id) REFERENCES countries(id),
    FOREIGN KEY (city_id) REFERENCES cities(id),
    FOREIGN KEY (resort_id) REFERENCES resorts(id),
    FOREIGN KEY (hotel_category_id) REFERENCES hotel_categories(id),
    FOREIGN KEY (meal_id) REFERENCES meals(id)
);

CREATE TABLE IF NOT EXISTS hotel_descriptions (
    hotel_api_id INTEGER PRIMARY KEY,
    hotel_name TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для ускорения поиска туров
CREATE INDEX IF NOT EXISTS idx_tours_country ON tours(country_id);
CREATE INDEX IF NOT EXISTS idx_tours_city    ON tours(city_id);
CREATE INDEX IF NOT EXISTS idx_tours_resort  ON tours(resort_id);
CREATE INDEX IF NOT EXISTS idx_tours_date    ON tours(check_in);
CREATE INDEX IF NOT EXISTS idx_tours_price   ON tours(price);