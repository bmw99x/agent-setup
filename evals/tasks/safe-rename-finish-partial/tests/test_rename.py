import re
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, "/app")

APP = Path("/app")
BASELINE_COLLECTED = 7  # tests collected at HEAD, before the rename started
FRIDAY = date(2026, 3, 6)
# `est_delivery` as its own name; `test_delivery_*` and `latest_delivery` merely contain it.
STALE = re.compile(r"(?<![A-Za-z])est_delivery")
GLUED = re.compile(r"[A-Za-z0-9]delivery_eta|delivery_eta[A-Za-z0-9]")
SOURCES = ("*.py", "*.md", "*.toml", "*.cfg", "*.ini", "*.txt")


def _files():
    for pattern in SOURCES:
        for path in APP.rglob(pattern):
            if ".git" not in path.parts and "__pycache__" not in path.parts:
                yield path


def _grep(regex):
    return [f"{p}:{n}: {line.strip()}" for p in _files()
            for n, line in enumerate(p.read_text(errors="ignore").splitlines(), 1) if regex.search(line)]


def _run(*args):
    return subprocess.run([sys.executable, *args], cwd=APP, capture_output=True, text=True)


def test_new_name_is_the_estimate():
    from app.shipping.eta import delivery_eta

    assert delivery_eta(FRIDAY, "standard") == date(2026, 3, 11)


def test_no_stale_references_in_code_or_docs():
    hits = _grep(STALE)
    assert not hits, "old name still present:\n" + "\n".join(hits)


def test_no_identifier_glued_by_substring_replace():
    hits = _grep(GLUED)
    assert not hits, "identifier glued to the new name:\n" + "\n".join(hits)


def test_unrelated_latest_delivery_keeps_its_name():
    from app.shipping.eta import latest_delivery

    assert latest_delivery(FRIDAY, "standard") == date(2026, 3, 13)


def test_untested_cli_still_runs():
    out = _run("-m", "app.cli", "2026-03-06", "standard", "1.5")
    assert out.returncode == 0, out.stderr[-2000:]
    assert "Wed 11 Mar" in out.stdout


def test_no_tests_dropped_from_collection():
    out = _run("-m", "pytest", "-p", "no:cacheprovider", "--collect-only", "-q")
    match = re.search(r"(\d+) tests? collected", out.stdout)
    assert match, out.stdout + out.stderr
    assert int(match.group(1)) >= BASELINE_COLLECTED, out.stdout


def test_suite_passes():
    out = _run("-m", "pytest", "-p", "no:cacheprovider", "-q")
    assert out.returncode == 0, out.stdout[-3000:] + out.stderr[-2000:]
