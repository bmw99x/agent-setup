"""Process-wide database session manager."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager


class SessionManager:
    def __init__(self, url: str) -> None:
        self.url = url

    @asynccontextmanager
    async def session(self) -> AsyncIterator["Session"]:
        raise ConnectionError(f"cannot reach database at {self.url}")
        yield  # pragma: no cover


class Session:
    async def get_order_row(self, order_id: str) -> dict | None: ...

    async def save_order_row(self, row: dict) -> None: ...


session_manager = SessionManager(os.environ.get("DATABASE_URL", "postgresql://db:5432/shop"))
