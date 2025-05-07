import logging
import asyncio
from aiogram import Bot, Dispatcher
from config.settings import TELEGRAM_BOT_TOKEN, DATABASE_URL
from src.telegram_bot.database import Database
from src.telegram_bot.handlers import register_handlers
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types.base import TelegramObject

logging.basicConfig(level=logging.INFO)

try:
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
except ValueError as e:
    logging.error(f"Ошибка в токене Telegram: {e}")
    exit(1)

dp = Dispatcher()


class DbMiddleware(BaseMiddleware):
    def __init__(self, db_pool):
        super().__init__()
        self.db_pool = db_pool

    async def __call__(self, handler, event: TelegramObject, data: dict):
        data["db_pool"] = self.db_pool
        return await handler(event, data)


async def main():
    """
    Entrypoint to the bot app.
    """
    db = Database(DATABASE_URL)
    await db.connect()
    dp.update.middleware(DbMiddleware(db))
    register_handlers(dp)

    try:
        logging.info("Бот запущен!")
        await dp.start_polling(bot)
    finally:
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
