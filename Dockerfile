FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/* \

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Копируем папку с фотографиями
COPY mushroom_photo /app/mushroom_photo

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]