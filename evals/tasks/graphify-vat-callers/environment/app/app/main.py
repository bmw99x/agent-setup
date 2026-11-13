"""Application factory."""

from app.api.routes import build_router
from app.db import connect


def create_app(db_path=":memory:"):
    return build_router(connect(db_path))
