from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AppModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SupplierDatum(AppModel):
    id: UUID
    code: str
    name: str
    country_code: str


def normalise_code(raw: str) -> str:
    """Supplier codes are stored upper-case without surrounding whitespace."""
    return raw.strip().upper()
