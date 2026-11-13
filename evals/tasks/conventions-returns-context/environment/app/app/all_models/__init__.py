"""Every ORM model, imported so `Base.metadata` knows all tables."""

from app.orders.models import Order

__all__ = ["Order"]
