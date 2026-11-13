import dataclasses
import inspect
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import BaseModel, ValidationError

sys.path.insert(0, "/app")
from app.validation.schemas import AppBaseModel  # noqa: E402

SOURCE = Path("/app/app/products/schemas.py")


@pytest.fixture(scope="module")
def module():
    import importlib

    return importlib.import_module("app.products.schemas")


def _classes(module):
    return {n: c for n, c in inspect.getmembers(module, inspect.isclass) if c.__module__ == module.__name__}


def _one(module, predicate, label):
    found = [c for n, c in _classes(module).items() if predicate(n)]
    assert len(found) == 1, f"expected exactly one {label} schema, found {[c.__name__ for c in found]}"
    return found[0]


def read_schema(m):
    return _one(m, lambda n: n.endswith("Datum") and "Upsert" not in n, "read (…Datum)")


def write_schema(m):
    return _one(m, lambda n: n.endswith(("UpsertDatum", "Upsert")) and "Many" not in n, "write (…Upsert/…UpsertDatum)")


def bulk_schema(m):
    return _one(m, lambda n: n.endswith("UpsertMany"), "bulk (…UpsertMany)")


def test_read_schema_named_datum_and_uses_project_base(module):
    cls = read_schema(module)
    assert issubclass(cls, AppBaseModel)
    assert BaseModel not in cls.__bases__


def test_write_schema_named_upsert_and_uses_project_base(module):
    cls = write_schema(module)
    assert issubclass(cls, AppBaseModel)
    assert BaseModel not in cls.__bases__
    assert "id" not in cls.model_fields


def test_bulk_schema_is_dataclass_with_data_list(module):
    cls = bulk_schema(module)
    assert dataclasses.is_dataclass(cls)
    assert not issubclass(cls, BaseModel)
    assert "data" in {f.name for f in dataclasses.fields(cls)}


def test_read_schema_from_orm_dumps_camel_case(module):
    cls = read_schema(module)
    now = datetime(2026, 1, 1)
    orm = SimpleNamespace(id=uuid4(), name="Kettle", sku="K-1", price=Decimal("9.99"), description=None,
                          created_at=now, updated_at=now)
    dumped = cls.model_validate(orm).model_dump(by_alias=True, mode="json")
    assert "createdAt" in dumped and "updatedAt" in dumped
    assert "created_at" not in dumped


def test_write_schema_constraints(module):
    cls = write_schema(module)
    ok = {"name": "Kettle", "sku": "K-1", "price": "9.99"}
    cls.model_validate(ok)
    with pytest.raises(ValidationError):
        cls.model_validate({**ok, "price": "0"})
    with pytest.raises(ValidationError):
        cls.model_validate({**ok, "name": "x" * 256})


def test_optional_uses_pipe_none_not_optional():
    text = SOURCE.read_text()
    assert "Optional[" not in text
    assert "| None" in text
