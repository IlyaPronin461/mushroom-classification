import psycopg2
import logging
import os
from dotenv import load_dotenv
import time

load_dotenv()

class DataBase:
    def __init__(self):
        # Загружаем параметры из .env
        self.name_db = os.getenv("POSTGRES_DB", "mushroom_classification")
        self.host = os.getenv("POSTGRES_HOST", "db")
        self.user = os.getenv("POSTGRES_USER", "postgres")
        self.password = os.getenv("POSTGRES_PASSWORD", "postgres")
        self.port = os.getenv("POSTGRES_PORT", "5432")

        # Настройка логирования
        logging.basicConfig(
            format='%(asctime)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )

    def get_user_by_telegram_id(self, telegram_user_id):
        """Получить пользователя по Telegram ID"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                logging.info(f"Запрос на получение пользователя с Telegram ID: {telegram_user_id}")
                cursor.execute(
                    "SELECT id FROM users WHERE telegram_user_id = %s",
                    (telegram_user_id,)
                )
                user = cursor.fetchone()
                if user:
                    logging.info(f"Пользователь найден с ID: {user[0]}")
                    return user
                logging.info(f"Пользователь с Telegram ID {telegram_user_id} не найден.")
                return None
        except Exception as e:
            logging.error(f"Ошибка при получении пользователя: {e}")
            return None
        finally:
            conn.close()

    def create_user(self, username, telegram_user_id):
        """Добавить пользователя в базу данных, если его нет"""
        # Проверяем, существует ли уже пользователь
        existing_user = self.get_user_by_telegram_id(telegram_user_id)

        if existing_user:
            logging.info(f"Пользователь с ID {telegram_user_id} уже существует.")
            return existing_user[0]  # Возвращаем ID существующего пользователя

        # Если пользователя нет, добавляем нового
        conn = self.get_connection()
        try:
            logging.info(f"Создание нового пользователя с Telegram ID {telegram_user_id} и username {username}")
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO users (username, telegram_user_id)
                    VALUES (%s, %s)
                    RETURNING id;
                    """,
                    (username, telegram_user_id)
                )
                conn.commit()
                user_id = cursor.fetchone()[0]  # Получаем ID нового пользователя
                logging.info(f"Новый пользователь добавлен с ID: {user_id}")
                return user_id
        except Exception as e:
            logging.error(f"Ошибка добавления пользователя: {e}")
            raise
        finally:
            conn.close()

    def get_connection(self, database=None, max_retries=5, retry_delay=5):
        """Улучшенная функция подключения с повторами"""
        for attempt in range(max_retries):
            try:
                conn = psycopg2.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=database if database else self.name_db,
                    port=self.port,
                    connect_timeout=5
                )
                logging.info(f"Успешное подключение к БД {database or self.name_db}")
                return conn
            except psycopg2.OperationalError as e:
                logging.warning(
                    f"Попытка {attempt + 1}/{max_retries}: Ошибка подключения к {self.host}:{self.port}. "
                    f"Ошибка: {e}. Повтор через {retry_delay} сек..."
                )
                if attempt == max_retries - 1:
                    logging.error(f"Не удалось подключиться после {max_retries} попыток")
                    raise
                time.sleep(retry_delay)
            except psycopg2.Error as e:
                logging.error(f"Критическая ошибка подключения: {e}")
                raise
