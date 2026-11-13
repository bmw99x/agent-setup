import asyncio
import re
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from advanced_alchemy.exceptions import NotFoundError
from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

sys.path.insert(0, "/app")
import app.orm.all_models  # noqa: E402,F401
from app.billing.models.invoice import Invoice  # noqa: E402
from app.billing.models.invoice_line import InvoiceLine  # noqa: E402
from app.customers.models import Customer  # noqa: E402
from app.orm.base import Base  # noqa: E402
from app.repository.database import SQLAlchemyAsyncSessionRepository  # noqa: E402

BILLING = Path("/app/app/billing")


def _service_cls():
    from app.billing.service import InvoiceService

    return InvoiceService


def _repository_cls():
    from app.billing.repository import InvoiceRepository

    return InvoiceRepository


def _run(scenario):
    """Run scenario(maker, ids, statements) against a seeded in-memory database."""

    async def main():
        engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
        statements: list[str] = []
        event.listen(engine.sync_engine, "before_cursor_execute", lambda *a: statements.append(a[2]))
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        maker = async_sessionmaker(engine, expire_on_commit=False)
        now = datetime.now(UTC)
        async with maker() as session:
            ada, bob = Customer(name="Ada", email="a@x.io"), Customer(name="Bob", email="b@x.io")
            session.add_all([ada, bob])
            await session.flush()
            ids = {
                "open": Invoice(customer_id=ada.id, number="1", issued_at=now - timedelta(days=2)),
                "open2": Invoice(customer_id=ada.id, number="2", issued_at=now - timedelta(days=1)),
                "paid": Invoice(customer_id=ada.id, number="3", issued_at=now, paid_at=now),
                "deleted": Invoice(customer_id=ada.id, number="4", issued_at=now, deleted_at=now),
                "other": Invoice(customer_id=bob.id, number="5", issued_at=now),
            }
            session.add_all(ids.values())
            await session.flush()
            for inv in ids.values():
                session.add_all(
                    [
                        InvoiceLine(invoice_id=inv.id, description="a", quantity=1, unit_price_minor=100),
                        InvoiceLine(invoice_id=inv.id, description="b", quantity=2, unit_price_minor=250),
                    ]
                )
            ids = {k: v.id for k, v in ids.items()} | {"ada": ada.id}
            await session.commit()
        statements.clear()
        try:
            await scenario(maker, ids, statements)
        finally:
            await engine.dispose()

    asyncio.run(main())


def test_repository_built_on_advanced_alchemy_not_legacy_base():
    repo = _repository_cls()
    assert issubclass(repo, SQLAlchemyAsyncRepository)
    assert not issubclass(repo, SQLAlchemyAsyncSessionRepository)
    assert repo.model_type is Invoice


def test_service_built_on_advanced_alchemy_service():
    from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

    service = _service_cls()
    assert issubclass(service, SQLAlchemyAsyncRepositoryService)
    assert service.repository_type is _repository_cls()


def test_builtin_reads_hide_soft_deleted_invoices():
    async def scenario(maker, ids, _):
        async with maker() as session:
            service = _service_cls()(session=session)
            listed = {i.id for i in await service.list()}
            assert ids["deleted"] not in listed and ids["open"] in listed
            with pytest.raises(NotFoundError):
                await service.get(ids["deleted"])

    _run(scenario)


def test_delete_is_soft():
    async def scenario(maker, ids, _):
        async with maker() as session:
            await _service_cls()(session=session).delete(ids["open"])
            await session.commit()
        async with maker() as session:
            row = await session.scalar(select(Invoice).where(Invoice.id == ids["open"]))
            assert row is not None, "invoice row was hard-deleted"
            assert row.deleted_at is not None

    _run(scenario)


def test_outstanding_listing_excludes_soft_deleted():
    async def scenario(maker, ids, _):
        async with maker() as session:
            result = await _service_cls()(session=session).list_outstanding_for_customer(ids["ada"])
        got = {i.id for i in result}
        assert ids["deleted"] not in got
        assert got == {ids["open"], ids["open2"]}

    _run(scenario)


def test_outstanding_listing_eager_loads_lines():
    async def scenario(maker, ids, _):
        async with maker() as session:
            result = list(await _service_cls()(session=session).list_outstanding_for_customer(ids["ada"]))
        assert result
        for inv in result:
            assert len(inv.lines) == 2

    _run(scenario)


def test_collection_loaded_with_selectin_not_join():
    async def scenario(maker, ids, statements):
        async with maker() as session:
            await _service_cls()(session=session).list_outstanding_for_customer(ids["ada"])
        joins = [s for s in statements if re.search(r"JOIN\s+invoice_lines", s, re.I)]
        assert not joins, joins

    _run(scenario)


def test_no_legacy_query_api():
    for path in BILLING.rglob("*.py"):
        assert not re.search(r"\.query\(", path.read_text()), path
