"""Helpers for reading the housekeeping brief and journal the agent wrote."""

import re
from pathlib import Path

ROOT = Path("/app/.claude/housekeeping")
DATED_DIR = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*$")
VAGUE_REOPEN = re.compile(
    r"^\W*$|^(n/?a|none|tbd|later|maybe|unknown)\W*$|revisit|time allows|time permits|when time|if needed|someday|when possible",
    re.IGNORECASE,
)


def new_dirs(existing=()):
    if not ROOT.is_dir():
        return []
    return [d for d in sorted(ROOT.iterdir()) if d.is_dir() and d.name not in existing]


def output_dir(existing=()):
    dirs = [d for d in new_dirs(existing) if (d / "brief.md").is_file()]
    assert dirs, f"no new <date>-<slug> directory with brief.md under {ROOT}"
    return dirs[-1]


def read(path):
    return path.read_text(encoding="utf-8")


def word_count(markdown):
    """Words in the brief: cell text counts, table pipes and separator rows don't."""
    words = 0
    for line in markdown.splitlines():
        if re.fullmatch(r"[\s|:\-]*", line):
            continue
        words += sum(1 for token in line.replace("|", " ").split() if re.search(r"\w", token))
    return words


def sections(markdown):
    """Map of lower-cased level-2 heading -> body text."""
    found, current = {}, None
    for line in markdown.splitlines():
        heading = re.match(r"^##\s+(.*?)\s*#*\s*$", line)
        if heading:
            current = heading.group(1).strip().lower()
            found[current] = []
        elif current is not None:
            found[current].append(line)
    return {k: "\n".join(v) for k, v in found.items()}


def section(markdown, *keywords):
    """Body of the first section whose heading contains every keyword (case-insensitive)."""
    for heading, body in sections(markdown).items():
        if all(k in heading for k in keywords):
            return body
    raise AssertionError(f"brief has no section headed with {keywords}; headings: {list(sections(markdown))}")


def table_rows(body):
    rows = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or re.fullmatch(r"[\s|:\-]*", stripped):
            continue
        rows.append([cell.strip() for cell in stripped.strip("|").split("|")])
    return rows


def row_matching(body, pattern):
    """First table row (as cells) or bullet line (as one cell) matching pattern."""
    regex = re.compile(pattern, re.IGNORECASE)
    for row in table_rows(body)[1:]:
        if regex.search(" ".join(row)):
            return row
    for line in body.splitlines():
        if regex.search(line):
            return [line]
    raise AssertionError(f"no row matching {pattern!r} in:\n{body}")


def column(body, row, header_keyword):
    """The cell of row under the header containing header_keyword; last cell when headers don't say."""
    rows = table_rows(body)
    if rows and len(row) > 1:
        for index, header in enumerate(rows[0]):
            if header_keyword in header.lower() and index < len(row):
                return row[index]
    return row[-1]
