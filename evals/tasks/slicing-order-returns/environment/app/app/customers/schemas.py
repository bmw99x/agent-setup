from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class CustomerDatum(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str
    phone: str | None


class CustomerUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
