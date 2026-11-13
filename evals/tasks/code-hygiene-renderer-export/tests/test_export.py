import ast
import importlib
import re
import socket
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, "/app")

APP = Path("/app/app")
DEV_URL = "http://renderer.internal:8080"
LEAKS = ("renderer.internal", "8080", "/render", "Errno", "gaierror", "URLError", "ConnectError",
         "Name or service not known", "name resolution", "Traceback", "UpstreamError", "failed:")


def _is_settings_module(path: Path) -> bool:
    return any(part.startswith(("config", "settings")) for part in path.relative_to(APP).with_suffix("").parts)


def _python_files():
    return [p for p in APP.rglob("*.py") if "__pycache__" not in p.parts]


@pytest.fixture
def client(monkeypatch):
    for name in ("RENDERER_URL", "RENDERER_BASE_URL", "RENDERER_API_URL", "PDF_RENDERER_URL",
                 "RENDERER_SERVICE_URL", "RENDERER_HOST"):
        monkeypatch.setenv(name, DEV_URL)

    def unresolvable(host, *args, **kwargs):
        raise socket.gaierror(-2, f"Name or service not known: {host}")

    monkeypatch.setattr(socket, "getaddrinfo", unresolvable)
    for mod in [m for m in sys.modules if m == "app" or m.startswith("app.")]:
        del sys.modules[mod]
    main = importlib.import_module("app.main")
    return TestClient(main.app, raise_server_exceptions=False)


def test_unreachable_renderer_returns_503(client):
    assert client.post("/reports/r-1/export").status_code == 503


def test_user_facing_error_hides_hosts_and_exception_text(client):
    response = client.post("/reports/r-1/export")
    assert response.status_code == 503
    leaked = [token for token in LEAKS if token.lower() in response.text.lower()]
    assert not leaked, f"error response exposes internals {leaked}: {response.text}"


def test_renderer_url_not_hardcoded_outside_settings():
    offenders = [str(p) for p in _python_files()
                 if not _is_settings_module(p) and "renderer.internal" in p.read_text()]
    assert not offenders, f"renderer host hardcoded in {offenders}"


def test_single_use_timeout_not_hoisted_to_module_constant():
    offenders = []
    for path in _python_files():
        if _is_settings_module(path):
            continue
        for node in ast.parse(path.read_text()).body:
            if isinstance(node, ast.Assign):
                targets, value = node.targets, node.value
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                targets, value = [node.target], node.value
            else:
                continue
            names = [t.id for t in targets if isinstance(t, ast.Name)]
            if not any(re.fullmatch(r"[A-Z][A-Z0-9_]*", n) for n in names):
                continue
            try:
                literal = ast.literal_eval(value)
            except (ValueError, SyntaxError, TypeError):
                continue
            if isinstance(literal, (int, float)) and not isinstance(literal, bool) and literal == 60:
                offenders.append(f"{path}:{node.lineno} {names}")
    assert not offenders, f"single-use timeout hoisted to a module constant: {offenders}"
