# запустить: docker-compose up -d
# остановить: docker-compose down
# пересобрать и запустить: docker-compose up --build -d
# удалить старые контейнеры и volumes: docker-compose down -v
# вывести логи: docker-compose logs -f   (выйти ctrl+C)


# смотрим информацию и докере (id в том числе): docker ps
# подлючение к контейнеру с PostgreSQL: docker exec -it mushroom-classification-db-1 bash
# для подключения к базе данных: PGPASSWORD=<password> psql -U <user> -h db -d mushroom_classification
# и потом делать запрос: SELECT * FROM users;
# включить и выключить расширенный режим вывода: \x
# и потом делать запрос: SELECT * FROM interactions;
# логи БД: docker logs mushroom-classification-db-1


from fastapi import FastAPI
from app.config import logger
import asyncio
from app.telegram_bot import TelegramBot
from app.services import MushroomClassifier
from app.config import settings
from app.DataBase import DataBase  # Импортируем DataBase для добавления пользователя

app = FastAPI(
    title="Mushroom Classification API",
    description="API для классификации грибов по изображениям",
    version="1.0.3"
)

db = DataBase()  # Создаём объект для работы с БД

def read_token_from_file():
    try:
        token = settings.telegram_bot_token
        if not token:
            raise ValueError("Токен Telegram пуст")
        return token
    except Exception as e:
        logger.error(f"Ошибка чтения токена: {str(e)}")
        raise


@app.on_event("startup")
async def startup_event():
    logger.info("Запуск сервера и бота...")

    # Добавляем задержку перед подключением к БД
    await asyncio.sleep(10)  # Задержка в 10 секунд

    # Инициализируем бота с передачей объекта базы данных
    token = read_token_from_file()
    classifier = MushroomClassifier()  # Создаём экземпляр классификатора
    bot = TelegramBot(token, classifier, db)  # Передаем db и классификатор в конструктор бота

    # Запускаем бота в фоновом режиме
    asyncio.create_task(bot.run())

    logger.info("Сервер и бот успешно запущены")
