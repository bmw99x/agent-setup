"""Every ORM model, imported so Alembic autogenerate sees the full metadata."""

from app.billing.models.invoice import Invoice
from app.customers.models import Customer

__all__ = ["Customer", "Invoice"]
