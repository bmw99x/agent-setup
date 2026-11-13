from pydantic import BaseModel, ConfigDict, Field


class MemberRegistration(BaseModel):
    email: str = Field(..., min_length=3, max_length=320, pattern=r"^[^@\s]+@[^@\s]+$")
    name: str = Field(..., min_length=1, max_length=120)


class MemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
