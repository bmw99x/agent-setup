"""Loyalty code moved into app/loyalty/, and the OrderPlaced -> award points subscription still fires."""

import ast
import json
import subprocess
import sys
import textwrap
from pathlib import Path

APP = Path("/app")
LOYALTY_NAMES = {"points_for", "LoyaltyAccount", "InsufficientPoints", "LoyaltyRepository", "LoyaltyService", "award_loyalty_points"}


def _run(script):
    """Fresh interpreter per scenario: subscriptions are registered at import time."""
    path = Path("/tmp/eval_scenario.py")
    path.write_text(textwrap.dedent(script))
    proc = subprocess.run([sys.executable, str(path)], cwd=APP, capture_output=True, text=True, timeout=60,
                          env={"PYTHONPATH": str(APP), "PATH": "/usr/local/bin:/usr/bin:/bin"})
    assert proc.returncode == 0, proc.stderr[-3000:]
    return json.loads(proc.stdout.strip().splitlines()[-1])


def _definitions(root, skip=None):
    found = []
    for file in root.rglob("*.py"):
        if skip and skip in file.parents:
            continue
        for node in ast.walk(ast.parse(file.read_text())):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                found.append((file.relative_to(APP), node.name))
    return found


def test_loyalty_package_holds_the_loyalty_code():
    package = APP / "app/loyalty"
    assert (package / "__init__.py").exists(), "app/loyalty is not a package"
    assert _definitions(package), "app/loyalty defines nothing"


def test_no_loyalty_code_left_in_layer_folders():
    leftovers = [d for d in _definitions(APP / "app", skip=APP / "app/loyalty") if d[1] in LOYALTY_NAMES]
    assert not leftovers, f"loyalty code still defined outside app/loyalty: {leftovers}"


def test_placing_an_order_still_awards_loyalty_points():
    result = _run("""
        import json
        from app.main import create_app
        router = create_app()
        status, _ = router.handle("POST", "/orders", {"customerId": 7, "customerEmail": "ada@example.com", "totalCents": 12500})
        assert status == 201, status
        _, body = router.handle("GET", "/customers/7/loyalty")
        print(json.dumps(body))
    """)
    assert result["points"] == 150, f"expected 125 + 25 bonus points after a 125.00 order, got {result}"


def test_placing_an_order_still_emails_a_receipt():
    result = _run("""
        import json
        from app.main import create_app
        from app.adapters.mailer import OUTBOX
        router = create_app()
        router.handle("POST", "/orders", {"customerId": 7, "customerEmail": "ada@example.com", "totalCents": 2500})
        print(json.dumps([m["to"] for m in OUTBOX]))
    """)
    assert result == ["ada@example.com"], result


def test_loyalty_endpoints_still_work():
    result = _run("""
        import json
        from app.main import create_app
        from app.db import current_connection
        router = create_app()
        current_connection().execute("INSERT INTO loyalty_accounts (customer_id, points) VALUES (9, 500)")
        _, before = router.handle("GET", "/customers/9/loyalty")
        redeemed = router.handle("POST", "/customers/9/loyalty/redemptions", {"points": 200})
        too_many = router.handle("POST", "/customers/9/loyalty/redemptions", {"points": 1000})
        print(json.dumps([before["points"], redeemed[0], redeemed[1]["points"], too_many[0]]))
    """)
    assert result == [500, 200, 300, 409], result


def test_project_suite_passes():
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], cwd=APP,
                          capture_output=True, text=True, timeout=300)
    assert proc.returncode == 0, proc.stdout[-3000:]
