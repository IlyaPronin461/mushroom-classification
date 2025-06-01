import tempfile
import base64
import redis
import pickle
from app.services import MushroomClassifier
from app.config import settings
import logging
from app.celery_app import celery_app

@celery_app.task(bind=True)
def classify_mushroom_image(self, photo_base64: str):
    """Фоновая задача для классификации гриба по изображению"""
    try:
        # Извлекаем модель из Redis
        redis_client = redis.StrictRedis(host='redis', port=6379, db=0)
        classifier_data = redis_client.get('mushroom_classifier')

        if classifier_data is None:
            # Если модель не найдена в Redis, создаем новую
            classifier = MushroomClassifier()
        else:
            classifier = pickle.loads(classifier_data)

        # Декодируем изображение из base64
        photo_bytes = base64.b64decode(photo_base64)

        # Создаем временный файл для изображения
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_file.write(photo_bytes)
            temp_file_path = temp_file.name

        # Теперь передаем путь к временно сохраненному файлу в сервис для классификации
        predictions = classifier.predict(temp_file_path)

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
