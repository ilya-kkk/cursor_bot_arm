FROM python:3.12-slim

# curl, bash, unzip, git
RUN apt-get update && apt-get install -y curl bash unzip git nodejs npm && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Установка Cursor
RUN curl https://cursor.com/install -fsS | bash

# Копируем бота
COPY bot/ ./bot

WORKDIR /app/bot
RUN pip install --no-cache-dir pyTelegramBotAPI
