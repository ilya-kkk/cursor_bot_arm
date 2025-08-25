FROM python:3.12-slim

# Устанавливаем Node.js
RUN apt-get update && apt-get install -y nodejs npm curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем бота
COPY bot/ ./bot
# Копируем cursor-agent
COPY cursor-agent-package/ ./cursor-agent

WORKDIR /app/bot
RUN pip install --no-cache-dir pyTelegramBotAPI

CMD ["python", "bot.py"]
