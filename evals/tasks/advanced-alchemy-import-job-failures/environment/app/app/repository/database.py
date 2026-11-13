"""Legacy hand-rolled repository base. Kept for existing contexts."""

from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ModelT = TypeVar("ModelT")
CreateSchemaT = TypeVar("CreateSchemaT", bound=BaseModel)
UpdateSchemaT = TypeVar("UpdateSchemaT", bound=BaseModel)


class SQLAlchemyAsyncSessionRepository(Generic[ModelT, CreateSchemaT, UpdateSchemaT]):
    def __init__(self, model: type[ModelT], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get(self, id: UUID) -> ModelT | None:
        return await self.session.get(self.model, id)

    async def list(self, **filters: Any) -> list[ModelT]:
        stmt = select(self.model).filter_by(**filters)
        return list(await self.session.scalars(stmt))

    async def create(self, data: CreateSchemaT) -> ModelT:
        instance = self.model(**data.model_dump())
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update(self, id: UUID, data: UpdateSchemaT) -> ModelT | None:
        instance = await self.get(id)
        if instance is None:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(instance, key, value)
        await self.session.flush()
        return instance

    async def delete(self, id: UUID) -> None:
        instance = await self.get(id)
        if instance is not None:
            await self.session.delete(instance)
            await self.session.flush()
