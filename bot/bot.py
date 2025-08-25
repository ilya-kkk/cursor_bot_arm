import subprocess
import json
import os
from pathlib import Path
from telebot import TeleBot

TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN не задан в переменных окружениях!")

bot = TeleBot(TOKEN)
USERS_FILE = Path("users.json")

# Если файла нет — создаём пустой
if not USERS_FILE.exists():
    USERS_FILE.touch()

# Загрузка пользователей
allowed_users = []
if USERS_FILE.is_file() and USERS_FILE.stat().st_size > 0:
    try:
        allowed_users = json.load(open(USERS_FILE, "r"))
    except json.JSONDecodeError:
        allowed_users = []


def extract_text_from_line(line: str) -> str | None:
    """Вытаскивает текст из JSON-строки cursor-agent, если это ответ ассистента."""
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return None

    if data.get("type") == "assistant":
        message = data.get("message", {})
        content = message.get("content", [])
        texts = [item["text"] for item in content if item.get("type") == "text" and "text" in item]
        return "".join(texts)
    return None


def extract_tool_call_status(line: str) -> str | None:
    """
    Вытаскивает информацию о вызовах инструментов (tool_call) из JSON-строки.
    Возвращает строку статуса для отображения прогресса.
    """
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return None

    if data.get("type") == "tool_call":
        subtype = data.get("subtype")
        call_id = data.get("call_id")
        tool_info = data.get("tool_call", {})

        # Если инструмент завершился с ошибкой
        result_text = ""
        if subtype == "completed":
            for tool_name, result in tool_info.items():
                res = result.get("result", {})
                if "error" in res:
                    error_msg = res["error"].get("errorMessage", "неизвестная ошибка")
                    result_text = f"[{tool_name}] Ошибка: {error_msg}\n"
                else:
                    result_text = f"[{tool_name}] Выполнено успешно\n"
        elif subtype == "started":
            result_text = f"[{list(tool_info.keys())[0]}] Запуск...\n"

        return f"({call_id}) {result_text}"
    return None


@bot.message_handler(commands=['work_rock'])
def register_user(message):
    global allowed_users
    if allowed_users:
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
    thread_id = getattr(message, "message_thread_id", None)

    if chat_id not in allowed_users:
        return

    command_text = message.text
    if not command_text:
        bot.send_message(chat_id, "Нет текста для отправки в Cursor CLI.", message_thread_id=thread_id)
        return

    try:
        # отправляем "заглушку", чтобы потом редактировать её
        sent = bot.send_message(chat_id, "⏳ Выполняю запрос...", message_thread_id=thread_id)

        process = subprocess.Popen(
            ["/home/orangepi/.local/bin/cursor-agent"] + command_text.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        accumulated_text = ""
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue

            assistant_text = extract_text_from_line(line)
            tool_status = extract_tool_call_status(line)

            update_text = ""
            if assistant_text:
                update_text += assistant_text + "\n"
            if tool_status:
                update_text += tool_status + "\n"

            if update_text:
                accumulated_text += update_text
                try:
                    bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=sent.message_id,
                        text=accumulated_text[-4000:]
                    )
                except Exception as e:
                    print(f"Ошибка редактирования: {e}")

        process.wait()

    except Exception as e:
        bot.send_message(chat_id, f"Ошибка запуска cursor-agent: {e}", message_thread_id=thread_id)


print("Бот запущен...")
bot.polling(none_stop=True)
