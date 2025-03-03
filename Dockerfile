FROM python:3.12-slim

# Установка ffmpeg для обработки видео
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Установка зависимостей Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем только точку входа, НЕ включая app/
COPY server.py .

# Создаем необходимые директории
RUN mkdir -p downloads temp static logs

# Открываем порт
EXPOSE 5001

# Запускаем сервер
CMD ["python", "server.py"]