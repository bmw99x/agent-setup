# Drawing the SVG panels

Each panel is a bare `<svg viewBox="0 0 760 H" role="img" aria-label="<title words>">`, saved to its own file and
named in the manifest. The page scales it to the column, so author at 760 wide and let height grow downward.

## Tokens and type

Colours come only from the page tokens, so both themes work: words `var(--ink)`, quiet words `var(--muted)`, borders
and arrows `var(--axis)`, lifelines and rules `var(--grid)`, bands `var(--tint)`, the one emphasised element
`var(--accent)` (stroke 2, same colour as fill at `fill-opacity="0.12"`). Every `<text>` sets `fill`.

Title 15/600 at y=30. Box names 13/600. Body lines 11.5. Lines are 16 apart; a box with a name and n lines is
`40 + 16n` tall (name baseline 24 down, first line at 42).

SVG does not wrap. Width a box to its longest line + 24: about 7.4 units a character for a 13/600 name, 6.2 for an
11.5 line. Count before you draw; a line over the border is the most common defect.

One arrowhead marker per colour in `<defs>`:
`<marker id="x-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="var(--axis)"/></marker>`.

## Layout per panel

**C4 context (container level).** Top row: what triggers the system and the external services. Middle: the system
boundary as a dashed rounded rect holding its containers stacked in call order, joined by short vertical arrows. Right:
the main store or downstream service. Bottom row: the stores read, arrows pointing into the boundary (double-headed
for one that is also written). Route a call to an external service as an elbow in the gap between the boundary and
the right column, so it crosses no box.

**Sequence.** Up to 7 participants, centres 100 apart (72 … 672), boxes 92 × 40. Dashed lifelines in `--grid`.
Messages 28 apart, all left-to-right where possible, label 8 right of the sender and 6 above the arrow. A tinted
full-width band titles each command or phase (draw it after the lifelines so it covers them). A dashed frame with a
quiet label marks a loop. The commit point is the one accent arrow.

**Data flow.** Top-down in three rows: sources → processing steps → stores, four columns 180 apart (boxes 164 wide).
Put the stores inside one tinted container labelled with the store and its write path. Each arrow runs straight down
in its column; a step fed by two steps sits between their columns one row lower. A value passed through unchanged
gets a straight arrow down an empty column with a short label. Emphasise the store the flow exists to fill.

## Self-check before building

- Every arrow starts and ends on a box edge and crosses no box and no label.
- Edge labels sit beside their line with a clear gap, never on it.
- Every name, path, count and rule in the drawing is something you read in the code at the pinned commit.
- Escape `<`, `>` and `&` in text; write `{id}` as plain text in raw SVG.
