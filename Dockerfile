FROM python:3.9-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем зависимости отдельно для кеширования
COPY requirements.txt .

# Устанавливаем pip и пакеты с отключенной проверкой SSL
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    --retries 5 \
    --timeout 300 \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    -r requirements.txt

# Копируем остальные файлы
COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]