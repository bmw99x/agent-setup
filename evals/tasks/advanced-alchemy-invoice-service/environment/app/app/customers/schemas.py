from pydantic import BaseModel


class CustomerCreate(BaseModel):
    name: str
    email: str


class CustomerUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
