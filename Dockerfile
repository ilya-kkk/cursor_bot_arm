FROM python:3.12-slim

RUN apt-get update && apt-get install -y curl bash unzip git nodejs npm && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Установка Cursor
RUN curl https://cursor.com/install -fsS | bash

# Копируем бота
COPY bot/ ./bot

WORKDIR /app/bot
RUN pip install --no-cache-dir pyTelegramBotAPI

# Выполняем автологин через токен из ENV
RUN /root/.local/bin/cursor-agent login --token $CURSOR_TOKEN

