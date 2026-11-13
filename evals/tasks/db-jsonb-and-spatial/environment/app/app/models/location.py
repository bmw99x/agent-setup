from uuid import UUID, uuid4

from geoalchemy2 import Geometry
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    label: Mapped[str] = mapped_column(String(255))
    # Indexes are declared explicitly in __table_args__, never implicitly by geoalchemy2.
    geom = mapped_column(Geometry("POINT", srid=4326, spatial_index=False))
