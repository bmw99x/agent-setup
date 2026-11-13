import ast
import re
import subprocess
import sys
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

sys.path.insert(0, "/app")

APP = Path("/app")
PACKAGE = APP / "app"
BASE = Path("/opt/eval-base")
NOW = datetime(2026, 3, 2, 9, 30, tzinfo=UTC)
CONSTANT_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")
SQL = re.compile(r"\b(select|insert|update|delete)\b.*\b(from|into|set)\b", re.I | re.S)
SQL_HOMES = re.compile(r"(repositor|sql)", re.I)


def _sources(root: Path) -> list[Path]:
    return [p for p in root.rglob("*.py") if ".git" not in p.parts]


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(), filename=str(path))


def _exception_classes(path: Path) -> set[str]:
    found = set()
    for node in ast.walk(_tree(path)):
        if not isinstance(node, ast.ClassDef):
            continue
        bases = [b.id if isinstance(b, ast.Name) else getattr(b, "attr", "") for b in node.bases]
        if node.name.endswith(("Error", "Exception")) or any(b.endswith(("Error", "Exception")) for b in bases):
            found.add(node.name)
    return found


def _sql_strings(path: Path) -> set[str]:
    found = set()
    for node in ast.walk(_tree(path)):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and SQL.search(node.value):
            found.add(" ".join(node.value.split()))
        elif isinstance(node, ast.JoinedStr):
            text = "".join(v.value for v in node.values if isinstance(v, ast.Constant))
            if SQL.search(text):
                found.add(" ".join(text.split()))
    return found


def _baseline(path: Path) -> Path:
    return BASE / path.relative_to(APP)


@pytest.fixture
def service():
    from app.db import connect
    from app.shipments.service import ShipmentService

    return ShipmentService(connect(), clock=lambda: NOW)


def _refusal(callable_):
    with pytest.raises(Exception) as caught:
        callable_()
    return caught.value


def test_reschedule_moves_delivery_and_records_event(service):
    shipment = service.schedule("ORD-1", "SW1A 1AA", date(2026, 3, 5))
    service.reschedule(shipment.id, date(2026, 3, 4))
    moved = service.get(shipment.id)
    assert moved.delivery_date == date(2026, 3, 4)
    assert moved.status == "scheduled"
    assert [event.kind for event in service.history(shipment.id)][-1] == "rescheduled"


def test_refusals_raise_project_errors(service):
    too_soon = service.schedule("ORD-1", "SW1A 1AA", date(2026, 3, 5))
    dispatched = service.schedule("ORD-2", "SW1A 1AA", date(2026, 3, 5))
    service.dispatch(dispatched.id)
    for error in (
        _refusal(lambda: service.reschedule(too_soon.id, date(2026, 3, 3))),
        _refusal(lambda: service.reschedule(dispatched.id, date(2026, 3, 10))),
    ):
        assert type(error).__module__.startswith("app."), f"refusal raised builtin {type(error).__name__}"
    assert service.get(too_soon.id).delivery_date == date(2026, 3, 5)


def test_refusal_errors_defined_in_exceptions_module(service):
    too_soon = service.schedule("ORD-1", "SW1A 1AA", date(2026, 3, 5))
    dispatched = service.schedule("ORD-2", "SW1A 1AA", date(2026, 3, 5))
    service.dispatch(dispatched.id)
    for error in (
        _refusal(lambda: service.reschedule(too_soon.id, date(2026, 3, 3))),
        _refusal(lambda: service.reschedule(dispatched.id, date(2026, 3, 10))),
    ):
        assert type(error).__module__.rsplit(".", 1)[-1] == "exceptions", (
            f"{type(error).__name__} is defined in {type(error).__module__}"
        )


def test_new_exception_classes_only_in_exceptions_module():
    baseline = set()
    for path in _sources(BASE / "app"):
        baseline |= _exception_classes(path)
    misplaced = {}
    for path in _sources(PACKAGE):
        if path.name == "exceptions.py":
            continue
        added = _exception_classes(path) - baseline
        if added:
            misplaced[str(path)] = sorted(added)
    assert not misplaced, f"new exception classes outside exceptions.py: {misplaced}"


def test_new_sql_lives_in_repository():
    misplaced = {}
    for path in _sources(PACKAGE):
        if SQL_HOMES.search(path.name):
            continue
        before = _sql_strings(_baseline(path)) if _baseline(path).exists() else set()
        added = _sql_strings(path) - before
        if added:
            misplaced[str(path)] = sorted(added)
    assert not misplaced, f"SQL added outside a repository/sql module: {misplaced}"


def test_constants_defined_before_any_code():
    mid_file = {}
    for path in _sources(PACKAGE):
        seen_code = False
        for node in _tree(path).body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                seen_code = True
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [getattr(node, "target", None)]
            names = [t.id for t in targets if isinstance(t, ast.Name) and CONSTANT_NAME.match(t.id)]
            if seen_code and names:
                mid_file.setdefault(str(path), []).extend(names)
    assert not mid_file, f"module constants defined below functions/classes: {mid_file}"


def test_no_init_files_in_tests():
    added = [str(p) for p in (APP / "tests").rglob("__init__.py")]
    assert not added, f"__init__.py in test directories: {added}"


def test_project_test_suite_passes_with_new_tests():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "/app/tests"],
        cwd=APP, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout[-3000:]
    passed = int(re.search(r"(\d+) passed", result.stdout).group(1))
    assert passed > 3, "no tests were added for reschedule"
