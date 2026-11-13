import ast
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

sys.path.insert(0, "/app")

from app.customers.models import Customer  # noqa: E402
from app.customers.repository import CustomerRepository  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402

CUSTOMERS = Path("/app/app/customers")
DRIVER_ERROR_NAMES = {"IntegrityError", "UniqueViolation", "DBAPIError", "SQLAlchemyError", "OperationalError"}


def _email() -> str:
    return f"{uuid4().hex}@example.com"


def _driver_error_references(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and (node.module.startswith("sqlalchemy.exc") or node.module.startswith("psycopg") or node.module == "sqlite3"):
            found.add(node.module)
        if isinstance(node, ast.Name) and node.id in DRIVER_ERROR_NAMES:
            found.add(node.id)
        if isinstance(node, ast.Attribute) and node.attr in DRIVER_ERROR_NAMES:
            found.add(node.attr)
    return found


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


@pytest.fixture
def conflict():
    """The exception the repository raises when an email is registered twice."""
    Base.metadata.create_all(engine)
    email = _email()
    with SessionLocal() as session:
        repository = CustomerRepository(session)
        repository.add(Customer(name="First", email=email))
        if hasattr(repository, "commit"):
            repository.commit()
        with pytest.raises(Exception) as raised:
            repository.add(Customer(name="Second", email=email))
            if hasattr(repository, "commit"):
                repository.commit()
            session.flush()
    return raised.value


def test_duplicate_email_returns_409(client):
    email = _email()
    assert client.post("/customers", json={"name": "Ada", "email": email}).status_code == 201
    duplicate = client.post("/customers", json={"name": "Ada L", "email": email})
    assert duplicate.status_code == 409
    assert "email" in duplicate.text.lower()


def test_registration_still_works_after_a_conflict(client):
    email = _email()
    client.post("/customers", json={"name": "Ada", "email": email})
    client.post("/customers", json={"name": "Ada", "email": email})
    assert client.post("/customers", json={"name": "Grace", "email": _email()}).status_code == 201


def test_repository_translates_database_error_to_domain_error(conflict):
    assert not isinstance(conflict, SQLAlchemyError), f"repository leaked {type(conflict).__name__}"


def test_domain_error_lives_in_an_exceptions_module(conflict):
    module = type(conflict).__module__
    assert module.split(".")[-1] == "exceptions", f"{type(conflict).__name__} defined in {module}"


def test_routes_see_domain_errors_only():
    assert not _driver_error_references(CUSTOMERS / "routes.py")


def test_service_does_not_handle_driver_errors():
    assert not _driver_error_references(CUSTOMERS / "service.py")
