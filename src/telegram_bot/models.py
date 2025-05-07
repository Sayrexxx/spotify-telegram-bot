from src.telegram_bot.database import Database
from sqlalchemy import Column, Integer, String, DateTime
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
