from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from src.telegram_bot.models import save_user, is_user_authenticated
from src.spotify.client import SpotifyAPI

spotify = SpotifyAPI()


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
        "- /search <тип> <запрос>: Поиск трека, артиста или альбома (например, /search track Imagine Dragons)"
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


async def search_command_handler(message: Message, command: CommandObject):
    """
    Handler for /search command. Finds track, artist and album names in Spotify.
    """
    if not command.args:
        await message.reply(
            "Пожалуйста, укажите тип поиска (track, artist, album) и запрос. Пример: /search track Imagine Dragons"
        )
        return

    args = command.args.split(maxsplit=1)
    if len(args) < 2:
        await message.reply(
            "Пожалуйста, укажите тип поиска (track, artist, album) и запрос. Пример: /search track Imagine Dragons"
        )
        return

    search_type, query = args
    if search_type not in {"track", "artist", "album"}:
        await message.reply(
            "Неверный тип поиска. Используйте один из следующих: track, artist, album. Пример: /search track Imagine Dragons"
        )
        return

    try:
        results = spotify.search(query, search_type=search_type, limit=5)
    except Exception as e:
        await message.reply(f"Произошла ошибка при запросе к Spotify API: {e}")
        return

    items = results.get(f"{search_type}s", {}).get("items", [])
    if not items:
        await message.reply("Ничего не найдено. Попробуйте изменить запрос.")
        return

    response = f"Вот лучшие результаты поиска ({search_type}):\n\n"
    for idx, item in enumerate(items, start=1):
        if search_type == "track":
            name = item.get("name", "Unknown Track")
            artists = ", ".join(artist["name"] for artist in item.get("artists", []))
            album_name = item.get("album", {}).get("name", "Unknown Album")
            response += f"{idx}. **{name}**\n   - Исполнитель(и): {artists}\n   - Альбом: {album_name}\n\n"
        elif search_type == "artist":
            name = item.get("name", "Unknown Artist")
            genres = ", ".join(item.get("genres", []))
            response += f"{idx}. **{name}**\n   - Жанры: {genres or 'Не указаны'}\n\n"
        elif search_type == "album":
            name = item.get("name", "Unknown Album")
            artists = ", ".join(artist["name"] for artist in item.get("artists", []))
            release_date = item.get("release_date", "Unknown Date")
            response += f"{idx}. **{name}**\n   - Исполнитель(и): {artists}\n   - Дата релиза: {release_date}\n\n"

    await message.reply(response, parse_mode="Markdown")


def register_handlers(dp):
    dp.message.register(start_command_handler, Command("start"))
    dp.message.register(help_command_handler, Command("help"))
    dp.message.register(auth_command_handler, Command("auth"))
    dp.message.register(search_command_handler, Command("search"))
