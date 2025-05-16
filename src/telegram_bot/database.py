import aiosqlite
import logging
from src.telegram_bot.sql_scripts import (
    CREATE_USERS_TABLE,
    CREATE_LIKED_TRACKS_TABLE,
    CREATE_PLAYLISTS_TABLE,
    CREATE_PLAYLIST_TRACKS_TABLE,
)
from urllib.parse import urlparse
from typing import Optional


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection: Optional[aiosqlite.Connection] = None

    async def connect(self):
        try:
            parsed_url = urlparse(self.db_path)
            self.db_path = parsed_url.path
            self.connection = await aiosqlite.connect(self.db_path)
            logging.info("Подключение к базе данных установлено.")
            await self._create_tables()
        except Exception as e:
            logging.error(f"Ошибка подключения к базе данных: {e}")
            raise

    async def _create_tables(self):
        if not self.connection:
            raise RuntimeError("Соединение с базой данных не установлено.")
        async with self.connection.cursor() as cursor:
            await cursor.execute(CREATE_USERS_TABLE)
            await cursor.execute(CREATE_LIKED_TRACKS_TABLE)
            await cursor.execute(CREATE_PLAYLISTS_TABLE)
            await cursor.execute(CREATE_PLAYLIST_TRACKS_TABLE)
            await self.connection.commit()
            logging.info("Таблицы в базе данных проверены и созданы.")

    async def close(self):
        if self.connection:
            await self.connection.close()
            logging.info("Соединение с базой данных закрыто.")

    async def execute(self, query: str, params: tuple = ()):
        if not self.connection:
            raise RuntimeError("Соединение с базой данных не установлено.")
        logging.info(f"Executing query: {query} with params: {params}")
        async with self.connection.cursor() as cursor:
            await cursor.execute(query, params)
            await self.connection.commit()

    async def fetchone(self, query: str, params: tuple = ()):
        if not self.connection:
            raise RuntimeError("Соединение с базой данных не установлено.")
        logging.info(f"Fetching one row with query: {query} and params: {params}")
        async with self.connection.cursor() as cursor:
            await cursor.execute(query, params)
            return await cursor.fetchone()

    async def fetchall(self, query: str, params: tuple = ()):
        if not self.connection:
            raise RuntimeError("Соединение с базой данных не установлено.")
        logging.info(f"Fetching all rows with query: {query} and params: {params}")
        async with self.connection.cursor() as cursor:
            await cursor.execute(query, params)
            return await cursor.fetchall()

    async def log_all_users(self):
        if not self.connection:
            raise RuntimeError("Соединение с базой данных не установлено.")
        query = "SELECT * FROM users;"
        logging.info("Fetching all users from the database...")
        async with self.connection.cursor() as cursor:
            await cursor.execute(query)
            rows = await cursor.fetchall()
            logging.info(f"All users in the database: {rows}")
