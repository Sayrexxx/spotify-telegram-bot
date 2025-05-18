from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from main_handlers import spotify


async def play_command_handler(message: Message, command: CommandObject):
    """
    Handler for /play command.
    Fetches a track by its name or ID from Spotify and sends a 30-second preview to the user.
    """
    if not command.args:
        await message.reply(
            "Пожалуйста, укажите название трека, ID трека или эпизода. Пример: /play Imagine Dragons"
        )
        return

    query = command.args.strip()
    try:
        results = spotify.search(query, search_type="track", limit=1)
        tracks = results.get("tracks", {}).get("items", [])
        episodes = results.get("episodes", {}).get("items", [])
        print(results)
        if not tracks and not episodes:
            await message.reply("Ничего не найдено. Попробуйте другой запрос.")
            return

        if tracks:
            track = tracks[0]
            track_name = track.get("name", "Unknown Track")
            artists = ", ".join(artist["name"] for artist in track.get("artists", []))
            preview_url = track.get("preview_url")

            if not preview_url:
                await message.reply(
                    f"К сожалению, для трека '{track_name}' ({artists}) нет доступного предпрослушивания."
                )
                return

            audio_data = await spotify.download_preview(preview_url)

            await message.answer_audio(
                audio=audio_data,
                title=track_name,
                performer=artists,
                caption=f"🎵 {track_name}\n👤 {artists}",
            )
            return

        if episodes:
            episode = episodes[0]
            print(episode)
            episode_name = episode.get("name", "Unknown Episode")
            preview_url = episode.get("audio_preview_url")

            if not preview_url:
                await message.reply(
                    f"К сожалению, для эпизода '{episode_name}' нет доступного предпрослушивания."
                )
                return

            audio_data = await spotify.download_preview(preview_url)

            await message.answer_audio(
                audio=audio_data,
                title=episode_name,
                caption=f"🎧 {episode_name}\nПредпрослушивание эпизода.",
            )
            return
    except Exception as e:
        await message.reply(f"Произошла ошибка: {e}")


def register_playback_handlers(dp):
    dp.message.register(play_command_handler, Command("play"))
