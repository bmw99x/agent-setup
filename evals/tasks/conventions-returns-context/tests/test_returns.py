import enum
import importlib
import inspect
import pkgutil
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.routing import APIRoute, APIRouter
from fastapi.testclient import TestClient

sys.path.insert(0, "/app")
from app.auth.dependencies import current_user, require_staff  # noqa: E402

AUTH = {require_staff, current_user}
STAFF = {"Authorization": "Bearer staff-token"}
CUSTOMER = {"Authorization": "Bearer customer-token"}
RETURN_STATUSES = {"requested", "approved", "rejected"}


@pytest.fixture(scope="module")
def app():
    return importlib.import_module("app.main").app


@pytest.fixture(scope="module")
def client(app):
    return TestClient(app)


@pytest.fixture(scope="module")
def order_id(client):
    res = client.post("/orders", json={"customer_email": "a@example.com", "total": "40.00"}, headers=STAFF)
    assert res.status_code == 201, res.text
    return res.json()["id"]


def _returns_routes(app):
    routes = [r for r in app.routes if isinstance(r, APIRoute) and r.path.startswith("/returns")]
    assert routes, "no /returns routes are mounted on the app"
    return routes


def _app_modules():
    import app as root

    mods = []
    for info in pkgutil.walk_packages(root.__path__, "app."):
        try:
            mods.append(importlib.import_module(info.name))
        except Exception:  # noqa: BLE001
            continue
    return mods


def _owning_router(endpoint):
    module = sys.modules[endpoint.__module__]
    for value in vars(module).values():
        if isinstance(value, APIRouter):
            for route in value.routes:
                if isinstance(route, APIRoute) and route.endpoint is endpoint:
                    return value, route
    return None, None


def test_return_lifecycle(client, order_id):
    created = client.post("/returns", json={"order_id": order_id, "reason": "Too small"}, headers=STAFF)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["status"] == "requested" and body["order_id"] == order_id
    rid = body["id"]
    assert client.get(f"/returns/{rid}", headers=STAFF).json()["reason"] == "Too small"
    assert client.post(f"/returns/{rid}/approve", headers=STAFF).status_code in (200, 201)
    assert client.get(f"/returns/{rid}", headers=STAFF).json()["status"] == "approved"
    assert client.post(f"/returns/{rid}/reject", headers=STAFF).status_code == 409
    assert client.post("/returns", json={"order_id": 99999, "reason": "x"}, headers=STAFF).status_code == 404
    assert client.get("/returns/99999", headers=STAFF).status_code == 404


def test_returns_endpoints_require_staff(client, order_id):
    assert client.post("/returns", json={"order_id": order_id, "reason": "x"}).status_code == 401
    assert client.post("/returns", json={"order_id": order_id, "reason": "x"}, headers=CUSTOMER).status_code == 403
    assert client.get("/returns/1", headers=CUSTOMER).status_code == 403


def test_auth_dependency_declared_on_router_not_handlers(app):
    # A handler may still take the user as a parameter to read it; what matters is
    # that the auth gate sits on the router, not repeated per handler.
    for app_route in _returns_routes(app):
        assert any(d.dependency in AUTH for d in app_route.dependencies), (
            f"{app_route.path}: the project's auth dependency is not attached to the router"
        )
        router, route = _owning_router(app_route.endpoint)
        if router is not None:
            per_route = [d for d in route.dependencies if d not in router.dependencies]
            assert not any(d.dependency in AUTH for d in per_route), (
                f"{app_route.path}: auth wired per handler via dependencies=[...]"
            )


def test_no_hand_rolled_token_check():
    for path in Path("/app/app").rglob("*.py"):
        rel = path.relative_to("/app/app").as_posix()
        if rel.startswith(("auth/", "orders/")) or "return" not in rel.lower():
            continue
        src = path.read_text()
        for needle in ("Bearer", "decode_token", "HTTPBearer", "Authorization", "authorization"):
            assert needle not in src, f"{rel} handles tokens itself ({needle!r})"


def test_return_status_enum_lives_in_enums_module_not_models():
    found = []
    for module in _app_modules():
        for obj in vars(module).values():
            if (
                inspect.isclass(obj)
                and issubclass(obj, enum.Enum)
                and obj.__module__ == module.__name__
                and RETURN_STATUSES <= {str(m.value).lower() for m in obj}
            ):
                found.append(obj)
    for cls in found:
        assert cls.__module__.split(".")[-1] == "enums", f"{cls.__name__} defined in {cls.__module__}, not an enums module"
    for module in _app_modules():
        if module.__name__.endswith(".models") and "return" in module.__name__:
            enums = [n for n, o in vars(module).items()
                     if inspect.isclass(o) and issubclass(o, enum.Enum) and o.__module__ == module.__name__]
            assert not enums, f"{module.__name__} defines enums {enums}"


def test_returns_router_registered_in_central_router():
    from app.api.router import api_router

    paths = {r.path for r in api_router.routes if isinstance(r, APIRoute)}
    assert any(p.startswith("/returns") for p in paths), "returns router not included in app/api/router.py"


def test_project_test_suite_passes():
    res = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "/app/tests"],
                         cwd="/app", capture_output=True, text=True)
    assert res.returncode == 0, res.stdout[-2000:] + res.stderr[-2000:]
