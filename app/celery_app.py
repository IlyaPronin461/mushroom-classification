from celery import Celery

# Настройка брокера (Redis)
celery_app = Celery(
    'mushroom_classification',
    broker='redis://redis:6379/0',  # измените localhost на имя сервиса Redis
    backend='redis://redis:6379/0'
)

# Настройки Celery
celery_app.conf.update(
    result_expires=3600,  # Время жизни результатов задачи
    task_serializer='json',  # Формат сериализации задач
    accept_content=['json'],  # Разрешенные форматы задач
)