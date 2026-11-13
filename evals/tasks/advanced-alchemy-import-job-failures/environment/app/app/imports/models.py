from enum import StrEnum

from advanced_alchemy.base import BasicAttributes
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.orm.base import Base
from app.orm.mixins import CreatedAtMixIn, UpdatedAtMixIn, UUIDPKMixIn


class ImportJobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ImportJob(Base, BasicAttributes, UUIDPKMixIn, CreatedAtMixIn, UpdatedAtMixIn):
    __tablename__ = "import_jobs"

    source_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=ImportJobStatus.PENDING)
