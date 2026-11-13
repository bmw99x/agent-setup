#!/bin/bash
set -euo pipefail
cd /app
cat > app/imports/models.py <<'PY'
from enum import StrEnum
from uuid import UUID

from advanced_alchemy.base import BasicAttributes
from sqlalchemy import ForeignKey, String, Text, func, select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.orm.base import Base
from app.orm.mixins import CreatedAtMixIn, UpdatedAtMixIn, UUIDPKMixIn


class ImportJobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ImportJobError(Base, BasicAttributes, UUIDPKMixIn, CreatedAtMixIn):
    __tablename__ = "import_job_errors"

    import_job_id: Mapped[UUID] = mapped_column(ForeignKey("import_jobs.id", ondelete="CASCADE"), index=True)
    error: Mapped[str] = mapped_column(Text, nullable=False)


class ImportJob(Base, BasicAttributes, UUIDPKMixIn, CreatedAtMixIn, UpdatedAtMixIn):
    __tablename__ = "import_jobs"

    source_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=ImportJobStatus.PENDING)

    errors: Mapped[list[ImportJobError]] = relationship(
        ImportJobError, lazy="selectin", order_by=ImportJobError.created_at
    )

    @hybrid_property
    def attempts(self) -> int:
        return len(self.errors)

    @attempts.expression  # type: ignore[no-redef]
    @classmethod
    def attempts(cls) -> object:
        return (
            select(func.count(ImportJobError.id))
            .where(ImportJobError.import_job_id == cls.id)
            .correlate(cls)
            .scalar_subquery()
        )
PY
cat >> app/imports/service.py <<'PY'

    async def record_failure(self, job_id: UUID, message: str) -> ImportJob:
        self.repository.session.add(ImportJobError(import_job_id=job_id, error=message))
        return await self.update({"status": ImportJobStatus.FAILED}, item_id=job_id, auto_commit=True)
PY
sed -i 's/from app.imports.models import ImportJob, ImportJobStatus/from app.imports.models import ImportJob, ImportJobError, ImportJobStatus/' app/imports/service.py
