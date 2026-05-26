-- Таблица фильмов
CREATE TABLE IF NOT EXISTS movies (
    id SERIAL PRIMARY KEY,
    kinopoisk_id INT UNIQUE,           -- ID Кинопоиска для синхронизации и апдейтов
    title VARCHAR(255) NOT NULL,       -- Название фильма
    year INT,                          -- Год выпуска
    description TEXT,                  -- Описание для бота
    poster_url VARCHAR(512),           -- Ссылка на постер
    kp_url VARCHAR(512),               -- Ссылка на Кинопоиск
    rutube_url VARCHAR(512),           -- Ссылка на Rutube
    created_at TIMESTAMP DEFAULT NOW()
);

-- Таблица цветов (настроений)
CREATE TABLE IF NOT EXISTS colors (
    id SERIAL PRIMARY KEY,
    color_name VARCHAR(50) UNIQUE NOT NULL, -- Кодовое имя (red, deep_blue, yellow и т.д.)
    hex_code VARCHAR(7),                     -- #HEX код для интерфейса
    mood_description VARCHAR(255)            -- Описание эмоции
);

-- Таблица связей Многие-ко-Многим (Один фильм может подходить под разные цвета)
CREATE TABLE IF NOT EXISTS movie_colors (
    movie_id INT REFERENCES movies(id) ON DELETE CASCADE,
    color_id INT REFERENCES colors(id) ON DELETE CASCADE,
    weight INT DEFAULT 100,                  -- Вес цвета (интенсивность)
    PRIMARY KEY (movie_id, color_id)
);

-- Индексы для ускорения выборок ботом
CREATE INDEX IF NOT EXISTS idx_movies_kinopoisk_id ON movies(kinopoisk_id);
CREATE INDEX IF NOT EXISTS idx_movie_colors_color ON movie_colors(color_id);

-- Наполнение расширенной палитры настроений для проекта KinoTavr
INSERT INTO colors (color_name, hex_code, mood_description) VALUES
('deep_blue',   '#1A365D', 'Грусть (Меланхолия, драмы, одиночество)'),
('yellow',      '#ECC94B', 'Радость (Комедии, семейные, позитив)'),
('crimson',     '#9B2C2C', 'Жестокость (Криминал, жесткий экшен, месть)'),
('black',       '#171717', 'Страх (Ужасы, хорроры, гнетущая атмосфера)'),
('purple',      '#553C9A', 'Загадочность (Фантастика, космос, магия, фэнтези)'),
('emerald',     '#22543D', 'Интрига (Детективы, шпионские игры, заговоры)')
ON CONFLICT (color_name) DO NOTHING;