from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession


async def get_session() -> AsyncSession:  # pragma: no cover - wired by the app factory
    raise NotImplementedError


SESSION = Depends(get_session)
