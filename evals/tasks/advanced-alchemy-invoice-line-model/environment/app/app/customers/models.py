from advanced_alchemy.base import BasicAttributes
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.orm.base import Base
from app.orm.mixins import CreatedAtMixIn, SoftDeleteMixIn, UpdatedAtMixIn, UUIDPKMixIn


class Customer(Base, BasicAttributes, UUIDPKMixIn, CreatedAtMixIn, SoftDeleteMixIn, UpdatedAtMixIn):
    __tablename__ = "customers"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
