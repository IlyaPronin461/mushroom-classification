from app.celery_app import celery_app
from app.services import MushroomClassifier
from app.config import settings
from PIL import Image
import tempfile
import io
import base64
import logging


@celery_app.task(bind=True)
def classify_mushroom_image(self, photo_base64: str):
    """Фоновая задача для классификации гриба по изображению"""
    try:
        logging.info("Начинаю обработку изображения...")

        # Декодируем фото из base64 обратно в байты
        photo_bytes = base64.b64decode(photo_base64)

        logging.info("Фото успешно декодировано.")

        # Преобразуем фото в изображение
        image = Image.open(io.BytesIO(photo_bytes))
        if image.mode != "RGB":
            image = image.convert("RGB")

        logging.info("Изображение успешно преобразовано в формат RGB.")

        # Временный файл для изображения
        with tempfile.NamedTemporaryFile(suffix=".jpg") as temp_file:
            image.save(temp_file, format="JPEG")
            logging.info("Изображение сохранено во временный файл.")

            # Используем классификатор для предсказания
            classifier = MushroomClassifier()
            predictions = classifier.predict(temp_file.name)
            logging.info(f"Получены предсказания: {predictions}")

        # Формируем результаты
        response = []
        for pred in predictions[:5]:
            class_name = pred['class_name']
            description = settings.mushroom_descriptions.get(
                class_name,
                f"{class_name}. Информация о съедобности отсутствует"
            )
            response.append({
                'class_name': class_name,
                'confidence': pred['confidence'],
                'description': description
            })

        logging.info("Результаты классификации сформированы.")

        return response

    except Exception as e:
        logging.error(f"Ошибка при обработке изображения: {str(e)}", exc_info=True)
        raise self.retry(exc=e)  # В случае ошибки повторяем задачу
