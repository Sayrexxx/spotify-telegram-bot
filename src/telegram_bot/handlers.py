from aiogram.filters import Command
from aiogram.types import Message
from src.telegram_bot.models import save_user, is_user_authenticated


async def start_command_handler(message: Message, db_pool):
    """
    Handler for /start command.
    """
    telegram_id = message.from_user.id
    username = message.from_user.username

    await save_user(db_pool, telegram_id, username)
    await db_pool.log_all_users()
    welcome_text = (
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Вот что я умею:\n"
        "- Находить и включать музыку\n"
        "- Лайкать понравившиеся треки и создавать плейлисты\n\n"
        "Начните с ввода команды /help, чтобы узнать больше."
    )
    await message.answer(welcome_text)


async def help_command_handler(message: Message):
    """
    Handler for /help command.
    """
    help_text = (
        "📖 <b>Доступные команды:</b>\n"
        "- /start: Начать работу с ботом\n"
        "- /help: Показать это сообщение\n"
        "- /auth: Проверка регистрации\n\n"
    )
    await message.answer(help_text, parse_mode="HTML")


async def auth_command_handler(message: Message, db_pool):
    """
    Handler for /auth command. Checks and returns message if user is authenticated.
    """
    telegram_id = message.from_user.id
    authenticated = await is_user_authenticated(db_pool, telegram_id)
    await db_pool.log_all_users()
    if authenticated:
        await message.answer("✅ Вы успешно аутентифицированы!")
    else:
        await message.answer(
            "❌ Вы не зарегистрированы. Пожалуйста, используйте команду /start для регистрации."
        )


def register_handlers(dp):
    dp.message.register(start_command_handler, Command("start"))
    dp.message.register(help_command_handler, Command("help"))
    dp.message.register(auth_command_handler, Command("auth"))
