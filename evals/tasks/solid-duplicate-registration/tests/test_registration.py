import ast
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.exceptions import HTTPException

sys.path.insert(0, "/app")
from app.db import Base, get_session  # noqa: E402
from app.main import create_app  # noqa: E402

APP_ROOT = Path("/app/app")
DATABASE_ERROR_NAMES = {"IntegrityError", "DBAPIError", "SQLAlchemyError", "UniqueViolation", "OperationalError"}
DATABASE_ERROR_MODULES = ("sqlalchemy.exc", "psycopg", "psycopg2", "asyncpg", "sqlite3")


def _session_factory():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
def app():
    factory = _session_factory()

    def session_override():
        with factory() as session:
            yield session

    application = create_app()
    application.dependency_overrides[get_session] = session_override
    return application


def _http_modules():
    """Every module under app/ that defines routes or builds the FastAPI app."""
    modules = []
    for path in APP_ROOT.rglob("*.py"):
        text = path.read_text()
        if "APIRouter" in text or "FastAPI(" in text or "@router." in text or "@app." in text:
            modules.append((path, ast.parse(text)))
    return modules


def test_duplicate_registration_returns_409(app):
    client = TestClient(app, raise_server_exceptions=False)
    assert client.post("/members", json={"email": "ann@example.com", "name": "Ann"}).status_code == 201

    response = client.post("/members", json={"email": "ANN@example.com", "name": "Annie"})

    assert response.status_code == 409
    assert response.json() == {"detail": "email already registered"}
    assert client.post("/members", json={"email": "bo@example.com", "name": "Bo"}).status_code == 201


def test_service_reports_duplicate_email_as_domain_error():
    from app.members.repository import MemberRepository
    from app.members.service import MemberService

    with _session_factory()() as session:
        service = MemberService(MemberRepository(session))
        service.register("ann@example.com", "Ann")
        with pytest.raises(Exception) as caught:
            service.register("Ann@Example.com", "Annie")

    error = caught.value
    assert not isinstance(error, SQLAlchemyError), f"database error leaked out of the service: {error!r}"
    assert not isinstance(error, HTTPException), "service raised an HTTP error instead of a domain error"
    assert type(error).__module__.startswith("app."), f"expected an app-defined domain error, got {type(error)!r}"


def test_http_layer_registers_no_database_error_handlers(app):
    for exc_type in app.exception_handlers:
        assert not (isinstance(exc_type, type) and issubclass(exc_type, SQLAlchemyError)), (
            f"HTTP layer handles database error {exc_type.__name__}"
        )


def test_http_layer_does_not_reference_database_errors():
    for path, tree in _http_modules():
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith(DATABASE_ERROR_MODULES):
                imported = {alias.name for alias in node.names}
                assert not imported & DATABASE_ERROR_NAMES, f"{path} imports {imported & DATABASE_ERROR_NAMES}"
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith(("psycopg", "asyncpg", "sqlite3")), f"{path} imports {alias.name}"
            if isinstance(node, (ast.Name, ast.Attribute)):
                name = node.id if isinstance(node, ast.Name) else node.attr
                assert name not in DATABASE_ERROR_NAMES, f"{path}:{node.lineno} references {name}"


def test_http_layer_does_not_query_the_database():
    for path, tree in _http_modules():
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
            assert name not in {"select", "text", "execute", "scalar", "scalars", "query"}, (
                f"{path}:{node.lineno} runs SQL ({name}) in the HTTP layer"
            )
