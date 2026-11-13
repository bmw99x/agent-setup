#!/bin/bash
set -euo pipefail
cd /app
cat > app/billing/models/invoice_line.py <<'PY'
from uuid import UUID

from advanced_alchemy.base import BasicAttributes
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.orm.base import Base
from app.orm.mixins import CreatedAtMixIn, SoftDeleteMixIn, UpdatedAtMixIn, UUIDPKMixIn


class InvoiceLine(Base, BasicAttributes, UUIDPKMixIn, CreatedAtMixIn, SoftDeleteMixIn, UpdatedAtMixIn):
    __tablename__ = "invoice_lines"

    invoice_id: Mapped[UUID] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price_minor: Mapped[int] = mapped_column(nullable=False)

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="lines", lazy="raise")
PY
python3 - <<'PY'
from pathlib import Path
p = Path("app/billing/models/invoice.py")
s = p.read_text()
s = s.replace("from sqlalchemy.orm import Mapped, mapped_column", "from sqlalchemy.orm import Mapped, mapped_column, relationship")
s += '\n    lines: Mapped[list["InvoiceLine"]] = relationship("InvoiceLine", back_populates="invoice", lazy="raise")\n'
p.write_text(s)
p = Path("app/orm/all_models/__init__.py")
s = p.read_text()
s = s.replace("from app.billing.models.invoice import Invoice\n", "from app.billing.models.invoice import Invoice\nfrom app.billing.models.invoice_line import InvoiceLine\n")
s = s.replace('__all__ = ["Customer", "Invoice"]', '__all__ = ["Customer", "Invoice", "InvoiceLine"]')
p.write_text(s)
PY
