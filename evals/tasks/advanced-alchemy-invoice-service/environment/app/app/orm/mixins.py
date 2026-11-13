"""Shared column mixins and soft-delete behaviour for repositories and services."""

from datetime import UTC, datetime
from typing import Any, Generic, TypeVar
from uuid import UUID, uuid4

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

ModelT = TypeVar("ModelT")
RepositoryT = TypeVar("RepositoryT", bound=SQLAlchemyAsyncRepository[Any])


def _utcnow() -> datetime:
    return datetime.now(UTC)


class UUIDPKMixIn:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)


class CreatedAtMixIn:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)


class UpdatedAtMixIn:
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )


class SoftDeleteMixIn:
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)


class SoftDeleteRepositoryMixIn:
    """Scopes the repository's base statement to rows where deleted_at IS NULL."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.statement = self.statement.where(self.model_type.deleted_at.is_(None))  # type: ignore[attr-defined]


class SoftDeleteServiceMixIn(Generic[ModelT, RepositoryT]):
    """Turns service.delete(id) into setting deleted_at instead of removing the row."""

    async def delete(self, item_id: Any, *, auto_commit: bool | None = None, **kwargs: Any) -> ModelT:
        instance = await self.get(item_id)  # type: ignore[attr-defined]
        instance.deleted_at = _utcnow()
        session = self.repository.session  # type: ignore[attr-defined]
        await session.flush()
        if auto_commit if auto_commit is not None else self.repository.auto_commit:  # type: ignore[attr-defined]
            await session.commit()
        return instance
