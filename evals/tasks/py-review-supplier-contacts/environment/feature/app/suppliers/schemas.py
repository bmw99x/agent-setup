from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AppModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SupplierDatum(AppModel):
    id: UUID
    code: str
    name: str
    country_code: str


class SupplierContactDatum(AppModel):
    id: UUID
    name: str
    email: str | None
    is_primary: bool


class SupplierContactUpsert(AppModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr | None = None
    is_primary: bool = False


def normalise_code(raw: str) -> str:
    """Supplier codes are stored upper-case without surrounding whitespace."""
    return raw.strip().upper()


def normalise_email(raw: str | None) -> str | None:
    """Contact emails compare case-insensitively, so store them lower-case."""
    return raw.strip().lower() if raw else None
