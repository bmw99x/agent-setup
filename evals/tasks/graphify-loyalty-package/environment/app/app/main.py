"""Application factory."""

from app.api.routes import build_router
from app.db import connect
from app.events.discovery import autodiscover


def create_app(db_path=":memory:"):
    conn = connect(db_path)
    autodiscover()
    return build_router(conn)
