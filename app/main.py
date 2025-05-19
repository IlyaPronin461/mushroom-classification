# запустить: docker-compose up -d
# остановить: docker-compose down
# пересобрать и запустить: docker-compose up --build -d
# удалить старые контейнеры и volumes: docker-compose down -v
# вывести логи: docker-compose logs -f   (выйти ctrl+C)


from fastapi import FastAPI
from app.config import logger
import asyncio
from app.telegram_bot import TelegramBot
from app.services import MushroomClassifier
from pathlib import Path

app = FastAPI(
    title="Mushroom Classification API",
    description="API для классификации грибов по изображениям",
    version="1.0.0"
)


def read_token_from_file():
    try:
        token_path = Path("telegram_bot_token.txt")
        with open(token_path, 'r') as f:
            token = f.read().strip()
        if not token:
            raise ValueError("Файл токена пуст")
        return token
    except Exception as e:
        logger.error(f"Ошибка чтения токена: {str(e)}")
        raise


@app.on_event("startup")
async def startup_event():
    logger.info("Запуск сервера и бота...")

    # Сначала инициализируем бота
    token = read_token_from_file()
    bot = TelegramBot(token, MushroomClassifier())

    # Запускаем бота в фоновом режиме
    asyncio.create_task(bot.run())

    logger.info("Сервер и бот успешно запущены")