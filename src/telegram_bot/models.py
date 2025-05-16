from src.telegram_bot.database import Database
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import Any

Base: Any = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class LikedTrack(Base):
    __tablename__ = "liked_tracks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)  # Foreign key reference to User.id
    track_id = Column(String, nullable=False)
    track_name = Column(String, nullable=False)
    artist_name = Column(String, nullable=False)
    album_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)


class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(DateTime, default=datetime.now)


class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    playlist_id = Column(
        Integer, ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False
    )
    track_id = Column(String, nullable=False)
    added_at = Column(DateTime, default=datetime.now)


async def save_user(db: Database, telegram_id: int, username: str):
    """
    Сохраняет пользователя в базу данных.
    """
    existing_user = await db.fetchone(
        "SELECT id FROM users WHERE telegram_id = ?;", (telegram_id,)
    )
    if existing_user:
        print(f"User with telegram_id={telegram_id} already exists: {existing_user}")
        if existing_user[0] is None:  # Если id=NULL
            print(f"User with telegram_id={telegram_id} has NULL id. Fixing...")
            await db.execute("DELETE FROM users WHERE telegram_id = ?;", (telegram_id,))
            await db.execute(
                """
                INSERT INTO users (telegram_id, username, created_at)
                VALUES (?, ?, ?);
                """,
                (telegram_id, username, datetime.now()),
            )
    else:
        print(f"Saving user: telegram_id={telegram_id}, username={username}")
        await db.execute(
            """
            INSERT INTO users (telegram_id, username, created_at)
            VALUES (?, ?, ?);
            """,
            (telegram_id, username, datetime.now()),
        )
    all_users = await db.fetchall("SELECT * FROM users;")
    print(f"All users: {all_users}")


async def is_user_authenticated(db: Database, telegram_id: int) -> bool:
    """
    Проверяет, существует ли пользователь в базе данных.
    """
    result = await db.fetchone(
        """
        SELECT COUNT(*)
        FROM users
        WHERE telegram_id = ?;
        """,
        (telegram_id,),
    )
    return result[0] > 0


async def save_liked_track(
    db: Database,
    user_id: int,
    track_id: str,
    track_name: str,
    artist_name: str,
    album_name: str,
):
    """
    Сохраняет лайкнутый трек в базу данных.
    """
    existing_track = await db.fetchone(
        """
        SELECT id
        FROM liked_tracks
        WHERE user_id = ? AND track_id = ?;
        """,
        (user_id, track_id),
    )
    if existing_track:
        print(f"Track {track_id} already liked by user {user_id}")
        return

    print(f"Saving liked track: user_id={user_id}, track_id={track_id}")
    await db.execute(
        """
        INSERT INTO liked_tracks (user_id, track_id, track_name, artist_name, album_name)
        VALUES (?, ?, ?, ?, ?);
        """,
        (user_id, track_id, track_name, artist_name, album_name),
    )


async def get_liked_tracks(db: Database, user_id: int):
    """
    Получает все лайкнутые треки пользователя.
    """
    liked_tracks = await db.fetchall(
        """
        SELECT track_name, artist_name, album_name
        FROM liked_tracks
        WHERE user_id = ?;
        """,
        (user_id,),
    )
    return [
        {
            "track_name": track[0],
            "artist_name": track[1],
            "album_name": track[2],
        }
        for track in liked_tracks
    ]


async def save_playlist(db: Database, user_id: int, playlist_name: str):
    """
    Сохраняет плейлист в базу данных.
    """
    existing_playlist = await db.fetchone(
        """
        SELECT id
        FROM playlists
        WHERE user_id = ? AND name = ?;
        """,
        (user_id, playlist_name),
    )
    if existing_playlist:
        print(f"Playlist '{playlist_name}' already exists for user {user_id}")
        return

    print(f"Saving playlist: user_id={user_id}, playlist_name={playlist_name}")
    await db.execute(
        """
        INSERT INTO playlists (user_id, name, created_at)
        VALUES (?, ?, ?);
        """,
        (user_id, playlist_name, datetime.now()),
    )


async def add_track_to_playlist(db: Database, playlist_id: int, track_id: str):
    """
    Добавляет трек в указанный плейлист.
    """
    existing_track = await db.fetchone(
        """
        SELECT id
        FROM playlist_tracks
        WHERE playlist_id = ? AND track_id = ?;
        """,
        (playlist_id, track_id),
    )
    if existing_track:
        print(f"Track {track_id} already exists in playlist {playlist_id}")
        return

    print(f"Adding track {track_id} to playlist {playlist_id}")
    await db.execute(
        """
        INSERT INTO playlist_tracks (playlist_id, track_id, added_at)
        VALUES (?, ?, ?);
        """,
        (playlist_id, track_id, datetime.now()),
    )


async def remove_track_from_playlist(db: Database, playlist_id: int, track_id: str):
    """
    Удаляет трек из указанного плейлиста.
    """
    print(f"Removing track {track_id} from playlist {playlist_id}")
    await db.execute(
        """
        DELETE FROM playlist_tracks
        WHERE playlist_id = ? AND track_id = ?;
        """,
        (playlist_id, track_id),
    )


async def get_user_playlists(db: Database, user_id: int):
    """
    Получает все плейлисты пользователя.
    """
    rows = await db.fetchall(
        """
        SELECT id, name FROM playlists WHERE user_id = ? ORDER BY created_at DESC;
        """,
        (user_id,),
    )
    return [{"id": r[0], "name": r[1]} for r in rows]


async def get_playlist_tracks(db: Database, playlist_id: int):
    """
    Получает все треки для конкретного плейлиста.
    """
    rows = await db.fetchall(
        """
        SELECT track_id FROM playlist_tracks WHERE playlist_id = ?;
        """,
        (playlist_id,),
    )
    return [{"track_id": r[0]} for r in rows]


async def get_playlist_name(db: Database, playlist_id: int):
    """
    Получает название плейлиста по его id.
    """
    row = await db.fetchone(
        """
        SELECT name FROM playlists WHERE id = ?;
        """,
        (playlist_id,),
    )
    return row[0] if row else None


async def get_full_playlist_tracks(db: Database, playlist_id: int):
    """
    Получает полную информацию о треках плейлиста.
    """
    rows = await db.fetchall(
        """
        SELECT lt.track_name, lt.artist_name, lt.album_name
        FROM playlist_tracks pt
        JOIN liked_tracks lt ON pt.track_id = lt.track_id
        WHERE pt.playlist_id = ?;
        """,
        (playlist_id,),
    )
    return [{"track_name": r[0], "artist_name": r[1], "album_name": r[2]} for r in rows]
