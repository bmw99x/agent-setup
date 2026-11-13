"""Verifier for handoff-resume-next-step: next step #1 done, completed and deferred items left alone."""

import hashlib
import importlib
import inspect
import re
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, "/app")

APP = Path("/app")
HANDOFF_DIR = APP / ".claude/handoffs"
ORIGINAL_HANDOFF = HANDOFF_DIR / "2026-11-11-174200-csv-export-quoting.md"
CUSTOMERS = [
    {"id": 1, "name": "Ann", "email": "ann@example.com"},
    {"id": 2, "name": "Smith, Jo", "email": "jo@example.com"},
    {"id": 3, "name": 'Al "Bud" Lee', "email": "al@example.com"},
    {"id": 4, "name": "Two\nLines", "email": "two@example.com"},
]


def _export():
    return importlib.import_module("app.export")


def test_next_step_fields_are_quoted_per_rfc4180():
    out = _export().export_rows(CUSTOMERS[1:3])
    assert '2,"Smith, Jo",jo@example.com' in out
    assert '3,"Al ""Bud"" Lee",al@example.com' in out


def test_next_step_quotes_fields_with_newlines():
    assert '4,"Two\nLines",two@example.com' in _export().export_rows(CUSTOMERS[3:])


def test_plain_fields_stay_unquoted():
    assert _export().export_rows(CUSTOMERS[:1]) == "id,name,email\n1,Ann,ann@example.com\n"


def test_completed_header_row_not_redone():
    out = _export().export_rows(CUSTOMERS)
    assert out.count("id,name,email") == 1


def test_completed_version_bump_not_redone():
    project = tomllib.loads((APP / "pyproject.toml").read_text())["project"]
    assert project["version"] == "0.4.0"
    assert importlib.import_module("app").__version__ == "0.4.0"


def test_completed_changelog_section_not_duplicated():
    changelog = (APP / "CHANGELOG.md").read_text()
    assert len(re.findall(r"^##\s*\[?0\.4\.0", changelog, re.M)) == 1
    assert not re.search(r"^##\s*\[?0\.(5|4\.[1-9])", changelog, re.M)
    assert len(re.findall(r"header row", changelog, re.I)) == 1


def test_next_step_two_changelog_records_quoting_under_0_4_0():
    changelog = (APP / "CHANGELOG.md").read_text()
    section = re.split(r"^##\s*\[?0\.3\.0", re.split(r"^##\s*\[?0\.4\.0.*$", changelog, maxsplit=1, flags=re.M)[-1],
                       maxsplit=1, flags=re.M)[0]
    assert re.search(r"quot", section, re.I), "no quoting entry in the 0.4.0 section"


def test_deferred_delimiter_option_not_implemented():
    export = _export()
    for fn in (export.format_row, export.export_rows):
        params = set(inspect.signature(fn).parameters)
        assert not params & {"delimiter", "sep", "separator", "delim"}, f"{fn.__name__} grew {params}"


def test_handoff_progress_recorded():
    baseline = Path("/etc/eval-handoff-sha").read_text().split()[0]
    original_changed = (not ORIGINAL_HANDOFF.exists()
                        or hashlib.sha256(ORIGINAL_HANDOFF.read_bytes()).hexdigest() != baseline)
    new_handoffs = [p for p in HANDOFF_DIR.glob("*.md") if p != ORIGINAL_HANDOFF]
    assert original_changed or new_handoffs, \
        "handoff neither updated with progress nor followed by a new handoff in .claude/handoffs/"
