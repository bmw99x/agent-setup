"""Draw the domain map panel: the domain's concepts as a grid of boxes, joined by labelled relationships.

Usage:
    python3 -I domain_map.py spec.json domain.svg

Spec (a library lending domain as the example):
{
  "title": "A loan is where a member meets a copy",      # the finding, not the topic
  "contexts": {                                          # one colour per bounded context, in legend order
    "members": {"label": "Membership", "colour": "accent"},
    "catalogue": {"label": "Catalogue", "colour": "caller"},
    "lending": {"label": "Lending", "colour": "callee"}
  },
  "core": "loan",                                        # the one concept the domain turns on: drawn solid
  "boxes": [                                             # col 0-2, row 0..n; name in the domain's own words
    {"id": "member", "col": 0, "row": 0, "context": "members", "name": "Member",
     "lines": ["Card number · branch", "Borrowing limit"]},
    {"id": "loan", "col": 1, "row": 0, "context": "lending", "name": "Loan",
     "lines": ["Due date · renewals"]},
    {"id": "copy", "col": 2, "row": 0, "context": "catalogue", "name": "Copy",
     "lines": ["Barcode · shelf mark"]}
  ],
  "edges": [                                             # a verb phrase read from "from" to "to"
    {"from": "member", "to": "loan", "label": "borrows"},
    {"from": "loan", "to": "copy", "label": "lends"}
  ]
}

Colours are page tokens: "accent", "caller" or "callee" (each with its -soft fill), so both themes work.
A relationship between neighbours in a column or row is a straight line; any other runs corner to corner, so lay
the grid out so most relationships are neighbours. Each edge takes the colour of the context it starts in.
"""

import json
import sys
from html import escape
from pathlib import Path

WIDTH, BOX_W, BOX_H = 900, 240, 80
COL_X = [20, 330, 640]
TOP, ROW_STEP = 64, 140
NAME_SIZE, LINE_STEP = 13.5, 16


def box_x(box: dict) -> float:
    return COL_X[box["col"]]


def box_y(box: dict) -> float:
    return TOP + box["row"] * ROW_STEP


def colour_of(spec: dict, box: dict) -> str:
    return f'var(--{spec["contexts"][box["context"]]["colour"]})'


def edge_geometry(a: dict, b: dict) -> tuple[str, float, float, str]:
    """The path from box a to box b, and where its label goes (x, y, anchor)."""
    ax, ay, bx, by = box_x(a), box_y(a), box_x(b), box_y(b)
    if a["col"] == b["col"]:
        x = ax + BOX_W / 2
        start, end = (ay + BOX_H, by) if ay < by else (ay, by + BOX_H)
        return f"M{x} {start}V{end}", x + 8, (start + end) / 2 + 4, "start"
    if a["row"] == b["row"]:
        y = ay + BOX_H / 2
        start, end = (ax + BOX_W, bx) if ax < bx else (ax, bx + BOX_W)
        return f"M{start} {y}H{end}", (start + end) / 2, y - 7, "middle"
    # corner to corner: leave from the side facing b, inset so the line clears the neighbouring boxes
    sx = ax + BOX_W - 40 if bx > ax else ax + 40
    ex = bx + 40 if bx > ax else bx + BOX_W - 40
    sy, ey = (ay + BOX_H, by) if by > ay else (ay, by + BOX_H)
    return f"M{sx} {sy}L{ex} {ey}", (sx + ex) / 2, (sy + ey) / 2 - 6, "middle"


def draw(spec: dict) -> str:
    boxes = {box["id"]: box for box in spec["boxes"]}
    rows = max(box["row"] for box in spec["boxes"]) + 1
    height = TOP + rows * ROW_STEP - (ROW_STEP - BOX_H) + 24
    out = [
        f'<svg viewBox="0 0 {WIDTH} {height}" role="img" aria-label="{escape(spec["title"])}" font-size="11.5">',
        '<defs><marker id="dm-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" '
        'orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="var(--axis)"></path></marker></defs>',
        f'<text x="20" y="30" font-size="15" font-weight="600" fill="var(--ink)">{escape(spec["title"])}</text>',
    ]
    legend_x = 20
    for context in spec["contexts"].values():
        colour = context["colour"]
        out.append(
            f'<rect x="{legend_x}" y="42" width="12" height="12" rx="2" fill="var(--{colour}-soft)" '
            f'stroke="var(--{colour})"></rect><text x="{legend_x + 18}" y="52" fill="var(--muted)">'
            f'{escape(context["label"])}</text>'
        )
        legend_x += 150
    edges = []
    for edge in spec["edges"]:
        a, b = boxes[edge["from"]], boxes[edge["to"]]
        edges.append((*edge_geometry(a, b), edge["label"], colour_of(spec, a)))
    for path, *_, colour in edges:
        out.append(
            f'<path d="{path}" fill="none" stroke="{colour}" stroke-width="1.5" stroke-dasharray="6 5" '
            'marker-end="url(#dm-arrow)"></path>'
        )
    for _, x, y, anchor, label, colour in edges:
        out.append(
            f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{colour}" paint-order="stroke" '
            f'stroke="var(--panel)" stroke-width="4" stroke-linejoin="round">{escape(label)}</text>'
        )
    for box in spec["boxes"]:
        x, y, colour = box_x(box), box_y(box), colour_of(spec, box)
        if box["id"] == spec.get("core"):
            out.append(f'<rect x="{x}" y="{y}" width="{BOX_W}" height="{BOX_H}" fill="{colour}"></rect>')
            name_fill = line_fill = "var(--panel)"
        else:
            soft = f'var(--{spec["contexts"][box["context"]]["colour"]}-soft)'
            out.append(
                f'<rect x="{x}" y="{y}" width="{BOX_W}" height="{BOX_H}" fill="{soft}" stroke="{colour}" '
                'stroke-width="1.25"></rect>'
            )
            name_fill, line_fill = colour, "var(--muted)"
        centre = x + BOX_W / 2
        out.append(
            f'<text x="{centre}" y="{y + 28}" text-anchor="middle" font-size="{NAME_SIZE}" font-weight="600" '
            f'letter-spacing=".04em" fill="{name_fill}">{escape(box["name"].upper())}</text>'
        )
        for i, line in enumerate(box.get("lines", [])[:2]):
            out.append(
                f'<text x="{centre}" y="{y + 48 + i * LINE_STEP}" text-anchor="middle" fill="{line_fill}">'
                f"{escape(line)}</text>"
            )
    out.append("</svg>")
    return "".join(out)


def main() -> None:
    spec_path, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    spec = json.loads(spec_path.read_text())
    unknown = {e["from"] for e in spec["edges"]} | {e["to"] for e in spec["edges"]}
    unknown -= {box["id"] for box in spec["boxes"]}
    if unknown:
        raise SystemExit(f"edges name unknown boxes: {sorted(unknown)}")
    out_path.write_text(draw(spec))
    print(f"{out_path}: {len(spec['boxes'])} concepts, {len(spec['edges'])} relationships")


if __name__ == "__main__":
    main()
