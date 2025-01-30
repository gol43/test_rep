from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from app.redis import get_redis
from app.handlers import router, app
from app.keyboards import set_main_bot_commands

import uvicorn
import logging
import asyncio
import os

load_dotenv()

logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = Bot(TELEGRAM_TOKEN)
dp = Dispatcher()

async def start_bot():
    """Функция для запуска бота"""
    dp.include_router(router)
    await dp.start_polling(bot)

async def start_fastapi():
    """Функция для запуска FastAPI"""
    config = uvicorn.Config("main:app", host="127.0.0.1", port=8000, reload=True)
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    """Запуск бота и FastAPI одновременно"""
    await get_redis()
    await set_main_bot_commands(bot)
    
    # Запускаем оба процесса параллельно
    bot_task = asyncio.create_task(start_bot())
    api_task = asyncio.create_task(start_fastapi())

    await asyncio.gather(bot_task, api_task)  # Ожидаем завершения обеих задач

if __name__ == "__main__":
    try:
        asyncio.run(main())  # Запуск бота и API
    except KeyboardInterrupt:
        logging.info("Выход из программы...")
