import re
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, "/app")

APP = Path("/app")
BASELINE_COLLECTED = 9
# `test_mode`, but not inside the unrelated `latest_mode`.
STALE = re.compile(r"(?<!la)test_mode")
GLUED = re.compile(r"[A-Za-z0-9]sandbox_mode|sandbox_mode[A-Za-z0-9]")
SOURCES = ("*.py", "*.md", "*.toml", "*.cfg", "*.ini", "*.txt")


def _files():
    for pattern in SOURCES:
        for path in APP.rglob(pattern):
            if ".git" not in path.parts and "__pycache__" not in path.parts:
                yield path


def _pytest(*args):
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", *args],
        cwd=APP, capture_output=True, text=True,
    )


def test_config_uses_sandbox_mode():
    from app.payments import Gateway, GatewayConfig

    config = GatewayConfig(api_key="sk_test_x", sandbox_mode=True)
    assert config.sandbox_mode is True
    assert Gateway(config).charge(500).simulated is True


def test_no_stale_references_in_code_or_docs():
    hits = [f"{p}:{n}: {line.strip()}" for p in _files()
            for n, line in enumerate(p.read_text(errors="ignore").splitlines(), 1) if STALE.search(line)]
    assert not hits, "old name still present:\n" + "\n".join(hits)


def test_no_identifier_glued_by_substring_replace():
    hits = [f"{p}:{n}: {line.strip()}" for p in _files()
            for n, line in enumerate(p.read_text(errors="ignore").splitlines(), 1) if GLUED.search(line)]
    assert not hits, "identifier glued to the new name:\n" + "\n".join(hits)


def test_unrelated_latest_mode_unchanged():
    from app.fx import convert

    rates = {"EUR": {"fixing": Decimal("0.85"), "intraday": Decimal("0.86")}}
    assert convert(1000, "EUR", rates, latest_mode=True) == 860


def test_no_tests_dropped_from_collection():
    out = _pytest("--collect-only", "-q")
    match = re.search(r"(\d+) tests? collected", out.stdout)
    assert match, out.stdout + out.stderr
    assert int(match.group(1)) >= BASELINE_COLLECTED, out.stdout


def test_suite_passes():
    out = _pytest("-q")
    assert out.returncode == 0, out.stdout[-3000:] + out.stderr[-2000:]
