import subprocess
import json
import os
from pathlib import Path
from telebot import TeleBot, types

# Получаем токен из переменной окружения
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN не задан в переменных окружения!")

bot = TeleBot(TOKEN)
USERS_FILE = Path("users.json")

# Загрузка сохраненных пользователей
if USERS_FILE.exists():
    with open(USERS_FILE, "r") as f:
        allowed_users = json.load(f)
else:
    allowed_users = []

@bot.message_handler(commands=['work_arm'])
def register_user(message):
    global allowed_users
    if USERS_FILE.exists():
        bot.reply_to(message, "Файл с пользователями уже существует. Регистрация закрыта.")
        return

    chat_id = message.chat.id
    allowed_users.append(chat_id)
    with open(USERS_FILE, "w") as f:
        json.dump(allowed_users, f)
    bot.reply_to(message, f"Регистрация завершена. Этот chat_id будет использоваться для сообщений.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    if USERS_FILE.exists():
        if chat_id not in allowed_users:
            return  # Игнорируем незарегистрированных пользователей
    else:
        return  # ещё никто не зарегистрирован

    command_text = message.text
    if not command_text:
        bot.reply_to(message, "Нет текста для отправки в Cursor CLI.")
        return

    try:
        result = subprocess.run(
            ["cursor"] + command_text.split(),
            capture_output=True,
            text=True
        )
        output = result.stdout or result.stderr
    except Exception as e:
        output = f"Ошибка запуска Cursor CLI: {e}"

    bot.reply_to(message, output[:4000])  # Telegram ограничение 4096 символов

print("Бот запущен...")
bot.polling(none_stop=True)
