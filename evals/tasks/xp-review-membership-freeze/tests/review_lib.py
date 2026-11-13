"""Parses /app/REVIEW.md and matches its findings against planted design smells and decoys.

A finding is a top-level bullet. Its leading `path:line` (or `path:start-end`) locates it;
further refs inside the bullet also count when matching a planted smell. Line numbers are
resolved from anchor strings in the feature-branch commit, so they never drift from the repo.

Bullets under a praise heading ("Done well", "Strengths", ...) are not problems, and a bullet
that explicitly leaves code as it is ("fine for now") is a valid review, not a flag.
"""

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

REVIEW = Path("/app/REVIEW.md")
FEATURE_SHA = Path("/etc/eval-feature-sha").read_text().strip()
LINE_TOLERANCE = 3
MAX_DEFECT_SPAN = 60
MAX_DECOY_SPAN = 25

REF = re.compile(r"`?((?:[\w.-]+/)*[\w.-]+\.(?:py|toml|ini|cfg)):(\d+)(?:\s*[-–]\s*L?(\d+))?")
BULLET = re.compile(r"^\s{0,3}(?:[-*+]|\d+[.)])\s+")
HEADING = re.compile(r"^\s{0,3}(?:#{1,6}\s+(.*)|\*\*(.+?)\*\*:?\s*$)")
PRAISE_HEADING = re.compile(
    r"\b(done well|well done|good|strengths?|praise|positives?|likes?|nice|kudos|keep|fine|no action|leave)\b",
    re.I,
)
LEFT_AS_IS = re.compile(
    r"fine (for now|as is|here)|leave (it|this|them|as is)|left as is|no (change|action) (needed|required)|"
    r"not (yet )?worth|wait (for|until) (a |the )?third|second (occurrence|copy|time|strike)|"
    r"acceptable|not a (problem|blocker)|don.?t (extract|refactor|change)",
    re.I,
)


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
    heading: str

    @property
    def lead(self) -> Ref | None:
        return self.refs[0] if self.refs else None

    @property
    def is_problem(self) -> bool:
        return not PRAISE_HEADING.search(self.heading)


def _refs(text: str) -> tuple[Ref, ...]:
    refs = []
    for match in REF.finditer(text):
        start = int(match.group(2))
        end = int(match.group(3)) if match.group(3) else start
        refs.append(Ref(match.group(1).lstrip("./"), min(start, end), max(start, end)))
    return tuple(refs)


def findings() -> list[Finding]:
    assert REVIEW.exists(), "/app/REVIEW.md was not written"
    bullets: list[tuple[str, list[str]]] = []
    heading = ""
    open_bullet = False
    for line in REVIEW.read_text().splitlines():
        heading_match = HEADING.match(line)
        if heading_match and not BULLET.match(line):
            heading = heading_match.group(1) or heading_match.group(2) or ""
            open_bullet = False
        elif BULLET.match(line) and not line.startswith(("    ", "\t")):
            bullets.append((heading, [line]))
            open_bullet = True
        elif open_bullet and line.strip() and line.startswith((" ", "\t")):
            bullets[-1][1].append(line)
        elif line.strip():
            open_bullet = False
    result = []
    for bullet_heading, lines in bullets:
        text = "\n".join(lines)
        refs = _refs(text)
        if refs:
            result.append(Finding(text, refs, bullet_heading))
    return result


def problems() -> list[Finding]:
    return [f for f in findings() if f.is_problem]


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
    pattern = re.compile(keywords, re.IGNORECASE | re.DOTALL)
    ranges = [(s.path, *s.range()) for s in sites]
    all_problems = problems()
    for finding in all_problems:
        if not pattern.search(finding.text):
            continue
        for ref in finding.refs:
            if any(ref.hits(p, a, b, LINE_TOLERANCE, MAX_DEFECT_SPAN) for p, a, b in ranges):
                return
    raise AssertionError(
        f"{label}: no finding cites {ranges} (±{LINE_TOLERANCE}) and matches /{keywords}/. "
        f"Problem findings parsed: {len(all_problems)}"
    )


def assert_not_flagged(site: Site, label: str) -> None:
    path, start, end = site.path, *site.range()
    for finding in problems():
        lead = finding.lead
        if lead and lead.hits(path, start, end, 1, MAX_DECOY_SPAN) and not LEFT_AS_IS.search(finding.text):
            raise AssertionError(f"{label} should not be flagged, but was:\n{finding.text}")
