"""Parse a session retrospective written as Markdown into the skill's seven sections."""

import hashlib
import re
from pathlib import Path

SECTIONS = [
    ("hard_nos", r"hard[\s-]*no|never (again|do|to)|\bdon'?ts\b|do not repeat|anti-?patterns?|mistakes? not to repeat"),
    ("changed_mind", r"changed (my|your|our|claude'?s) mind|(user|you) (was|were) right|where i was wrong|i was wrong|corrections?\b|corrected"),
    ("push_back", r"push[\s-]*back|disagree|unresolved|open (items|questions|issues)"),
    ("positive", r"positive|what worked|worked well|keep doing"),
    ("solid", r"\bsolid\b"),
    ("coding", r"coding|craft"),
    ("skills", r"skill"),
]
ORDER = ["hard_nos", "positive", "solid", "coding", "skills", "changed_mind", "push_back"]

NEGATION = re.compile(
    r"\b(not|no|none|never|n't|one[\s-]?off|reject(ed)?|skip(ped)?|exclud(e|ed)|ignore[d]?|drop(ped)?|"
    r"doesn'?t|isn'?t|wasn'?t|don'?t|nothing)\b|n't\b|✗|❌",
    re.IGNORECASE,
)

HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
BOLD_LINE = re.compile(r"^\*\*(.+?)\*\*:?\s*$")


def _classify(title: str) -> str | None:
    t = title.lower()
    for key, pattern in SECTIONS:
        if re.search(pattern, t):
            return key
    return None


def parse(text: str) -> tuple[list[str], dict[str, str]]:
    """Return (section keys in order of first appearance, section key -> body text)."""
    lines = text.splitlines()
    has_h2 = any(re.match(r"^#{2,6}\s", line) for line in lines)
    order: list[str] = []
    bodies: dict[str, list[str]] = {}
    current = None
    for line in lines:
        m = HEADING.match(line.strip())
        title = None
        if m and not (has_h2 and len(m.group(1)) == 1):
            title = m.group(2)
        elif not m:
            b = BOLD_LINE.match(line.strip())
            if b:
                title = b.group(1)
        if title is not None:
            key = _classify(title)
            if key is not None:
                current = key
                if key not in order:
                    order.append(key)
                bodies.setdefault(key, [])
                bodies[key].append(line)
                continue
        if current is not None:
            bodies[current].append(line)
    return order, {k: "\n".join(v) for k, v in bodies.items()}


def section(text: str, key: str) -> str:
    """Body of a section, or the whole document when the section is absent."""
    _, bodies = parse(text)
    return bodies.get(key, text)


def items(body: str) -> list[str]:
    """Split a body into top-level items (bullets, table rows, paragraphs) with their continuation lines."""
    out: list[str] = []
    for line in body.splitlines():
        if not line.strip():
            continue
        indented = line[:1] in (" ", "\t")
        if indented and out:
            out[-1] += "\n" + line
        else:
            out.append(line)
    return out


def norm(text: str) -> str:
    text = text.lower().replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = re.sub(r"[`*_>\"'|]", " ", text)
    return re.sub(r"\s+", " ", text)


def has_all(text: str, groups: list[list[str]]) -> bool:
    """True when every group has at least one regex matching the text."""
    t = text.lower()
    return all(any(re.search(p, t) for p in group) for group in groups)


def quotes_any_window(text: str, utterance: str, size: int = 5) -> bool:
    """True when the text contains any run of `size` consecutive words from the utterance."""
    words = re.findall(r"[a-z0-9.\-]+", norm(utterance))
    hay = " ".join(re.findall(r"[a-z0-9.\-]+", norm(text)))
    return any(" ".join(words[i:i + size]) in hay for i in range(len(words) - size + 1))


def baseline_unchanged() -> list[str]:
    """Paths whose sha256 differs from the build-time baseline (missing files included)."""
    changed = []
    for line in Path("/etc/eval-base-hashes").read_text().splitlines():
        digest, rel = line.split(None, 1)
        p = Path("/app") / rel.strip()
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            changed.append(rel)
    return changed


def new_skill_files() -> list[str]:
    base = set(Path("/etc/eval-base-skill-files").read_text().split())
    now = {str(p) for p in Path("/app").rglob("SKILL.md")}
    claude_now = {str(p) for p in Path("/app/.claude").rglob("*") if p.is_file()}
    hashed = {"/app/" + line.split(None, 1)[1].strip() for line in Path("/etc/eval-base-hashes").read_text().splitlines()}
    return sorted((now - base) | (claude_now - hashed))
