FROM python:3.12-slim

# Устанавливаем зависимости для Python и Cursor CLI (если нужно)
RUN apt-get update && apt-get install -y curl unzip git && rm -rf /var/lib/apt/lists/*

WORKDIR /app/cursor-agent
COPY /home/orangepi/.local/bin/cursor-agent ./cursor-agent
COPY /home/orangepi/.local/lib/node_modules ./node_modules
RUN chmod +x cursor-agent
# Копируем бота
COPY bot/ ./bot
WORKDIR /app/bot

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir pyTelegramBotAPI



