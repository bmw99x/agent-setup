import ast
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

os.environ["TENANT_DATA_DIR"] = tempfile.mkdtemp()
sys.path.insert(0, "/app")
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app import tenancy  # noqa: E402
from app.db import Base  # noqa: E402
from app.main import create_app  # noqa: E402
from app.orders.models import Order  # noqa: E402

STATS_PACKAGE = Path("/app/app/stats")
TENANT_RESOLUTION_NAMES = {"resolve_tenant_engine", "current_tenant", "_engine_for", "TENANT_DATA_DIR", "TENANT_HEADER"}
QUERY_CALLS = {"select", "text", "execute", "scalar", "scalars", "query", "count", "sum"}


def _seed(directory: Path, tenant: str, *orders: tuple[str, int]) -> None:
    engine = create_engine(f"sqlite:///{directory / f'{tenant}.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all(
            Order(customer="c", status=status, total_cents=total, placed_at=datetime(2026, 1, day + 1))
            for day, (status, total) in enumerate(orders)
        )
        session.commit()
    engine.dispose()


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(tenancy, "TENANT_DATA_DIR", tmp_path)
    _seed(tmp_path, "acme", ("paid", 1000), ("paid", 2000), ("pending", 1200), ("cancelled", 999), ("cancelled", 1))
    _seed(tmp_path, "globex", ("shipped", 700))
    return TestClient(create_app(), raise_server_exceptions=False)


def _domain_modules():
    """Modules in app/stats that do not serve HTTP."""
    assert STATS_PACKAGE.joinpath("service.py").exists(), "app/stats/service.py missing"
    for path in sorted(STATS_PACKAGE.rglob("*.py")):
        text = path.read_text()
        if path.name == "routes.py" or "APIRouter" in text:
            continue
        yield path, ast.parse(text)


def test_order_stats_for_calling_tenant(client):
    acme = client.get("/stats/orders", headers={"X-Tenant": "acme"})
    globex = client.get("/stats/orders", headers={"X-Tenant": "globex"})

    assert acme.status_code == 200, acme.text
    assert acme.json() == {"total_orders": 5, "by_status": {"paid": 2, "pending": 1, "cancelled": 2},
                           "revenue_cents": 4200}
    assert globex.json() == {"total_orders": 1, "by_status": {"shipped": 1}, "revenue_cents": 700}


def test_order_stats_tenant_errors_match_orders(client):
    assert client.get("/stats/orders", headers={"X-Tenant": "nobody"}).status_code == 404
    assert client.get("/stats/orders").status_code == 400


def test_stats_service_does_not_resolve_tenant():
    for path, tree in _domain_modules():
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                names = {alias.name for alias in node.names}
                assert not names & TENANT_RESOLUTION_NAMES, f"{path} imports {names & TENANT_RESOLUTION_NAMES}"
            if isinstance(node, (ast.Name, ast.Attribute)):
                name = node.id if isinstance(node, ast.Name) else node.attr
                assert name not in TENANT_RESOLUTION_NAMES, f"{path}:{node.lineno} resolves the tenant ({name})"
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                assert node.value.lower() != "x-tenant", f"{path}:{node.lineno} reads the tenant header"


def test_stats_route_runs_no_sql():
    path = STATS_PACKAGE / "routes.py"
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
            assert name not in QUERY_CALLS, f"{path}:{node.lineno} queries or aggregates ({name}) in the route"
