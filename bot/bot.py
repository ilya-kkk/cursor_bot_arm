import subprocess
import json
import os
import time
from pathlib import Path
from telebot import TeleBot

TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN не задан в переменных окружениях!")

bot = TeleBot(TOKEN)
USERS_FILE = Path("users.json")
SESSIONS_FILE = Path("cursor_sessions.json")

for f in [USERS_FILE, SESSIONS_FILE]:
    if not f.exists():
        f.touch()

allowed_users = []
if USERS_FILE.is_file() and USERS_FILE.stat().st_size > 0:
    try:
        allowed_users = json.load(open(USERS_FILE, "r"))
    except json.JSONDecodeError:
        allowed_users = []

sessions = {}
if SESSIONS_FILE.is_file() and SESSIONS_FILE.stat().st_size > 0:
    try:
        sessions = json.load(open(SESSIONS_FILE, "r"))
    except json.JSONDecodeError:
        sessions = {}


def save_sessions():
    with open(SESSIONS_FILE, "w") as f:
        json.dump(sessions, f)


def extract_text_from_line(line: str) -> str | None:
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return None

    if data.get("type") == "assistant":
        message = data.get("message", {})
        content = message.get("content", [])
        texts = [item["text"] for item in content if item.get("type") == "text" and "text" in item]
        return "".join(texts)
    
    # Сохраняем session_id
    if data.get("type") == "system" and data.get("subtype") == "init":
        sid = data.get("session_id")
        if sid:
            sessions["last_session_id"] = sid
            save_sessions()
    return None


def extract_tool_call_status(line: str) -> str | None:
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return None

    if data.get("type") == "tool_call":
        subtype = data.get("subtype")
        call_id = data.get("call_id")
        tool_info = data.get("tool_call", {})

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

    resume_flag = ""
    for part in command_text.split():
        if part.startswith("--resume="):
            resume_flag = part
            break
    if not resume_flag and "last_session_id" in sessions:
        resume_flag = f"--resume={sessions['last_session_id']}"

    try:
        sent = bot.send_message(chat_id, "⏳ Выполняю запрос...", message_thread_id=thread_id)

        cmd = ["/home/orangepi/.local/bin/cursor-agent"]
        if resume_flag:
            cmd.append(resume_flag)
        cmd += [part for part in command_text.split() if not part.startswith("--resume=")]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        accumulated_text = ""
        buffer = ""
        last_update_time = time.time()
        UPDATE_INTERVAL = 1.0  # секунда

        for line in process.stdout:
            line = line.strip()
            if not line:
                continue

            assistant_text = extract_text_from_line(line)
            tool_status = extract_tool_call_status(line)

            if assistant_text:
                buffer += assistant_text + "\n"
            if tool_status:
                buffer += tool_status + "\n"

            if buffer and (time.time() - last_update_time > UPDATE_INTERVAL or len(buffer) > 500):
                accumulated_text += buffer
                try:
                    bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=sent.message_id,
                        text=accumulated_text[-4000:]
                    )
                except Exception as e:
                    print(f"Ошибка редактирования: {e}")
                buffer = ""
                last_update_time = time.time()

        # финальный апдейт
        if buffer:
            accumulated_text += buffer

        # добавляем session_id в конец
        if "last_session_id" in sessions:
            accumulated_text += f"\n\nSession ID: {sessions['last_session_id']}"

        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=sent.message_id,
                text=accumulated_text[-4000:]
            )
        except Exception as e:
            print(f"Ошибка редактирования финального текста: {e}")

        process.wait()

    except Exception as e:
        bot.send_message(chat_id, f"Ошибка запуска cursor-agent: {e}", message_thread_id=thread_id)


print("Бот запущен...")
bot.polling(none_stop=True)
