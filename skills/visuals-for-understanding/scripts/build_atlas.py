"""Build the one-page atlas: tabs of diagram panels, the dependency explorer, and an embedded archify walkthrough.

Usage:
    python3 -I build_atlas.py manifest.json out.html

Manifest (paths relative to the manifest):
{
  "title": "Checkout Pipeline Atlas",            # <title>, a name not a sentence
  "heading": "Checkout pipeline atlas",          # visible h1
  "subtitle": "repo <code>branch</code> @ abc1234",  # HTML allowed
  "panels": [                                    # one tab each, in order
    {"id": "context", "label": "C4 context", "lead": "One-sentence point.",
     "svg": "c4.svg", "notes": ["Short note", "..."]},
    {"id": "domain", "label": "Domain map", "lead": "...", "svg": "domain.svg",   # from domain_map.py
     "glossary": [["Loan", "A copy lent to a member until its due date."]]},     # optional: term, meaning
    {"id": "flows", "label": "Key flows", "lead": "...",      # several titled figures in one tab
     "figures": [{"title": "The join", "lead": "...", "svg": "join.svg", "notes": ["..."]}]}
  ],
  "graph": "graph.json",                         # optional: from callgraph.py -> Dependencies tab
  "dependency_lead": "What the explorer covers.",
  "source_url": "https://host/group/repo/-/blob/<sha>/",  # optional: links each symbol to path#Lline
  "default_symbol": "pkg.module.func",           # optional: explorer's first selection
  "archify_html": "walkthrough.html",            # optional: archify output -> Walkthrough tab
  "walkthrough_lead": "Five chapters from trigger to commit."
}
SVG colours should use the page tokens: var(--ink) var(--muted) var(--axis) var(--grid) var(--tint) var(--accent).
"""

import base64
import html
import json
import re
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "atlas.template.html"


def strip_block(page: str, marker: str) -> str:
    return re.sub(rf"<!--{marker}-->.*?<!--/{marker}-->\n?", "", page, flags=re.S)


def keep_block(page: str, marker: str) -> str:
    return page.replace(f"<!--{marker}-->\n", "").replace(f"<!--/{marker}-->\n", "")


def read_svg(base: Path, name: str) -> str:
    svg = (base / name).read_text().strip()
    if not svg.startswith("<svg"):
        raise SystemExit(f"{name}: expected a bare <svg> element")
    return svg


def notes_html(notes: list[str]) -> str:
    return f'  <ul class="notes">{"".join(f"<li>{note}</li>" for note in notes)}</ul>\n' if notes else ""


def glossary_html(terms: list[list[str]]) -> str:
    """The domain map's glossary: one row per term, its meaning in the domain's own words."""
    if not terms:
        return ""
    rows = "".join(f"<tr><td><b>{html.escape(term)}</b></td><td>{html.escape(meaning)}</td></tr>" for term, meaning in terms)
    return (
        '  <h3 class="fig-title">Glossary</h3>\n'
        '  <div class="card" style="max-width:900px"><table><thead><tr><th style="width:24%">Term</th>'
        f"<th>Meaning</th></tr></thead><tbody>{rows}</tbody></table></div>\n"
    )


def figures_html(panel: dict, base: Path) -> str:
    """Several titled figures in one tab, with a contents row that scrolls to each."""
    figures = panel["figures"]
    contents = "".join(
        f'<button type="button" data-goto="f-{panel["id"]}-{i}">{html.escape(f["title"])}</button>'
        for i, f in enumerate(figures)
    )
    body = "".join(
        f'  <h3 class="fig-title" id="f-{panel["id"]}-{i}">{html.escape(f["title"])}</h3>\n'
        + (f'  <p class="fig-lead">{f["lead"]}</p>\n' if f.get("lead") else "")
        + f'  <div class="figure">{read_svg(base, f["svg"])}</div>\n'
        + notes_html(f.get("notes", []))
        for i, f in enumerate(figures)
    )
    return f'  <div class="contents">{contents}</div>\n{body}'


def panel_html(panel: dict, base: Path, first: bool) -> str:
    if "figures" in panel:
        content = figures_html(panel, base)
    else:
        content = (
            f'  <div class="figure">{read_svg(base, panel["svg"])}</div>\n'
            + glossary_html(panel.get("glossary", []))
            + notes_html(panel.get("notes", []))
        )
    return (
        f'<section class="panel" id="p-{panel["id"]}"{"" if first else " hidden"}>\n'
        f'  <p class="lead">{panel["lead"]}</p>\n' + content + "</section>\n"
    )


def main() -> None:
    manifest_path, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    base = manifest_path.parent
    manifest = json.loads(manifest_path.read_text())
    page = TEMPLATE.read_text()
    views = [p["id"] for p in manifest.get("panels", [])]
    nav = [(p["id"], p["label"]) for p in manifest.get("panels", [])]
    panels = "\n".join(
        panel_html(p, base, i == 0) for i, p in enumerate(manifest.get("panels", []))
    )

    if manifest.get("graph"):
        graph = (base / manifest["graph"]).read_text().replace("</", "<\\/")
        page = keep_block(page, "DEP")
        page = (
            page.replace("__GRAPH__", graph)
            .replace("__SOURCE_URL__", json.dumps(manifest.get("source_url", "")))
            .replace("__DEFAULT_SYMBOL__", json.dumps(manifest.get("default_symbol")))
            .replace("__DEP_LEAD__", manifest.get("dependency_lead", ""))
        )
        views.append("dependencies")
        nav.append(("dependencies", "Dependencies"))
    else:
        page = strip_block(page, "DEP")

    if manifest.get("archify_html"):
        encoded = base64.b64encode(
            (base / manifest["archify_html"]).read_bytes()
        ).decode()
        page = keep_block(page, "WALK").replace("__ARCHIFY_B64__", encoded)
        page = page.replace("__WALK_LEAD__", manifest.get("walkthrough_lead", ""))
        views.append("walkthrough")
        nav.append(("walkthrough", "Walkthrough"))
    else:
        page = strip_block(page, "WALK")

    if not views:
        raise SystemExit("manifest has no panels, graph or archify_html")
    if not manifest.get("panels"):
        page = page.replace(f'id="p-{views[0]}" hidden', f'id="p-{views[0]}"', 1)

    page = (
        page.replace("__TITLE__", html.escape(manifest["title"]))
        .replace("__HEADING__", html.escape(manifest.get("heading", manifest["title"])))
        .replace("__SUBTITLE__", manifest.get("subtitle", ""))
        .replace(
            "__NAV__",
            "".join(f'<a href="#{v}">{html.escape(label)}</a>' for v, label in nav),
        )
        .replace("__PANELS__", panels)
        .replace("__VIEWS__", json.dumps(views))
    )
    leftover = sorted(set(re.findall(r"__[A-Z_]+__", page)) - {"__init__"})
    if leftover:
        raise SystemExit(f"unfilled placeholders: {leftover}")
    out_path.write_text(page)
    print(f"{out_path}: {len(page):,} bytes, tabs {views}")


if __name__ == "__main__":
    main()
