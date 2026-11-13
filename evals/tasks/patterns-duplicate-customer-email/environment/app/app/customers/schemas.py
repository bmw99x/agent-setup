from pydantic import BaseModel, ConfigDict


class CustomerRegistration(BaseModel):
    name: str
    email: str


class CustomerDatum(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
