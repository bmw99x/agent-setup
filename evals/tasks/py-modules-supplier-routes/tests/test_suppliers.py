import ast
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import pytest

sys.path.insert(0, "/app")

APP = Path("/app")
PACKAGE = APP / "app"
BASE = Path("/opt/eval-base")


def _sources(root: Path) -> list[Path]:
    return [p for p in root.rglob("*.py") if ".git" not in p.parts]


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(), filename=str(path))


def _module_path(module: str) -> Path:
    return APP.joinpath(*module.split(".")).with_suffix(".py")


def _calls_gzip(func: ast.AST) -> bool:
    for node in ast.walk(func):
        if isinstance(node, ast.Call):
            target = node.func
            name = target.attr if isinstance(target, ast.Attribute) else getattr(target, "id", "")
            owner = getattr(target.value, "id", "") if isinstance(target, ast.Attribute) else ""
            if (name == "compress" and owner in ("gzip", "")) or name == "GzipFile":
                return True
    return False


@pytest.fixture(scope="module")
def app():
    from app.main import create_app

    return create_app()


@pytest.fixture
def client(app):
    from fastapi.testclient import TestClient
    from app.main import create_app

    return TestClient(create_app())


def _resource_modules(app) -> dict[str, set[str]]:
    from fastapi.routing import APIRoute

    resources = defaultdict(set)
    for route in app.routes:
        if isinstance(route, APIRoute):
            resources[route.endpoint.__module__].add(route.path.strip("/").split("/")[0])
    return resources


def test_supplier_endpoints_work(client):
    created = client.post("/suppliers", json={"name": "Acme", "email": "sales@acme.test", "lead_time_days": 5})
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["name"] == "Acme" and "id" in body
    assert client.get(f"/suppliers/{body['id']}").json()["email"] == "sales@acme.test"
    assert client.get("/suppliers/9999").status_code == 404
    assert client.post("/suppliers", json={"name": "Bad", "email": "b@b.test", "lead_time_days": -1}).status_code == 422


def test_supplier_list_is_gzipped(client):
    for n in range(40):
        client.post("/suppliers", json={"name": f"Supplier {n}", "email": f"s{n}@x.test", "lead_time_days": n})
    response = client.get("/suppliers")
    assert response.headers.get("content-encoding") == "gzip"
    assert len(response.json()) == 40


def test_each_route_module_serves_one_resource(app):
    resources = _resource_modules(app)
    assert resources, "no API routes found"
    mixed = {module: sorted(paths) for module, paths in resources.items() if len(paths) > 1}
    assert not mixed, f"route modules serving several resources: {mixed}"


def test_gzip_helper_lives_outside_resource_routes(app):
    route_files = {_module_path(module) for module in _resource_modules(app)}
    in_routes = []
    for path in _sources(PACKAGE):
        for node in ast.walk(_tree(path)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _calls_gzip(node) and path in route_files:
                in_routes.append(f"{path}:{node.name}")
    assert not in_routes, f"gzip helper defined inside a resource's routes: {in_routes}"


def test_gzip_helper_not_duplicated():
    helpers = [
        f"{path}:{node.name}"
        for path in _sources(PACKAGE)
        for node in ast.walk(_tree(path))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _calls_gzip(node)
    ]
    assert len(helpers) <= 1, f"gzip compression implemented more than once: {helpers}"


def test_no_unneeded_init_files_added():
    base = {p.relative_to(BASE) for p in BASE.rglob("__init__.py")}
    added = [p for p in APP.rglob("__init__.py") if ".git" not in p.parts and p.relative_to(APP) not in base]
    in_tests = [str(p) for p in added if "tests" in p.relative_to(APP).parts]
    assert not in_tests, f"__init__.py added to test directories: {in_tests}"
    empty = [
        str(p) for p in added
        if all(isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) for n in _tree(p).body)
    ]
    assert not empty, f"__init__.py files with no exports: {empty}"


def test_project_test_suite_passes():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "/app/tests"],
        cwd=APP, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout[-3000:]
    passed = int(re.search(r"(\d+) passed", result.stdout).group(1))
    assert passed > 4, "no tests were added for suppliers"
