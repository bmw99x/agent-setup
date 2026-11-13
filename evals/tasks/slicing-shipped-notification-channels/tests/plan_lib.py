"""Parse /app/SLICES.md into slices and classify the files each one touches."""

import re
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path, PurePosixPath

PLAN = Path("/app/SLICES.md")
BASE = Path("/opt/base")

HEADING = re.compile(r"^#{1,4}\s*\**\s*Slice\s+(\d+)\b\s*[:.)\-–—]?\s*(.*)$", re.I)
DEPENDS = re.compile(r"^[\s*_>-]*depends\s+on[\s*_]*:[\s*_]*(.*)$", re.I)
FILES = re.compile(r"^[\s*_>-]*files[\s*_]*:[\s*_]*(.*)$", re.I)
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*)$")
NO_DEPENDENCY = re.compile(r"^\W*(none|nothing|no\b|n/?a\b|-+$|—|–|main\b|default\b|$)", re.I)
SLICE_REF = re.compile(r"(?:slice\s*|#)(\d+)", re.I)
BACKTICKED = re.compile(r"`([^`]+)`")
PATH_LIKE = re.compile(r"^[\w./-]+$")

ENTRY_POINT = re.compile(r"(route|router|endpoint|views?\b|api\b|cli\b|command|handler|job|worker|consumer|subscriber|listener)", re.I)
DOMAIN_LOGIC = re.compile(r"(service|domain|use_?case|logic)", re.I)
MIGRATION = re.compile(r"(^|/)(migrations|alembic)/versions/")
MODEL = re.compile(r"(^|/)models(\.py$|/)")


@dataclass
class Slice:
    number: int
    title: str
    depends_on: set[int] = field(default_factory=set)
    files: list[str] = field(default_factory=list)


def normalise_path(token: str) -> str | None:
    token = token.strip().strip("`'\"").rstrip(":,;.)")
    for prefix in ("/app/", "./"):
        if token.startswith(prefix):
            token = token[len(prefix):]
    if not token or not PATH_LIKE.match(token):
        return None
    if "/" not in token and "." not in token:
        return None
    return token


def paths_in(text: str) -> list[str]:
    ticked = BACKTICKED.findall(text)
    candidates = ticked if ticked else [part for part in re.split(r"[\s,]+", text) if part][:1]
    return [path for path in (normalise_path(candidate) for candidate in candidates) if path]


def parse_dependencies(text: str) -> set[int]:
    if NO_DEPENDENCY.match(text):
        return set()
    referenced = SLICE_REF.findall(text)
    if not referenced:
        referenced = re.findall(r"\b(\d{1,2})\b", text)
    return {int(number) for number in referenced}


@cache
def slices() -> tuple[Slice, ...]:
    assert PLAN.exists(), "/app/SLICES.md was not written"
    parsed: list[Slice] = []
    in_files = False
    for line in PLAN.read_text().splitlines():
        if heading := HEADING.match(line):
            parsed.append(Slice(int(heading.group(1)), heading.group(2).strip()))
            in_files = False
            continue
        if not parsed:
            continue
        current = parsed[-1]
        if line.lstrip().startswith("#"):
            in_files = False
            continue
        if depends := DEPENDS.match(line):
            current.depends_on |= parse_dependencies(depends.group(1))
            in_files = False
            continue
        if files := FILES.match(line):
            current.files += paths_in(files.group(1)) if files.group(1).strip() else []
            in_files = True
            continue
        if in_files:
            if item := LIST_ITEM.match(line):
                current.files += paths_in(item.group(1))
            elif line.strip() and not line.startswith((" ", "\t")):
                in_files = False
    return tuple(parsed)


def by_number() -> dict[int, Slice]:
    return {slice_.number: slice_ for slice_ in slices()}


def depended_upon() -> list[Slice]:
    """Slices at least one other slice waits for (the foundation, in a fan-out)."""
    needed = {number for slice_ in slices() for number in slice_.depends_on}
    return [slice_ for slice_ in slices() if slice_.number in needed]


def leaves() -> list[Slice]:
    """Slices nothing else waits for (the behaviour changes, in a fan-out)."""
    needed = {number for slice_ in slices() for number in slice_.depends_on}
    return [slice_ for slice_ in slices() if slice_.number not in needed]


def is_test(path: str) -> bool:
    name = PurePosixPath(path).name
    return path.startswith("tests/") or "/tests/" in path or name.startswith("test_") or name.endswith("_test.py") or name == "conftest.py"


def is_production(path: str) -> bool:
    return path.endswith(".py") and not is_test(path) and not path.startswith(("docs/", ".http", "http/"))


def is_entry_point(path: str) -> bool:
    return is_production(path) and bool(ENTRY_POINT.search(PurePosixPath(path).stem))


def is_domain_logic(path: str) -> bool:
    return is_production(path) and bool(DOMAIN_LOGIC.search(path))


def is_schema_change(path: str) -> bool:
    return bool(MIGRATION.search(path)) or (is_production(path) and bool(MODEL.search(path)))


def describe(slice_: Slice) -> str:
    return f"Slice {slice_.number} ({slice_.title!r}, depends on {sorted(slice_.depends_on) or 'none'}, files {slice_.files})"
