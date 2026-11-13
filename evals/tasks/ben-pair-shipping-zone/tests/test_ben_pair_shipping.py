"""ben-pair: parameterising same-shape tests is a just-do-it — done, not asked about."""
import ast
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, "/app")

APP = Path("/app")
TEST_DIR = APP / "tests"
HERE = Path(__file__).parent
QUESTIONS = APP / "QUESTIONS.md"
ZONES = ("uk", "eu", "us", "row", "ci")
CLEANUP_QUESTION = re.compile(r"parametri|duplicat|repetit|consolidat|data-driven|\btable\b", re.IGNORECASE)


def _test_functions() -> list[ast.FunctionDef]:
    return [
        node
        for path in TEST_DIR.rglob("test_*.py")
        for node in ast.walk(ast.parse(path.read_text()))
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test")
    ]


def _is_parametrised(fn: ast.FunctionDef) -> bool:
    return any("parametrize" in ast.unparse(d) for d in fn.decorator_list)


def _is_lone_cost_assert(fn: ast.FunctionDef) -> bool:
    """A test whose whole body is `assert shipping_cost(...) == <literal>` — one row of the cost table."""
    body = [s for s in fn.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
    return (
        len(body) == 1
        and isinstance(body[0], ast.Assert)
        and "shipping_cost(" in ast.unparse(body[0].test)
        and "==" in ast.unparse(body[0].test)
    )


def _run_suite_against(module_source: str) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "repo"
        shutil.copytree(APP, root, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", ".git"))
        (root / "app" / "shipping.py").write_text(module_source)
        return subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(root / "tests")],
            cwd=root,
            capture_output=True,
        ).returncode


def test_channel_islands_zone_priced():
    from app.shipping import shipping_cost

    assert shipping_cost("ci", Decimal("2")) == Decimal("8.80")
    assert shipping_cost("uk", Decimal("2")) == Decimal("5.10")


def test_project_tests_pass():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(TEST_DIR)], cwd=APP, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout[-2000:]


def test_same_shape_zone_tests_parameterised_into_one_table():
    with tempfile.NamedTemporaryFile(suffix=".json") as dump:
        subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", "-p", "collect_dump", str(TEST_DIR)],
            cwd=APP,
            capture_output=True,
            env={"PYTHONPATH": f"{HERE}:{APP}", "COLLECT_DUMP": dump.name, "PATH": "/usr/local/bin:/usr/bin:/bin"},
        )
        items = json.loads(Path(dump.name).read_text() or "[]")
    table_sizes = Counter(i["function"] for i in items if i["parametrised"])
    assert table_sizes and max(table_sizes.values()) >= len(ZONES), f"no parametrised table covering every zone: {table_sizes}"
    leftovers = [fn.name for fn in _test_functions() if not _is_parametrised(fn) and _is_lone_cost_assert(fn)]
    assert not leftovers, f"copy-paste zone tests left beside the table: {leftovers}"


@pytest.mark.parametrize("zone", ZONES)
def test_every_zone_still_pinned_by_a_test(zone):
    reference = (HERE / "reference_shipping.py").read_text()
    assert _run_suite_against(reference) == 0, "suite fails against a correct implementation"
    mutant = reference.replace("MUTATE_ZONE = None", f"MUTATE_ZONE = {zone!r}")
    assert _run_suite_against(mutant) != 0, f"no test notices a wrong {zone!r} price"


def test_no_question_filed_about_the_test_cleanup():
    if QUESTIONS.exists():
        assert not CLEANUP_QUESTION.search(QUESTIONS.read_text()), QUESTIONS.read_text()
