import asyncio
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from advanced_alchemy.base import BasicAttributes
from sqlalchemy import select
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import configure_mappers
from sqlalchemy.pool import StaticPool

sys.path.insert(0, "/app")
from app.billing.models.invoice import Invoice  # noqa: E402
from app.orm.base import Base  # noqa: E402
from app.orm.mixins import CreatedAtMixIn, SoftDeleteMixIn, UpdatedAtMixIn, UUIDPKMixIn  # noqa: E402

for _path in Path("/app/app").rglob("*.py"):
    _mod = ".".join(_path.relative_to("/app").with_suffix("").parts)
    if _mod.endswith(".__init__"):
        _mod = _mod[: -len(".__init__")]
    if "migrations" not in _mod:
        __import__(_mod)
configure_mappers()


def _line_model():
    found = [
        m.class_
        for m in Base.registry.mappers
        if m.class_ is not Invoice and any(fk.column.table.name == "invoices" for fk in m.local_table.foreign_keys)
    ]
    assert len(found) == 1, f"expected one model with a foreign key to invoices, got {found}"
    return found[0]


def _relationships():
    line = _line_model()
    to_lines = [r for r in Invoice.__mapper__.relationships if r.mapper.class_ is line]
    to_invoice = [r for r in line.__mapper__.relationships if r.mapper.class_ is Invoice]
    assert to_lines and to_invoice, "need a relationship on both Invoice and the line model"
    return to_lines + to_invoice


def test_table_name_is_snake_case_plural():
    assert re.fullmatch(r"invoice_lines|invoice_line_items", _line_model().__tablename__)


def test_uses_shared_column_mixins():
    line = _line_model()
    for mixin in (UUIDPKMixIn, CreatedAtMixIn, UpdatedAtMixIn, SoftDeleteMixIn):
        assert issubclass(line, mixin), mixin.__name__


def test_inherits_basic_attributes():
    assert issubclass(_line_model(), BasicAttributes)


def test_columns_declared_with_mapped_annotations():
    src = Path(sys.modules[_line_model().__module__].__file__).read_text()
    assert not re.search(r"\bColumn\(", src), "legacy Column() used instead of Mapped[] + mapped_column()"


def test_relationships_use_back_populates_not_backref():
    for rel in _relationships():
        assert rel.backref is None, f"{rel} declared with backref"
        assert rel.back_populates, f"{rel} has no back_populates"


def test_relationships_raise_on_lazy_load():
    for rel in _relationships():
        assert rel.lazy == "raise", f"{rel} lazy={rel.lazy!r}"


def test_lazy_access_raises_at_runtime():
    line_cls = _line_model()
    to_lines = next(r for r in Invoice.__mapper__.relationships if r.mapper.class_ is line_cls)

    async def scenario():
        engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        maker = async_sessionmaker(engine, expire_on_commit=False)
        from app.customers.models import Customer

        async with maker() as session:
            customer = Customer(name="Ada", email="ada@example.com")
            session.add(customer)
            await session.flush()
            session.add(Invoice(customer_id=customer.id, number="INV-1", issued_at=datetime.now(UTC)))
            await session.commit()
        async with maker() as session:
            invoice = (await session.scalars(select(Invoice))).one()
            with pytest.raises(InvalidRequestError):
                getattr(invoice, to_lines.key)
        await engine.dispose()

    asyncio.run(scenario())


def test_registered_with_autogenerate_metadata(tmp_path):
    table = _line_model().__tablename__
    script = tmp_path / "check.py"
    script.write_text(
        "import sys\n"
        "sys.path.insert(0, '/app')\n"
        "import app.orm.all_models  # noqa: F401\n"
        "from app.orm.base import Base\n"
        f"assert {table!r} in Base.metadata.tables, sorted(Base.metadata.tables)\n"
    )
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, cwd="/")
    assert result.returncode == 0, result.stderr
