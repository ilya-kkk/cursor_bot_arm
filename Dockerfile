FROM python:3.12-slim

# Устанавливаем зависимые пакеты для cursor CLI (если есть)
RUN apt-get update && apt-get install -y \
    curl unzip git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем бота
COPY bot/ ./bot
WORKDIR /app/bot

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir pyTelegramBotAPI


