import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from config.settings import TELEGRAM_BOT_TOKEN

logging.basicConfig(level=logging.INFO)

try:
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
except ValueError as e:
    logging.error(f"Ошибка в токене Telegram: {e}")
    exit(1)

dp = Dispatcher()


@dp.message(Command("start"))
async def start_command_handler(message: Message):
    """
    Handler for /start command.
    """
    welcome_text = (
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Вот что я умею:\n"
        "- Находить и включать музыку\n"
        "- Лайкать понравившиеся треки и создавать плейлисты\n\n"
        "Начните с ввода команды /help, чтобы узнать больше."
    )
    await message.answer(welcome_text)


@dp.message(Command("help"))
async def help_command_handler(message: Message):
    """
    Handler for /help command.
    """
    help_text = (
        "📖 <b>Доступные команды:</b>\n"
        "- /start: Начать работу с ботом\n"
        "- /help: Показать это сообщение\n\n"
    )
    await message.answer(help_text, parse_mode="HTML")


async def main():
    """
    Entrypoint to the bot app.
    """
    dp.message.register(start_command_handler, Command("start"))
    dp.message.register(help_command_handler, Command("help"))

    logging.info("Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
