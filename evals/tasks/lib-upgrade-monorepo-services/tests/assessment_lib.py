"""Reads the upgrade assessment and matches it against the baseline repo.

Call-site line numbers are resolved from anchor strings in the baseline commit, so they never
drift from the repo. A citation is a doc line naming the file (any path suffix, e.g.
`app/http.py`, `/app/app/http.py`, `http.py`) and the line number (`:9`, `L9`, `line 9`, or a
number in the same table row).
"""

import re
import subprocess
from pathlib import Path

BASE_SHA = Path("/etc/eval-base-sha").read_text().strip()
LINE_TOLERANCE = 1

HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*)$|^\s{0,3}\*\*([^*]+)\*\*:?\s*$")
PATH = re.compile(r"(?:[\w.-]+/)*[\w.-]+\.(?:py|toml|lock)")
IMPACT_HEADING = re.compile(
    r"affect|impact|need\w* (?:\w+ )?(?:edit|change)|call.?sites?|edits? (?:required|needed)|"
    r"required (?:edits|changes)|to (?:edit|change)|break(?:s|ing)? (?:us|our)",
    re.IGNORECASE,
)
NOT_IMPACT_HEADING = re.compile(
    r"\bnot\b|n't|\bno\b|\bsafe\b|unaffected|inapplicable|irrelevant|don.?t|other|remaining", re.IGNORECASE
)
NEGATED = re.compile(
    r"\bnot\b|n't|\bno\b|\bnone\b|unused|never|unaffected|\bsafe\b|n/a|\bzero\b|(?<![\w.])0(?![\w.])|irrelevant|"
    r"inapplicable|nothing|already|without impact|no-op|\bok\b|✅|fine\b",
    re.IGNORECASE,
)


def assessment(path: str) -> str:
    doc = Path(path)
    assert doc.exists(), f"{path} was not written"
    text = doc.read_text()
    assert len(text.split()) >= 30, f"{path} is too short to be an assessment"
    return text


def base_lines(path: str) -> list[str]:
    out = subprocess.run(
        ["git", "-C", "/app", "show", f"{BASE_SHA}:{path}"], capture_output=True, text=True, check=True
    )
    return out.stdout.splitlines()


def line_of(path: str, anchor: str, occurrence: int = 1) -> int:
    hits = [i for i, line in enumerate(base_lines(path), 1) if anchor in line]
    assert len(hits) >= occurrence, f"anchor {anchor!r} not in {path}"
    return hits[occurrence - 1]


def _path_matches(cited: str, path: str) -> bool:
    cited = cited.removeprefix("./")
    return ("/" + path).endswith("/" + cited) or cited.endswith("/" + path)


def _numbers(text: str) -> set[int]:
    return {int(n) for n in re.findall(r"(?<![\w.])L?(\d{1,4})(?![\w.]|\.\d)", text)}


def cites(text: str, path: str, line: int) -> bool:
    """True when some doc line names `path` together with `line` (±LINE_TOLERANCE)."""
    for doc_line in text.splitlines():
        if not any(_path_matches(p, path) for p in PATH.findall(doc_line)):
            continue
        if any(abs(n - line) <= LINE_TOLERANCE for n in _numbers(doc_line)):
            return True
    return False


def sections(text: str) -> list[tuple[str, int, list[str]]]:
    """(heading, level, body lines) for every heading; bold-only lines count as level-6 headings."""
    found: list[tuple[str, int, list[str]]] = [("", 0, [])]
    for line in text.splitlines():
        match = HEADING.match(line)
        if match:
            level = len(match.group(1)) if match.group(1) else 6
            found.append(((match.group(2) or match.group(3)).strip(), level, []))
        else:
            found[-1][2].append(line)
    return found


def section_text(text: str, heading: re.Pattern) -> str | None:
    """Body of the first heading matching `heading`, including its sub-sections."""
    all_sections = sections(text)
    for index, (title, level, body) in enumerate(all_sections):
        if title and heading.search(title):
            parts = [*body]
            for sub_title, sub_level, sub_body in all_sections[index + 1 :]:
                if sub_level <= level:
                    break
                parts += [sub_title, *sub_body]
            return "\n".join(parts)
    return None


def impacting_lines(text: str) -> list[tuple[str, bool]]:
    """(line, under an 'affects us / needs edits' heading) for every non-heading doc line."""
    result = []
    impacting = False
    for line in text.splitlines():
        match = HEADING.match(line)
        if match:
            title = match.group(2) or match.group(3)
            impacting = bool(IMPACT_HEADING.search(title)) and not NOT_IMPACT_HEADING.search(title)
            continue
        result.append((line, impacting))
    return result


def reported_as_impacting(text: str, token: str, repo_paths: list[str]) -> list[str]:
    """Doc lines that present `token` as affecting us: under an impact heading, or next to one of our
    source files, without saying it does not apply."""
    offending = []
    for line, impacting in impacting_lines(text):
        if token not in line or NEGATED.search(line):
            continue
        cites_repo = any(_path_matches(p, rp) for p in PATH.findall(line) for rp in repo_paths)
        if impacting or cites_repo:
            offending.append(line.strip())
    return offending


def file_flagged_for_edits(text: str, path: str) -> list[str]:
    """Doc lines under an impact heading that name `path` without saying it is safe/unaffected."""
    return [
        line.strip()
        for line, impacting in impacting_lines(text)
        if impacting and any(_path_matches(p, path) for p in PATH.findall(line)) and not NEGATED.search(line)
    ]


def repo_untouched(*packages: str) -> None:
    head = subprocess.run(["git", "-C", "/app", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    assert head.stdout.strip() == BASE_SHA, "a commit was made or HEAD moved; the task was to investigate only"
    status = subprocess.run(
        ["git", "-C", "/app", "status", "--porcelain", "--untracked-files=no"],
        capture_output=True, text=True, check=True,
    )
    assert not status.stdout.strip(), f"tracked files changed (upgrade or edits performed):\n{status.stdout}"
