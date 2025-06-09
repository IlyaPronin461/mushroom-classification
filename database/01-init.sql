-- Создание таблицы для пользователей
CREATE TABLE IF NOT EXISTS users
(
    id              bigserial PRIMARY KEY,
    username        varchar(255),
    telegram_user_id bigint    NOT NULL UNIQUE,
    created_at      timestamp DEFAULT CURRENT_TIMESTAMP,
    last_activity   timestamp DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_telegram_user_id ON users (telegram_user_id);

-- Пример вставки тестового пользователя
INSERT INTO users (username, telegram_user_id)
VALUES
('test_user', 123456789);
