import re
import sys

from sqlalchemy import Index, UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex

sys.path.insert(0, "/app")
from app.models import Customer  # noqa: E402

TABLE = Customer.__table__
COLS = {"tenant_id", "email"}


def _unique_index():
    found = [i for i in TABLE.indexes if i.unique and {c.name for c in i.columns} == COLS]
    assert len(found) == 1, f"expected one unique index on {COLS}, got {[i.name for i in TABLE.indexes]}"
    return found[0]


def test_enforced_with_unique_index_not_plain_constraint():
    plain = [c for c in TABLE.constraints if isinstance(c, UniqueConstraint) and {col.name for col in c.columns} == COLS]
    assert not plain, "a plain UNIQUE constraint blocks re-creating a soft-deleted customer"
    _unique_index()


def test_unique_ignores_soft_deleted_rows():
    ddl = str(CreateIndex(_unique_index()).compile(dialect=postgresql.dialect()))
    assert re.search(r"WHERE\s+\(?\s*deleted_at IS NULL", ddl), ddl


def test_index_name_follows_convention():
    name = _unique_index().name
    assert re.fullmatch(r"(uq|ix)_customers_(tenant_id_email|email_tenant_id)(_partial)?", name), name


def test_declared_in_table_args():
    assert any(isinstance(a, Index) for a in Customer.__table_args__ if not isinstance(a, dict))
