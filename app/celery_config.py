from app.celery_app import celery_app  # Импортируем уже готовый объект Celery
from app.tasks import classify_mushroom_image  # Импортируем задачи