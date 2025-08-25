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

# Cursor CLI: предполагаем что у тебя есть бинарь ARM в ./cursor
COPY cursor /usr/local/bin/cursor
RUN chmod +x /usr/local/bin/cursor

CMD ["python", "bot.py"]
