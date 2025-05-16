from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from src.telegram_bot.models import (
    save_playlist,
    add_track_to_playlist,
    remove_track_from_playlist,
    get_user_playlists,
    get_full_playlist_tracks,
    get_playlist_name,
)
from aiogram.utils.keyboard import InlineKeyboardMarkup


async def create_playlist_handler(message: Message, db_pool):
    """
    Handler for /create_playlist command.
    """
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply(
            "Пожалуйста, укажите название плейлиста. Пример: /create_playlist Мой Плейлист"
        )
        return

    playlist_name = args[1]
    user_id = message.from_user.id

    try:
        await save_playlist(db_pool, user_id, playlist_name)
        await message.reply(f"✅ Плейлист '{playlist_name}' создан успешно!")
    except Exception as e:
        await message.reply(f"❌ Ошибка при создании плейлиста: {e}")


async def rename_playlist_handler(message: Message, db_pool):
    """
    Handler for /rename_playlist command.
    """
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.reply(
            "Пожалуйста, укажите старое и новое название. Пример: /rename_playlist Старое Новое"
        )
        return

    old_name, new_name = args[1], args[2]
    user_id = message.from_user.id

    query = """
    UPDATE playlists
    SET name = ?
    WHERE name = ? AND user_id = ?;
    """

    try:
        result = await db_pool.execute(query, (new_name, old_name, user_id))
        if result == "UPDATE 0":
            await message.reply("❌ Плейлист с таким названием не найден.")
        else:
            await message.reply(
                f"✅ Плейлист '{old_name}' переименован в '{new_name}'!"
            )
    except Exception as e:
        await message.reply(f"❌ Ошибка при переименовании плейлиста: {e}")


async def delete_playlist_handler(message: Message, db_pool):
    """
    Handler for /delete_playlist command.
    """
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply(
            "Пожалуйста, укажите название плейлиста для удаления. Пример: /delete_playlist Мой Плейлист"
        )
        return

    playlist_name = args[1]
    user_id = message.from_user.id

    query = """
    DELETE FROM playlists
    WHERE name = ? AND user_id = ?;
    """

    try:
        result = await db_pool.execute(query, (playlist_name, user_id))
        if result == "DELETE 0":
            await message.reply("❌ Плейлист с таким названием не найден.")
        else:
            await message.reply(f"✅ Плейлист '{playlist_name}' удалён!")
    except Exception as e:
        await message.reply(f"❌ Ошибка при удалении плейлиста: {e}")


async def add_to_playlist_handler(message: Message, db_pool):
    """
    Handler for /add_to_playlist command.
    """
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.reply(
            "Пожалуйста, укажите плейлист и id трека. Пример: /add_to_playlist МойПлейлист track_id"
        )
        return

    playlist_name, track_id = args[1], args[2]
    user_id = message.from_user.id

    query_playlist = """
    SELECT id FROM playlists WHERE name = ? AND user_id = ?;
    """

    try:
        playlist_id = await db_pool.fetchone(query_playlist, (playlist_name, user_id))
        if not playlist_id:
            await message.reply("❌ Плейлист с таким названием не найден.")
            return

        await add_track_to_playlist(db_pool, playlist_id[0], track_id)
        await message.reply(
            f"✅ Трек '{track_id}' добавлен в плейлист '{playlist_name}'!"
        )
    except Exception as e:
        await message.reply(f"❌ Ошибка при добавлении трека в плейлист: {e}")


async def remove_from_playlist_handler(message: Message, db_pool):
    """
    Handler for /remove_from_playlist command.
    """
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.reply(
            "Пожалуйста, укажите плейлист и id трека. Пример: /remove_from_playlist МойПлейлист track_id"
        )
        return

    playlist_name, track_id = args[1], args[2]
    user_id = message.from_user.id

    query_playlist = """
    SELECT id FROM playlists WHERE name = ? AND user_id = ?;
    """

    try:
        playlist_id = await db_pool.fetchone(query_playlist, (playlist_name, user_id))
        if not playlist_id:
            await message.reply("❌ Плейлист с таким названием не найден.")
            return

        await remove_track_from_playlist(db_pool, playlist_id[0], track_id)
        await message.reply(
            f"✅ Трек '{track_id}' удалён из плейлиста '{playlist_name}'!"
        )
    except Exception as e:
        await message.reply(f"❌ Ошибка при удалении трека из плейлиста: {e}")


async def view_playlists_handler(message: Message, db_pool):
    """
    Handler for /playlists command.
    Shows list of playlist in separated messages with button to show all playlist`s tracks.
    """
    user_id = message.from_user.id

    playlists = await get_user_playlists(db_pool, user_id)

    if not playlists:
        await message.reply(
            "У вас пока нет плейлистов. Создайте их через /create_playlist!"
        )
        return

    for pl in playlists:
        pl_id, pl_name = pl["id"], pl["name"]
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Просмотреть плейлист",
                        callback_data=f"show_playlist:{pl_id}",
                    )
                ]
            ]
        )
        await message.answer(
            f"🎵 <b>{pl_name}</b>", reply_markup=keyboard, parse_mode="HTML"
        )


async def show_playlist_callback_handler(callback_query: CallbackQuery, db_pool):
    data = callback_query.data
    if not data.startswith("show_playlist:"):
        await callback_query.answer("Неверный формат запроса.", show_alert=True)
        return

    playlist_id = int(data.split(":", 1)[1])
    pl_name = await get_playlist_name(db_pool, playlist_id)
    if not pl_name:
        pl_name = "Неизвестный плейлист"

    tracks = await get_full_playlist_tracks(db_pool, playlist_id)
    if not tracks:
        await callback_query.message.answer(
            f"Плейлист <b>{pl_name}</b> пуст.", parse_mode="HTML"
        )
    else:
        text = f"🎼 <b>{pl_name}</b>\nТреки:\n"
        for idx, track in enumerate(tracks, 1):
            text += (
                f"{idx}. {track['track_name']}\n"
                f"   - Исполнитель(и): {track['artist_name']}\n"
                f"   - Альбом: {track['album_name']}\n\n"
            )
        await callback_query.message.answer(text, parse_mode="HTML")
    await callback_query.answer()


def register_playlist_handlers(dp):
    dp.message.register(create_playlist_handler, Command("create_playlist"))
    dp.message.register(rename_playlist_handler, Command("rename_playlist"))
    dp.message.register(delete_playlist_handler, Command("delete_playlist"))
    dp.message.register(add_to_playlist_handler, Command("add_to_playlist"))
    dp.message.register(remove_from_playlist_handler, Command("remove_from_playlist"))
    dp.message.register(view_playlists_handler, Command("playlists"))
    dp.callback_query.register(
        show_playlist_callback_handler, lambda c: c.data.startswith("show_playlist:")
    )
