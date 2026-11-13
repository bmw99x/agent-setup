import ast
import importlib
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, "/app")

LOYALTY = Path("/app/app/loyalty")
SCHEMA = (LOYALTY / "schema.sql").read_text()
MONTH = "2026-10"
# customer id -> points for 2026-10
EXPECTED = {1: 550, 2: 600, 3: 240, 4: 0}


def _seed(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    conn.executemany(
        "INSERT INTO customers (id, name, birth_month) VALUES (?, ?, ?)",
        [(1, "Ada", 10), (2, "Bea", 3), (3, "Cal", 10), (4, "Dee", 1)],
    )
    conn.executemany(
        "INSERT INTO orders (customer_id, total, placed_at) VALUES (?, ?, ?)",
        [
            (1, "100.99", "2026-10-02"),  # birthday month: (100 + 150) x 2 = 500 -> +50
            (1, "150.00", "2026-10-20"),
            (1, "999.00", "2026-09-30"),  # other month
            (2, "300.50", "2026-10-05"),  # 300 + 250 = 550 -> +50
            (2, "250.00", "2026-10-06"),
            (3, "120.00", "2026-10-07"),  # birthday month: 240, below streak threshold
            (4, "80.00", "2026-09-01"),   # nothing this month
        ],
    )
    conn.commit()
    conn.close()


def _ledger(path: Path) -> dict[int, int]:
    conn = sqlite3.connect(path)
    try:
        rows = conn.execute("SELECT customer_id, points FROM points_ledger WHERE month = ?", (MONTH,)).fetchall()
    finally:
        conn.close()
    return dict(rows)


@pytest.fixture
def db(tmp_path, monkeypatch):
    path = tmp_path / "loyalty.db"
    _seed(path)
    monkeypatch.setenv("LOYALTY_DB", str(path))
    return path


def test_run_awards_points_with_birthday_bonus(db):
    job = importlib.import_module("app.loyalty.job")
    job.run_monthly_award(MONTH)
    assert _ledger(db) == EXPECTED


def test_run_uses_one_connection(db, monkeypatch):
    original = sqlite3.connect
    opened = []

    def counting_connect(*args, **kwargs):
        opened.append(args)
        return original(*args, **kwargs)

    job = importlib.import_module("app.loyalty.job")
    monkeypatch.setattr(sqlite3, "connect", counting_connect)
    for name, module in list(sys.modules.items()):
        if name.startswith("app."):
            for attr, value in list(vars(module).items()):
                if value is original:
                    monkeypatch.setattr(module, attr, counting_connect)
    job.run_monthly_award(MONTH)
    monkeypatch.undo()
    assert len(opened) == 1, f"opened {len(opened)} connections"
    assert _ledger(db) == EXPECTED


def test_command_line_still_works(db):
    result = subprocess.run(
        [sys.executable, "-m", "app.loyalty.job", MONTH],
        cwd="/app", env={**os.environ, "LOYALTY_DB": str(db)}, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert _ledger(db) == EXPECTED


DB_CALLS = {"connect", "execute", "executemany", "executescript", "commit", "fetchall", "fetchone", "cursor"}
RULE_NAMES = {"STREAK_THRESHOLD", "STREAK_BONUS"}


def _does_db_io(func: ast.AST) -> bool:
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute | ast.Name)
        and (node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id) in DB_CALLS
        for node in ast.walk(func)
    )


def _points_rules_in(func: ast.AST) -> list[str]:
    found = []
    for node in ast.walk(func):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult | ast.FloorDiv | ast.Div | ast.Mod):
            found.append(f"line {node.lineno}: arithmetic")
        elif isinstance(node, ast.AugAssign):
            found.append(f"line {node.lineno}: accumulation")
        elif isinstance(node, ast.Name) and node.id in RULE_NAMES:
            found.append(f"line {node.lineno}: {node.id}")
        elif isinstance(node, ast.Compare):
            parts = [node.left, *node.comparators]
            if any(isinstance(p, ast.Constant) and type(p.value) in (int, float) and p.value > 1 for p in parts):
                found.append(f"line {node.lineno}: numeric threshold")
            if any(isinstance(p, ast.Attribute) and "birth_month" in p.attr for p in parts) or any(
                isinstance(p, ast.Name) and "birth_month" in p.id for p in parts
            ):
                found.append(f"line {node.lineno}: birthday check")
    return found


def test_database_code_does_not_apply_points_rules():
    """Functions that talk to SQLite only fetch and persist; the points rules live in code with no DB access."""
    offenders = []
    for path in sorted(LOYALTY.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and _does_db_io(node):
                offenders += [f"{path.name}:{node.name} {hit}" for hit in _points_rules_in(node)]
    assert not offenders, offenders
