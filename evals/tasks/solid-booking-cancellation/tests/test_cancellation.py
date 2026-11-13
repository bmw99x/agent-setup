import ast
import inspect
import re
import sys
import textwrap
import typing
from datetime import timedelta

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, "/app")
from app.bookings.models import Booking  # noqa: E402
from app.clock import utcnow  # noqa: E402
from app.db import Base, get_session  # noqa: E402
from app.main import create_app  # noqa: E402

CANCEL_PATH = re.compile(r"/bookings/\{\w+\}/cancel")
QUERY_CALLS = {"select", "text", "update", "delete", "insert"}
SESSION_METHODS = {"execute", "scalar", "scalars", "get", "add", "commit", "flush", "refresh", "query", "merge"}
POLICY_WINDOW_NAMES = {"timedelta", "total_seconds", "days", "hours", "seconds"}
BOOKING_STATES = {"cancelled", "confirmed", "canceled"}


@pytest.fixture
def factory():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
def client(factory):
    def session_override():
        with factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_session] = session_override
    return TestClient(app, raise_server_exceptions=False)


def _seed(factory, *, hours_ahead: float, status: str = "confirmed", price_cents: int = 24_001) -> int:
    with factory() as session:
        booking = Booking(guest_name="Ann", room_type="double", starts_at=utcnow() + timedelta(hours=hours_ahead),
                          nights=2, price_cents=price_cents, status=status)
        session.add(booking)
        session.commit()
        return booking.id


@pytest.fixture(scope="module")
def cancel_endpoint():
    routes = [r for r in create_app().routes
              if isinstance(r, APIRoute) and CANCEL_PATH.fullmatch(r.path) and "POST" in r.methods]
    assert len(routes) == 1, "expected one POST /bookings/{id}/cancel route"
    endpoint = routes[0].endpoint
    tree = ast.parse(textwrap.dedent(inspect.getsource(endpoint)))
    return endpoint, tree.body[0]


@pytest.mark.parametrize(("hours_ahead", "refund"), [(100, 24_001), (72.5, 24_001), (48, 12_000), (25, 12_000), (10, 0)])
def test_cancellation_refunds_by_notice_period(client, factory, hours_ahead, refund):
    booking_id = _seed(factory, hours_ahead=hours_ahead)

    response = client.post(f"/bookings/{booking_id}/cancel")

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "cancelled"
    assert response.json()["refund_cents"] == refund
    assert client.get(f"/bookings/{booking_id}").json()["status"] == "cancelled"


def test_cancellation_conflicts_and_missing_booking(client, factory):
    cancelled = _seed(factory, hours_ahead=100, status="cancelled")
    started = _seed(factory, hours_ahead=-2)

    assert client.post("/bookings/9999/cancel").status_code == 404
    assert client.post(f"/bookings/{cancelled}/cancel").json() == {"detail": "booking already cancelled"}
    assert client.post(f"/bookings/{cancelled}/cancel").status_code == 409
    assert client.post(f"/bookings/{started}/cancel").json() == {"detail": "booking already started"}
    assert client.post(f"/bookings/{started}/cancel").status_code == 409


def test_cancel_route_holds_no_business_rules(cancel_endpoint):
    _, function = cancel_endpoint
    for node in ast.walk(function):
        if isinstance(node, ast.Compare):
            assert not any(isinstance(op, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)) for op in node.ops), (
                f"line {node.lineno}: ordering comparison (a policy rule) in the route"
            )
        if isinstance(node, ast.BinOp):
            assert not isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod)), (
                f"line {node.lineno}: arithmetic in the route"
            )
        if isinstance(node, (ast.Name, ast.Attribute)):
            name = node.id if isinstance(node, ast.Name) else node.attr
            assert name not in POLICY_WINDOW_NAMES, f"line {node.lineno}: route measures the notice period ({name})"
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            assert node.value not in BOOKING_STATES, f"line {node.lineno}: route decides booking state ({node.value!r})"
        if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            assert not any(isinstance(t, ast.Attribute) for t in targets), (
                f"line {node.lineno}: route mutates domain state"
            )


def test_cancel_route_runs_no_sql(cancel_endpoint):
    endpoint, function = cancel_endpoint
    hints = typing.get_type_hints(endpoint)
    session_params = {name for name, hint in hints.items() if isinstance(hint, type) and issubclass(hint, Session)}
    session_params |= {name for name in inspect.signature(endpoint).parameters if "session" in name or name == "db"}
    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name):
            assert func.id not in QUERY_CALLS, f"line {node.lineno}: route builds SQL ({func.id})"
        if isinstance(func, ast.Attribute):
            assert func.attr not in QUERY_CALLS, f"line {node.lineno}: route builds SQL ({func.attr})"
            receiver = func.value.id if isinstance(func.value, ast.Name) else None
            assert not (receiver in session_params and func.attr in SESSION_METHODS), (
                f"line {node.lineno}: route uses the session directly ({receiver}.{func.attr})"
            )
