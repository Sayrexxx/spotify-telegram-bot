from aiogram.filters import Command, CommandObject
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardMarkup
from src.telegram_bot.models import (
    save_user,
    is_user_authenticated,
    save_liked_track,
    get_liked_tracks,
)
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
        "- /auth: Проверка регистрации\n"
        "- /search тип запрос: Поиск трека, артиста или альбома (например, /search track Imagine Dragons)\n"
        "- /likes: Показать ваши лайкнутые треки\n"
        "- /create_playlist название: Создать новый плейлист\n"
        "- /rename_playlist старое_название новое_название: Переименовать существующий плейлист\n"
        "- /delete_playlist название: Удалить плейлист\n"
        "- /add_to_playlist название_плейлиста track_id: Добавить трек в плейлист\n"
        "- /remove_from_playlist название_плейлиста track_id: Удалить трек из плейлиста\n"
        "- /playlists: Показать все ваши плейлисты (каждый плейлист — отдельным сообщением с кнопкой для просмотра содержимого)\n\n"
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


async def search_command_handler(message: Message, command: CommandObject, db_pool):
    """
    Handler for /search command. Finds track, artist and album names in Spotify.
    Sends each track as a separate message with a "Like" button.
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

    for idx, item in enumerate(items, start=1):
        if search_type == "track":
            track_id = item.get("id", "Unknown ID")
            track_name = item.get("name", "Unknown Track")
            artists = ", ".join(artist["name"] for artist in item.get("artists", []))
            album_name = item.get("album", {}).get("name", "Unknown Album")

            response = (
                f"{idx}. **{track_name}**\n"
                f"   - Исполнитель(и): {artists}\n"
                f"   - Альбом: {album_name}\n"
            )

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=f"❤️ Лайк: {track_name}",
                            callback_data=f"like:{track_id}",
                        )
                    ]
                ]
            )

            await message.answer(response, reply_markup=keyboard, parse_mode="Markdown")
        elif search_type == "artist":
            name = item.get("name", "Unknown Artist")
            genres = ", ".join(item.get("genres", []))
            response = f"{idx}. **{name}**\n   - Жанры: {genres or 'Не указаны'}\n\n"
            await message.answer(response, parse_mode="Markdown")
        elif search_type == "album":
            name = item.get("name", "Unknown Album")
            artists = ", ".join(artist["name"] for artist in item.get("artists", []))
            release_date = item.get("release_date", "Unknown Date")
            response = (
                f"{idx}. **{name}**\n"
                f"   - Исполнитель(и): {artists}\n"
                f"   - Дата релиза: {release_date}\n"
            )
            await message.answer(response, parse_mode="Markdown")


async def like_track_callback_handler(callback_query: CallbackQuery, db_pool):
    """
    Handler for liking a track via inline button.
    """
    data = callback_query.data
    if not data.startswith("like:"):
        await callback_query.answer("Неверный формат действия.", show_alert=True)
        return

    _, track_id = data.split(":", 1)
    user_id = callback_query.from_user.id

    try:
        track = spotify.get_track(track_id)
        track_name = track.get("name", "Unknown Track")
        artists = ", ".join(artist["name"] for artist in track.get("artists", []))
        album_name = track.get("album", {}).get("name", "Unknown Album")

        await save_liked_track(
            db_pool, user_id, track_id, track_name, artists, album_name
        )
        await callback_query.answer(
            f"Трек '{track_name}' добавлен в ваши лайки!", show_alert=True
        )
    except Exception as e:
        await callback_query.answer(
            f"Ошибка при добавлении трека: {e}", show_alert=True
        )


async def likes_command_handler(message: Message, db_pool):
    """
    Handler for /likes command. Displays the user's liked tracks.
    """
    user_id = message.from_user.id
    liked_tracks = await get_liked_tracks(db_pool, user_id)

    if not liked_tracks:
        await message.reply(
            "У вас пока нет лайкнутых треков. Начните с команды /search и лайкните понравившиеся треки!"
        )
        return

    response = "Ваши лайкнутые треки:\n\n"
    for idx, track in enumerate(liked_tracks, start=1):
        response += f"{idx}. **{track['track_name']}**\n   - Исполнитель(и): {track['artist_name']}\n   - Альбом: {track['album_name']}\n\n"

    await message.reply(response, parse_mode="Markdown")


def register_main_handlers(dp):
    dp.message.register(start_command_handler, Command("start"))
    dp.message.register(help_command_handler, Command("help"))
    dp.message.register(auth_command_handler, Command("auth"))
    dp.message.register(search_command_handler, Command("search"))
    dp.message.register(likes_command_handler, Command("likes"))
    dp.callback_query.register(
        like_track_callback_handler, lambda call: call.data.startswith("like:")
    )
