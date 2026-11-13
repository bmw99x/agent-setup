import asyncio
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, "/app")
sys.path.insert(0, str(Path(__file__).parent))
from typecheck_support import APP, check_case, run_mypy  # noqa: E402


def test_project_typechecks_strict_without_ignores():
    result = run_mypy("app", "tests")
    assert result.returncode == 0, result.stdout + result.stderr
    silenced = [str(p) for p in (APP / "app").rglob("*.py") if "type: ignore" in p.read_text()]
    assert not silenced, f"type: ignore in {silenced}"


def test_project_tests_pass():
    result = subprocess.run(["python3", "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"],
                            cwd=APP, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def _counting(failures, error):
    calls = []

    async def operation(value):
        calls.append(value)
        if len(calls) <= failures:
            raise error
        return value * 2

    return operation, calls


def test_retry_reruns_transient_failures_then_reraises():
    from app.errors import TransientError
    from app.retry import retry

    operation, calls = _counting(failures=2, error=TransientError("blip"))
    assert asyncio.run(retry(attempts=3)(operation)(21)) == 42
    assert len(calls) == 3

    operation, calls = _counting(failures=5, error=TransientError("down"))
    with pytest.raises(TransientError):
        asyncio.run(retry(attempts=2)(operation)(1))
    assert len(calls) == 2

    operation, calls = _counting(failures=5, error=ValueError("bad"))
    with pytest.raises(ValueError):
        asyncio.run(retry(attempts=3)(operation)(1))
    assert len(calls) == 1


def test_decorated_methods_still_satisfy_protocol_and_keep_types():
    """Probe the shape you will write: decorated methods must still conform to the protocol."""
    check_case("accepted.py")


def test_decorated_call_mistakes_still_rejected():
    """The EXPECT ERROR direction: an Any-typed decorator would pass everything."""
    check_case("rejected.py")
