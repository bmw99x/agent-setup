# Alembic environment (trimmed). Autogenerate compares the DB against this metadata.
from app.orm import all_models  # noqa: F401
from app.orm.base import Base

target_metadata = Base.metadata
