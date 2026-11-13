#!/bin/bash
set -euo pipefail
cd /app
cat > app/billing/repository.py <<'PY'
from collections.abc import Sequence
from uuid import UUID

from advanced_alchemy.extensions.fastapi import repository
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.billing.models.invoice import Invoice
from app.orm.mixins import SoftDeleteRepositoryMixIn


class InvoiceRepository(SoftDeleteRepositoryMixIn, repository.SQLAlchemyAsyncRepository[Invoice]):
    model_type = Invoice

    async def list_outstanding_for_customer(self, customer_id: UUID) -> Sequence[Invoice]:
        stmt = (
            select(Invoice)
            .where(Invoice.customer_id == customer_id, Invoice.paid_at.is_(None), Invoice.deleted_at.is_(None))
            .options(selectinload(Invoice.lines))
            .order_by(Invoice.issued_at.desc())
        )
        return (await self.session.scalars(stmt)).all()
PY
cat > app/billing/service.py <<'PY'
from collections.abc import Sequence
from uuid import UUID

from advanced_alchemy.extensions.fastapi import service

from app.billing.models.invoice import Invoice
from app.billing.repository import InvoiceRepository
from app.orm.mixins import SoftDeleteServiceMixIn


class InvoiceService(
    SoftDeleteServiceMixIn[Invoice, InvoiceRepository],
    service.SQLAlchemyAsyncRepositoryService[Invoice, InvoiceRepository],
):
    repository_type = InvoiceRepository

    async def list_outstanding_for_customer(self, customer_id: UUID) -> Sequence[Invoice]:
        return await self.repository.list_outstanding_for_customer(customer_id)
PY
