#!/usr/bin/env python3
"""Telegram-бот для RAG-системы на aiogram (Задание 4, интерфейс)"""

import asyncio
import logging
import os
import sys

# На Python 3.9 Dispatcher() требует существующий event loop в основном потоке.
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rag_core import get_rag_core

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

rag = get_rag_core()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    welcome_text = """
🧙‍♂️ Добро пожаловать в RAG-бот по вселенной Гарри Поттера!

Я могу отвечать на вопросы о персонажах, заклинаниях, зельях и других аспектах вселенной Гарри Поттера.

Доступные команды:
/start - Показать это сообщение
/help - Показать справку
/query <вопрос> - Задать вопрос

Примеры вопросов:
• Кто такой Гарри Поттер?
• Какое зелье приносит удачу?
• Какой факультет у Гарри Поттера?
• Что такое патронус?

Просто напишите ваш вопрос, и я постараюсь ответить! 🪄
    """
    await message.answer(welcome_text)


@dp.message(Command("help"))
async def cmd_help(message: Message):
    help_text = """
📖 Справка по использованию бота

Команды:
/start - Начать работу с ботом
/help - Показать эту справку
/query <вопрос> - Задать вопрос

Как задавать вопросы:
1. Просто напишите вопрос в чат
2. Бот найдет релевантную информацию в базе знаний
3. Бот сгенерирует ответ на основе найденной информации

Примеры вопросов:
• Кто такой Гарри Поттер?
• Какие зелья существуют?
• Расскажи о факультетах Хогвартса
• Что такое патронус?

Если бот не может ответить на вопрос, он скажет "Я не знаю".

💡 Совет: Формулируйте вопросы четко и конкретно для лучших результатов!
    """
    await message.answer(help_text)


@dp.message(Command("query"))
async def cmd_query(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❌ Пожалуйста, укажите вопрос после команды.\n"
            "Пример: /query Кто такой Гарри Поттер?"
        )
        return

    await _answer_query(message, args[1])


@dp.message()
async def handle_message(message: Message):
    if not message.text:
        await message.answer("❌ Пожалуйста, отправьте текстовое сообщение с вопросом.")
        return
    await _answer_query(message, message.text)


async def _answer_query(message: Message, query: str) -> None:
    status_message = await message.answer("🔍 Ищу информацию...")
    try:
        # rag.query — синхронный и тяжёлый, прячем его в пул потоков,
        # чтобы не блокировать event-loop aiogram.
        result = await asyncio.to_thread(rag.query, query)

        answer_text = f"📚 Ответ:\n\n{result['answer']}\n\n📖 Источники:\n"
        for i, source in enumerate(result['sources'], 1):
            answer_text += f"{i}. {source}\n"

        # Telegram limit = 4096 символов
        if len(answer_text) > 4000:
            answer_text = answer_text[:3990] + "…"

        await status_message.edit_text(answer_text)
    except Exception as e:
        logger.exception("Ошибка при обработке запроса")
        await status_message.edit_text(
            f"❌ Произошла ошибка при обработке запроса: {str(e)[:300]}"
        )


async def main():
    if TELEGRAM_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        logger.error("Установите TELEGRAM_TOKEN в переменных окружения")
        return

    await bot.delete_webhook(drop_pending_updates=True)

    # Прогреваем LLM: загружаем модель в RAM Ollama, чтобы первый
    # пользовательский запрос не упёрся в таймаут.
    warmup = getattr(rag.llm, "warmup", None)
    if callable(warmup):
        logger.info("Прогрев LLM (%s)...", rag.llm.name)
        await asyncio.to_thread(warmup)
        logger.info("Прогрев LLM завершён")

    logger.info("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
