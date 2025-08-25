import os
import json
import asyncio
from telegram import Bot
from telegram.constants import ParseMode
from cursor_agent import Agent

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))
TOPIC_ID = int(os.getenv("TOPIC_ID", "0"))  # ID топика, если нужен

bot = Bot(token=TELEGRAM_TOKEN)
agent = Agent()

async def send_request_to_cursor(query: str):
    """Отправляем запрос в Cursor и получаем потоковый ответ"""
    response_text = ""
    async for chunk in agent.ask_stream(query):  # потоковый ответ
        try:
            data = json.loads(chunk)
            if "content" in data:
                response_text += data["content"]
                yield response_text
        except json.JSONDecodeError:
            continue

async def process_message(query: str):
    # отправляем первое сообщение
    msg = await bot.send_message(
        chat_id=CHAT_ID,
        text="⏳ Выполняю запрос...",
        message_thread_id=TOPIC_ID if TOPIC_ID > 0 else None
    )

    # обновляем сообщение по мере поступления данных
    async for partial_text in send_request_to_cursor(query):
        try:
            await bot.edit_message_text(
                chat_id=CHAT_ID,
                message_id=msg.message_id,
                text=partial_text,
                parse_mode=ParseMode.MARKDOWN,
                message_thread_id=TOPIC_ID if TOPIC_ID > 0 else None
            )
            await asyncio.sleep(0.5)  # чтобы не упереться в лимит Telegram
        except Exception as e:
            print(f"Ошибка редактирования: {e}")

async def main():
    # пример: запрос вручную
    await process_message("Привет, объясни что такое JSON поток?")

if __name__ == "__main__":
    asyncio.run(main())
