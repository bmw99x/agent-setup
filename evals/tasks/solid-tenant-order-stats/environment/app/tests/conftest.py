from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app import tenancy
from app.db import Base
from app.main import create_app
from app.orders.models import Order


@pytest.fixture
def tenant_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(tenancy, "TENANT_DATA_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def seed_orders(tenant_dir):
    def seed(tenant: str, *orders: tuple[str, int]) -> None:
        engine = create_engine(f"sqlite:///{tenant_dir / f'{tenant}.db'}")
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            session.add_all(
                Order(customer="c", status=status, total_cents=total, placed_at=datetime(2026, 1, day + 1))
                for day, (status, total) in enumerate(orders)
            )
            session.commit()
        engine.dispose()

    return seed


@pytest.fixture
def client():
    return TestClient(create_app())
