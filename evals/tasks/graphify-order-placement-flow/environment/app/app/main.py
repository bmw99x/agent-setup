"""Application factory."""

from app.api.routes import build_router
from app.db import connect
from app.events import wiring


def create_app(db_path=":memory:"):
    conn = connect(db_path)
    wiring.load_subscribers()
    return build_router(conn)
