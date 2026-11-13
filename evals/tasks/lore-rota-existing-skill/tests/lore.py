"""Shared helpers for the lore-generate verifiers: find the generated skill, split its Markdown
into rule-sized items, and check frontmatter, mantra, checklist and global-skill writes."""

import os
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

APP = Path("/app")
SKILLS = APP / ".claude" / "skills"
NEGATION = re.compile(
    r"\bnot?\b|n't|\bnever\b|\bavoid|\bdon.?t\b|\binstead\b|one.?off|\bexception\b|\blegacy\b|contradict|reject|"
    r"\bstop\b|\bunless\b|rather than|\bdrop|\bremov|\breplac|\bbanned\b|\bforbid|anti.?pattern|red herring|"
    r"out of date|outdated|stale|\bwrong\b|\bdo not\b|\bwithout\b|\bnone\b|\bdeprecat|\bunpick|tolerated|"
    r"\bisn.?t\b|\bwas\b.*\bnow\b|superseded|\bold\b|\bdrift|free of|\bfewer\b|\bdelete",
    re.I,
)
LIST_ITEM = re.compile(r"^\s*([-*+]|\d+[.)])\s+")
HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*)$")
SKIP_WALK = ("/proc", "/sys", "/dev", "/app", "/opt/claude-plugins")


@dataclass
class Item:
    text: str
    heading: str
    file: Path


def skill_dir(repo: str) -> Path:
    """The generated conventions skill: /app/.claude/skills/<repo>-conventions/ (an `app-` prefix is tolerated)."""
    found = [d for d in SKILLS.glob("*-conventions") if (d / "SKILL.md").is_file()] if SKILLS.is_dir() else []
    named = [d for d in found if repo in d.name or d.name == "app-conventions"]
    assert named, f"no {repo}-conventions/SKILL.md under {SKILLS} (found: {[d.name for d in found]})"
    return named[0]


def md_files(d: Path) -> list[Path]:
    return sorted(d.rglob("*.md"))


def body(path: Path) -> str:
    text = path.read_text()
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            return parts[2]
    return text


def items(path: Path) -> list[Item]:
    """Split Markdown into rule-sized units: list items (with continuation lines), table rows, paragraphs."""
    out, cur, heading, in_code = [], [], "", False

    def flush():
        if cur:
            out.append(Item(" ".join(s.strip() for s in cur), heading, path))
            cur.clear()

    for line in body(path).splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            flush()
            continue
        if in_code:
            cur.append(line)
            continue
        if m := HEADING.match(line):
            flush()
            heading = m.group(2)
            out.append(Item(m.group(2), heading, path))
            continue
        if not line.strip():
            flush()
        elif line.lstrip().startswith("|"):
            flush()
            out.append(Item(line.strip(), heading, path))
        elif LIST_ITEM.match(line):
            flush()
            cur.append(line)
        else:
            cur.append(line)
    flush()
    return out


def all_items(d: Path) -> list[Item]:
    return [i for p in md_files(d) for i in items(p)]


def matches(text: str, groups: list[str]) -> bool:
    return all(re.search(g, text, re.I) for g in groups)


def find(its: list[Item], groups: list[str]) -> list[Item]:
    return [i for i in its if matches(i.text, groups)]


def affirmed_as_rule(its: list[Item], pattern: str) -> list[str]:
    """Items naming *pattern* with no negation or caveat anywhere in them."""
    bad = []
    for i in its:
        if i.text.rstrip().endswith("?") or i.text.lstrip().startswith("|"):
            continue  # audit-checklist questions and glossary/synonym rows name the term to ban it
        if re.search(pattern, i.text, re.I):
            rest = re.sub(pattern, " ", i.text, flags=re.I)
            if not NEGATION.search(rest) and not NEGATION.search(i.heading):
                bad.append(i.text)
    return bad


def frontmatter(path: Path) -> dict:
    text = path.read_text()
    m = re.match(r"\A---\s*\n(.*?)\n---\s*(\n|\Z)", text, re.S)
    assert m, f"{path} does not open with a --- frontmatter block"
    meta = yaml.safe_load(m.group(1))
    assert isinstance(meta, dict), "frontmatter is not a mapping"
    return meta


def mantra_candidates(d: Path) -> list[str]:
    """Texts labelled as the mantra: after the label on the same line, or the next non-empty line."""
    out = []
    for p in md_files(d):
        lines = body(p).splitlines()
        for n, line in enumerate(lines):
            m = re.search(r"mantra", line, re.I)
            if not m:
                continue
            rest = re.sub(r"^[\s*_:)\]\-–—]+", "", line[m.end():])
            nxt = next((l for l in lines[n + 1:] if l.strip()), "")
            for cand in (rest, nxt):
                cand = re.sub(r"^[\s>*_\"'“`|-]+|[\s*_\"'”`|]+$", "", cand)
                if len(re.findall(r"[A-Za-z]+", cand)) >= 3:
                    out.append(cand)
    return out


def h2_sections(path: Path) -> list[tuple[str, str]]:
    out, cur, text = [], None, []
    in_code = False
    for line in body(path).splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
        m = re.match(r"^##\s+(.*)$", line) if not in_code else None
        if m:
            if cur is not None:
                out.append((cur, "\n".join(text)))
            cur, text = m.group(1), []
        elif cur is not None:
            text.append(line)
    if cur is not None:
        out.append((cur, "\n".join(text)))
    return out


def new_skill_files_outside_app() -> list[str]:
    """SKILL.md files anywhere outside /app (and the harness's plugin dir) that were not there at build."""
    base = set(Path("/etc/eval-base-global-skills").read_text().split())
    now = set()
    for root, dirs, files in os.walk("/"):
        if root.startswith(SKIP_WALK):
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if not os.path.join(root, d).startswith(SKIP_WALK)]
        if "SKILL.md" in files:
            now.add(os.path.join(root, "SKILL.md"))
    return sorted(now - base)
