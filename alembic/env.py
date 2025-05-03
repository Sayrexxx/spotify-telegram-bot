import os
import sys
from logging.config import fileConfig
from alembic import context  # type: ignore
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.future import Engine
from src.telegram_bot.models import Base
from dotenv import load_dotenv

load_dotenv()

target_metadata = Base.metadata


sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), "..")))

config = context.config
fileConfig(config.config_file_name)


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    context.configure(
        url=os.getenv("DATABASE_URL"),
        literal_binds=True,
        target_metadata=target_metadata,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Engine):
    context.configure(
        connection=connection,
        compare_type=True,
        target_metadata=target_metadata,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    """Run migrations in 'online' mode."""
    connectable = create_async_engine(os.getenv("DATABASE_URL"))

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    import asyncio

    asyncio.run(run_async_migrations())
