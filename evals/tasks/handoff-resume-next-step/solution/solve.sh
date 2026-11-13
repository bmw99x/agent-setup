#!/bin/bash
set -e
cd /app
python3 - <<'PY'
from pathlib import Path

export = Path("app/export.py")
export.write_text(export.read_text().replace(
    '''def format_row(values: Sequence[object]) -> str:
    return ",".join(str(value) for value in values)
''',
    '''def _quote(value: object) -> str:
    text = str(value)
    if any(char in text for char in ',"\\n\\r'):
        return '"' + text.replace('"', '""') + '"'
    return text


def format_row(values: Sequence[object]) -> str:
    return ",".join(_quote(value) for value in values)
'''))

changelog = Path("CHANGELOG.md")
changelog.write_text(changelog.read_text().replace(
    "- Export includes a header row (`id,name,email`).\n",
    "- Export includes a header row (`id,name,email`).\n"
    "- Fields containing commas, double quotes or newlines are quoted (RFC 4180).\n"))

handoff = Path(".claude/handoffs/2026-11-11-174200-csv-export-quoting.md")
handoff.write_text(handoff.read_text()
    .replace("1. In `format_row`, quote", "1. [x] DONE: In `format_row`, quote")
    .replace("2. Add a bullet", "2. [x] DONE: Add a bullet"))
PY
python3 -m pytest -q
