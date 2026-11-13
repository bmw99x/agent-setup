import asyncio

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

import app.customers.models  # noqa: F401
import app.orders.models  # noqa: F401
from app.config import settings
from app.db import Base

target_metadata = Base.metadata


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_async_engine(settings.database_url)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


asyncio.run(run_migrations_online())
