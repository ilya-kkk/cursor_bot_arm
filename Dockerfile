FROM python:3.12-slim

# Устанавливаем зависимости для Python и Cursor CLI (если нужно)
RUN apt-get update && apt-get install -y curl unzip git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем бота
COPY bot/ ./bot
WORKDIR /app/bot

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir pyTelegramBotAPI

RUN ln -s /usr/bin/node /usr/local/bin/node
