from uuid import UUID

from advanced_alchemy.extensions.fastapi import service

from app.imports.models import ImportJob, ImportJobStatus
from app.imports.repository import ImportJobRepository


class ImportJobService(service.SQLAlchemyAsyncRepositoryService[ImportJob, ImportJobRepository]):
    repository_type = ImportJobRepository

    async def mark_running(self, job_id: UUID) -> ImportJob:
        return await self.update({"status": ImportJobStatus.RUNNING}, item_id=job_id, auto_commit=True)

    async def mark_succeeded(self, job_id: UUID) -> ImportJob:
        return await self.update({"status": ImportJobStatus.SUCCEEDED}, item_id=job_id, auto_commit=True)

    async def mark_failed(self, job_id: UUID) -> ImportJob:
        return await self.update({"status": ImportJobStatus.FAILED}, item_id=job_id, auto_commit=True)
