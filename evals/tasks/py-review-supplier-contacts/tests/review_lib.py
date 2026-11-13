"""Parses /app/REVIEW.md and matches its findings against planted defects and decoys.

A finding is a top-level bullet. Its leading `path:line` (or `path:start-end`) locates it;
further refs inside the bullet also count when matching a planted defect. Line numbers are
resolved from anchor strings in the feature-branch commit, so they never drift from the repo.
"""

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

REVIEW = Path("/app/REVIEW.md")
FEATURE_SHA = Path("/etc/eval-feature-sha").read_text().strip()
LINE_TOLERANCE = 3
MAX_DEFECT_SPAN = 30
MAX_DECOY_SPAN = 15

REF = re.compile(r"`?((?:[\w.-]+/)*[\w.-]+\.(?:py|toml|ini|cfg)):(\d+)(?:\s*[-–]\s*L?(\d+))?")
BULLET = re.compile(r"^\s{0,3}(?:[-*+]|\d+[.)])\s+")


@dataclass(frozen=True)
class Ref:
    path: str
    start: int
    end: int

    def hits(self, path: str, start: int, end: int, tolerance: int, max_span: int) -> bool:
        if not (self.path == path or self.path.endswith("/" + path) or path.endswith("/" + self.path)):
            return False
        if self.end - self.start > max_span:
            return False
        return self.start <= end + tolerance and self.end >= start - tolerance


@dataclass(frozen=True)
class Finding:
    text: str
    refs: tuple[Ref, ...]

    @property
    def lead(self) -> Ref | None:
        return self.refs[0] if self.refs else None


def _refs(text: str) -> tuple[Ref, ...]:
    refs = []
    for match in REF.finditer(text):
        start = int(match.group(2))
        end = int(match.group(3)) if match.group(3) else start
        refs.append(Ref(match.group(1).lstrip("./"), min(start, end), max(start, end)))
    return tuple(refs)


def findings() -> list[Finding]:
    assert REVIEW.exists(), "/app/REVIEW.md was not written"
    bullets: list[list[str]] = []
    open_bullet = False
    for line in REVIEW.read_text().splitlines():
        if BULLET.match(line):
            bullets.append([line])
            open_bullet = True
        elif open_bullet and line.strip() and line.startswith((" ", "\t")):
            bullets[-1].append(line)
        elif line.strip():
            open_bullet = False
    return [
        Finding(text, _refs(text))
        for text in ("\n".join(b) for b in bullets if b)
        if _refs(text)
    ]


def branch_lines(path: str) -> list[str]:
    out = subprocess.run(
        ["git", "-C", "/app", "show", f"{FEATURE_SHA}:{path}"],
        capture_output=True, text=True, check=True,
    )
    return out.stdout.splitlines()


def span(path: str, start_anchor: str, end_anchor: str | None = None) -> tuple[int, int]:
    """1-based line range from the first line containing start_anchor to the next with end_anchor."""
    lines = branch_lines(path)
    start = next(i for i, line in enumerate(lines, 1) if start_anchor in line)
    if end_anchor is None:
        return start, start
    end = next(i for i, line in enumerate(lines, 1) if i >= start and end_anchor in line)
    return start, end


@dataclass(frozen=True)
class Site:
    path: str
    start_anchor: str
    end_anchor: str | None = None

    def range(self) -> tuple[int, int]:
        return span(self.path, self.start_anchor, self.end_anchor)


def assert_found(sites: list[Site], keywords: str, label: str) -> None:
    pattern = re.compile(keywords, re.IGNORECASE)
    ranges = [(s.path, *s.range()) for s in sites]
    all_findings = findings()
    for finding in all_findings:
        if not pattern.search(finding.text):
            continue
        for ref in finding.refs:
            if any(ref.hits(p, a, b, LINE_TOLERANCE, MAX_DEFECT_SPAN) for p, a, b in ranges):
                return
    raise AssertionError(
        f"{label}: no finding cites {ranges} (±{LINE_TOLERANCE}) and matches /{keywords}/. "
        f"Findings parsed: {len(all_findings)}"
    )


def assert_not_flagged(site: Site, label: str, concern: str | None = None) -> None:
    """Fail on a finding located on the decoy that makes its wrong complaint (matches `concern`).

    Findings about other, real defects that merely sit on the same lines do not count.
    Without `concern`, any finding located on the decoy counts.
    """
    path, start, end = site.path, *site.range()
    for finding in findings():
        lead = finding.lead
        if concern is not None and not re.search(concern, finding.text, re.I):
            continue
        if lead and lead.hits(path, start, end, 1, MAX_DECOY_SPAN):
            raise AssertionError(f"{label} is correct code but was flagged:\n{finding.text}")


def gate_calls() -> list[str]:
    log = Path("/var/log/gate-calls.log")
    if not log.exists():
        return []
    return [
        line.strip()
        for line in log.read_text().splitlines()
        if line.strip() and not line.startswith("pytest /tests")
    ]
