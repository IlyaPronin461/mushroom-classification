# запустить: docker-compose up -d
# остановить: docker-compose down
# пересобрать и запустить: docker-compose up --build -d
# удалить старые контейнеры и volumes: docker-compose down -v
# вывести логи: docker-compose logs -f   (выйти ctrl+C)

# curl.exe -X POST -F "file=@Amanita-rubescens-2012-08-31-IMG_9307.jpg" http://localhost:8000/predict
# curl.exe -X POST -F "file=@fomes-fomentarius-mushroom.jfif" http://localhost:8000/predict

# в postman http://localhost:8000/predict менять на http://127.0.0.1:8000/predict


from fastapi import FastAPI, UploadFile, File, HTTPException
from .models import TopPredictions
from .services import MushroomClassifier
import tempfile
import os
from PIL import Image
import io
import logging
from .config import logger

app = FastAPI(
    title="Mushroom Classification API",
    description="API для классификации грибов по изображениям",
    version="1.0.0"
)

logger = logging.getLogger("app.main")
classifier = MushroomClassifier()


@app.on_event("startup")
async def startup_event():
    logger.info("Сервер запущен")


@app.post("/predict", response_model=TopPredictions)
async def predict_mushroom(file: UploadFile = File(...)):
    logger.info(f"Получен запрос на классификацию от {file.filename}")
    try:
        # Читаем содержимое файла в память
        logger.debug("Чтение файла изображения")
        image_data = await file.read()

        # Открываем изображение с помощью PIL и конвертируем в RGB
        logger.debug("Обработка изображения")
        image = Image.open(io.BytesIO(image_data))
        if image.mode != "RGB":
            logger.debug("Конвертация изображения в RGB")
            image = image.convert("RGB")

        # Сохраняем временный файл
        logger.debug("Создание временного файла")
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            image.save(temp_file, format="JPEG")
            temp_path = temp_file.name
            logger.debug(f"Временный файл сохранен: {temp_path}")

        # Получаем предсказания
        logger.info("Запуск классификации изображения")
        predictions = classifier.predict(temp_path)

        # Удаляем временный файл
        logger.debug("Удаление временного файла")
        os.unlink(temp_path)

        logger.info("Запрос успешно обработан")
        return {"predictions": predictions}

    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    logger.info("Health check requested")
    return {"status": "OK"}