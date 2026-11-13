"""Read the visuals an agent produced: the one HTML page, its figures, tabs and embedded call graph."""

import html
import json
import re
from pathlib import Path

VISUALS = Path("/app/visuals")
NOTES = VISUALS / "NOTES.md"

SVG = re.compile(r"<svg\b.*?</svg>", re.S | re.I)
TEXT = re.compile(r"<text\b([^>]*)>(.*?)</text>", re.S | re.I)
Y_ATTR = re.compile(r'\by\s*=\s*"(-?[\d.]+)')
TAG = re.compile(r"<[^>]+>")
MERMAID = re.compile(
    r'<(?:pre|div)[^>]*class="[^"]*\bmermaid\b[^"]*"[^>]*>(.*?)</(?:pre|div)>|```mermaid\s*\n(.*?)```', re.S | re.I
)
GRAPH_START = re.compile(r'\{\s*"(?:nodes|edges)"\s*:')


def html_pages() -> list[Path]:
    return sorted(p for p in VISUALS.rglob("*") if p.suffix.lower() in (".html", ".htm")) if VISUALS.exists() else []


def page() -> str:
    pages = html_pages()
    assert len(pages) == 1, f"expected one HTML page under {VISUALS}, found {[str(p) for p in pages]}"
    return pages[0].read_text(errors="replace")


def notes() -> str:
    assert NOTES.exists(), f"{NOTES} missing"
    return NOTES.read_text(errors="replace")


def plain(fragment: str) -> str:
    return html.unescape(TAG.sub(" ", fragment))


def figures(source: str) -> list[list[tuple[float, str]]]:
    """Each drawn figure (inline SVG or Mermaid block) as its text items, each with a vertical position.

    SVG text sorts by its y attribute (document order breaks ties and covers text without one); Mermaid
    sorts by line order, which is message order in a sequence diagram."""
    found = []
    for svg in SVG.findall(source):
        items = []
        for index, (attrs, inner) in enumerate(TEXT.findall(svg)):
            match = Y_ATTR.search(attrs) or Y_ATTR.search(inner)
            y = float(match.group(1)) if match else float(index)
            items.append((y + index * 1e-6, " ".join(plain(inner).split())))
        if items:
            found.append(items)
    for pre, fenced in MERMAID.findall(source):
        body = html.unescape(pre or fenced)
        found.append([(float(i), line.strip()) for i, line in enumerate(body.splitlines()) if line.strip()])
    return found


def figure_text(figure: list[tuple[float, str]]) -> str:
    return "\n".join(text for _, text in figure)


def first_position(figure: list[tuple[float, str]], pattern: str) -> float | None:
    hits = [y for y, text in figure if re.search(pattern, text, re.I)]
    return min(hits) if hits else None


def tab_labels(source: str) -> list[str]:
    nav = re.search(r"<nav\b.*?</nav>", source, re.S | re.I)
    if nav:
        labels = [plain(a) for a in re.findall(r"<(?:a|button)\b[^>]*>(.*?)</(?:a|button)>", nav.group(0), re.S | re.I)]
        if labels:
            return [" ".join(label.split()) for label in labels]
    tabs = re.findall(r'<(?:a|button)\b[^>]*role="tab"[^>]*>(.*?)</(?:a|button)>', source, re.S | re.I)
    if tabs:
        return [" ".join(plain(t).split()) for t in tabs]
    return [" ".join(plain(h).split()) for h in re.findall(r"<h2\b[^>]*>(.*?)</h2>", source, re.S | re.I)]


def graphs(source: str) -> list[dict]:
    """Every embedded JSON object that carries both `nodes` and `edges` lists."""
    decoder = json.JSONDecoder()
    found = []
    for match in GRAPH_START.finditer(source):
        try:
            value, _ = decoder.raw_decode(source, match.start())
        except ValueError:
            continue
        if isinstance(value, dict) and isinstance(value.get("nodes"), list) and isinstance(value.get("edges"), list):
            found.append(value)
    return found


def graph(source: str) -> dict:
    found = graphs(source)
    assert found, "no embedded call graph (a JSON object with nodes and edges) in the page"
    return max(found, key=lambda g: len(g["nodes"]))


def symbol_key(node_id: str) -> str:
    """`accrual.AccrualService.accrue` -> `AccrualService.accrue`; `cli.cmd_checkout` -> `cmd_checkout`."""
    parts = re.split(r"[.:]+", node_id.strip())
    if len(parts) >= 2 and parts[-2][:1].isupper() and not parts[-1][:1].isupper():
        return f"{parts[-2]}.{parts[-1]}"
    return parts[-1]


def node_ids(g: dict) -> list[str]:
    return [n["id"] if isinstance(n, dict) else str(n) for n in g["nodes"]]


def edge_pairs(g: dict) -> list[tuple[str, str]]:
    pairs = []
    for e in g["edges"]:
        if isinstance(e, dict):
            source, target = e.get("from", e.get("source")), e.get("to", e.get("target"))
        else:
            source, target = e[0], e[1]
        pairs.append((str(source), str(target)))
    return pairs


def transitive_callers(g: dict, target_key: str) -> set[str]:
    incoming: dict[str, set[str]] = {}
    for source, target in edge_pairs(g):
        incoming.setdefault(target, set()).add(source)
    starts = [i for i in node_ids(g) if symbol_key(i) == target_key]
    assert starts, f"{target_key} is not a node in the embedded graph"
    seen, queue = set(starts), list(starts)
    while queue:
        for caller in incoming.get(queue.pop(), ()):
            if caller not in seen:
                seen.add(caller)
                queue.append(caller)
    return {symbol_key(i) for i in seen - set(starts)}


def reaches(g: dict, start_key: str, target_key: str) -> bool:
    outgoing: dict[str, set[str]] = {}
    for source, target in edge_pairs(g):
        outgoing.setdefault(source, set()).add(target)
    seen = [i for i in node_ids(g) if symbol_key(i) == start_key]
    queue = list(seen)
    while queue:
        node = queue.pop()
        if symbol_key(node) == target_key:
            return True
        for callee in outgoing.get(node, ()):
            if callee not in seen:
                seen.append(callee)
                queue.append(callee)
    return False
